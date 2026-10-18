#!/usr/bin/env python3
"""Build supplementary analyses that do not require new model calls."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper_analysis"
SUPP = PAPER / "supplementary_experiments"
TABLES = SUPP / "tables"
REPORTS = SUPP / "reports"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"
STD = PAPER / "data" / "standardized_predictions.json"
SPECIES = ROOT / "ferns_dataset" / "species_data.json"

FAMILY_TASKS = {"direct30_full155", "taxonomy_l3", "taxonomy_full155"}
HIGH_CONF = 0.8
BIN_EDGES = [i / 10 for i in range(0, 11)]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def parse_json_response(text: str) -> dict:
    if not text:
        return {}
    clean = str(text).strip()
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


def get_confidence(row: dict) -> float | None:
    parsed = parse_json_response(row.get("raw_response", ""))
    value = parsed.get("confidence")
    if value is None:
        value = parsed.get("family_confidence") or parsed.get("species_confidence")
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return None
    if conf > 1 and conf <= 100:
        conf = conf / 100
    if 0 <= conf <= 1:
        return conf
    return None


def genus_of_latin(name: str) -> str:
    text = str(name or "").strip()
    return text.split()[0] if text else ""


def group_count_label(n: int) -> str:
    if n <= 2:
        return "rare_1_2"
    if n <= 4:
        return "medium_3_4"
    return "common_5_plus"


def bin_label(conf: float) -> str:
    for lo, hi in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
        if lo <= conf < hi or (hi == 1 and conf == 1):
            return f"{lo:.1f}-{hi:.1f}"
    return "unknown"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    config = load_json(CONFIG)
    families = config["canonical_families"]
    l1 = config.get("l1_groups_by_family", {})
    rows = load_json(STD)
    species_data = load_json(SPECIES)["species"]
    family_total = Counter(sp["family"] for sp in species_data)
    chinese_to_latin = {sp["chinese_name"]: sp["latin_name"] for sp in species_data}
    chinese_to_family = {sp["chinese_name"]: sp["family"] for sp in species_data}

    dominant_families = {fam for fam, count in family_total.items() if count >= 7}

    per_family_rows = []
    macro_rows = []
    error_cases = []
    error_counter = Counter()
    confidence_items = []
    high_conf_errors = []

    by_model_task_family = defaultdict(list)
    by_model_task = defaultdict(list)
    for row in rows:
        if row["task"] in FAMILY_TASKS and row.get("level") == "family":
            by_model_task[(row["model_id"], row["model_label"], row["task"])].append(row)
            by_model_task_family[(row["model_id"], row["model_label"], row["task"], row["expected_family_std"])].append(row)

    for (model_id, model, task, fam), fam_rows in sorted(by_model_task_family.items()):
        n = len(fam_rows)
        valid = sum(1 for r in fam_rows if r["valid_output"])
        correct = sum(1 for r in fam_rows if r["family_correct"])
        top3 = sum(1 for r in fam_rows if r["family_top3_correct"])
        confusions = Counter(r["predicted_family_std"] for r in fam_rows if not r["family_correct"])
        per_family_rows.append({
            "model_id": model_id,
            "model": model,
            "task": task,
            "family": fam,
            "dataset_family_n": family_total.get(fam, 0),
            "family_size_group": group_count_label(family_total.get(fam, 0)),
            "n": n,
            "valid_count": valid,
            "correct": correct,
            "recall": pct(correct / n if n else 0),
            "top3_recall": pct(top3 / n if n else 0),
            "invalid_count": n - valid,
            "main_confusion": confusions.most_common(1)[0][0] if confusions else "",
            "main_confusion_count": confusions.most_common(1)[0][1] if confusions else 0,
        })

    for (model_id, model, task), task_rows in sorted(by_model_task.items()):
        n = len(task_rows)
        micro = sum(r["family_correct"] for r in task_rows) / n if n else 0
        family_recalls = []
        top3_recalls = []
        valid_rates = []
        group_scores = defaultdict(list)
        for fam in families:
            fam_rows = [r for r in task_rows if r["expected_family_std"] == fam]
            if not fam_rows:
                continue
            fam_acc = sum(r["family_correct"] for r in fam_rows) / len(fam_rows)
            family_recalls.append(fam_acc)
            top3_recalls.append(sum(r["family_top3_correct"] for r in fam_rows) / len(fam_rows))
            valid_rates.append(sum(r["valid_output"] for r in fam_rows) / len(fam_rows))
            group_scores[group_count_label(family_total.get(fam, 0))].append(fam_acc)
        macro = sum(family_recalls) / len(family_recalls) if family_recalls else 0
        macro_top3 = sum(top3_recalls) / len(top3_recalls) if top3_recalls else 0
        macro_valid = sum(valid_rates) / len(valid_rates) if valid_rates else 0
        macro_rows.append({
            "model_id": model_id,
            "model": model,
            "task": task,
            "n": n,
            "micro_family_acc": pct(micro),
            "macro_family_acc": pct(macro),
            "balanced_accuracy": pct(macro),
            "macro_top3_acc": pct(macro_top3),
            "macro_valid_rate": pct(macro_valid),
            "rare_family_macro_acc": pct(sum(group_scores["rare_1_2"]) / len(group_scores["rare_1_2"]) if group_scores["rare_1_2"] else 0),
            "medium_family_macro_acc": pct(sum(group_scores["medium_3_4"]) / len(group_scores["medium_3_4"]) if group_scores["medium_3_4"] else 0),
            "common_family_macro_acc": pct(sum(group_scores["common_5_plus"]) / len(group_scores["common_5_plus"]) if group_scores["common_5_plus"] else 0),
            "families_evaluated": len(family_recalls),
        })

    cue_words = ["标注", "文字", "页面", "标签", "题名", "图中写", "label", "text", "caption"]
    missing_words = ["证据不足", "不可见", "缺少", "无法观察", "看不清", "不清晰", "缺失证据", "关键证据"]

    for row in rows:
        if row["task"] not in FAMILY_TASKS or row.get("level") != "family":
            continue
        conf = get_confidence(row)
        correct = bool(row["family_correct"])
        if conf is not None:
            confidence_items.append((row, conf, correct))
            if conf >= HIGH_CONF and not correct:
                high_conf_errors.append({
                    "model": row["model_label"],
                    "task": row["task"],
                    "species_id": row["species_id"],
                    "expected_family": row["expected_family_std"],
                    "predicted_family": row["predicted_family_std"],
                    "confidence": f"{conf:.3f}",
                    "raw_response_head": row.get("raw_response", "")[:220],
                })
        if correct:
            continue
        raw = str(row.get("raw_response", ""))
        categories = []
        if not row["valid_output"]:
            categories.append("candidate_out_invalid")
        if row["predicted_family_std"] in dominant_families and row["predicted_family_std"] != row["expected_family_std"]:
            categories.append("dominant_family_attraction")
        if row["valid_output"] and l1.get(row["predicted_family_std"]) == l1.get(row["expected_family_std"]):
            categories.append("same_l1_group_confusion")
        if row["valid_output"] and l1.get(row["predicted_family_std"]) != l1.get(row["expected_family_std"]):
            categories.append("broad_group_confusion")
        if any(word.lower() in raw.lower() for word in missing_words):
            categories.append("missing_key_morphology")
        if any(word.lower() in raw.lower() for word in cue_words):
            categories.append("page_text_or_label_cue")
        if conf is not None and conf >= HIGH_CONF:
            categories.append("high_confidence_error")
        if not categories:
            categories.append("other_error")
        for cat in categories:
            error_counter[(row["model_id"], row["model_label"], row["task"], cat)] += 1
        error_cases.append({
            "model_id": row["model_id"],
            "model": row["model_label"],
            "task": row["task"],
            "species_id": row["species_id"],
            "expected_family": row["expected_family_std"],
            "predicted_family": row["predicted_family_std"],
            "confidence": f"{conf:.3f}" if conf is not None else "",
            "categories": ";".join(categories),
            "raw_response_head": raw[:240],
        })

    error_summary = [
        {
            "model_id": model_id,
            "model": model,
            "task": task,
            "error_category": cat,
            "count": count,
        }
        for (model_id, model, task, cat), count in sorted(error_counter.items())
    ]

    confidence_summary = []
    confidence_bins = []
    by_conf_key = defaultdict(list)
    for row, conf, correct in confidence_items:
        by_conf_key[(row["model_id"], row["model_label"], row["task"])].append((conf, correct, row))
    for (model_id, model, task), items in sorted(by_conf_key.items()):
        n = len(items)
        mean_conf = sum(conf for conf, _, _ in items) / n if n else 0
        acc = sum(correct for _, correct, _ in items) / n if n else 0
        wrong = [conf for conf, correct, _ in items if not correct]
        right = [conf for conf, correct, _ in items if correct]
        ece = 0.0
        for label in [f"{lo:.1f}-{hi:.1f}" for lo, hi in zip(BIN_EDGES[:-1], BIN_EDGES[1:])]:
            bin_items = [(conf, correct) for conf, correct, _ in items if bin_label(conf) == label]
            if not bin_items:
                continue
            bin_conf = sum(conf for conf, _ in bin_items) / len(bin_items)
            bin_acc = sum(correct for _, correct in bin_items) / len(bin_items)
            ece += len(bin_items) / n * abs(bin_acc - bin_conf)
            confidence_bins.append({
                "model_id": model_id,
                "model": model,
                "task": task,
                "bin": label,
                "n": len(bin_items),
                "mean_confidence": f"{bin_conf:.3f}",
                "accuracy": pct(bin_acc),
                "calibration_gap": f"{abs(bin_acc - bin_conf):.3f}",
            })
        confidence_summary.append({
            "model_id": model_id,
            "model": model,
            "task": task,
            "n_with_confidence": n,
            "accuracy": pct(acc),
            "mean_confidence": f"{mean_conf:.3f}",
            "mean_confidence_correct": f"{sum(right) / len(right):.3f}" if right else "",
            "mean_confidence_wrong": f"{sum(wrong) / len(wrong):.3f}" if wrong else "",
            "expected_calibration_error": f"{ece:.3f}",
            "high_conf_error_count": sum(1 for conf, correct, _ in items if conf >= HIGH_CONF and not correct),
            "high_conf_error_rate": pct(sum(1 for conf, correct, _ in items if conf >= HIGH_CONF and not correct) / n if n else 0),
        })

    species_rows = [r for r in rows if r["task"] == "species_l4"]
    genus_summary = []
    genus_cases = []
    by_model = defaultdict(list)
    for row in species_rows:
        by_model[(row["model_id"], row["model_label"])].append(row)
    for (model_id, model), model_rows in sorted(by_model.items()):
        n = len(model_rows)
        valid_species = 0
        genus_correct = 0
        top3_genus = 0
        species_correct = 0
        family_correct_genus_wrong = 0
        for row in model_rows:
            exp_latin = chinese_to_latin.get(row["expected_species"], "")
            pred_latin = chinese_to_latin.get(row["predicted_species"], "")
            exp_genus = genus_of_latin(exp_latin)
            pred_genus = genus_of_latin(pred_latin)
            valid = bool(pred_genus)
            valid_species += int(valid)
            g_correct = bool(valid and exp_genus == pred_genus)
            genus_correct += int(g_correct)
            species_correct += int(row["species_correct"])
            raw = parse_json_response(row.get("raw_response", ""))
            top3_names = raw.get("top3_species") or raw.get("top3") or []
            if isinstance(top3_names, str):
                top3_names = [p.strip() for p in re.split(r"[,，;；、\n]+", top3_names) if p.strip()]
            top3_genera = {genus_of_latin(chinese_to_latin.get(name, "")) for name in top3_names}
            top3_hit = exp_genus in top3_genera
            top3_genus += int(top3_hit)
            if row["family_correct"] and not g_correct:
                family_correct_genus_wrong += 1
            if not row["species_correct"]:
                genus_cases.append({
                    "model_id": model_id,
                    "model": model,
                    "species_id": row["species_id"],
                    "expected_species": row["expected_species"],
                    "expected_genus": exp_genus,
                    "predicted_species": row["predicted_species"],
                    "predicted_genus": pred_genus,
                    "genus_correct": int(g_correct),
                    "top3_genus_hit": int(top3_hit),
                    "family_correct": int(row["family_correct"]),
                    "predicted_family": row["predicted_family_std"],
                })
        genus_summary.append({
            "model_id": model_id,
            "model": model,
            "n": n,
            "valid_species_predictions": valid_species,
            "species_accuracy": pct(species_correct / n if n else 0),
            "genus_accuracy": pct(genus_correct / n if n else 0),
            "genus_top3_accuracy": pct(top3_genus / n if n else 0),
            "family_correct_but_genus_wrong": family_correct_genus_wrong,
            "genus_invalid_count": n - valid_species,
        })

    write_csv(TABLES / "per_family_performance.csv", per_family_rows, [
        "model_id", "model", "task", "family", "dataset_family_n", "family_size_group",
        "n", "valid_count", "correct", "recall", "top3_recall", "invalid_count",
        "main_confusion", "main_confusion_count",
    ])
    write_csv(TABLES / "macro_balanced_summary.csv", macro_rows, [
        "model_id", "model", "task", "n", "micro_family_acc", "macro_family_acc",
        "balanced_accuracy", "macro_top3_acc", "macro_valid_rate",
        "rare_family_macro_acc", "medium_family_macro_acc", "common_family_macro_acc",
        "families_evaluated",
    ])
    write_csv(TABLES / "error_taxonomy_summary.csv", error_summary, [
        "model_id", "model", "task", "error_category", "count",
    ])
    write_csv(TABLES / "error_taxonomy_cases.csv", error_cases, [
        "model_id", "model", "task", "species_id", "expected_family",
        "predicted_family", "confidence", "categories", "raw_response_head",
    ])
    write_csv(TABLES / "confidence_calibration_summary.csv", confidence_summary, [
        "model_id", "model", "task", "n_with_confidence", "accuracy",
        "mean_confidence", "mean_confidence_correct", "mean_confidence_wrong",
        "expected_calibration_error", "high_conf_error_count", "high_conf_error_rate",
    ])
    write_csv(TABLES / "confidence_bins.csv", confidence_bins, [
        "model_id", "model", "task", "bin", "n", "mean_confidence",
        "accuracy", "calibration_gap",
    ])
    write_csv(TABLES / "high_confidence_errors.csv", high_conf_errors, [
        "model", "task", "species_id", "expected_family", "predicted_family",
        "confidence", "raw_response_head",
    ])
    write_csv(TABLES / "genus_level_summary.csv", genus_summary, [
        "model_id", "model", "n", "valid_species_predictions", "species_accuracy",
        "genus_accuracy", "genus_top3_accuracy", "family_correct_but_genus_wrong",
        "genus_invalid_count",
    ])
    write_csv(TABLES / "species_to_genus_error_cases.csv", genus_cases, [
        "model_id", "model", "species_id", "expected_species", "expected_genus",
        "predicted_species", "predicted_genus", "genus_correct", "top3_genus_hit",
        "family_correct", "predicted_family",
    ])

    report = [
        "# No-call supplementary analysis report",
        "",
        f"Generated from `{STD}` without new model calls.",
        "",
        "## Output tables",
        "",
        "- `per_family_performance.csv`",
        "- `macro_balanced_summary.csv`",
        "- `error_taxonomy_summary.csv`",
        "- `confidence_calibration_summary.csv`",
        "- `genus_level_summary.csv`",
    ]
    (REPORTS / "no_call_supplementary_analysis_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote no-call supplementary tables to {TABLES}")


if __name__ == "__main__":
    main()
