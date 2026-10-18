#!/usr/bin/env python3
"""Validate supplementary experiment artifacts and checkpoints."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUPP = ROOT / "paper_analysis" / "supplementary_experiments"
RAW = SUPP / "results" / "raw"
STATE = SUPP / "state"
TABLES = SUPP / "tables"

EXPECTED_RAW = {
    "order": 540,
    "external": 270,
    "open": 360,
}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def raw_rows(pattern: str) -> tuple[int, int, int]:
    rows = 0
    success = 0
    errors = 0
    for path in RAW.glob(pattern):
        data = json.load(path.open("r", encoding="utf-8"))
        rows += len(data)
        success += sum(1 for r in data if r.get("success") and not r.get("error"))
        errors += sum(1 for r in data if r.get("error"))
    return rows, success, errors


def check_csv_readable() -> list[str]:
    messages = []
    for path in sorted(TABLES.glob("*.csv")):
        rows = read_csv(path)
        messages.append(f"CSV_READABLE {path.name}: {len(rows)} rows")
    return messages


def main() -> None:
    messages = []
    failures = []

    external = read_csv(SUPP / "datasets" / "external_validation" / "manifest.csv")
    ext_counts = Counter(r["family"] for r in external)
    messages.append(f"external_manifest_rows={len(external)} families={len(ext_counts)}")
    if len(external) != 90 or len(ext_counts) != 30 or set(ext_counts.values()) != {3}:
        failures.append("external_validation manifest is not exactly 90 rows / 30 families / 3 images each")

    open_set = read_csv(SUPP / "datasets" / "open_set" / "manifest.csv")
    open_counts = Counter(r["open_set_label"] for r in open_set)
    neg_counts = Counter(r["negative_group"] for r in open_set if r["open_set_label"] == "negative_out_of_scope")
    messages.append(f"open_set_manifest_rows={len(open_set)} labels={dict(open_counts)} negative_groups={dict(neg_counts)}")
    if len(open_set) != 120 or open_counts.get("positive_in_scope") != 60 or open_counts.get("negative_out_of_scope") != 60:
        failures.append("open_set manifest is not exactly 120 rows with 60 positive and 60 negative")

    for label, pattern in [
        ("order", "*__order_seed_*_direct30_masked60.json"),
        ("external", "*__external_validation_direct30_90.json"),
        ("open", "*__open_set_120.json"),
    ]:
        rows, success, errors = raw_rows(pattern)
        expected = EXPECTED_RAW[label]
        messages.append(f"raw_{label}: rows={rows} success={success} errors={errors} expected_final_rows={expected}")
        if rows != expected:
            failures.append(f"raw {label} rows are {rows}/{expected}; incomplete runs are checkpointed")

    incomplete = []
    for path in sorted(STATE.glob("*.state.json")):
        state = json.load(path.open("r", encoding="utf-8"))
        line = (
            f"STATE {path.name}: {state.get('status')} "
            f"{state.get('completed_count')}/{state.get('total_count')} next={state.get('next_sample_id')}"
        )
        messages.append(line)
        if state.get("status") != "completed":
            incomplete.append(line)
    if incomplete:
        failures.append("not all state files are completed; see checkpoint lines below")

    messages.extend(check_csv_readable())

    report = [
        "# Supplementary validation report",
        "",
        "## Checks",
        "",
        *[f"- {m}" for m in messages],
        "",
        "## Status",
        "",
    ]
    if failures:
        report.append("Validation completed with checkpointed incomplete runs:")
        report.extend(f"- {f}" for f in failures)
    else:
        report.append("All planned supplementary experiment artifacts are complete.")
    (SUPP / "reports" / "supplementary_validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(messages))
    if failures:
        print("\nCHECKPOINTED_INCOMPLETE")
        for failure in failures:
            print(failure)
    else:
        print("\nALL_COMPLETE")


if __name__ == "__main__":
    main()
