#!/usr/bin/env python3
"""Run text-masked ablation experiments on the 60-image subset."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import time
from pathlib import Path

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_analysis"
DATASET_ROOT = PAPER / "text_masked_dataset"
MANIFEST = DATASET_ROOT / "manifest.csv"
CONFIG_PATH = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"
SPECIES_PATH = ROOT / "ferns_dataset" / "species_data.json"
OUT = PAPER / "text_masked_experiments"
RAW_DIR = OUT / "results" / "raw"
STATE_DIR = OUT / "state"
TMP_DIR = OUT / "tmp" / "resized_images"


PROVIDERS = {
    "gemini": {
        "provider": "google-gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "models": ["gemini-3.1-flash-lite"],
        "disable_thinking": False,
    },
    "qwen35": {
        "provider": "dashscope-qwen35-flash",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "models": ["qwen3.5-flash", "qwen3.5-flash-2026-02-23"],
        "disable_thinking": True,
    },
    "qwen397b": {
        "provider": "dashscope-qwen397b",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "models": ["qwen3.5-397b-a17b", "qwen3.5-plus"],
        "disable_thinking": True,
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def safe_slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def prepare_image(path: Path, max_side: int) -> Path:
    if max_side <= 0:
        return path
    with Image.open(path) as img:
        w, h = img.size
        longest = max(w, h)
        if longest <= max_side:
            return path
        scale = max_side / longest
        out_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        resized = img.convert("RGB").resize(out_size, Image.Resampling.LANCZOS)
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        out = TMP_DIR / f"{path.stem}_max{max_side}.jpg"
        resized.save(out, "JPEG", quality=90)
        return out


def image_to_data_url(path: Path, max_side: int) -> str:
    path = prepare_image(path, max_side)
    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def parse_json_response(text: str) -> dict:
    if not text:
        return {}
    clean = text.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    for pattern in [r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*```", r"(\{.*\})"]:
        m = re.search(pattern, clean, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
    return {}


def normalize_choice(value: str, candidates: list[str]) -> str:
    text = str(value or "").strip()
    if text in candidates:
        return text
    text2 = re.sub(r"^\s*\d+\s*[.、．)]\s*", "", text).strip()
    if text2 in candidates:
        return text2
    hits = [c for c in candidates if c and c in text2]
    return hits[0] if len(hits) == 1 else text


def normalize_list(value, candidates: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
    elif isinstance(value, str):
        items = [p.strip() for p in re.split(r"[,，;；、\n]+", value) if p.strip()]
    else:
        return []
    out = []
    for item in items:
        mapped = normalize_choice(item, candidates)
        if mapped in candidates and mapped not in out:
            out.append(mapped)
    return out[:3]


def estimate_tokens(prompt: str, response: str = "") -> int:
    return max(1, int((len(prompt) + len(response)) / 1.5) + 1600)


def prompt_direct30(families: list[str]) -> str:
    options = "\n".join(f"{i + 1}. {fam}" for i, fam in enumerate(families))
    return f"""你是蕨类植物分类学专家。请只根据图片判断该植物属于以下 30 个候选科中的哪一个。

候选科：
{options}

要求：
- selected_option 必须严格等于候选科中文名之一。
- top3 给出最可能的前三个候选科，均必须来自候选列表。
- 不要输出候选外科名。
- 如果证据不足，也选择最可能科，并在 reasoning 中说明不确定原因。

只回复 JSON：
{{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}}
"""


def prompt_taxonomy(config: dict, species_data: list[dict]) -> str:
    families = config["canonical_families"]
    examples = {fam: [] for fam in families}
    latin = {}
    for sp in species_data:
        fam = sp["family"]
        latin.setdefault(fam, sp.get("family_latin", ""))
        if fam in examples and len(examples[fam]) < 2:
            examples[fam].append(sp["chinese_name"])
    lines = []
    for i, fam in enumerate(families, 1):
        group = config.get("l1_groups_by_family", {}).get(fam, "")
        lines.append(f"{i}. {fam} ({latin.get(fam, '')})；类群：{group}；示例：{'、'.join(examples.get(fam, []))}")
    return f"""你是蕨类植物分类学专家。请进行 30 科闭集识别。

标准候选科及简要约束：
{chr(10).join(lines)}

观察重点：生活型、叶片分裂方式、叶片质地、叶柄/根状茎特征、孢子囊群位置和形状。

