# Reproducing the results

Three levels of reproduction are possible, in increasing cost. The first needs
no GPU and no images at all.

## Level 1 — regenerate every table and figure

Both scripts read released result files and never load a model:

```bash
python code/paper_artifacts/make_paper_tables.py --out /tmp/tables
python code/paper_artifacts/make_figures.py     --out /tmp/figures
```

`make_paper_tables.py` emits Tables 1–10 as CSV and Markdown;
`make_figures.py` emits Figures 3–8 at 600 dpi. Inputs are
`results/*/test_metrics.json`, `results/*/config.json`,
`results/*/predictions.jsonl`, `data/manifests/*.csv`, `data/splits/*.csv` and
the baseline records under `data/external_baselines/`.

This level reproduces the paper's numbers exactly, including the significance
tests, because everything it needs is in the released records.

## Level 2 — re-evaluate the released predictions

The per-image predictions in `results/*/predictions.jsonl` support any
recomputation that does not need a forward pass: per-family accuracy, the
confusion structure, calibration and risk–coverage curves, and open-set
thresholds. `code/analysis/confusion_analysis.py` and
`code/analysis/paired_significance.py` are the entry points.

## Level 3 — retrain

Requires a GPU and the images.

```bash
export FERN_ROOT=/path/to/working/tree
export API_CONTACT="you@example.org"      # only needed for harvesting

python code/models/train_fern.py \
    --backbone bioclip2 --mode linear --img-size 336 \
    --epochs 15 --batch-size 32 --lr 1e-3 \
    --wd 0.05 --warmup 1 --label-smoothing 0.1 \
    --seed 20261010 --out "$FERN_ROOT/results/my_run"
```

The BioCLIP 2 checkpoint goes in `$FERN_ROOT/weights/bioclip-2/`. The exact
hyperparameters of every reported run are in that run's `config.json`, so the
most reliable way to re-run a configuration is to copy its arguments from
there rather than from the paper's prose.

Protocols used across the reported runs, all of which appear in `config.json`:

| Setting | Frozen linear probe | Full fine-tune |
|---|---|---|
| Epochs | 15 (12 for the 336 px fine-tune) | 12 |
| Batch size | 32 (64 at 224 px) | 16 |
| Learning rate | 1e-3 | 2e-5 |
| Weight decay | 0.05 | 0.05 |
| Warm-up | 1 epoch, then cosine decay | same |
| Label smoothing | 0.1 | 0.1 |
| Gradient clipping | 1.0 | 1.0 |
| Optimiser | AdamW | AdamW |
| Precision | fp16 autocast | fp16 autocast |
| Model selection | best validation top-1 | same |

## Rebuilding the dataset from source

Harvesting is not reproducible in the strict sense, because iNaturalist and
GBIF records change over time. What is reproducible is the order of
operations, and the released manifests are a snapshot of one pass through it.

The canonical order is:

```bash
export API_CONTACT="you@example.org"

python code/dataset/download_dual.py        # harvest, writes manifest.csv
python code/dataset/build_gbif_bulk.py      # the GBIF bulk pass, if used
python code/dataset/build_dataset.py        # licence classes, cap, splits
python code/dataset/clean_country.py        # adds country_clean to the splits
python code/dataset/build_testsets.py       # the seven evaluation subsets
python code/dataset/download_negatives.py   # the 700 open-set negatives
```

Three notes on this sequence.

**`clean_country.py` runs after the splits are built, not before.** It adds a
`country_clean` column to `splits/*.csv` and leaves the raw `country` column
untouched. Anything that reads a split expects both columns to be present.

**The released `testsets/*.csv` carry `country_iso` but not `country_clean`.**
They were built before the balanced manifest gained the cleaned country column,
and the difference is one column of metadata that no result depends on. Running
`build_testsets.py` against the released manifest today produces files with
both columns, and the row contents are otherwise identical. This is recorded
rather than tidied, because tidying it would mean regenerating a file the
reported numbers were computed against.

**`build_testsets.py` writes into `data/testsets/` in place.** Running it
replaces the released subsets, so re-run `tools/stage_release.py` afterwards if
you want to restore them.

## Three things that will otherwise not match

**1. The label space is rebuilt from the filtered training split.** Earlier
transfer runs built it from the unfiltered split, which let classes with no
training images carry random weights into the competition. Those published
values are void and are disclosed in the paper. `train_fern.py` now rebuilds the
label space after filtering; the released `config.json` files carry the
corrected values.

**2. Standard deviations are population standard deviations (ddof = 0).** This
is the convention throughout. Recomputing the three-seed spreads with the
sample convention (ddof = 1) will not reproduce the published figures. For
example, `0.9139 ± 0.0073` becomes `±0.0090` under ddof = 1.

**3. Fine-tuning is not bit-deterministic.** Re-running the same seed of a
fine-tuned configuration moves species top-1 by roughly ±0.2 pp, because the
backward pass uses non-deterministic CUDA atomics. This is expected, not a
bug, and it is why the recipe comparison is reported as a three-seed mean. The
frozen linear probe reproduced its published values exactly on a re-run.

## Transfer experiment directory names

The four transfer runs under `results/` are named in the opposite direction to
what they contain for two of the four cases:

| Directory | Actually trains on | Tests on |
|---|---|---|
| `xfer_gbif2inat` | GBIF | iNaturalist |
| `xfer_inat2gbif` | iNaturalist | GBIF |
| `xfer_field2spec` | **specimen** | **field** |
| `xfer_spec2field` | **field** | **specimen** |

`field2spec` and `spec2field` are inverted relative to their names. Read the
`train_where` and `eval_where` fields in each `config.json` rather than
inferring direction from the directory name. The numbers are unaffected.

## Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `FERN_ROOT` | Evaluation and analysis scripts | Working tree holding `results/`, `weights/` and the data |
| `FERN_PYTHON` | `code/scripts/*.sh` | Interpreter for the shell drivers; defaults to `python3` |
| `API_CONTACT` | `code/dataset/download_*.py` | Contact address for the iNaturalist and GBIF User-Agent |
| `DASHSCOPE_API_KEY` | `code/baselines/vlm_eval.py` | Commercial vision–language-model API |
| `PLANTNET_API_KEY` | `code/baselines/plantnet_eval.py` | Pl@ntNet identification service |

## Environment used for the reported results

Ubuntu 24.04, one NVIDIA RTX 4090 D (24 GB), PyTorch 2.10.0 built against CUDA
12.6, `timm` 1.0.30, `open_clip` 3.3.0, Tesseract for the OCR audit, and a
local vLLM server for the 8B vision–language model. The exact pinned versions
are in `requirements.txt`.

## A note on the OCR audit

`code/baselines/text_leakage.py` shells out to the Tesseract binary. It is the
instrument behind the paper's claim that herbarium accuracy is inflated by
printed label text, and it deliberately does not use the model under test to
read the labels. Re-running it needs Tesseract installed and the images
present; its released output, `data/external_baselines/vlm/text_ocr.jsonl`,
records the characters recovered per image.
