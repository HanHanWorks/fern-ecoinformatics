#!/usr/bin/env python3
"""Analyze text-masked ablation results against the original-image subset."""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_analysis"
OUT = PAPER / "text_masked_experiments"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
DATA = OUT / "data"
MANIFEST = PAPER / "text_masked_dataset" / "manifest.csv"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"


MODEL_SPECS = [
    {
        "model_id": "gemini_3.1_flash_lite",
        "model": "Gemini 3.1 Flash Lite",
        "masked_files": {
            "direct30": OUT / "results/raw/google-gemini__gemini-3.1-flash-lite__direct30_masked60.json",
            "taxonomy": OUT / "results/raw/google-gemini__gemini-3.1-flash-lite__taxonomy_masked60.json",
        },
        "original_files": {
            "direct30": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__direct30_full155.json",
            "taxonomy": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__taxonomy_prompt_full155.json",
        },
    },
    {
        "model_id": "qwen3.5_35b_a3b",
        "model": "Qwen3.5-35B-A3B / qwen3.5-flash",
        "masked_files": {
            "direct30": OUT / "results/raw/dashscope-qwen35-flash__qwen3.5-flash__direct30_masked60.json",
            "taxonomy": OUT / "results/raw/dashscope-qwen35-flash__qwen3.5-flash__taxonomy_masked60.json",
        },
        "original_files": {
            "direct30": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__direct30_full155.json",
            "taxonomy": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__taxonomy_prompt_full155.json",
        },
    },
    {
        "model_id": "qwen3.5_plus_397b",
        "model": "Qwen3.5 Plus / 397B",
        "masked_files": {
            "direct30": OUT / "results/raw/dashscope-qwen397b__qwen3.5-397b-a17b__direct30_masked60.json",
            "taxonomy": OUT / "results/raw/dashscope-qwen397b__qwen3.5-397b-a17b__taxonomy_masked60.json",
        },
        "original_files": {
            "direct30": ROOT / "qwen35_plus_sci2_pipeline/results/raw/dashscope-2026__qwen3.5-plus-2026-02-15__direct30_full155.json",
            "taxonomy": ROOT / "qwen35_plus_sci2_pipeline/results/raw/dashscope-alias__qwen3.5-plus__taxonomy_prompt_full155.json",
        },
    },
]