要求：
- selected_option 必须严格等于上述 30 个中文科名之一。
- top3 必须从上述 30 科中选择。
- 如果关键证据不可见，请说明缺失证据。
- 不要输出候选外科名。

只回复 JSON：
{{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "visible_features": ["可见特征1"],
  "missing_evidence": ["缺失证据1"],
  "reasoning": "简短理由"
}}
"""


def load_samples() -> list[dict]:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    samples = []
    for row in rows:
        samples.append({
            "species_id": row["species_id"],
            "image_path": str(ROOT / row["masked_image"]),
            "expected_family": row["family"],
            "expected_family_latin": row["family_latin"],
            "expected_species": row["chinese_name"],
            "expected_species_latin": row["latin_name"],
            "source_image": row["source_image"],
            "source_type": row["source_type"],
            "masked_area_ratio": float(row["masked_area_ratio"]),
            "text_boxes": int(row["text_boxes"]),
        })
    return samples


def row_is_complete(row: dict) -> bool:
    return bool(row.get("success") and not row.get("error") and str(row.get("predicted_family", "")).strip())


def api_call(base_url: str, api_key: str, model: str, prompt: str, image_path: Path, *, max_tokens: int, max_image_side: int, disable_thinking: bool) -> tuple[str, dict]:
    text = prompt
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": image_to_data_url(image_path, max_image_side)}},
            ],
        }],
        "temperature": 0.0,
        "top_p": 0.1,
        "max_tokens": max_tokens,
    }
    if disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        payload["messages"][0]["content"][0]["text"] = "/no_think\n不要输出分析过程。只输出一个合法 JSON 对象。\n" + prompt
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=360)
    meta = {"status_code": response.status_code, "headers": dict(response.headers), "model": model}
    if response.status_code >= 400:
        meta["error_text"] = response.text[:1200]
        response.raise_for_status()
    data = response.json()
    meta["usage"] = data.get("usage", {})
    content = ""
    if data.get("choices"):
        message = data["choices"][0].get("message", {})
        content = message.get("content") or message.get("reasoning_content") or ""
    return content.strip(), meta


def robust_call(provider_cfg: dict, api_key: str, prompt: str, image_path: Path, args) -> tuple[str, dict]:
    errors = []
    for model in provider_cfg["models"]:
        for attempt in range(3):
            try:
                return api_call(
                    provider_cfg["base_url"],
                    api_key,
                    model,
                    prompt,
                    image_path,
                    max_tokens=args.max_output_tokens,
                    max_image_side=args.max_image_side,
                    disable_thinking=provider_cfg["disable_thinking"],
                )
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                body = getattr(exc.response, "text", "")[:500]
                errors.append(f"{model}: HTTP {status} {body}")
                if status in {429, 500, 502, 503, 504} and attempt < 2:
                    wait = 20 * (attempt + 1)
                    print(f"  transient {status} on {model}, retrying in {wait}s")
                    time.sleep(wait)
                    continue
                break
            except (requests.Timeout, requests.ConnectionError) as exc:
                errors.append(f"{model}: {exc}")
                if attempt < 2:
                    wait = 20 * (attempt + 1)
                    print(f"  transient network issue on {model}, retrying in {wait}s")
                    time.sleep(wait)
                    continue
                break
    raise RuntimeError("All models failed: " + " | ".join(errors))


def write_state(path: Path, name: str, rows: list[dict], samples: list[dict], provider_cfg: dict, status: str, message: str) -> None:
    done = {r.get("species_id") for r in rows if row_is_complete(r)}
    next_sample = next((s for s in samples if s["species_id"] not in done), None)
    state = {
        "experiment": name,
        "provider": provider_cfg["provider"],
        "models": provider_cfg["models"],
        "status": status,
        "message": message,
        "completed_count": len(done),
        "total_count": len(samples),
        "next_species_id": next_sample["species_id"] if next_sample else None,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "result_file": str(RAW_DIR / f"{name}.json"),
    }
    save_json(path, state)


def run_experiment(provider_key: str, task: str, prompt: str, families: list[str], args) -> None:
    provider_cfg = PROVIDERS[provider_key]
    api_key = args.api_key or os.getenv(provider_cfg["api_key_env"], "")
    if not api_key:
        raise SystemExit(f"Missing API key for {provider_key}.")
    samples = load_samples()
    name = f"{provider_cfg['provider']}__{safe_slug(provider_cfg['models'][0])}__{task}_masked60"
    result_path = RAW_DIR / f"{name}.json"
    state_path = STATE_DIR / f"{name}.state.json"
    rows = load_json(result_path) if result_path.exists() and not args.force else []
    done = {r.get("species_id") for r in rows if row_is_complete(r)}
    est = sum(int(r.get("estimated_tokens") or 0) for r in rows)
    print(f"\n== {name}: total={len(samples)}, resume_done={len(done)}, tokens~{est} ==")
    write_state(state_path, name, rows, samples, provider_cfg, "running", "started/resumed")
    for idx, sample in enumerate(samples, 1):
        if sample["species_id"] in done:
            continue
        rows = [r for r in rows if r.get("species_id") != sample["species_id"]]
        start = time.time()
        try:
            response, meta = robust_call(provider_cfg, api_key, prompt, Path(sample["image_path"]), args)
            parsed = parse_json_response(response)
            selected = normalize_choice(parsed.get("selected_option", ""), families)
            top3 = normalize_list(parsed.get("top3") or parsed.get("top_3"), families)
            usage = meta.get("usage", {})
            tokens = int(usage.get("total_tokens") or estimate_tokens(prompt, response))
            row = {
                **sample,
                "predicted_family": selected,
                "top3_family": top3,
                "family_correct": selected == sample["expected_family"],
                "family_top3_correct": sample["expected_family"] in top3,
                "predicted_species": "",
                "top3_species": [],
                "species_correct": False,
                "species_top3_correct": False,
                "family_confidence": float(parsed.get("confidence", 0) or 0),
                "elapsed_seconds": round(time.time() - start, 1),
                "success": bool(response),
                "result_level": "family",
                "method": name,
                "provider": provider_cfg["provider"],
                "model": meta.get("model", provider_cfg["models"][0]),
                "base_url": provider_cfg["base_url"],
                "raw_response": response,
                "reasoning": parsed.get("reasoning", ""),
                "api_usage": usage,
                "estimated_tokens": tokens,
                "error": "",
            }
        except Exception as exc:
            tokens = estimate_tokens(prompt)
            row = {
                **sample,
                "predicted_family": "",
                "top3_family": [],
                "family_correct": False,
                "family_top3_correct": False,
                "predicted_species": "",
                "top3_species": [],
                "species_correct": False,
                "species_top3_correct": False,
                "elapsed_seconds": round(time.time() - start, 1),
                "success": False,
                "result_level": "family",
                "method": name,
                "provider": provider_cfg["provider"],
                "model": provider_cfg["models"][0],
                "base_url": provider_cfg["base_url"],
                "raw_response": "",
                "api_usage": {},
                "estimated_tokens": tokens,
                "error": str(exc),
            }
            rows.append(row)
            save_json(result_path, rows)
            write_state(state_path, name, rows, samples, provider_cfg, "error_saved", str(exc))
            print(f"[{idx}/{len(samples)}] ERROR saved {sample['species_id']}: {exc}")
            return
        rows.append(row)
        save_json(result_path, rows)
        write_state(state_path, name, rows, samples, provider_cfg, "running", "sample saved")
        mark = "OK" if row["family_correct"] else "--"
        print(f"[{idx}/{len(samples)}] {sample['species_id']} {mark} {sample['expected_family']} -> {selected} ({row['elapsed_seconds']}s, tokens~{tokens}, model={row['model']})")

    completed = sum(1 for r in rows if row_is_complete(r))
    status = "completed" if completed == len(samples) else "incomplete"
    write_state(state_path, name, rows, samples, provider_cfg, status, "all samples completed" if status == "completed" else "some samples invalid")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", nargs="+", default=["gemini", "qwen35", "qwen397b"], choices=sorted(PROVIDERS))
    parser.add_argument("--tasks", nargs="+", default=["direct30", "taxonomy"], choices=["direct30", "taxonomy"])
    parser.add_argument("--api-key", default="", help="override API key for a single-provider run")
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--max-image-side", type=int, default=1536)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG_PATH)
    species_data = load_json(SPECIES_PATH)["species"]
    families = config["canonical_families"]
    prompts = {
        "direct30": prompt_direct30(families),
        "taxonomy": prompt_taxonomy(config, species_data),
    }
    task_names = {"direct30": "direct30", "taxonomy": "taxonomy"}
    for provider in args.providers:
        for task in args.tasks:
            run_experiment(provider, task_names[task], prompts[task], families, args)


if __name__ == "__main__":
    main()
