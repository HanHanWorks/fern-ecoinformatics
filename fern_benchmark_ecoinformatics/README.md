# A fern identification benchmark with domain, source and geographic annotations

Code and derived data for a study of how far an automated fern identification
model's accuracy travels when the image domain, the data source or the
geography changes.

The benchmark contains **5,969 images** of **152 fern species** in **30
families**, drawn from iNaturalist and GBIF (including iDigBio-digitised
herbarium sheets). Every image carries provenance annotations for its image
domain (field photograph or herbarium specimen), its data source, and its
country. Splits are group-aware by observation, so no single plant appears on
both sides of an evaluation. The benchmark is paired with 700 open-set
negatives in eight groups.

The paper's headline recipe is a **frozen BioCLIP 2 trunk with a linear head at
336 px**, reaching **91.4 ± 0.7%** species top-1 over three seeds — statistically
indistinguishable from full fine-tuning while training only a linear layer.

## What is in this repository

| Path | Contents |
|---|---|
| `data/manifests/` | Image manifests: the balanced benchmark (5,969 rows), the pre-balancing collection (6,237 rows), the openly licensed subset (1,432 rows) and the 700 negatives |
| `data/splits/` | Train, validation and test splits — 4,185 / 882 / 902 images |
| `data/testsets/` | The seven evaluation subsets used for the shift analyses, plus the protocol note that defines them |
| `data/external_baselines/` | Per-image response records for the Pl@ntNet API run and the two vision–language-model runs, including the OCR text-leakage audit |
| `data/open_images/` | The 1,432 openly licensed images and their attribution file (not present until `--images` is staged) |
| `code/dataset/` | Harvesting from iNaturalist and GBIF, licence classification, country normalisation, balancing, splits, negative collection |
| `code/models/` | Training, full-metric evaluation, open-set evaluation, zero-shot probing |
| `code/baselines/` | Pl@ntNet and vision–language-model harnesses, and the text-leakage audit |
| `code/analysis/` | Paired significance tests, confusion analysis, run summarisation |
| `code/paper_artifacts/` | The two scripts that regenerate every table and figure in the paper |
| `code/scripts/` | Shell drivers for the experiment batches |
| `results/` | Per-run configuration, metrics and per-image predictions for all 37 runs |
| `manuscript/` | The tables, figures and section drafts of the paper, plus the LaTeX submission |
| `manuscript/latex/` | `main.tex` — the format actually submitted to the journal — and the vector figure PDFs it includes |
| `code/latex/` | The converter, figure renderer, verifier and build script that produce `main.tex` |
| `docs/` | Data availability, licence layers, reproduction instructions, release checklist |
| `tools/` | Release staging and privacy scanning |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

To regenerate the paper's tables and figures from the released result files:

```bash
python code/paper_artifacts/make_paper_tables.py --out /tmp/tables
python code/paper_artifacts/make_figures.py     --out /tmp/figures
```

Neither script needs a GPU or the images: both read `results/*/test_metrics.json`
and `results/*/predictions.jsonl`.

To retrain the headline model, point the scripts at a local copy of the data:

```bash
export FERN_ROOT=/path/to/working/tree      # where results/, weights/ and data live

python code/models/train_fern.py \
    --backbone bioclip2 --mode linear --img-size 336 \
    --epochs 15 --batch-size 32 --lr 1e-3 \
    --seed 20261010 --out "$FERN_ROOT/results/my_run"
```

Training requires the BioCLIP 2 checkpoint in `$FERN_ROOT/weights/bioclip-2/`,
which is not redistributed here; download it from the
[BioCLIP repository](https://github.com/Imageomics/bioclip-2). DINOv2 weights
are fetched by `timm` on first use.

## Rebuilding the dataset

The harvesting scripts read `API_CONTACT` from the environment and send it in
the request User-Agent, as the iNaturalist and GBIF API guidelines require:

```bash
export API_CONTACT="you@example.org"
python code/dataset/download_dual.py        # iNaturalist + GBIF harvesting
python code/dataset/build_dataset.py        # licence classes, cap at 60/species, splits
python code/dataset/download_negatives.py   # the 700 open-set negatives
python code/dataset/build_testsets.py       # the seven evaluation subsets
```

## Images and licensing

Only images that their source platform released under a permissive licence are
redistributed: CC0, CC BY or CC BY-SA. That is **1,432 of the 5,969 images
(24.0%)**. The remaining 4,537 are licensed under CC BY-NC or CC BY-NC-SA and
are described in the manifest but not redistributed.

**The openly licensed subset is not a random 24%.** It is 63.3% herbarium
specimens, against 28.0% in the benchmark as a whole, because digitisation
programmes release sheets under permissive terms while volunteer field
photographs are predominantly CC BY-NC. In the test split it covers 216 of 902
images overall, but only 69 of 640 field images against 147 of 262 specimen
images. Field-side results and the geographic holdouts therefore **cannot** be
reproduced from the open images alone. See `docs/DATA_AVAILABILITY.md`.

Two licences apply. Code is MIT (`LICENSE`). Manifests, derived tables and
derived metadata are CC BY 4.0 (`LICENSE-DATA.md`); the licence of each image
is unchanged and is recorded per image in the manifest.

## The LaTeX submission

The journal is Elsevier's *Ecological Informatics*, which accepts `.tex`. The
Markdown drafts under `manuscript/text/` are the source of truth; `main.tex` is
generated from them and must never be edited by hand.

```bash
cd manuscript/latex
../../code/latex/build_latex.sh      # convert, render figures, compile, verify
```

The script runs four steps and stops if any fails:

1. `md_to_latex.py` converts the Markdown to `elsarticle`, inlining Tables 1-10
   from the manifests and Figures 1-8, and resolving every citation and cross
   reference.
2. `make_figure_pdfs.py` renders Figures 3-8 as **vector PDF**. Elsevier requires
   at least 1000 dpi for bitmapped line drawings and the source figures are
   600 dpi; vector output has no resolution limit at all.
3. `tectonic` compiles the document.
4. `verify_latex.py` checks the compiled PDF: no unresolved `??` or `undefined`
   references, every numeric token from the Markdown present in the PDF, all
   tables, figures and sections present, and no leaked machine code.

Figures 1 and 2 are referenced in the text but have not been drawn yet; they
appear as clearly marked placeholders so that the references resolve. The design
specification for both is in the paper workspace.

## Using the staging tools

This repository is generated from a working tree rather than edited in place.
`tools/stage_release.py` copies the curated file set, sanitises personal and
machine-specific content while copying, then verifies that everything parses
and that no private material survives:

```bash
python tools/stage_release.py --dry-run     # show the copy plan
python tools/stage_release.py               # stage metadata and code
python tools/stage_release.py --images      # also stage the 1,432 open images
```

`tools/privacy_scan.py` can also be run alone, and exits non-zero if it finds
anything blocking.

## Citation

See `CITATION.cff`. If you use the benchmark, please also cite the source
platforms whose images it draws on, as listed in each manifest row.

## Contact

Issues and questions are welcome through the repository's issue tracker.
