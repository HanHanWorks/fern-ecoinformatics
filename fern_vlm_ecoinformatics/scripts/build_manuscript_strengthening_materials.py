#!/usr/bin/env python3
"""Build manuscript-strengthening tables and supplementary notes.

This script does not call any model APIs. It only reads existing manifests,
raw results, state files, and dataset metadata.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_analysis"
TABLES = PAPER / "tables"
SUPP = PAPER / "supplementary_experiments"
SUPP_TABLES = SUPP / "tables"
RAW_DIR = SUPP / "results" / "raw"
MANUSCRIPTS = PAPER / "manuscript_drafts"
SPECIES_JSON = ROOT / "ferns_dataset" / "species_data.json"
DATASET_MANIFEST = ROOT / "ferns_dataset" / "dataset_manifest.json"
MASTER_TABLE = PAPER / "tables" / "master_model_task_summary.csv"
EXT_MANIFEST = SUPP / "datasets" / "external_validation" / "manifest.csv"
OPEN_MANIFEST = SUPP / "datasets" / "open_set" / "manifest.csv"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"


MODEL_LABELS = {
    "google-gemini": "Gemini 3.1 Flash Lite",
    "dashscope-qwen35-flash": "Qwen3.5-35B-A3B / qwen3.5-flash",
    "dashscope-qwen397b": "Qwen3.5 Plus / 397B",
}

REPRO_ROWS = [
    {
        "model_label": "mimo-v2.5",
        "exact_model_ids": "mimo-v2.5",
        "provider_route": "Mimo API / existing completed pipeline",
        "endpoint_type": "OpenAI-compatible or provider-compatible vision chat interface",
        "tasks": "main experiments",
        "temperature": "0.0",
        "max_output_tokens": "2200 in Mimo runner",
        "max_image_side": "not consistently recorded in raw rows",
        "fallback_aliases": "none recorded",
    },
    {
        "model_label": "Qwen3.5 Plus / 397B",
        "exact_model_ids": "qwen3.5-plus-2026-02-15; qwen3.5-plus; qwen3.5-397b-a17b; Qwen/Qwen3.5-397B-A17B",
        "provider_route": "DashScope + ModelScope",
        "endpoint_type": "OpenAI-compatible /chat/completions",
        "tasks": "main and supplementary experiments",
        "temperature": "0.0",
        "max_output_tokens": "900 in Qwen and supplementary runners",
        "max_image_side": "2048 in main Qwen runner; 1536 in supplementary runner",
        "fallback_aliases": "DashScope Beijing/Singapore/US aliases and ModelScope alias where available",
    },
    {
        "model_label": "Qwen3.5-27B",
        "exact_model_ids": "Qwen/Qwen3.5-27B",
        "provider_route": "ModelScope",
        "endpoint_type": "OpenAI-compatible /chat/completions",
        "tasks": "main experiments",
        "temperature": "0.0",
        "max_output_tokens": "900",
        "max_image_side": "2048",
        "fallback_aliases": "none recorded",
    },
    {
        "model_label": "Qwen3.5-35B-A3B / qwen3.5-flash",
        "exact_model_ids": "Qwen/Qwen3.5-35B-A3B; qwen3.5-flash; qwen3.5-flash-2026-02-23",
        "provider_route": "ModelScope + DashScope",
        "endpoint_type": "OpenAI-compatible /chat/completions",
        "tasks": "main and supplementary experiments",
        "temperature": "0.0",
        "max_output_tokens": "900",
        "max_image_side": "2048 in main Qwen runner; 1536 in supplementary runner",
        "fallback_aliases": "qwen3.5-flash-2026-02-23 for DashScope supplementary runs",
    },
    {
        "model_label": "Gemini 3.1 Flash Lite",
        "exact_model_ids": "gemini-3.1-flash-lite",
        "provider_route": "Google OpenAI-compatible API",
        "endpoint_type": "OpenAI-compatible /chat/completions",
        "tasks": "main and supplementary experiments",
        "temperature": "0.0",
        "max_output_tokens": "900 in supplementary runner",
        "max_image_side": "1536 in supplementary runner",
        "fallback_aliases": "none recorded",
    },
]


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def ci_text(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{pct(lo)}-{pct(hi)}"


def provider_from_path(path: Path) -> str:
    return path.name.split("__")[0]


def truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_taxonomy() -> tuple[list[str], set[str], dict[str, str]]:
    cfg = read_json(CONFIG)
    canonical_families = cfg["canonical_families"]
    return canonical_families, set(canonical_families), cfg.get("aliases", {})


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
    hits = [fam for fam in canonical if fam and fam in compact]
    if len(hits) == 1:
        return hits[0], True
    return f"INVALID_OOV::{raw}", False


def top3_valid(row: dict, expected: str, canonical: set[str], aliases: dict[str, str]) -> bool:
    raw = row.get("top3_family") or row.get("top3") or []
    if not isinstance(raw, list):
        return False
    for item in raw:
        mapped, valid = norm_family(item, canonical, aliases)
        if valid and mapped == expected:
            return True
    return False


def build_baseline_table() -> None:
    species = read_json(SPECIES_JSON)["species"]
    family_counts = Counter(row["family"] for row in species)
    n = len(species)
    n_families = len(family_counts)
    majority_family, majority_n = family_counts.most_common(1)[0]
    baseline_rows = [
        {
            "entry_type": "baseline",
            "model_or_baseline": "Random 30-family top-1",
            "task": "direct30_full155",
            "n": n,
            "family_correct": f"{1 / n_families:.4f} expected probability",
            "family_acc": pct(1 / n_families),
            "family_acc_95ci": "",
            "top3_acc": pct(3 / n_families),
            "invalid_rate": "0.0%",
            "note": "Uniform random guess among 30 candidate families; top-3 assumes three distinct random candidates.",
        },
        {
            "entry_type": "baseline",
            "model_or_baseline": f"Majority-family baseline ({majority_family})",
            "task": "direct30_full155",
            "n": n,
            "family_correct": majority_n,
            "family_acc": pct(majority_n / n),
            "family_acc_95ci": ci_text(majority_n, n),
            "top3_acc": "",
            "invalid_rate": "0.0%",
            "note": "Always predicts the most frequent family in the local dataset.",
        },
    ]
    for row in read_csv(MASTER_TABLE):
        if row["task"] != "direct30_full155":
            continue
        baseline_rows.append({
            "entry_type": "model",
            "model_or_baseline": row["model"],
            "task": row["task"],
            "n": row["n"],
            "family_correct": row["family_correct"],
            "family_acc": row["family_acc"],
            "family_acc_95ci": row["family_acc_95ci"],
            "top3_acc": row["family_top3_acc"],
            "invalid_rate": row["invalid_rate"],
            "note": row["provider"],
        })
    write_csv(TABLES / "baseline_comparison.csv", baseline_rows, [
        "entry_type", "model_or_baseline", "task", "n", "family_correct",
        "family_acc", "family_acc_95ci", "top3_acc", "invalid_rate", "note",
    ])


def summarize_family_rows(rows: list[dict], canonical: set[str], aliases: dict[str, str]) -> dict:
    n = len(rows)
    valid = 0
    correct = 0
    top3 = 0
    for row in rows:
        expected, exp_valid = norm_family(row.get("expected_family", ""), canonical, aliases)
        pred, pred_valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
        row_valid = bool(truthy(row.get("success")) and not row.get("error") and pred_valid)
        valid += int(row_valid)
        correct += int(row_valid and exp_valid and pred == expected)
        top3 += int(row_valid and exp_valid and top3_valid(row, expected, canonical, aliases))
    return {
        "n": n,
        "valid_count": valid,
        "family_correct": correct,
        "family_acc": pct(correct / n if n else 0),
        "family_acc_95ci": ci_text(correct, n),
        "top3_correct": top3,
        "top3_acc": pct(top3 / n if n else 0),
        "top3_acc_95ci": ci_text(top3, n),
        "invalid_count": n - valid,
        "invalid_rate": pct((n - valid) / n if n else 0),
        "estimated_tokens": sum(int(r.get("estimated_tokens") or 0) for r in rows),
        "avg_time_s": f"{sum(float(r.get('elapsed_seconds') or 0) for r in rows) / n:.1f}" if n else "0.0",
    }


def build_external_by_source() -> None:
    _, canonical, aliases = load_taxonomy()
    manifest_counts = Counter(r["source"] for r in read_csv(EXT_MANIFEST))
    rows_out = []
    for path in sorted(RAW_DIR.glob("*__external_validation_direct30_90.json")):
        provider = provider_from_path(path)
        model = MODEL_LABELS.get(provider, provider)
        raw = read_json(path)
        by_source = defaultdict(list)
        for row in raw:
            by_source[row.get("source", "")].append(row)
        for source in sorted(by_source):
            metrics = summarize_family_rows(by_source[source], canonical, aliases)
            rows_out.append({
                "provider": provider,
                "model": model,
                "source": source,
                "manifest_source_n": manifest_counts.get(source, 0),
                **metrics,
            })
    write_csv(SUPP_TABLES / "external_validation_by_source.csv", rows_out, [
        "provider", "model", "source", "manifest_source_n", "n", "valid_count",
        "family_correct", "family_acc", "family_acc_95ci", "top3_correct",
        "top3_acc", "top3_acc_95ci", "invalid_count", "invalid_rate",
        "estimated_tokens", "avg_time_s",
    ])


def build_open_by_negative_group() -> None:
    manifest = read_csv(OPEN_MANIFEST)
    group_manifest_counts = Counter(r["negative_group"] for r in manifest if r.get("negative_group"))
    rows_out = []
    for path in sorted(RAW_DIR.glob("*__open_set_120.json")):
        provider = provider_from_path(path)
        model = MODEL_LABELS.get(provider, provider)
        raw = read_json(path)
        neg = [r for r in raw if r.get("expected_decision") == "none_of_the_above"]
        by_group = defaultdict(list)
        for row in neg:
            by_group[row.get("negative_group", "")].append(row)
        for group in sorted(by_group):
            rows = by_group[group]
            n = len(rows)
            rejection = sum(1 for r in rows if r.get("decision") in {"none_of_the_above", "uncertain"})
            false_pos = [r for r in rows if r.get("decision") == "in_scope"]
            high_conf_fp = sum(1 for r in false_pos if float(r.get("confidence") or 0) >= 0.8)
            selected_counts = Counter(str(r.get("selected_option") or r.get("predicted_family") or "").strip() for r in false_pos)
            selected_counts.pop("", None)
            rows_out.append({
                "provider": provider,
                "model": model,
                "negative_group": group,
                "manifest_group_n": group_manifest_counts.get(group, 0),
                "n": n,
                "rejection_correct": rejection,
                "rejection_accuracy": pct(rejection / n if n else 0),
                "rejection_95ci": ci_text(rejection, n),
                "false_positive_count": len(false_pos),
                "false_positive_rate": pct(len(false_pos) / n if n else 0),
                "false_positive_95ci": ci_text(len(false_pos), n),
                "high_conf_false_positive_count": high_conf_fp,
                "main_false_positive_families": ";".join(f"{k}:{v}" for k, v in selected_counts.most_common(5)),
            })
    write_csv(SUPP_TABLES / "open_set_by_negative_group.csv", rows_out, [
        "provider", "model", "negative_group", "manifest_group_n", "n",
        "rejection_correct", "rejection_accuracy", "rejection_95ci",
        "false_positive_count", "false_positive_rate", "false_positive_95ci",
        "high_conf_false_positive_count", "main_false_positive_families",
    ])


def local_dataset_markdown() -> str:
    dataset = read_json(DATASET_MANIFEST)
    species = read_json(SPECIES_JSON)["species"]
    family_counts = Counter(row["family"] for row in species)
    image_context = Counter("full_page" if "_full" in row.get("image_refs", [""])[0] else "cropped_photo" for row in species)
    lines = [
        "# Local Dataset Provenance and License Note",
        "",
        "This note documents the local research-only evaluation dataset used in the manuscript draft.",
        "",
        "## Source and Scope",
        "",
        f"- Dataset name: {dataset.get('dataset_name', '')}.",
        f"- Version recorded in manifest: {dataset.get('version', '')}.",
        f"- Source recorded in manifest: {dataset.get('source', '')}.",
        f"- Total records: {len(species)} species-level entries.",
        f"- Project families: {len(family_counts)} Chinese family labels with associated Latin family labels.",
        "- Each record includes `species_id`, Chinese species name, Latin binomial, Chinese family label, Latin family label, morphology, distribution, habitat, and one local `image_refs` entry.",
        "",
        "## Image Context",
        "",
        f"- Full-page or page-context images: {image_context.get('full_page', 0)}.",
        f"- Cropped plant-photo images: {image_context.get('cropped_photo', 0)}.",
        "- Some full-page images may contain visible page text or labels. This risk was handled analytically through the 60-image text-masked robustness subset rather than by claiming that the original local set is text-free.",
        "",
        "## Label Handling",
        "",
        "- Labels were treated as source-standardized labels: species and family names were derived from the source reference and standardized to the project canonical taxonomy.",
        "- The current manuscript should not claim independent expert re-identification or expert review of all labels unless such review is completed later.",
        "- Synonym and family-name handling was performed through the project canonical taxonomy and alias normalization used in the analysis scripts.",
        "",
        "## License and Redistribution",
        "",
        "- The local images are used as a local research-only evaluation dataset.",
        "- Original local images are not redistributed with the manuscript, repository, or supplementary materials.",
        "- Releasable materials should be limited to metadata, non-sensitive manifests, prompts, scripts, raw/standardized model outputs where allowed, and derived result tables.",
        "- External validation images retain their original GBIF/iNaturalist source URLs, license strings, and rights-holder metadata in the external manifest.",
        "",
        "## Family Distribution",
        "",
        "| Family | Latin family | n |",
        "|---|---|---:|",
    ]
    latin_by_family = {row["family"]: row.get("family_latin", "") for row in species}
    for family, count in family_counts.most_common():
        lines.append(f"| {family} | {latin_by_family.get(family, '')} | {count} |")
    lines.append("")
    return "\n".join(lines)


def prompt_supplement_markdown() -> str:
    return """# Supplementary Prompts and Reproducibility Notes

