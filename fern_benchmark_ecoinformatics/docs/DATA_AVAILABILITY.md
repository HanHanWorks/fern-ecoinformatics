# Data availability

This document is the long form of the paper's data availability statement. It
records what is released, what is not, and the consequences of the difference.

## What is released

| Artefact | Rows / files | Location |
|---|---:|---|
| Balanced benchmark manifest | 5,969 | `data/manifests/manifest_balanced.csv` |
| Pre-balancing collection manifest | 6,237 | `data/manifests/manifest_full.csv` |
| Openly licensed subset manifest | 1,432 | `data/manifests/release_manifest.csv` |
| Open-set negative manifest | 700 | `data/manifests/manifest_negatives.csv` |
| Splits | 4,185 / 882 / 902 | `data/splits/` |
| Evaluation subsets | 7 files | `data/testsets/` |
| Pl@ntNet response records | 910 | `data/external_baselines/plantnet/` |
| Vision–language-model records | 7 files | `data/external_baselines/vlm/` |
| OCR text-leakage audit | 902 | `data/external_baselines/vlm/text_ocr.jsonl` |
| Experimental runs | 37 | `results/` |

Each manifest row records the source record identifier, the source URL, the
licence, the rights holder, the image domain, the data source, the country,
the taxonomic assignment, the image dimensions and the SHA-1 digest, and the
group key used to build the splits. This is what allows the restricted images
to be re-obtained from source without this repository holding them.

## What is not released, and why

**4,537 images (76.0%).** They are licensed CC BY-NC (3,783) or CC BY-NC-SA
(754). The NonCommercial clause is the only reason any image is withheld; no
image is withheld because of a platform's terms of use, an unclear rights
holder, or missing provenance.

**Model checkpoints.** BioCLIP 2 and DINOv2 weights are downloaded from their
publishers. They are not redistributed here.

**Credentials.** The Pl@ntNet and vision–language-model runs need keys, read
from environment variables. None are included.

## The open subset is not a random sample

This is the most important limitation of the release, and it is a property of
image licensing rather than of the benchmark design.

| | Balanced benchmark | Open subset |
|---|---:|---:|
| Images | 5,969 | 1,432 (24.0%) |
| Herbarium specimens | 28.0% | **63.3%** |
| GBIF records | 47.1% | **77.6%** |

The cause is a licensing difference between the two sources:

| Source and domain | Redistributable |
|---|---:|
| GBIF, herbarium specimen | 54.3% (907 / 1,669) |
| GBIF, field photograph | 17.8% (204 / 1,143) |
| iNaturalist, field photograph | 10.2% (321 / 3,157) |

Institutional digitisation programmes release sheets under permissive terms.
Volunteer field photographs, which supply the whole field domain, are
predominantly CC BY-NC.

## What this means for reproduction

| Split | Images | Openly licensed | Field open | Specimen open |
|---|---:|---:|---:|---:|
| Train | 4,185 | 995 (23.8%) | 378 / 3,019 (12.5%) | 617 / 1,166 (52.9%) |
| Validation | 882 | 221 (25.1%) | 78 / 641 (12.2%) | 143 / 241 (59.3%) |
| Test | 902 | 216 (23.9%) | 69 / 640 (10.8%) | 147 / 262 (56.1%) |

Three consequences follow.

1. **The specimen-side results are reproducible from the released images.** So
   is the specimen-to-field direction of the domain transfer analysis.
2. **The field-side experiments and the geographic holdouts are not.** Both are
   dominated by field imagery, of which only about a tenth is open.
3. **The full 902-image accuracy cannot be verified from the images alone.** It
   can be verified for the 216-image open portion, for which per-image
   predictions are released.

Anyone who wants to reproduce the full benchmark can reconstruct it from the
manifests and the source platforms, subject to their terms. Anyone who wants a
field-identification benchmark should not treat the open subset as one.

## Where the images live

The 1,432 openly licensed images are deposited as an archive with a DOI rather
than committed to git, because they run to several hundred megabytes. The
archive contains the images, a per-image licence and attribution file
(`LICENCES.csv`), and the release manifest. `tools/stage_release.py --images`
assembles the directory and generates the attribution file.

**Archive DOI:** to be inserted before submission.

## License summary

Code: MIT. Manifests, splits, derived results, documentation: CC BY 4.0.
Images: their original licences, unchanged. See `docs/LICENCE_LAYERS.md` for
the per-licence obligations and the exact attribution fields.

## Licence-class breakdown (long form)

Restricted records, by NonCommercial variant: 3,783 CC BY-NC and 754
CC BY-NC-SA. No image is withheld for platform terms of use, an unclear
rights holder, or missing provenance. Released images by licence:
743 CC0, 618 CC BY, 71 CC BY-SA.

Open-subset coverage by split: test 216 of 902 (23.9%); training
995 of 4,185 (23.8%); validation 221 of 882 (25.1%).
