# fern-ecoinformatics

Companion releases for two manuscripts on automated fern identification and
its evaluation protocols.

## `fern_benchmark_ecoinformatics/`

Release for *"Mixed-domain fern benchmarks overstate identification
capability"* (Ecological Informatics submission). Contains the 5,969-image
benchmark manifests, splits, evaluation subsets, open-set negatives, openly
licensed images, and the full code needed to regenerate every table and
figure in the paper.

- `DATA_CARD.md` — what is released and what is not
- `docs/` — licence layers, reproduction notes, release checklist
- `manuscript/` — LaTeX source, tables, figures, text

## `fern_vlm_ecoinformatics/`

Release for the earlier audit of five general-purpose vision–language models
on a 155-image herbarium set, including the text-masking experiments.
**Note:** this audit was re-run on the full benchmark with text-leakage
control in the companion paper; the two sets of numbers are not comparable.

## Citation

See `fern_benchmark_ecoinformatics/CITATION.cff`.
