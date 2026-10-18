# Data card — fern identification benchmark

This card describes the dataset as released. It states what the data is, what
it should and should not be used for, and the limits a user must know before
drawing conclusions from it. The full paper is the reference for method.

## Summary

| | |
|---|---|
| Name | Fern identification benchmark, 5,969 images |
| Content | Images of 152 fern species in 30 families, with field photographs and herbarium specimens |
| Sources | iNaturalist (volunteer observations) and GBIF, the latter including iDigBio-digitised herbarium sheets |
| Annotations | Image domain, data source, country, taxonomic assignment (species, genus, family under PPG I), licence and rights holder, source record identifiers and URLs, image dimensions and SHA-1 |
| Splits | 4,185 train / 882 validation / 902 test, group-aware by observation |
| Evaluation subsets | Seven, over the test split: mixed (902), field (640), specimen (262), iNaturalist (476), GBIF (426), well-sampled species (870), sparsely sampled species (32) |
| Open-set negatives | 700 images in eight groups: horsetail, out-of-scope lycophyte, bryophyte, cycad, palm, angiosperm, fungus, conifer |
| Released images | 1,432 of 5,969 (24.0%), under CC0, CC BY or CC BY-SA |
| Task | Closed-set species classification (152 classes), plus open-set rejection |

## Composition

| Property | Balanced benchmark | Openly licensed subset |
|---|---:|---:|
| Images | 5,969 | 1,432 (24.0%) |
| Species / families | 152 / 30 | — |
| Herbarium specimens | 1,669 (28.0%) | 907 (63.3%) |
| GBIF records | 2,812 (47.1%) | 1,111 (77.6%) |
| Country values (raw strings) | 80 | — |
| Country unresolved | 5.5% | — |

The collection total before balancing was 6,237 images; 268 were removed by a
cap of 60 images per species, drawn round-robin across the two image domains so
that capping did not collapse the domain balance.

## Intended use

- Evaluating closed-set species classification and open-set rejection for
  ferns, and comparing systems on a common image set.
- Measuring the cost of distribution shift along three axes that are labelled
  per image: image domain, data source, and geography.
- Studying confidence calibration and the accuracy–coverage trade-off in a
  fine-grained botanical setting.
- Reusing the harvested manifests to build differently balanced or differently
  split benchmarks: every row records its source record identifier and URL.

## Out-of-scope use

- **Do not treat the released images as a stand-alone field-identification
  benchmark.** They are 63.3% specimens against 28.0% in the full benchmark,
  and cover only 69 of the 640 field test images.
- **Do not compare accuracies computed on this benchmark with accuracies
  computed on a different image set.** The numbers in the paper are tied to
  these 902 test images.
- **Do not use the country annotation for fine-grained geography.** It is
  normalised from 80 raw source strings, and 5.5% of images have no country.
- **Do not read the geographic results as a distance effect.** The dataset
  carries no coordinates; the analysis is region-level, and the paper reports
  the association between holdout cost and out-of-region training support as
  positive but weak.
- **Do not use the model outputs for safety-critical decisions.** The audit of
  general-purpose models found that accuracy on herbarium material is inflated
  by printed label text, and that no system tested is reliable enough to
  identify ferns unsupervised.

## Known biases and limits

1. **Licence-driven sampling bias in the released images.** The open subset
   over-represents herbarium material by a factor of about two relative to the
   benchmark and by a factor of about five in the field domain. This is a
   property of how the two sources license imagery, not of how the benchmark
   was built, but it constrains what can be independently reproduced.
2. **Occurrence-record bias in the underlying data.** Records are uneven in
   space and taxonomy, as in all datasets built on iNaturalist and GBIF. The
   geographic holdouts inherit this.
3. **Class-imbalance control changes the target distribution.** The 60
   images-per-species cap makes the benchmark more uniform than nature. An
   accuracy measured here is not an estimate of accuracy on a random sample of
   occurrences.
4. **The test split covers 150 species, not 152.** Species-level error
   statistics in the paper use 148 species, meaning those with at least two
   test images; two species have a single test image each. This is stated
   because the three counts are easy to confuse.
5. **Domain labels are assigned per image, not per observation.** A single
   occurrence yields images in one domain by construction, and the group-aware
   split keeps them together, but the labels are not independently verified
   for every image.
6. **Negative groups are imbalanced by design.** The angiosperm group holds
   210 images, three times each of the others, so aggregate open-set rates are
   not population estimates.

## Collection and annotation

Images were harvested through the iNaturalist and GBIF APIs under their terms
of use, with a contact address in the request User-Agent as both require.
Licences were classified from the source platform's field: CC0, CC BY, CC BY-SA
and public-domain marks as redistributable, CC BY-NC and CC BY-NC-SA as
restricted. Country strings were normalised to ISO 3166-1 alpha-2 codes with
the raw value retained for audit. Family assignment follows PPG I. Taxonomic
assignment used the source platforms' determinations; no independent
re-identification of specimens was performed.

## Maintenance

The manifests and code are generated from a working tree by
`tools/stage_release.py`, which sanitises and then verifies the staged copy.
Corrections to the manifests are welcome through the issue tracker and will be
issued as a new version with a note in `docs/RELEASE_CHECKLIST.md`.

## Licence

Code: MIT. Manifests, derived results and documentation: CC BY 4.0. Images:
their original licences, recorded per image. See `LICENSE`, `LICENSE-DATA.md`
and `docs/LICENCE_LAYERS.md`.
