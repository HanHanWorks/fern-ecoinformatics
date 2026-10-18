# Supplementary experiments report

## Completion status

| Experiment | Provider | Completed | Status | Next sample | Resume command |
|---|---|---:|---|---|---|
| dashscope-qwen35-flash__qwen3.5-flash__external_validation_direct30_90 | dashscope-qwen35-flash | 90/90 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments external --providers qwen35 --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen35-flash__qwen3.5-flash__open_set_120 | dashscope-qwen35-flash | 120/120 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments open --providers qwen35 --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260512_direct30_masked60 | dashscope-qwen35-flash | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen35 --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260513_direct30_masked60 | dashscope-qwen35-flash | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen35 --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260514_direct30_masked60 | dashscope-qwen35-flash | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen35 --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen397b__qwen3.5-397b-a17b__external_validation_direct30_90 | dashscope-qwen397b | 90/90 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments external --providers qwen397b --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen397b__qwen3.5-397b-a17b__open_set_120 | dashscope-qwen397b | 120/120 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments open --providers qwen397b --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260512_direct30_masked60 | dashscope-qwen397b | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen397b --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260513_direct30_masked60 | dashscope-qwen397b | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen397b --max-output-tokens 900 --max-image-side 1536` |
| dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260514_direct30_masked60 | dashscope-qwen397b | 60/60 | completed |  | `DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers qwen397b --max-output-tokens 900 --max-image-side 1536` |
| google-gemini__gemini-3.1-flash-lite__external_validation_direct30_90 | google-gemini | 90/90 | completed |  | `GEMINI_API_KEY='<GEMINI_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments external --providers gemini --max-output-tokens 900 --max-image-side 1536` |
| google-gemini__gemini-3.1-flash-lite__open_set_120 | google-gemini | 120/120 | completed |  | `GEMINI_API_KEY='<GEMINI_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments open --providers gemini --max-output-tokens 900 --max-image-side 1536` |
| google-gemini__gemini-3.1-flash-lite__order_seed_20260512_direct30_masked60 | google-gemini | 60/60 | completed |  | `GEMINI_API_KEY='<GEMINI_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers gemini --max-output-tokens 900 --max-image-side 1536` |
| google-gemini__gemini-3.1-flash-lite__order_seed_20260513_direct30_masked60 | google-gemini | 60/60 | completed |  | `GEMINI_API_KEY='<GEMINI_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers gemini --max-output-tokens 900 --max-image-side 1536` |
| google-gemini__gemini-3.1-flash-lite__order_seed_20260514_direct30_masked60 | google-gemini | 60/60 | completed |  | `GEMINI_API_KEY='<GEMINI_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments order --providers gemini --max-output-tokens 900 --max-image-side 1536` |

## Key tables

- `supplementary_master_summary.csv`
- `order_robustness_summary.csv`
- `supplementary_pairwise_mcnemar_bootstrap.csv`
- `external_validation_summary.csv`
- `open_set_rejection_summary.csv`
- `macro_balanced_summary.csv`
- `confidence_calibration_summary.csv`
- `genus_level_summary.csv`

## Main interpretation

All supplementary API experiments are complete: candidate-order robustness, external validation, and open-set rejection were finished for Qwen3.5-35B/qwen3.5-flash, Qwen3.5 Plus/397B, and Gemini 3.1 Flash Lite.

Pairwise tests were generated for 21 paired comparisons. These paired comparisons can now be used as final supplementary evidence because all state files are completed.

## What each experiment adds

- No-call macro/balanced analysis: shows micro accuracy overstates performance because rare families have much lower recall.
- Error taxonomy: turns individual mistakes into interpretable ecological-informatics failure modes.
- Confidence calibration: shows high-confidence errors and poor reliability, limiting direct deployment.
- Candidate-order robustness: tests whether closed-set predictions are stable under shuffled candidate lists.
- External validation: tests cross-source generalization using iNaturalist/GBIF-derived images.
- Open-set rejection: tests whether models can reject images outside the candidate fern families.
- Genus-level analysis: shows species-level failure persists even after collapsing to genus.
