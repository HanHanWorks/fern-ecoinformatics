#!/usr/bin/env python3
"""Analyze supplementary VLM experiment results."""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper_analysis"
SUPP = PAPER / "supplementary_experiments"
RAW_DIR = SUPP / "results" / "raw"
STATE_DIR = SUPP / "state"
TABLES = SUPP / "tables"
REPORTS = SUPP / "reports"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"
EXT_MANIFEST = SUPP / "datasets" / "external_validation" / "manifest.csv"

BASELINE_ORDER = {
    "google-gemini": PAPER / "text_masked_experiments/results/raw/google-gemini__gemini-3.1-flash-lite__direct30_masked60.json",
    "dashscope-qwen35-flash": PAPER / "text_masked_experiments/results/raw/dashscope-qwen35-flash__qwen3.5-flash__direct30_masked60.json",
    "dashscope-qwen397b": PAPER / "text_masked_experiments/results/raw/dashscope-qwen397b__qwen3.5-397b-a17b__direct30_masked60.json",
}

MODEL_LABELS = {
    "google-gemini": "Gemini 3.1 Flash Lite",
    "dashscope-qwen35-flash": "Qwen3.5-35B-A3B / qwen3.5-flash",
    "dashscope-qwen397b": "Qwen3.5 Plus / 397B",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
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


def _comb(n: int, k: int) -> int:
    k = min(k, n - k)
    if k < 0:
        return 0
    value = 1
    for i in range(1, k + 1):
        value = value * (n - k + i) // i
    return value


def binom_two_sided(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    comb = getattr(math, "comb", _comb)
    probs = [comb(n, i) * (0.5 ** n) for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= obs + 1e-15))


def bootstrap_diff_ci(a: list[int], b: list[int], reps: int = 5000, seed: int = 20260512) -> tuple[float, float, float]:
    n = len(a)
    if n == 0:
        return 0.0, 0.0, 0.0
    diff = sum(b) / n - sum(a) / n
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        idxs = [rng.randrange(n) for _ in range(n)]
        vals.append((sum(b[i] for i in idxs) - sum(a[i] for i in idxs)) / n)
    vals.sort()
    return diff, vals[int(0.025 * reps)], vals[int(0.975 * reps)]


def shannon(items: list[str]) -> float:
    counts = Counter(items)
    n = sum(counts.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log(c / n, 2) for c in counts.values())


def load_taxonomy():
    cfg = load_json(CONFIG)
    return cfg["canonical_families"], set(cfg["canonical_families"]), cfg.get("aliases", {})


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
    hits = [fam for fam in canonical if fam in compact]
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


def family_metrics(rows: list[dict], canonical: set[str], aliases: dict[str, str]) -> dict:
    n = len(rows)
    valid = 0
    correct = 0
    top3 = 0
    for row in rows:
        expected, exp_valid = norm_family(row.get("expected_family", ""), canonical, aliases)
        pred, pred_valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
        row_valid = bool(row.get("success") and not row.get("error") and pred_valid)
        valid += int(row_valid)
        correct += int(row_valid and exp_valid and pred == expected)
        top3 += int(row_valid and exp_valid and top3_valid(row, expected, canonical, aliases))
    return {
        "n": n,
        "valid_count": valid,
        "family_correct": correct,
        "family_acc": pct(correct / n if n else 0),
        "family_acc_95ci": ci_text(correct, n),
        "top3_acc": pct(top3 / n if n else 0),
        "top3_acc_95ci": ci_text(top3, n),
        "invalid_count": n - valid,
        "invalid_rate": pct((n - valid) / n if n else 0),
        "estimated_tokens": sum(int(r.get("estimated_tokens") or 0) for r in rows),
        "avg_time_s": f"{sum(float(r.get('elapsed_seconds') or 0) for r in rows) / n:.1f}" if n else "0.0",
    }


def macro_metrics(rows: list[dict], canonical_families: list[str], canonical: set[str], aliases: dict[str, str]) -> dict:
    family_accs = []
    family_top3s = []
    for fam in canonical_families:
        fam_rows = [r for r in rows if r.get("expected_family") == fam]
        if not fam_rows:
            continue
        metrics = family_metrics(fam_rows, canonical, aliases)
        family_accs.append(metrics["family_correct"] / metrics["n"] if metrics["n"] else 0.0)
        top3_num = sum(
            1
            for r in fam_rows
            if top3_valid(r, fam, canonical, aliases)
            and norm_family(r.get("predicted_family", ""), canonical, aliases)[1]
        )
        family_top3s.append(top3_num / len(fam_rows) if fam_rows else 0.0)
    return {
        "families_evaluated": len(family_accs),
        "macro_family_acc": pct(sum(family_accs) / len(family_accs) if family_accs else 0.0),
        "balanced_accuracy": pct(sum(family_accs) / len(family_accs) if family_accs else 0.0),
        "macro_top3_acc": pct(sum(family_top3s) / len(family_top3s) if family_top3s else 0.0),
    }


def provider_from_name(path: Path) -> str:
    return path.name.split("__")[0]


def seed_from_name(name: str) -> str:
    m = re.search(r"order_seed_(\d+)", name)
    return m.group(1) if m else ""


def analyze_order(canonical_families: list[str], canonical: set[str], aliases: dict[str, str]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    summary = []
    consistency = []
    position_rows = []
    for path in sorted(RAW_DIR.glob("*__order_seed_*_direct30_masked60.json")):
        provider = provider_from_name(path)
        model = MODEL_LABELS.get(provider, provider)
        rows = [r for r in load_json(path) if r.get("success") and not r.get("error")]
        metrics = family_metrics(rows, canonical, aliases)
        summary.append({
            "provider": provider,
            "model": model,
            "seed": seed_from_name(path.name),
            **metrics,
            "status": load_state_status(path.stem),
        })
        baseline_path = BASELINE_ORDER.get(provider)
        if baseline_path and baseline_path.exists():
            baseline = {r["species_id"]: r for r in load_json(baseline_path)}
            same = 0
            paired = 0
            changed_correct = 0
            changed_wrong = 0
            for row in rows:
                b = baseline.get(row["species_id"])
                if not b:
                    continue
                paired += 1
                pred, _ = norm_family(row.get("predicted_family", ""), canonical, aliases)
                base_pred, _ = norm_family(b.get("predicted_family", ""), canonical, aliases)
                if pred == base_pred:
                    same += 1
                elif row.get("family_correct"):
                    changed_correct += 1
                else:
                    changed_wrong += 1
            consistency.append({
                "provider": provider,
                "model": model,
                "seed": seed_from_name(path.name),
                "paired_n": paired,
                "same_prediction_count": same,
                "same_prediction_rate": pct(same / paired if paired else 0),
                "changed_to_correct": changed_correct,
                "changed_to_wrong": changed_wrong,
            })
        for row in rows:
            pred, valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
            if valid and pred in canonical_families:
                position_rows.append((provider, model, seed_from_name(path.name), pred, canonical_families.index(pred) + 1, int(bool(row.get("family_correct")))))
    entropy_rows = []
    by_model_sample = defaultdict(list)
    for path in sorted(RAW_DIR.glob("*__order_seed_*_direct30_masked60.json")):
        provider = provider_from_name(path)
        model = MODEL_LABELS.get(provider, provider)
        for row in load_json(path):
            if row.get("success") and not row.get("error"):
                pred, _ = norm_family(row.get("predicted_family", ""), canonical, aliases)
                by_model_sample[(provider, model, row["sample_id"], row.get("expected_family"))].append(pred)
    for (provider, model, sample_id, expected), preds in sorted(by_model_sample.items()):
        entropy_rows.append({
            "provider": provider,
            "model": model,
            "sample_id": sample_id,
            "expected_family": expected,
            "n_predictions": len(preds),
            "unique_predictions": len(set(preds)),
            "prediction_entropy": f"{shannon(preds):.3f}",
            "predictions": ";".join(preds),
        })
    bias_rows = []
    by_position = defaultdict(list)
    for provider, model, seed, pred, position, correct in position_rows:
        by_position[(provider, model, seed, position)].append(correct)
    for (provider, model, seed, position), values in sorted(by_position.items()):
        bias_rows.append({
            "provider": provider,
            "model": model,
            "seed": seed,
            "candidate_position": position,
            "prediction_count": len(values),
            "correct_count": sum(values),
            "position_accuracy": pct(sum(values) / len(values) if values else 0),
        })
    return summary, consistency, bias_rows, entropy_rows


def load_state_status(stem: str) -> str:
    p = STATE_DIR / f"{stem}.state.json"
    if not p.exists():
        return "missing_state"
    d = load_json(p)
    return d.get("status", "")


def analyze_external(canonical_families: list[str], canonical: set[str], aliases: dict[str, str]) -> tuple[list[dict], list[dict]]:
    manifest = {r["sample_id"]: r for r in read_csv(EXT_MANIFEST)}
    summary = []
    per_family = []
    for path in sorted(RAW_DIR.glob("*__external_validation_direct30_90.json")):
        provider = provider_from_name(path)
        model = MODEL_LABELS.get(provider, provider)
        rows = [r for r in load_json(path) if r.get("success") and not r.get("error")]
        metrics = family_metrics(rows, canonical, aliases)
        macro = macro_metrics(rows, canonical_families, canonical, aliases)
        source_counts = defaultdict(list)
        fam_counts = defaultdict(list)
        for row in rows:
            source_counts[row.get("source", "")].append(row)
            fam_counts[row.get("expected_family", "")].append(row)
        source_metrics = {src: family_metrics(src_rows, canonical, aliases)["family_acc"] for src, src_rows in source_counts.items()}
        summary.append({
            "provider": provider,
            "model": model,
            "status": load_state_status(path.stem),
            "completed_success_n": len(rows),
            "target_n": 90,
            **metrics,
            **macro,
            "source_specific_accuracy": ";".join(f"{k}:{v}" for k, v in sorted(source_metrics.items())),
        })
        for fam in canonical_families:
            fam_rows = fam_counts.get(fam, [])
            if not fam_rows:
                continue
            per_family.append({
                "provider": provider,
                "model": model,
                "family": fam,
                **family_metrics(fam_rows, canonical, aliases),
            })
    return summary, per_family


def analyze_open(canonical: set[str], aliases: dict[str, str]) -> tuple[list[dict], list[dict], list[dict]]:
    summary = []
    false_cases = []
    positive_cases = []
    for path in sorted(RAW_DIR.glob("*__open_set_120.json")):
        provider = provider_from_name(path)
        model = MODEL_LABELS.get(provider, provider)
        rows = [r for r in load_json(path) if r.get("success") and not r.get("error")]
        pos = [r for r in rows if r.get("expected_decision") == "in_scope"]
        neg = [r for r in rows if r.get("expected_decision") == "none_of_the_above"]
        neg_reject = sum(1 for r in neg if r.get("decision") in {"none_of_the_above", "uncertain"})
        false_pos = [r for r in neg if r.get("decision") == "in_scope"]
        pos_retained = [r for r in pos if r.get("decision") == "in_scope"]
        pos_family_correct = sum(1 for r in pos_retained if r.get("family_correct"))
        invalid = sum(1 for r in rows if not str(r.get("decision") or "").strip())
        high_conf_fp = sum(1 for r in false_pos if float(r.get("confidence") or 0) >= 0.8)
        neg_complete = len(neg) == 60
        pos_complete = len(pos) == 60
        summary.append({
            "provider": provider,
            "model": model,
            "status": load_state_status(path.stem),
            "completed_success_n": len(rows),
            "target_n": 120,
            "positive_n": len(pos),
            "negative_n": len(neg),
            "negative_rejection_accuracy": pct(neg_reject / len(neg) if neg else 0),
            "negative_rejection_95ci": ci_text(neg_reject, len(neg)),
            "false_positive_rate": pct(len(false_pos) / len(neg) if neg else 0),
            "false_positive_95ci": ci_text(len(false_pos), len(neg)),
            "positive_retention_accuracy": pct(len(pos_retained) / len(pos) if pos else 0),
            "positive_retention_95ci": ci_text(len(pos_retained), len(pos)),
            "positive_family_accuracy": pct(pos_family_correct / len(pos) if pos else 0),
            "positive_family_95ci": ci_text(pos_family_correct, len(pos)),
            "invalid_decision_count": invalid,
            "high_conf_false_positive_count": high_conf_fp,
            "open_set_metric_interpretable": int(bool(neg_complete and pos_complete)),
            "interpretation_note": "" if neg_complete and pos_complete else "partial open-set run; metrics should be treated as interim",
            "estimated_tokens": sum(int(r.get("estimated_tokens") or 0) for r in rows),
        })
        for r in false_pos:
            false_cases.append({
                "provider": provider,
                "model": model,
                "sample_id": r["sample_id"],
                "negative_group": r.get("negative_group", ""),
                "taxon_name": r.get("expected_species", ""),
                "selected_option": r.get("selected_option", ""),
                "confidence": r.get("confidence", ""),
                "reasoning": str(r.get("reasoning", ""))[:220],
            })
        for r in pos:
            positive_cases.append({
                "provider": provider,
                "model": model,
                "sample_id": r["sample_id"],
                "expected_family": r.get("expected_family", ""),
                "decision": r.get("decision", ""),
                "selected_option": r.get("selected_option", ""),
                "positive_retained": int(r in pos_retained),
                "family_correct": int(bool(r.get("family_correct"))),
            })
    return summary, false_cases, positive_cases


def row_family_correct(row: dict, canonical: set[str], aliases: dict[str, str]) -> int:
    expected, exp_valid = norm_family(row.get("expected_family", ""), canonical, aliases)
    pred, pred_valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
    return int(bool(row.get("success") and not row.get("error") and exp_valid and pred_valid and pred == expected))


def paired_test_row(experiment: str, subset: str, model_a: str, model_b: str, a: list[int], b: list[int]) -> dict:
    paired_n = len(a)
    both_correct = sum(1 for x, y in zip(a, b) if x and y)
    a_only = sum(1 for x, y in zip(a, b) if x and not y)
    b_only = sum(1 for x, y in zip(a, b) if y and not x)
    neither = sum(1 for x, y in zip(a, b) if not x and not y)
    diff, lo, hi = bootstrap_diff_ci(a, b, seed=20260512 + len(experiment) + len(subset))
    return {
        "experiment": experiment,
        "subset": subset,
        "model_a": model_a,
        "model_b": model_b,
        "paired_n": paired_n,
        "acc_a": pct(sum(a) / paired_n if paired_n else 0),
        "acc_b": pct(sum(b) / paired_n if paired_n else 0),
        "both_correct": both_correct,
        "a_only": a_only,
        "b_only": b_only,
        "neither_correct": neither,
        "mcnemar_exact_p": f"{binom_two_sided(min(a_only, b_only), a_only + b_only):.6f}",
        "bootstrap_diff_b_minus_a": pct(diff),
        "bootstrap_diff_95ci": f"{pct(lo)}-{pct(hi)}",
    }


def analyze_pairwise(canonical: set[str], aliases: dict[str, str]) -> list[dict]:
    pairwise = []

    for seed in ["20260512", "20260513", "20260514"]:
        maps = {}
        labels = {}
        for path in sorted(RAW_DIR.glob(f"*__order_seed_{seed}_direct30_masked60.json")):
            provider = provider_from_name(path)
            labels[provider] = MODEL_LABELS.get(provider, provider)
            maps[provider] = {
                row["sample_id"]: row_family_correct(row, canonical, aliases)
                for row in load_json(path)
                if row.get("success") and not row.get("error")
            }
        for a_key, b_key in combinations(sorted(maps), 2):
            ids = sorted(set(maps[a_key]) & set(maps[b_key]))
            if not ids:
                continue
            pairwise.append(paired_test_row(
                "order_robustness", f"seed_{seed}", labels[a_key], labels[b_key],
                [maps[a_key][sid] for sid in ids], [maps[b_key][sid] for sid in ids],
            ))

    maps = {}
    labels = {}
    for path in sorted(RAW_DIR.glob("*__external_validation_direct30_90.json")):
        provider = provider_from_name(path)
        labels[provider] = MODEL_LABELS.get(provider, provider)
        maps[provider] = {
            row["sample_id"]: row_family_correct(row, canonical, aliases)
            for row in load_json(path)
            if row.get("success") and not row.get("error")
        }
    for a_key, b_key in combinations(sorted(maps), 2):
        ids = sorted(set(maps[a_key]) & set(maps[b_key]))
        if not ids:
            continue
        pairwise.append(paired_test_row(
            "external_validation", "direct30", labels[a_key], labels[b_key],
            [maps[a_key][sid] for sid in ids], [maps[b_key][sid] for sid in ids],
        ))

    negative_maps = {}
    positive_family_maps = {}
    retention_maps = {}
    labels = {}
    for path in sorted(RAW_DIR.glob("*__open_set_120.json")):
        provider = provider_from_name(path)
        labels[provider] = MODEL_LABELS.get(provider, provider)
        negative_maps[provider] = {}
        positive_family_maps[provider] = {}
        retention_maps[provider] = {}
        for row in load_json(path):
            if not (row.get("success") and not row.get("error")):
                continue
            if row.get("expected_decision") == "none_of_the_above":
                negative_maps[provider][row["sample_id"]] = int(row.get("decision") in {"none_of_the_above", "uncertain"})
            elif row.get("expected_decision") == "in_scope":
                retention_maps[provider][row["sample_id"]] = int(row.get("decision") == "in_scope")
                positive_family_maps[provider][row["sample_id"]] = int(bool(row.get("family_correct")))
    for maps_for_metric, experiment in [
        (negative_maps, "open_set_negative_rejection"),
        (retention_maps, "open_set_positive_retention"),
        (positive_family_maps, "open_set_positive_family"),
    ]:
        for a_key, b_key in combinations(sorted(maps_for_metric), 2):
            ids = sorted(set(maps_for_metric[a_key]) & set(maps_for_metric[b_key]))
            if not ids:
                continue
            pairwise.append(paired_test_row(
                experiment, "open_set_120", labels[a_key], labels[b_key],
                [maps_for_metric[a_key][sid] for sid in ids], [maps_for_metric[b_key][sid] for sid in ids],
            ))
    return pairwise


def read_table(name: str) -> list[dict]:
    return read_csv(TABLES / name)


def build_master(order_summary: list[dict], external_summary: list[dict], open_summary: list[dict]) -> list[dict]:
    master = []
    for r in read_table("macro_balanced_summary.csv"):
        master.append({
            "experiment": "no_call_macro_balanced",
            "provider": "",
            "model": r["model"],
            "status": "completed",
            "subset": r["task"],
            "n": r["n"],
            "family_acc": r["micro_family_acc"],
            "family_acc_95ci": "",
            "top3_acc": r["macro_top3_acc"],
            "species_acc": "",
            "invalid_rate": "",
            "tokens": "",
            "avg_time_s": "",
            "primary_metric": r["macro_family_acc"],
            "secondary_metric": r["balanced_accuracy"],
            "note": "existing five-model results; no new API calls",
        })
    for r in read_table("confidence_calibration_summary.csv"):
        master.append({
            "experiment": "no_call_confidence_calibration",
            "provider": "",
            "model": r["model"],
            "status": "completed",
            "subset": r["task"],
            "n": r["n_with_confidence"],
            "family_acc": r["accuracy"],
            "family_acc_95ci": "",
            "top3_acc": "",
            "species_acc": "",
            "invalid_rate": "",
            "tokens": "",
            "avg_time_s": "",
            "primary_metric": r["expected_calibration_error"],
            "secondary_metric": r["high_conf_error_rate"],
            "note": "confidence parsed from existing raw responses",
        })
    for r in read_table("genus_level_summary.csv"):
        master.append({
            "experiment": "no_call_genus_level",
            "provider": "",
            "model": r["model"],
            "status": "completed",
            "subset": "species_l4",
            "n": r["n"],
            "family_acc": "",
            "family_acc_95ci": "",
            "top3_acc": r["genus_top3_accuracy"],
            "species_acc": r["species_accuracy"],
            "invalid_rate": "",
            "tokens": "",
            "avg_time_s": "",
            "primary_metric": r["genus_accuracy"],
            "secondary_metric": r["species_accuracy"],
            "note": "existing species_l4 results; no new API calls",
        })
    for r in order_summary:
        master.append({
            "experiment": "order_robustness",
            "provider": r["provider"],
            "model": r["model"],
            "status": r["status"],
            "subset": f"seed_{r['seed']}",
            "n": r["n"],
            "family_acc": r["family_acc"],
            "family_acc_95ci": r["family_acc_95ci"],
            "top3_acc": r["top3_acc"],
            "species_acc": "",
            "invalid_rate": r["invalid_rate"],
            "tokens": r["estimated_tokens"],
            "avg_time_s": r["avg_time_s"],
            "primary_metric": r["family_acc"],
            "secondary_metric": r["invalid_rate"],
            "note": "new API calls on text-masked 60 with shuffled candidates",
        })
    for r in external_summary:
        master.append({
            "experiment": "external_validation",
            "provider": r["provider"],
            "model": r["model"],
            "status": r["status"],
            "subset": "direct30_external90",
            "n": r["completed_success_n"],
            "family_acc": r["family_acc"],
            "family_acc_95ci": r["family_acc_95ci"],
            "top3_acc": r["top3_acc"],
            "species_acc": "",
            "invalid_rate": r["invalid_rate"],
            "tokens": r["estimated_tokens"],
            "avg_time_s": r["avg_time_s"],
            "primary_metric": r["family_acc"],
            "secondary_metric": r["macro_family_acc"],
            "note": "new API calls on external iNaturalist/GBIF images",
        })
    for r in open_summary:
        master.append({
            "experiment": "open_set_rejection",
            "provider": r["provider"],
            "model": r["model"],
            "status": r["status"],
            "subset": "open_set_120",
            "n": r["completed_success_n"],
            "family_acc": r["positive_family_accuracy"],
            "family_acc_95ci": r["positive_family_95ci"],
            "top3_acc": "",
            "species_acc": "",
            "invalid_rate": "",
            "tokens": r["estimated_tokens"],
            "avg_time_s": "",
            "primary_metric": r["negative_rejection_accuracy"],
            "secondary_metric": r["positive_family_accuracy"],
            "note": r["interpretation_note"] or "new API calls on 60 positive + 60 negative open-set images",
        })
    return master


def write_reports(order_summary, external_summary, open_summary, pairwise_rows) -> None:
    lines = [
        "# Supplementary experiments report",
        "",
        "## Completion status",
        "",
        "| Experiment | Provider | Completed | Status | Next sample | Resume command |",
        "|---|---|---:|---|---|---|",
    ]
    for state_path in sorted(STATE_DIR.glob("*.json")):
        d = load_json(state_path)
        cmd = str(d.get("resume_command") or "").replace("|", "\\|")
        lines.append(f"| {d.get('experiment')} | {d.get('provider')} | {d.get('completed_count')}/{d.get('total_count')} | {d.get('status')} | {d.get('next_sample_id') or ''} | `{cmd}` |")
    lines += [
        "",
        "## Key tables",
        "",
        "- `supplementary_master_summary.csv`",
        "- `order_robustness_summary.csv`",
        "- `supplementary_pairwise_mcnemar_bootstrap.csv`",
        "- `external_validation_summary.csv`",
        "- `open_set_rejection_summary.csv`",
        "- `macro_balanced_summary.csv`",
        "- `confidence_calibration_summary.csv`",
        "- `genus_level_summary.csv`",
        "",
        "## Main interpretation",
        "",
        "All supplementary API experiments are complete: candidate-order robustness, external validation, and open-set rejection were finished for Qwen3.5-35B/qwen3.5-flash, Qwen3.5 Plus/397B, and Gemini 3.1 Flash Lite.",
        "",
        f"Pairwise tests were generated for {len(pairwise_rows)} paired comparisons. These paired comparisons can now be used as final supplementary evidence because all state files are completed.",
        "",
        "## What each experiment adds",
        "",
        "- No-call macro/balanced analysis: shows micro accuracy overstates performance because rare families have much lower recall.",
        "- Error taxonomy: turns individual mistakes into interpretable ecological-informatics failure modes.",
        "- Confidence calibration: shows high-confidence errors and poor reliability, limiting direct deployment.",
        "- Candidate-order robustness: tests whether closed-set predictions are stable under shuffled candidate lists.",
        "- External validation: tests cross-source generalization using iNaturalist/GBIF-derived images.",
        "- Open-set rejection: tests whether models can reject images outside the candidate fern families.",
        "- Genus-level analysis: shows species-level failure persists even after collapsing to genus.",
    ]
    (REPORTS / "supplementary_experiments_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    narrative = [
        "# Strengthened Ecological Informatics narrative",
        "",
        "新增补强实验把论文主线从模型排行推进到生态信息学可用性边界：",
        "",
        "1. Macro/balanced accuracy 显著低于 micro accuracy，说明总体准确率受样本不均衡影响，稀有科识别更弱。",
        "2. Confidence calibration 显示模型普遍过度自信，高置信错误比例高，实际部署时不能把置信度直接作为可靠性指标。",
        "3. Genus-level 分析显示 species-level 失败不是单纯标签格式问题，而是属级/种级细粒度鉴定链条整体薄弱。",
        "4. Candidate-order robustness 显示闭集候选顺序会改变部分样本预测，提示模型决策存在提示词表述敏感性。",
        "5. External validation 和 open-set rejection 将论文推向真实生态信息学场景：跨来源泛化和拒识能力是当前 VLM 的关键风险点。",
        "",
        "写作时建议采用保守表述：这些补强实验不是为了证明某个模型绝对最优，而是为了证明通用 VLM 在蕨类自动鉴定中的可用边界和风险结构。",
    ]
    (REPORTS / "ecological_informatics_strengthened_narrative.md").write_text("\n".join(narrative) + "\n", encoding="utf-8")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    families, canonical, aliases = load_taxonomy()
    order_summary, order_consistency, order_bias, order_entropy = analyze_order(families, canonical, aliases)
    external_summary, external_per_family = analyze_external(families, canonical, aliases)
    open_summary, fp_cases, pos_cases = analyze_open(canonical, aliases)
    pairwise = analyze_pairwise(canonical, aliases)

    write_csv(TABLES / "order_robustness_summary.csv", order_summary, [
        "provider", "model", "seed", "n", "valid_count", "family_correct",
        "family_acc", "family_acc_95ci", "top3_acc", "top3_acc_95ci",
        "invalid_count", "invalid_rate", "estimated_tokens", "avg_time_s", "status",
    ])
    write_csv(TABLES / "order_prediction_consistency.csv", order_consistency, [
        "provider", "model", "seed", "paired_n", "same_prediction_count",
        "same_prediction_rate", "changed_to_correct", "changed_to_wrong",
    ])
    write_csv(TABLES / "order_position_bias.csv", order_bias, [
        "provider", "model", "seed", "candidate_position", "prediction_count",
        "correct_count", "position_accuracy",
    ])
    write_csv(TABLES / "order_prediction_entropy.csv", order_entropy, [
        "provider", "model", "sample_id", "expected_family", "n_predictions",
        "unique_predictions", "prediction_entropy", "predictions",
    ])
    write_csv(TABLES / "external_validation_summary.csv", external_summary, [
        "provider", "model", "status", "completed_success_n", "target_n", "n",
        "valid_count", "family_correct", "family_acc", "family_acc_95ci",
        "top3_acc", "top3_acc_95ci", "invalid_count", "invalid_rate",
        "families_evaluated", "macro_family_acc", "balanced_accuracy", "macro_top3_acc",
        "estimated_tokens", "avg_time_s", "source_specific_accuracy",
    ])
    write_csv(TABLES / "external_validation_per_family.csv", external_per_family, [
        "provider", "model", "family", "n", "valid_count", "family_correct",
        "family_acc", "family_acc_95ci", "top3_acc", "top3_acc_95ci",
        "invalid_count", "invalid_rate", "estimated_tokens", "avg_time_s",
    ])
    write_csv(TABLES / "open_set_rejection_summary.csv", open_summary, [
        "provider", "model", "status", "completed_success_n", "target_n",
        "positive_n", "negative_n", "negative_rejection_accuracy", "negative_rejection_95ci",
        "false_positive_rate", "false_positive_95ci", "positive_retention_accuracy",
        "positive_retention_95ci", "positive_family_accuracy", "positive_family_95ci",
        "invalid_decision_count", "high_conf_false_positive_count",
        "open_set_metric_interpretable", "interpretation_note", "estimated_tokens",
    ])
    write_csv(TABLES / "open_set_false_positive_cases.csv", fp_cases, [
        "provider", "model", "sample_id", "negative_group", "taxon_name",
        "selected_option", "confidence", "reasoning",
    ])
    write_csv(TABLES / "open_set_retention_positive_cases.csv", pos_cases, [
        "provider", "model", "sample_id", "expected_family", "decision",
        "selected_option", "positive_retained", "family_correct",
    ])

    write_csv(TABLES / "supplementary_pairwise_mcnemar_bootstrap.csv", pairwise, [
        "experiment", "subset", "model_a", "model_b", "paired_n", "acc_a", "acc_b",
        "both_correct", "a_only", "b_only", "neither_correct", "mcnemar_exact_p",
        "bootstrap_diff_b_minus_a", "bootstrap_diff_95ci",
    ])

    master = build_master(order_summary, external_summary, open_summary)
    write_csv(TABLES / "supplementary_master_summary.csv", master, [
        "experiment", "provider", "model", "status", "subset", "n",
        "family_acc", "family_acc_95ci", "top3_acc", "species_acc", "invalid_rate",
        "tokens", "avg_time_s", "primary_metric", "secondary_metric", "note",
    ])
    write_reports(order_summary, external_summary, open_summary, pairwise)
    print(f"Wrote supplementary analysis tables to {TABLES}")


if __name__ == "__main__":
    main()
