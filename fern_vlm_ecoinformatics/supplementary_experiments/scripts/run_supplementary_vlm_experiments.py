#!/usr/bin/env python3
"""Run supplementary VLM experiments with checkpointing."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import os
import random
import re
import time
from collections import Counter
from pathlib import Path

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper_analysis"
SUPP = PAPER / "supplementary_experiments"
RAW_DIR = SUPP / "results" / "raw"
STATE_DIR = SUPP / "state"
TMP_DIR = SUPP / "tmp" / "resized_images"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"
SPECIES = ROOT / "ferns_dataset" / "species_data.json"
TEXT_MASKED = PAPER / "text_masked_dataset" / "manifest.csv"
EXT_MANIFEST = SUPP / "datasets" / "external_validation" / "manifest.csv"
OPEN_MANIFEST = SUPP / "datasets" / "open_set" / "manifest.csv"

ORDER_SEEDS = [20260512, 20260513, 20260514]

PROVIDERS = {
    "gemini": {
        "provider": "google-gemini",
        "label": "Gemini 3.1 Flash Lite",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "models": ["gemini-3.1-flash-lite"],
        "disable_thinking": False,
    },
    "qwen35": {
        "provider": "dashscope-qwen35-flash",
        "label": "Qwen3.5-35B-A3B / qwen3.5-flash",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "models": ["qwen3.5-flash", "qwen3.5-flash-2026-02-23"],
        "disable_thinking": True,
    },
    "qwen397b": {
        "provider": "dashscope-qwen397b",
        "label": "Qwen3.5 Plus / 397B",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "models": ["qwen3.5-397b-a17b", "qwen3.5-plus"],
        "fallback_base_urls": [{
            "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "models": ["qwen3.5-397b-a17b", "qwen3.5-plus"],
        }, {
            "base_url": "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "models": ["qwen3.5-397b-a17b", "qwen3.5-plus"],
        }, {
            "base_url": "https://api-inference.modelscope.cn/v1",
            "api_key_env": "MODELSCOPE_API_KEY",
            "models": ["Qwen/Qwen3.5-397B-A17B"],
        }],
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


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text).strip()).strip("-") or "unknown"


def prepare_image(path: Path, max_side: int) -> Path:
    if max_side <= 0:
        return path
    with Image.open(path) as img:
        w, h = img.size
        longest = max(w, h)
        if longest <= max_side:
            return path
        scale = max_side / longest
        resized = img.convert("RGB").resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
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


def prompt_open_set(families: list[str]) -> str:
    options = "\n".join(f"{i + 1}. {fam}" for i, fam in enumerate(families))
    return f"""你是蕨类植物分类学专家。请判断图片是否属于下面 30 个候选蕨类科之一，或者不属于候选范围。

候选科：
{options}

允许的 decision：
- "in_scope"：图片确实属于上述 30 个候选科之一。
- "none_of_the_above"：图片不是蕨类，或属于候选列表之外的类群。
- "uncertain"：图片证据不足，无法可靠判断。

要求：
- 如果 decision 为 "in_scope"，selected_option 必须严格等于候选科中文名之一。
- 如果 decision 为 "none_of_the_above" 或 "uncertain"，selected_option 填空字符串。
- top3 只在 in_scope 时填写候选科；否则为空数组。
- 不要输出候选外科名作为 selected_option。

