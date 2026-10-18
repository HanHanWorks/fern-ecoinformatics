#!/usr/bin/env python3
"""Build one JSON file collecting all paper experiment results."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_analysis"
OUT = PAPER / "all_experiment_results_summary.json"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def raw_index(paths: list[Path]) -> list[dict]:
    out = []
    for path in sorted(paths):
        if not path.exists():
            continue
        try:
            data = json.load(path.open("r", encoding="utf-8"))
            rows = len(data) if isinstance(data, list) else None
            success = sum(1 for r in data if isinstance(r, dict) and r.get("success") and not r.get("error")) if isinstance(data, list) else None
            errors = sum(1 for r in data if isinstance(r, dict) and r.get("error")) if isinstance(data, list) else None
        except Exception as exc:
            rows, success, errors = None, None, None
            out.append({"path": str(path.relative_to(ROOT)), "error": str(exc)})
            continue
        out.append({
            "path": str(path.relative_to(ROOT)),
            "rows": rows,
            "success_rows": success,
            "error_rows": errors,
        })
    return out


def best_by_task(master: list[dict]) -> dict[str, list[dict]]:
    by_task: dict[str, list[dict]] = {}
    for row in master:
        by_task.setdefault(row["task"], []).append(row)
    for task, rows in by_task.items():
        by_task[task] = sorted(rows, key=lambda r: float(str(r.get("family_acc", "0")).strip("%") or 0), reverse=True)
    return by_task


def main() -> None:
    main_tables = PAPER / "tables"
    masked_tables = PAPER / "text_masked_experiments" / "tables"
    supp_tables = PAPER / "supplementary_experiments" / "tables"
    supp = PAPER / "supplementary_experiments"

    master = read_csv(main_tables / "master_model_task_summary.csv")
    external = read_csv(supp_tables / "external_validation_summary.csv")
    open_set = read_csv(supp_tables / "open_set_rejection_summary.csv")
    order = read_csv(supp_tables / "order_robustness_summary.csv")
    macro = read_csv(supp_tables / "macro_balanced_summary.csv")
    confidence = read_csv(supp_tables / "confidence_calibration_summary.csv")
    genus = read_csv(supp_tables / "genus_level_summary.csv")
    masked_paired = read_csv(masked_tables / "masked_vs_original_paired.csv")

    result = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(ROOT),
            "description": "Unified machine-readable summary of fern VLM experiments for the Ecological Informatics manuscript.",
            "api_keys_included": False,
        },
        "datasets": {
            "main_dataset": {
                "description": "Local fern image dataset used in five-model main experiments.",
                "species_data": "ferns_dataset/species_data.json",
                "images_dir": "ferns_dataset/images",
            },
            "text_masked_dataset": {
                "manifest": "paper_analysis/text_masked_dataset/manifest.csv",
                "n": 60,
                "purpose": "Test dependence on page text/OCR cues using masked real fern images.",
            },
            "external_validation": {
                "manifest": "paper_analysis/supplementary_experiments/datasets/external_validation/manifest.csv",
                "n": 90,
                "design": "30 candidate families x 3 external iNaturalist/GBIF images.",
            },
            "open_set": {
                "manifest": "paper_analysis/supplementary_experiments/datasets/open_set/manifest.csv",
                "n": 120,
                "design": "60 in-scope text-masked fern positives + 60 out-of-scope negatives.",
                "negative_groups": ["candidate_out_fern", "angiosperm", "gymnosperm_cycad", "bryophyte_liverwort"],
            },
        },
        "experiments": {
            "main_five_model_experiments": {
                "tables": {
                    "master_model_task_summary": master,
                    "pairwise_mcnemar_bootstrap": read_csv(main_tables / "pairwise_mcnemar_bootstrap.csv"),
                    "top_family_confusions": read_csv(main_tables / "top_family_confusions.csv"),
                    "invalid_outputs_unified": read_csv(main_tables / "invalid_outputs_unified.csv"),
                },
                "best_by_task": best_by_task(master),
            },
            "text_masked_experiments": {
                "tables": {
                    "masked_ablation_summary": read_csv(masked_tables / "masked_ablation_summary.csv"),
                    "masked_vs_original_paired": masked_paired,
                    "masked_by_source_type": read_csv(masked_tables / "masked_by_source_type.csv"),
                    "masked_by_text_presence": read_csv(masked_tables / "masked_by_text_presence.csv"),
                    "masked_invalid_outputs": read_csv(masked_tables / "masked_invalid_outputs.csv"),
                },
            },
            "supplementary_experiments": {
                "tables": {
                    "supplementary_master_summary": read_csv(supp_tables / "supplementary_master_summary.csv"),
                    "supplementary_pairwise_mcnemar_bootstrap": read_csv(supp_tables / "supplementary_pairwise_mcnemar_bootstrap.csv"),
                    "per_family_performance": read_csv(supp_tables / "per_family_performance.csv"),
                    "macro_balanced_summary": macro,
                    "error_taxonomy_summary": read_csv(supp_tables / "error_taxonomy_summary.csv"),
                    "confidence_calibration_summary": confidence,
                    "genus_level_summary": genus,
                    "order_robustness_summary": order,
                    "order_prediction_consistency": read_csv(supp_tables / "order_prediction_consistency.csv"),
                    "order_prediction_entropy": read_csv(supp_tables / "order_prediction_entropy.csv"),
                    "external_validation_summary": external,
                    "external_validation_per_family": read_csv(supp_tables / "external_validation_per_family.csv"),
                    "open_set_rejection_summary": open_set,
                    "open_set_false_positive_cases": read_csv(supp_tables / "open_set_false_positive_cases.csv"),
                },
            },
        },
        "raw_result_index": {
            "supplementary_raw": raw_index(list((supp / "results" / "raw").glob("*.json"))),
        },
        "key_findings": [
            "Main closed-set family classification reached moderate micro accuracy only: the best direct30_full155 result was Qwen3.5 Plus / 397B at 60.6%, closely followed by Gemini at 59.4%.",
            "Taxonomy prompting did not yield a stable, universal improvement; several models remained clustered around 57%-59% on taxonomy_full155.",
            "Species-level closed-set identification failed: species accuracy was 0%-2.6%, and genus-level collapse remained low at about 5.1%-7.7%.",
            "Macro/balanced accuracy was much lower than micro accuracy, showing that class imbalance and rare-family performance are central limitations.",
            "Text masking did not cause a consistent significant drop, suggesting the models were not relying only on visible page text, but their pure visual taxonomic performance remained limited.",
            "External validation accuracy dropped to 33.3%-43.3%, supporting limited cross-source generalization.",
            "Open-set rejection was stronger for Qwen3.5 Plus / 397B and Gemini than Qwen3.5-35B/qwen3.5-flash, but positive family accuracy stayed around 40.0%-46.7%.",
            "Confidence calibration showed substantial overconfidence and high-confidence errors, so model confidence should not be treated as deployment-ready reliability.",
        ],
        "manuscript_framework": {
            "working_title": "Capability boundaries of general-purpose vision-language models for fern identification in ecological informatics",
            "central_thesis": "General-purpose VLMs provide limited, moderately useful closed-set family-level fern recognition, but their ecological-informatics deployment is constrained by class imbalance, candidate-order sensitivity, external generalization drop, imperfect open-set rejection, confidence miscalibration, and severe genus/species-level failure.",
            "research_questions": [
                "How well do contemporary general-purpose VLMs identify fern families in closed-set tasks?",
                "Does taxonomic prompting improve family-level performance or mainly alter error distributions?",
                "Are model differences statistically meaningful after paired tests and bootstrap CIs?",
                "How robust are predictions to text masking and candidate-order perturbation?",
                "Do models generalize to external iNaturalist/GBIF images?",
                "Can models reject out-of-scope images in an open-set ecological-informatics setting?",
                "Does species-level failure persist after collapsing predictions to genus level?",
            ],
            "recommended_structure": [
                "Introduction: biodiversity informatics need, VLM promise, fern taxonomy as a fine-grained stress test.",
                "Methods: local fern dataset, five VLMs, four main tasks, text masking, external validation, open-set construction, candidate-order seeds, invalid handling, McNemar/bootstrap statistics.",
                "Results 1: main family-level and species-level performance.",
                "Results 2: prompting, significance tests, and model comparisons.",
                "Results 3: robustness analyses, including text masking and candidate order.",
                "Results 4: external generalization and open-set rejection.",
                "Results 5: error taxonomy, confidence calibration, and genus-level failure cascade.",
                "Discussion: why current VLMs are not deployment-ready identifiers, how they may be used as triage/assistive tools, limitations, and future work.",
            ],
            "recommended_claim_style": "Avoid claiming a single best model from small percentage gaps. Emphasize capability boundaries and risk structure rather than leaderboard ranking.",
        },
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