This supplement records the model-access and prompt protocol used by the completed experiments. API keys are intentionally excluded and must not be stored in manuscript files.

## Model and API Settings

| Model label | Exact model IDs / aliases used | Provider route | Endpoint type | Temperature | Max output tokens | Image long-side limit | Fallback handling |
|---|---|---|---|---:|---|---|---|
""" + "\n".join(
        f"| {r['model_label']} | `{r['exact_model_ids']}` | {r['provider_route']} | {r['endpoint_type']} | {r['temperature']} | {r['max_output_tokens']} | {r['max_image_side']} | {r['fallback_aliases']} |"
        for r in REPRO_ROWS
    ) + """

All OpenAI-compatible calls used image-plus-text chat messages and requested structured JSON outputs. Each sample was written to raw result files immediately after completion, with state files recording completion count, next sample, status, and resume command. Empty outputs, unparsable outputs, and out-of-candidate outputs were retained and marked invalid rather than discarded.

## Direct 30-Family Closed-Set Prompt Template

```text
你是蕨类植物分类学专家。请只根据图片判断该植物属于以下 30 个候选科中的哪一个。

候选科：
1. <family_1>
...
30. <family_30>

要求：
- selected_option 必须严格等于候选科中文名之一。
- top3 给出最可能的前三个候选科，均必须来自候选列表。
- 不要输出候选外科名。
- 如果证据不足，也选择最可能科，并在 reasoning 中说明不确定原因。

只回复 JSON：
{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Taxonomy-Prompted 30-Family Template

```text
你是蕨类植物分类学专家。请进行 30 科闭集识别。