TASK_LABELS = {
    "direct30": "30-family direct closed-set",
    "taxonomy": "30-family taxonomy prompt",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def binom_two_sided(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    comb = getattr(math, "comb", _comb)
    probs = [comb(n, i) * (0.5**n) for i in range(n + 1)]
    observed = probs[k]
    return min(1.0, sum(p for p in probs if p <= observed + 1e-15))


def _comb(n: int, k: int) -> int:
    k = min(k, n - k)
    if k < 0:
        return 0
    value = 1
    for i in range(1, k + 1):
        value = value * (n - k + i) // i
    return value


def bootstrap_diff_ci(a: list[int], b: list[int], reps: int = 10000, seed: int = 20260511) -> tuple[float, float, float]:
    n = len(a)
    if n == 0:
        return 0.0, 0.0, 0.0
    observed = sum(b) / n - sum(a) / n
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        idxs = [rng.randrange(n) for _ in range(n)]
        values.append((sum(b[i] for i in idxs) - sum(a[i] for i in idxs)) / n)
    values.sort()
    return observed, values[int(0.025 * reps)], values[int(0.975 * reps)]


def load_taxonomy() -> tuple[set[str], dict[str, str]]:
    config = load_json(CONFIG)
    return set(config["canonical_families"]), config.get("aliases", {})


def norm_family(label: str, canonical: set[str], aliases: dict[str, str]) -> tuple[str, bool]:
    raw = str(label or "").strip()
    if raw in aliases:
        mapped = aliases[raw]
        return mapped, mapped in canonical
    if raw in canonical:
        return raw, True
    if not raw:
        return "INVALID_EMPTY", False
    compact = re.sub(r"^\s*\d+\s*[.、．)]\s*", "", raw).strip()
    if compact in canonical:
        return compact, True
    m = re.match(r"^([\u4e00-\u9fff]+科)\s*\([^)]*\)$", compact)
    if m:
        stripped = m.group(1)
        return stripped, stripped in canonical
    hits = [fam for fam in canonical if fam in compact]
    if len(hits) == 1:
        return hits[0], True
    return f"INVALID_OOV::{raw}", False


def normalize_top3(value, canonical: set[str], aliases: dict[str, str]) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        raw_items = [p for p in re.split(r"[,，;；、\n]+", value) if p.strip()]
    else:
        raw_items = []
    out = []
    for item in raw_items:
        mapped, valid = norm_family(str(item), canonical, aliases)
        if valid and mapped not in out:
            out.append(mapped)
    return out[:3]


def row_is_valid(row: dict, pred_valid: bool) -> bool:
    if row.get("error"):
        return False
    if row.get("success") is False:
        return False
    if not str(row.get("predicted_family") or "").strip():
        return False
    return pred_valid


def standardize_row(
    row: dict,
    *,
    model_id: str,
    model: str,
    task: str,
    condition: str,
    manifest_row: dict,
    canonical: set[str],
    aliases: dict[str, str],
) -> dict:
    exp_family, exp_valid = norm_family(row.get("expected_family") or manifest_row["family"], canonical, aliases)
    pred_family, pred_valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
    top3 = normalize_top3(row.get("top3_family", []), canonical, aliases)
    valid_output = row_is_valid(row, pred_valid)
    family_correct = bool(valid_output and exp_valid and pred_valid and exp_family == pred_family)
    family_top3_correct = bool(valid_output and exp_valid and exp_family in top3)
    usage = row.get("api_usage") if isinstance(row.get("api_usage"), dict) else {}
    total_tokens = usage.get("total_tokens") or row.get("estimated_tokens") or 0
    return {
        "model_id": model_id,
        "model": model,
        "task": task,
        "task_label": TASK_LABELS[task],
        "condition": condition,
        "species_id": row.get("species_id") or manifest_row["species_id"],
        "source_type": manifest_row["source_type"],
        "text_presence": "ocr_text_detected" if int(manifest_row["text_boxes"]) > 0 else "no_ocr_text",
        "text_boxes": int(manifest_row["text_boxes"]),
        "masked_area_ratio": float(manifest_row["masked_area_ratio"]),
        "expected_family": manifest_row["family"],
        "expected_family_std": exp_family,
        "predicted_family": row.get("predicted_family", ""),
        "predicted_family_std": pred_family,
        "top3_family_std": ";".join(top3),
        "valid_output": int(valid_output),
        "family_correct": int(family_correct),
        "family_top3_correct": int(family_top3_correct),
        "estimated_tokens": int(total_tokens or 0),
        "elapsed_seconds": float(row.get("elapsed_seconds") or 0),
        "error": row.get("error", ""),
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    family_correct = sum(int(r["family_correct"]) for r in rows)
    top3_correct = sum(int(r["family_top3_correct"]) for r in rows)
    valid_count = sum(int(r["valid_output"]) for r in rows)
    lo, hi = wilson(family_correct, n)
    return {
        "n": n,
        "family_correct": family_correct,
        "family_acc": pct(family_correct / n if n else 0),
        "family_acc_95ci": f"{pct(lo)}-{pct(hi)}",
        "top3_correct": top3_correct,
        "top3_acc": pct(top3_correct / n if n else 0),
        "invalid_count": n - valid_count,
        "invalid_rate": pct((n - valid_count) / n if n else 0),
        "estimated_tokens": sum(int(r["estimated_tokens"]) for r in rows),
        "avg_time_s": f"{sum(float(r['elapsed_seconds']) for r in rows) / n:.1f}" if n else "0.0",
    }


def paired_summary(original_rows: list[dict], masked_rows: list[dict]) -> dict:
    original_by_id = {r["species_id"]: r for r in original_rows}
    masked_by_id = {r["species_id"]: r for r in masked_rows}
    species_ids = sorted(set(original_by_id) & set(masked_by_id))
    a = [int(original_by_id[sid]["family_correct"]) for sid in species_ids]
    b = [int(masked_by_id[sid]["family_correct"]) for sid in species_ids]
    original_only = sum(1 for x, y in zip(a, b) if x == 1 and y == 0)
    masked_only = sum(1 for x, y in zip(a, b) if x == 0 and y == 1)
    both = sum(1 for x, y in zip(a, b) if x == 1 and y == 1)
    neither = sum(1 for x, y in zip(a, b) if x == 0 and y == 0)
    diff, ci_lo, ci_hi = bootstrap_diff_ci(a, b)
    return {
        "paired_n": len(species_ids),
        "original_acc": pct(sum(a) / len(a) if a else 0),
        "masked_acc": pct(sum(b) / len(b) if b else 0),
        "masked_minus_original": pct(diff),
        "bootstrap_diff_95ci": f"{pct(ci_lo)}-{pct(ci_hi)}",
        "both_correct": both,
        "original_only": original_only,
        "masked_only": masked_only,
        "neither_correct": neither,
        "mcnemar_exact_p": f"{binom_two_sided(min(original_only, masked_only), original_only + masked_only):.6f}",
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    canonical, aliases = load_taxonomy()
    manifest_rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    manifest_by_id = {r["species_id"]: r for r in manifest_rows}
    subset_ids = set(manifest_by_id)

    standardized = []
    missing_files = []
    for spec in MODEL_SPECS:
        for task in ["direct30", "taxonomy"]:
            for condition, path in [
                ("original", spec["original_files"][task]),
                ("text_masked", spec["masked_files"][task]),
            ]:
                if not path.exists():
                    missing_files.append(str(path))
                    continue
                data = load_json(path)
                by_id = {r.get("species_id"): r for r in data if r.get("species_id") in subset_ids}
                missing_ids = sorted(subset_ids - set(by_id))
                if missing_ids:
                    raise RuntimeError(f"{path} missing subset samples: {missing_ids}")
                for sid in sorted(subset_ids):
                    standardized.append(
                        standardize_row(
                            by_id[sid],
                            model_id=spec["model_id"],
                            model=spec["model"],
                            task=task,
                            condition=condition,
                            manifest_row=manifest_by_id[sid],
                            canonical=canonical,
                            aliases=aliases,
                        )
                    )
    if missing_files:
        raise RuntimeError("Missing result files:\n" + "\n".join(missing_files))

    (DATA / "text_masked_standardized_predictions.json").write_text(
        json.dumps(standardized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(
        DATA / "text_masked_standardized_predictions.csv",
        standardized,
        [
            "model_id",
            "model",
            "task",
            "task_label",
            "condition",
            "species_id",
            "source_type",
            "text_presence",
            "text_boxes",
            "masked_area_ratio",
            "expected_family",
            "expected_family_std",
            "predicted_family",
            "predicted_family_std",
            "top3_family_std",
            "valid_output",
            "family_correct",
            "family_top3_correct",
            "estimated_tokens",
            "elapsed_seconds",
            "error",
        ],
    )

    by_key = defaultdict(list)
    for row in standardized:
        by_key[(row["model_id"], row["model"], row["task"], row["condition"])].append(row)

    summary_rows = []
    for spec in MODEL_SPECS:
        for task in ["direct30", "taxonomy"]:
            for condition in ["original", "text_masked"]:
                rows = by_key[(spec["model_id"], spec["model"], task, condition)]
                summary_rows.append(
                    {
                        "model_id": spec["model_id"],
                        "model": spec["model"],
                        "task": task,
                        "task_label": TASK_LABELS[task],
                        "condition": condition,
                        **summarize(rows),
                    }
                )
    write_csv(
        TABLES / "masked_ablation_summary.csv",
        summary_rows,
        [
            "model_id",
            "model",
            "task",
            "task_label",
            "condition",
            "n",
            "family_correct",
            "family_acc",
            "family_acc_95ci",
            "top3_correct",
            "top3_acc",
            "invalid_count",
            "invalid_rate",
            "estimated_tokens",
            "avg_time_s",
        ],
    )

    paired_rows = []
    for spec in MODEL_SPECS:
        for task in ["direct30", "taxonomy"]:
            original = by_key[(spec["model_id"], spec["model"], task, "original")]
            masked = by_key[(spec["model_id"], spec["model"], task, "text_masked")]
            paired_rows.append(
                {
                    "model_id": spec["model_id"],
                    "model": spec["model"],
                    "task": task,
                    "task_label": TASK_LABELS[task],
                    **paired_summary(original, masked),
                }
            )
    write_csv(
        TABLES / "masked_vs_original_paired.csv",
        paired_rows,
        [
            "model_id",
            "model",
            "task",
            "task_label",
            "paired_n",
            "original_acc",
            "masked_acc",
            "masked_minus_original",
            "bootstrap_diff_95ci",
            "both_correct",
            "original_only",
            "masked_only",
            "neither_correct",
            "mcnemar_exact_p",
        ],
    )

    source_rows = []
    for spec in MODEL_SPECS:
        for task in ["direct30", "taxonomy"]:
            for source_type in ["cropped_photo", "full_page"]:
                original = [
                    r
                    for r in by_key[(spec["model_id"], spec["model"], task, "original")]
                    if r["source_type"] == source_type
                ]
                masked = [
                    r
                    for r in by_key[(spec["model_id"], spec["model"], task, "text_masked")]
                    if r["source_type"] == source_type
                ]
                source_rows.append(
                    {
                        "model_id": spec["model_id"],
                        "model": spec["model"],
                        "task": task,
                        "task_label": TASK_LABELS[task],
                        "source_type": source_type,
                        **paired_summary(original, masked),
                    }
                )
    write_csv(
        TABLES / "masked_by_source_type.csv",
        source_rows,
        [
            "model_id",
            "model",
            "task",
            "task_label",
            "source_type",
            "paired_n",
            "original_acc",
            "masked_acc",
            "masked_minus_original",
            "bootstrap_diff_95ci",
            "both_correct",
            "original_only",
            "masked_only",
            "neither_correct",
            "mcnemar_exact_p",
        ],
    )

    text_rows = []
    for spec in MODEL_SPECS:
        for task in ["direct30", "taxonomy"]:
            for text_presence in ["no_ocr_text", "ocr_text_detected"]:
                original = [
                    r
                    for r in by_key[(spec["model_id"], spec["model"], task, "original")]
                    if r["text_presence"] == text_presence
                ]
                masked = [
                    r
                    for r in by_key[(spec["model_id"], spec["model"], task, "text_masked")]
                    if r["text_presence"] == text_presence
                ]
                text_rows.append(
                    {
                        "model_id": spec["model_id"],
                        "model": spec["model"],
                        "task": task,
                        "task_label": TASK_LABELS[task],
                        "text_presence": text_presence,
                        **paired_summary(original, masked),
                    }
                )
    write_csv(
        TABLES / "masked_by_text_presence.csv",
        text_rows,
        [
            "model_id",
            "model",
            "task",
            "task_label",
            "text_presence",
            "paired_n",
            "original_acc",
            "masked_acc",
            "masked_minus_original",
            "bootstrap_diff_95ci",
            "both_correct",
            "original_only",
            "masked_only",
            "neither_correct",
            "mcnemar_exact_p",
        ],
    )

    invalid_rows = [
        {
            "model": r["model"],
            "task": r["task"],
            "condition": r["condition"],
            "species_id": r["species_id"],
            "expected_family": r["expected_family"],
            "predicted_family": r["predicted_family"],
            "error": r["error"],
        }
        for r in standardized
        if not int(r["valid_output"])
    ]
    write_csv(
        TABLES / "masked_invalid_outputs.csv",
        invalid_rows,
        ["model", "task", "condition", "species_id", "expected_family", "predicted_family", "error"],
    )

    write_report(manifest_rows, summary_rows, paired_rows, source_rows, text_rows, invalid_rows)


def write_report(
    manifest_rows: list[dict],
    summary_rows: list[dict],
    paired_rows: list[dict],
    source_rows: list[dict],
    text_rows: list[dict],
    invalid_rows: list[dict],
) -> None:
    source_counts = defaultdict(int)
    text_counts = defaultdict(int)
    family_count = len({r["family"] for r in manifest_rows})
    for row in manifest_rows:
        source_counts[row["source_type"]] += 1
        text_counts["ocr_text_detected" if int(row["text_boxes"]) > 0 else "no_ocr_text"] += 1

    total_tokens = sum(r["estimated_tokens"] for r in summary_rows if r["condition"] == "text_masked")
    lines = [
        "# Text-masked 图像补充实验报告",
        "",
        "## 1. 实验完成状态",
        "",
        f"- 数据集：60 张真实蕨类图像，覆盖 {family_count} 个候选科。",
        f"- 图像来源：cropped_photo={source_counts['cropped_photo']}，full_page={source_counts['full_page']}。",
        f"- OCR 文本检测：no_ocr_text={text_counts['no_ocr_text']}，ocr_text_detected={text_counts['ocr_text_detected']}。",
        "- 已完成模型：Gemini 3.1 Flash Lite、Qwen3.5-35B-A3B/qwen3.5-flash、Qwen3.5 Plus/397B。",
        "- 已完成任务：direct30_masked60 与 taxonomy_masked60；每个模型每个任务 60/60。",
        f"- text-masked 调用总估算 token：{total_tokens:,}。",
        f"- 候选外/invalid 输出：{len(invalid_rows)} 个。",
        "",
        "## 2. Masked 条件下的科级识别结果",
        "",
        "| Model | Task | Family Acc | 95% CI | Top-3 Acc | Invalid | Avg time |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        if row["condition"] != "text_masked":
            continue
        lines.append(
            f"| {row['model']} | {row['task']} | {row['family_acc']} | {row['family_acc_95ci']} | "
            f"{row['top3_acc']} | {row['invalid_rate']} | {row['avg_time_s']}s |"
        )

    lines += [
        "",
        "## 3. 与原始图像的配对比较",
        "",
        "| Model | Task | Original | Masked | Delta | 95% bootstrap CI | McNemar p |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in paired_rows:
        lines.append(
            f"| {row['model']} | {row['task']} | {row['original_acc']} | {row['masked_acc']} | "
            f"{row['masked_minus_original']} | {row['bootstrap_diff_95ci']} | {row['mcnemar_exact_p']} |"
        )

    lines += [
        "",
        "## 4. 分来源解释",
        "",
        "cropped_photo 基本是纯照片或已裁切图片，full_page 更接近带页面文字的图文资料。若 full_page 在 masking 后准确率明显下降，说明模型可能利用了页面文字/OCR 线索；若下降不明显，则说明当前错误更多来自视觉形态证据不足或模型分类学知识不足。",
        "",
        "| Model | Task | Source | n | Original | Masked | Delta | McNemar p |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in source_rows:
        lines.append(
            f"| {row['model']} | {row['task']} | {row['source_type']} | {row['paired_n']} | "
            f"{row['original_acc']} | {row['masked_acc']} | {row['masked_minus_original']} | {row['mcnemar_exact_p']} |"
        )

    lines += [
        "",
        "## 5. 论文叙事中的用法",
        "",
        "这个补充实验可以作为 Ecological Informatics 稿件里的关键稳健性检验：它回答模型是否只是读到了图像中的文字标签，而不是依靠蕨类形态特征进行分类。正文建议将其放在 Results 的最后一节，题名可用 `Text-masking ablation of embedded textual cues`。",
        "",
        "推荐结论口径：在这 60 张图像子集上，text-masked 条件没有导致一致、显著的准确率下降，McNemar 检验均未达到显著水平。这个结果说明当前实验未观察到强 OCR/页面文字依赖；原始实验中的中等科级准确率更可能反映视觉形态线索、模型先验知识和闭集猜测共同作用下的有限分类能力。由于样本量较小且 masking 依赖 OCR 检测，正文应把它写成稳健性分析，而不是绝对排除文字线索影响。",
        "",
        "## 6. 输出文件",
        "",
        "- `paper_analysis/text_masked_experiments/tables/masked_ablation_summary.csv`",
        "- `paper_analysis/text_masked_experiments/tables/masked_vs_original_paired.csv`",
        "- `paper_analysis/text_masked_experiments/tables/masked_by_source_type.csv`",
        "- `paper_analysis/text_masked_experiments/tables/masked_by_text_presence.csv`",
        "- `paper_analysis/text_masked_experiments/data/text_masked_standardized_predictions.csv`",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "text_masked_ablation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
