# Fern VLM Ecological Informatics Audit

This repository contains the public, GitHub-ready code and derived analysis materials for a manuscript evaluating general-purpose vision-language models (VLMs) for fern identification in ecological informatics workflows.

The study audits whether off-the-shelf VLMs can support fern family-level candidate generation, whether their outputs are robust to prompt/data perturbations, and where they fail under external validation, open-set rejection, confidence calibration, and genus/species-level analysis.

## What Is Included

- `scripts/`: main analysis and table-building scripts.
- `supplementary_experiments/scripts/`: scripts for supplementary dataset construction, VLM calls, validation, and analysis.
- `tables/`: derived tables for the main five-model experiments.
- `supplementary_experiments/tables/`: derived tables for macro/balanced accuracy, external validation, open-set rejection, candidate-order robustness, confidence calibration, and genus-level analysis.
- `text_masked_experiments/tables/`: derived text-masking ablation tables.
- `data/standardized_predictions_public.json`: standardized prediction-level records with raw model responses removed.
- `data/all_experiment_results_summary.json`: machine-readable summary of the completed experiments.
- `data/metadata/`: public metadata manifests with local image paths and restricted image hashes removed.
- `manuscript/`: manuscript draft and supplementary reproducibility/provenance notes.
- `figures/html/`: one HTML file per figure for reproducible figure rendering.
- `figures/paper_ready/`: prepared figure files for Figures 2-8.

## What Is Not Included

The following are intentionally excluded from this public package:

- API keys, credentials, and provider account information.
- Original local reference-book images from *Color Atlas of Higher Plants of China*, Volumes 1-2.
- Text-masked derivatives of those local images.
- Downloaded external image files from iNaturalist/GBIF. Public manifests retain source URLs and license metadata instead.
- Raw API response JSON files and checkpoint state files.
- Temporary resized images, logs, caches, and local absolute paths.

## Dataset Metadata Summary

| Public metadata file | Rows | Notes |
|---|---:|---|
| `data/metadata/local_species_metadata_public.csv` | 155 | Taxonomic labels for the local research-only fern set; images are not redistributed. |
| `data/metadata/text_masked_manifest_public.csv` | 60 | Metadata for the 60-image text-masked subset; image paths removed. |
| `data/metadata/external_validation_manifest_public.csv` | 90 | iNaturalist/GBIF source metadata for the 90-image external validation set. |
| `data/metadata/open_set_manifest_public.csv` | 120 | Metadata for the 120-image open-set experiment. |
| `data/standardized_predictions_public.json` | 2020 | Standardized prediction records; raw responses removed. |

## Models Evaluated

The manuscript uses unified reporting names:

- `mimo-v2.5`
- `Qwen3.5-27B`
- `Qwen3.5-35B-A3B`
- `Qwen3.5-397B-A17B`
- `Gemini 3.1 Flash Lite`

Qwen-family models were accessed through DashScope-compatible APIs in the manuscript reporting. Gemini was accessed through Google AI Studio-compatible APIs. API keys are not included and should be supplied only through environment variables when re-running API experiments.

## Quick Start

Create a Python environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run non-API analysis scripts from the repository root:

```bash
python3 scripts/build_paper_analysis.py
python3 scripts/build_manuscript_strengthening_materials.py
python3 supplementary_experiments/scripts/build_no_call_supplementary_analysis.py
python3 supplementary_experiments/scripts/analyze_supplementary_experiments.py
```

API-running scripts require image files and provider credentials that are not included in this public package. See `.env.example` and `docs/DATA_AVAILABILITY.md`.

## Reproducibility Notes

The public package is designed to reproduce and inspect the derived analyses and manuscript tables without redistributing restricted image assets. To fully re-run model inference, users need either access to the original local research-only image set or their own replacement image corpus mapped to the same metadata schema.

## Citation

A formal citation will be added after manuscript submission or acceptance.