只回复 JSON：
{{
  "decision": "in_scope",
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}}
"""


def api_call(provider_cfg: dict, api_key: str, base_url: str, model: str, prompt: str, image_path: Path, args) -> tuple[str, dict]:
    text = prompt
    if provider_cfg["disable_thinking"]:
        text = "/no_think\n不要输出分析过程。只输出一个合法 JSON 对象。\n" + prompt
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": image_to_data_url(image_path, args.max_image_side)}},
            ],
        }],
        "temperature": 0.0,
        "top_p": 0.1,
        "max_tokens": args.max_output_tokens,
    }
    if provider_cfg["disable_thinking"]:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(base_url.rstrip("/") + "/chat/completions", headers=headers, json=payload, timeout=360)
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


def retry_delay_seconds(response, body: str, attempt: int) -> float:
    header = response.headers.get("Retry-After") if response is not None else None
    if header:
        try:
            return min(900.0, max(5.0, float(header) + 5.0))
        except ValueError:
            pass
    match = re.search(r"retry in\s+([0-9.]+)\s*s", body, re.IGNORECASE)
    if match:
        return min(900.0, max(5.0, float(match.group(1)) + 5.0))
    return min(900.0, 20.0 * (attempt + 1))


def robust_call(provider_cfg: dict, api_key: str, prompt: str, image_path: Path, args) -> tuple[str, dict]:
    errors = []
    buckets = [{
        "base_url": provider_cfg["base_url"],
        "api_key": api_key,
        "api_key_env": provider_cfg["api_key_env"],
        "models": provider_cfg["models"],
    }]
    for fallback in provider_cfg.get("fallback_base_urls", []):
        fallback_key = os.getenv(fallback["api_key_env"], "")
        if fallback_key:
            buckets.append({
                "base_url": fallback["base_url"],
                "api_key": fallback_key,
                "api_key_env": fallback["api_key_env"],
                "models": fallback["models"],
            })
    for bucket in buckets:
      for model in bucket["models"]:
        max_attempts = args.max_attempts
        for attempt in range(max_attempts):
            try:
                response, meta = api_call(provider_cfg, bucket["api_key"], bucket["base_url"], model, prompt, image_path, args)
                meta["base_url"] = bucket["base_url"]
                if response.strip():
                    return response, meta
                errors.append(f"{model}: empty response")
            except requests.HTTPError as exc:
                response = getattr(exc, "response", None)
                status = getattr(response, "status_code", None)
                body = getattr(response, "text", "")[:500]
                errors.append(f"{model}: HTTP {status} {body}")
                body_lower = body.lower()
                hard_quota = (
                    "today's quota" in body_lower
                    or "free tier of the model has been exhausted" in body_lower
                    or "allocationquota.freetieronly" in body_lower
                )
                if hard_quota:
                    break
                if status == 400 and "User location is not supported" in body and attempt < max_attempts - 1:
                    time.sleep(60 * (attempt + 1))
                    continue
                if status in {429, 500, 502, 503, 504} and attempt < max_attempts - 1:
                    time.sleep(retry_delay_seconds(response, body, attempt))
                    continue
                break
            except (requests.Timeout, requests.ConnectionError) as exc:
                errors.append(f"{model}: {exc}")
                if attempt < max_attempts - 1:
                    time.sleep(20 * (attempt + 1))
                    continue
                break
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                break
    raise RuntimeError("All models failed: " + " | ".join(errors))


def row_complete(row: dict, experiment_kind: str) -> bool:
    return bool(row.get("success") and not row.get("error"))


def provider_key_from_cfg(provider_cfg: dict) -> str:
    for key, cfg in PROVIDERS.items():
        if cfg["provider"] == provider_cfg["provider"]:
            return key
    return provider_cfg["provider"]


def model_fallbacks(provider_cfg: dict) -> list[dict]:
    buckets = [{
        "base_url": provider_cfg["base_url"],
        "api_key_env": provider_cfg["api_key_env"],
        "models": provider_cfg["models"],
    }]
    for fallback in provider_cfg.get("fallback_base_urls", []):
        buckets.append({
            "base_url": fallback["base_url"],
            "api_key_env": fallback["api_key_env"],
            "models": fallback["models"],
        })
    return buckets


def resume_command(provider_cfg: dict, experiment_kind: str) -> str:
    provider_key = provider_key_from_cfg(provider_cfg)
    env_names = []
    for bucket in model_fallbacks(provider_cfg):
        env = bucket["api_key_env"]
        if env not in env_names:
            env_names.append(env)
    env_prefix = " ".join(f"{env}='<{env}>'" for env in env_names)
    exp = "open" if experiment_kind == "open_set" else experiment_kind
    return (
        f"{env_prefix} python3 paper_analysis/supplementary_experiments/scripts/"
        f"run_supplementary_vlm_experiments.py --experiments {exp} "
        f"--providers {provider_key} --max-output-tokens 900 --max-image-side 1536"
    ).strip()


def write_state(path: Path, name: str, rows: list[dict], samples: list[dict], provider_cfg: dict, status: str, message: str, experiment_kind: str) -> None:
    done = {r.get("sample_id") for r in rows if row_complete(r, experiment_kind)}
    next_sample = next((s for s in samples if s["sample_id"] not in done), None)
    state = {
        "experiment": name,
        "experiment_kind": experiment_kind,
        "provider": provider_cfg["provider"],
        "models": provider_cfg["models"],
        "model_fallbacks": model_fallbacks(provider_cfg),
        "status": status,
        "message": message,
        "completed_count": len(done),
        "total_count": len(samples),
        "next_sample_id": next_sample["sample_id"] if next_sample else None,
        "next_species_id": next_sample.get("species_id") if next_sample else None,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "result_file": str(RAW_DIR / f"{name}.json"),
        "resume_command": resume_command(provider_cfg, experiment_kind),
    }
    save_json(path, state)


def load_order_samples() -> list[dict]:
    rows = read_csv(TEXT_MASKED)
    out = []
    for row in rows:
        out.append({
            "sample_id": row["species_id"],
            "species_id": row["species_id"],
            "image_path": str(ROOT / row["masked_image"]),
            "expected_family": row["family"],
            "expected_family_latin": row["family_latin"],
            "expected_species": row["chinese_name"],
            "expected_species_latin": row["latin_name"],
            "source": "local_text_masked",
        })
    return out


def load_external_samples() -> list[dict]:
    rows = read_csv(EXT_MANIFEST)
    out = []
    for row in rows:
        out.append({
            "sample_id": row["sample_id"],
            "species_id": row["species_id"],
            "image_path": str(ROOT / row["image_path"]),
            "expected_family": row["family"],
            "expected_family_latin": row["family_latin_project"],
            "expected_species": row["taxon_name"],
            "expected_species_latin": row["taxon_name"],
            "source": row["source"],
            "source_record_id": row["source_record_id"],
            "license": row["license"],
            "image_context": row["image_context"],
        })
    return out


def load_open_samples() -> list[dict]:
    rows = read_csv(OPEN_MANIFEST)
    out = []
    for row in rows:
        out.append({
            "sample_id": row["sample_id"],
            "species_id": row["species_id"],
            "image_path": str(ROOT / row["image_path"]),
            "open_set_label": row["open_set_label"],
            "negative_group": row["negative_group"],
            "expected_decision": row["expected_decision"],
            "expected_family": row["family"],
            "expected_family_latin": row["family_latin_project"],
            "expected_species": row["taxon_name"],
            "expected_species_latin": row["taxon_name"],
            "source": row["source"],
            "source_record_id": row["source_record_id"],
            "license": row["license"],
            "image_context": row["image_context"],
        })
    return out


def family_result_row(sample: dict, parsed: dict, response: str, meta: dict, prompt: str, provider_cfg: dict, name: str, elapsed: float, families: list[str]) -> dict:
    selected = normalize_choice(parsed.get("selected_option", ""), families)
    top3 = normalize_list(parsed.get("top3") or parsed.get("top_3"), families)
    usage = meta.get("usage", {})
    tokens = int(usage.get("total_tokens") or estimate_tokens(prompt, response))
    return {
        **sample,
        "predicted_family": selected,
        "top3_family": top3,
        "family_correct": selected == sample.get("expected_family"),
        "family_top3_correct": sample.get("expected_family") in top3,
        "family_confidence": float(parsed.get("confidence", 0) or 0),
        "elapsed_seconds": round(elapsed, 1),
        "success": bool(response),
        "result_level": "family",
        "method": name,
        "provider": provider_cfg["provider"],
        "model": meta.get("model", provider_cfg["models"][0]),
        "base_url": meta.get("base_url", provider_cfg["base_url"]),
        "raw_response": response,
        "reasoning": parsed.get("reasoning", ""),
        "api_usage": usage,
        "estimated_tokens": tokens,
        "error": "",
    }


def open_result_row(sample: dict, parsed: dict, response: str, meta: dict, prompt: str, provider_cfg: dict, name: str, elapsed: float, families: list[str]) -> dict:
    raw_decision = str(parsed.get("decision") or "").strip()
    decision = raw_decision if raw_decision in {"in_scope", "none_of_the_above", "uncertain"} else raw_decision
    selected = normalize_choice(parsed.get("selected_option", ""), families)
    top3 = normalize_list(parsed.get("top3") or parsed.get("top_3"), families)
    if decision in {"none_of_the_above", "uncertain"}:
        selected = "" if selected not in families else selected
        top3 = []
    if not decision and selected in families:
        decision = "in_scope"
    usage = meta.get("usage", {})
    tokens = int(usage.get("total_tokens") or estimate_tokens(prompt, response))
    expected_positive = sample["expected_decision"] == "in_scope"
    negative_correct = (not expected_positive) and decision in {"none_of_the_above", "uncertain"}
    positive_retained = expected_positive and decision == "in_scope"
    return {
        **sample,
        "decision": decision,
        "selected_option": selected,
        "top3_family": top3,
        "predicted_family": selected,
        "family_correct": bool(positive_retained and selected == sample.get("expected_family")),
        "family_top3_correct": bool(positive_retained and sample.get("expected_family") in top3),
        "negative_rejection_correct": bool(negative_correct),
        "positive_retained": bool(positive_retained),
        "false_positive": bool((not expected_positive) and decision == "in_scope"),
        "confidence": float(parsed.get("confidence", 0) or 0),
        "elapsed_seconds": round(elapsed, 1),
        "success": bool(response),
        "result_level": "open_set",
        "method": name,
        "provider": provider_cfg["provider"],
        "model": meta.get("model", provider_cfg["models"][0]),
        "base_url": meta.get("base_url", provider_cfg["base_url"]),
        "raw_response": response,
        "reasoning": parsed.get("reasoning", ""),
        "api_usage": usage,
        "estimated_tokens": tokens,
        "error": "",
    }


def run_family_experiment(provider_key: str, experiment_name: str, samples: list[dict], prompt: str, families: list[str], args, experiment_kind: str) -> None:
    provider_cfg = PROVIDERS[provider_key]
    api_key = args.api_key or os.getenv(provider_cfg["api_key_env"], "")
    if not api_key:
        raise SystemExit(f"Missing API key for {provider_key}; pass --api-key or set {provider_cfg['api_key_env']}.")
    name = f"{provider_cfg['provider']}__{safe_slug(provider_cfg['models'][0])}__{experiment_name}"
    result_path = RAW_DIR / f"{name}.json"
    state_path = STATE_DIR / f"{name}.state.json"
    rows = load_json(result_path) if result_path.exists() and not args.force else []
    done = {r.get("sample_id") for r in rows if row_complete(r, experiment_kind)}
    print(f"\n== {name}: total={len(samples)}, resume_done={len(done)} ==")
    write_state(state_path, name, rows, samples, provider_cfg, "running", "started/resumed", experiment_kind)
    for idx, sample in enumerate(samples, 1):
        if args.max_samples and len(done) >= args.max_samples:
            write_state(state_path, name, rows, samples, provider_cfg, "paused", "max_samples reached", experiment_kind)
            return
        if sample["sample_id"] in done:
            continue
        rows = [r for r in rows if r.get("sample_id") != sample["sample_id"]]
        start = time.time()
        try:
            response, meta = robust_call(provider_cfg, api_key, prompt, Path(sample["image_path"]), args)
            parsed = parse_json_response(response)
            row = family_result_row(sample, parsed, response, meta, prompt, provider_cfg, name, time.time() - start, families)
        except Exception as exc:
            row = {
                **sample,
                "predicted_family": "",
                "top3_family": [],
                "family_correct": False,
                "family_top3_correct": False,
                "elapsed_seconds": round(time.time() - start, 1),
                "success": False,
                "result_level": "family",
                "method": name,
                "provider": provider_cfg["provider"],
                "model": provider_cfg["models"][0],
                "base_url": provider_cfg["base_url"],
                "raw_response": "",
                "api_usage": {},
                "estimated_tokens": estimate_tokens(prompt),
                "error": str(exc),
            }
            rows.append(row)
            save_json(result_path, rows)
            write_state(state_path, name, rows, samples, provider_cfg, "error_saved", str(exc), experiment_kind)
            print(f"[{idx}/{len(samples)}] ERROR saved {sample['sample_id']}: {exc}")
            return
        rows.append(row)
        done.add(sample["sample_id"])
        save_json(result_path, rows)
        write_state(state_path, name, rows, samples, provider_cfg, "running", "sample saved", experiment_kind)
        mark = "OK" if row["family_correct"] else "--"
        print(f"[{idx}/{len(samples)}] {sample['sample_id']} {mark} {sample.get('expected_family')} -> {row['predicted_family']} ({row['elapsed_seconds']}s, model={row['model']})")
        if args.inter_sample_delay > 0:
            time.sleep(args.inter_sample_delay)
    status = "completed" if len(done) == len(samples) else "incomplete"
    write_state(state_path, name, rows, samples, provider_cfg, status, "all samples completed" if status == "completed" else "some samples incomplete", experiment_kind)


def run_open_experiment(provider_key: str, samples: list[dict], prompt: str, families: list[str], args) -> None:
    provider_cfg = PROVIDERS[provider_key]
    api_key = args.api_key or os.getenv(provider_cfg["api_key_env"], "")
    if not api_key:
        raise SystemExit(f"Missing API key for {provider_key}; pass --api-key or set {provider_cfg['api_key_env']}.")
    name = f"{provider_cfg['provider']}__{safe_slug(provider_cfg['models'][0])}__open_set_120"
    result_path = RAW_DIR / f"{name}.json"
    state_path = STATE_DIR / f"{name}.state.json"
    rows = load_json(result_path) if result_path.exists() and not args.force else []
    done = {r.get("sample_id") for r in rows if row_complete(r, "open_set")}
    print(f"\n== {name}: total={len(samples)}, resume_done={len(done)} ==")
    write_state(state_path, name, rows, samples, provider_cfg, "running", "started/resumed", "open_set")
    for idx, sample in enumerate(samples, 1):
        if args.max_samples and len(done) >= args.max_samples:
            write_state(state_path, name, rows, samples, provider_cfg, "paused", "max_samples reached", "open_set")
            return
        if sample["sample_id"] in done:
            continue
        rows = [r for r in rows if r.get("sample_id") != sample["sample_id"]]
        start = time.time()
        try:
            response, meta = robust_call(provider_cfg, api_key, prompt, Path(sample["image_path"]), args)
            parsed = parse_json_response(response)
            row = open_result_row(sample, parsed, response, meta, prompt, provider_cfg, name, time.time() - start, families)
        except Exception as exc:
            row = {
                **sample,
                "decision": "",
                "selected_option": "",
                "top3_family": [],
                "predicted_family": "",
                "family_correct": False,
                "negative_rejection_correct": False,
                "positive_retained": False,
                "false_positive": False,
                "elapsed_seconds": round(time.time() - start, 1),
                "success": False,
                "result_level": "open_set",
                "method": name,
                "provider": provider_cfg["provider"],
                "model": provider_cfg["models"][0],
                "base_url": provider_cfg["base_url"],
                "raw_response": "",
                "api_usage": {},
                "estimated_tokens": estimate_tokens(prompt),
                "error": str(exc),
            }
            rows.append(row)
            save_json(result_path, rows)
            write_state(state_path, name, rows, samples, provider_cfg, "error_saved", str(exc), "open_set")
            print(f"[{idx}/{len(samples)}] ERROR saved {sample['sample_id']}: {exc}")
            return
        rows.append(row)
        done.add(sample["sample_id"])
        save_json(result_path, rows)
        write_state(state_path, name, rows, samples, provider_cfg, "running", "sample saved", "open_set")
        print(f"[{idx}/{len(samples)}] {sample['sample_id']} expected={sample['expected_decision']} decision={row['decision']} selected={row['selected_option']} ({row['elapsed_seconds']}s, model={row['model']})")
        if args.inter_sample_delay > 0:
            time.sleep(args.inter_sample_delay)
    status = "completed" if len(done) == len(samples) else "incomplete"
    write_state(state_path, name, rows, samples, provider_cfg, status, "all samples completed" if status == "completed" else "some samples incomplete", "open_set")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiments", nargs="+", default=["order", "external", "open"], choices=["order", "external", "open"])
    parser.add_argument("--providers", nargs="+", default=["gemini", "qwen35", "qwen397b"], choices=sorted(PROVIDERS))
    parser.add_argument("--api-key", default="", help="override API key for a single-provider run")
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--max-image-side", type=int, default=1536)
    parser.add_argument("--max-attempts", type=int, default=6)
    parser.add_argument("--inter-sample-delay", type=float, default=0.0)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    config = load_json(CONFIG)
    families = config["canonical_families"]
    for provider in args.providers:
        if "order" in args.experiments:
            base_samples = load_order_samples()
            for seed in ORDER_SEEDS:
                shuffled = list(families)
                random.Random(seed).shuffle(shuffled)
                run_family_experiment(provider, f"order_seed_{seed}_direct30_masked60", base_samples, prompt_direct30(shuffled), shuffled, args, "order")
        if "external" in args.experiments:
            run_family_experiment(provider, "external_validation_direct30_90", load_external_samples(), prompt_direct30(families), families, args, "external")
        if "open" in args.experiments:
            run_open_experiment(provider, load_open_samples(), prompt_open_set(families), families, args)


if __name__ == "__main__":
    main()