标准候选科及简要约束：
1. <family> (<latin_family>)；类群：<higher_group>；示例：<example_species>
...

观察重点：生活型、叶片分裂方式、叶片质地、叶柄/根状茎特征、孢子囊群位置和形状。

要求：
- selected_option 必须严格等于上述 30 个中文科名之一。
- top3 必须从上述 30 科中选择。
- 如果关键证据不可见，请说明缺失证据。
- 不要输出候选外科名。

只回复 JSON：
{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "visible_features": ["可见特征1"],
  "missing_evidence": ["缺失证据1"],
  "reasoning": "简短理由"
}
```

## Species-Level Closed-Set Template

```text
你是蕨类植物分类学专家。请进行种级闭集识别：<task_title>

候选物种：
1. <Chinese species> (<Latin binomial>)；科：<family>；形态：<morphology excerpt>
...

要求：
- selected_species 必须严格等于候选物种中文名之一。
- top3_species 给出最可能的前三个候选物种中文名。
- selected_family 填写你认为的科名。
- 如果图片缺少关键证据，请在 reasoning 中说明。

只回复 JSON：
{
  "selected_species": "物种中文名",
  "top3_species": ["物种1", "物种2", "物种3"],
  "selected_family": "科名",
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Open-Set Rejection Template

```text
你是蕨类植物分类学专家。请判断图片是否属于下面 30 个候选蕨类科之一，或者不属于候选范围。

候选科：
1. <family_1>
...
30. <family_30>

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
{
  "decision": "in_scope",
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Reproducibility Caveat

Several systems are API-based and may change over time. The manuscript should therefore describe this as a checkpointed evaluation instance: prompts, raw responses, standardized outputs, state files, model identifiers, and access routes were archived locally for reproducibility of the completed runs.
"""


def write_markdown_notes() -> None:
    MANUSCRIPTS.mkdir(parents=True, exist_ok=True)
    (MANUSCRIPTS / "local_dataset_provenance_and_license.md").write_text(local_dataset_markdown(), encoding="utf-8")
    (MANUSCRIPTS / "supplementary_prompts_and_reproducibility.md").write_text(prompt_supplement_markdown(), encoding="utf-8")


def main() -> None:
    build_baseline_table()
    build_external_by_source()
    build_open_by_negative_group()
    write_markdown_notes()
    print("Wrote manuscript strengthening materials.")
    print(f"- {TABLES / 'baseline_comparison.csv'}")
    print(f"- {SUPP_TABLES / 'external_validation_by_source.csv'}")
    print(f"- {SUPP_TABLES / 'open_set_by_negative_group.csv'}")
    print(f"- {MANUSCRIPTS / 'local_dataset_provenance_and_license.md'}")
    print(f"- {MANUSCRIPTS / 'supplementary_prompts_and_reproducibility.md'}")


if __name__ == "__main__":
    main()
