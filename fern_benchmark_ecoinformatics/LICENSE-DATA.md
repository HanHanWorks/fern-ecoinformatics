# Data licence — CC BY 4.0

The manifests, split files, evaluation subsets, negative manifest, derived
result records, manuscript tables and figures, and the documentation in this
repository are released under the **Creative Commons Attribution 4.0
International licence (CC BY 4.0)**.

Full text: https://creativecommons.org/licenses/by/4.0/legalcode

You are free to share and adapt this material for any purpose, including
commercially, provided you give appropriate credit, link to the licence, and
indicate whether changes were made.

## What this licence covers

- `data/manifests/*.csv` — image manifests and the open-set negative manifest
- `data/splits/*.csv` — train, validation and test splits
- `data/testsets/*.csv` — the seven evaluation subsets, and `protocol.md`
- `data/external_baselines/**` — per-image response records for the Pl@ntNet
  and vision–language-model runs, and the OCR text-leakage audit
- `results/**` — per-run configuration, metrics and predictions
- `manuscript/**` — tables, figures and section text
- `docs/**` — documentation
- `code/**` and `tools/**` are covered by the MIT licence in `LICENSE`, not by
  this one

## What it does not cover

**Images.** Every image in `data/open_images/` remains under the licence its
source platform recorded for it — CC0, CC BY or CC BY-SA — and this repository
neither relicenses nor sublicenses them. Attribution for each image is in
`data/open_images/LICENCES.csv` and in the `license`, `rights_holder` and
source URL columns of the manifests. If you redistribute the images, you must
satisfy the terms of each image's own licence, which may require naming the
rights holder and linking to the licence.

**Attribution to the source platforms.** The images were obtained from
iNaturalist and GBIF. Cite them as their own terms and citation guidelines
require; the manifest records the source record identifier and URL for every
image so that this is possible for each one individually.

## Attribution

When citing this dataset, please cite the accompanying paper (see
`CITATION.cff`) and note the licence. A suitable form is:

> The fern identification benchmark is released under CC BY 4.0. The images it
> includes remain under their original licences, recorded per image in the
> manifest.
