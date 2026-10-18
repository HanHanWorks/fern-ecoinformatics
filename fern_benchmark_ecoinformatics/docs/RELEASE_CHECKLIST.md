# Release checklist

Run through this before the first push, and again before any later release.

## 1. Decisions to make first

These cannot be automated and are the only things standing between the current
state and a publishable repository.

### Repository name and owner

The absolute paths in `CITATION.cff`, `docs/DATA_AVAILABILITY.md` and the
manuscript's data availability statement still hold placeholders.

- [ ] Choose the GitHub owner and repository name
- [ ] Replace `REPLACE_OWNER/REPLACE_REPO` in `CITATION.cff` (still the only
      unfilled placeholder in that file)
- [ ] Replace `[repository URL]` in the manuscript's data availability
      statement (`manuscript/text/11_data_code_availability.md`)
- [ ] Decide whether to reuse the existing account
      (`HanHanWorks`) or open a new one. Note that the earlier
      fern-vision-language-model repository is a **different paper** and should
      not be reused or renamed.

### Author metadata

- [x] Authors block in `CITATION.cff`: filled with the five authors, their
      affiliations and the corresponding author (2026-10-14).
- [x] Licence choice confirmed: MIT for code, CC BY 4.0 for the data.
- [x] `manuscript/text/00_title_page.md` and `97_back_matter.md` carry the
      title page, CRediT contributions, funding and the declarations.
- [ ] **Privacy decision to confirm.** The title page contains the five authors'
      e-mail addresses. EI publishes the corresponding author's address and the
      same addresses appear in the published article, so shipping them here is
      consistent — but it does mean the release makes five personal addresses
      public. `tools/privacy_scan.py` reports them at INFO level rather than
      blocking, so they remain visible. If you would rather not ship them, add
      `manuscript/text/00_title_page.md` to the exclusion set in
      `tools/stage_release.py::is_excluded`. The address was deliberately left
      out of `CITATION.cff` for the same reason.

### Where the images go

The 1,432 openly licensed images are several hundred megabytes and are
**excluded from git** (see `.gitignore`). The recommended route is a Zenodo or
figshare deposit with its own DOI, which also gives the manuscript's
"archived at [DOI]" a target.

- [ ] Decide: Zenodo, figshare, or neither
- [ ] If depositing: `python tools/stage_release.py --images`, then archive
      `data/open_images/` including the generated `LICENCES.csv`
- [ ] Insert the archive DOI in `docs/DATA_AVAILABILITY.md` and in the
      manuscript's data availability statement
- [ ] If not depositing, say so explicitly in the manuscript rather than
      leaving the DOI placeholder

### Open decision carried over from the manuscript

- [ ] Figures 3–8 are currently six separate files, but their titles carry
      panel letters A–H, meaning they were drawn as one composite. Decide
      between combining them into a single Figure 3 with panels A–H, or
      removing the in-figure letters and keeping six figures. The manuscript
      text currently assumes six separate figures. `docs/` does not affect this
      choice; it is listed here because it changes what ships in
      `manuscript/figures/`.

## 2. Stage and verify

```bash
python tools/stage_release.py                 # stage, sanitise, then verify
python tools/stage_release.py --dry-run       # review the copy plan first
```

The staging script runs two gates automatically and returns non-zero if either
fails:

- **Syntax check** — every staged `.py` is compiled in memory and every `.sh`
  is parsed with `bash -n`. This exists because an earlier version of the
  sanitiser inserted `import os` above `from __future__ import annotations`,
  which broke ten files. The check is what caught it.
- **Privacy scan** — `tools/privacy_scan.py` scans for private IP addresses,
  SSH targets, credentials, personal contact addresses, absolute local paths
  and leftover TODO markers.

- [ ] Both gates report clean
- [ ] Read the "sanitised while copying" list and confirm each change is
      intended

## 3. Verify reproducibility

```bash
python code/paper_artifacts/make_paper_tables.py --out /tmp/t
python code/paper_artifacts/make_figures.py     --out /tmp/f
```

- [ ] Tables 1–10 match `manuscript/tables/` byte for byte
- [ ] Figures 3–8 match `manuscript/figures/` byte for byte

At the time of writing, 22 table files and 6 figures reproduce exactly. If a
file differs, something in the staging sanitisation or the layout adaptation
has broken the release. Do not commit until it is resolved.

## 4. Manual review

The scanner cannot judge these. Read the staged files.

- [ ] **`results/EXPERIMENT_LOG.md` and
      `code/analysis/build_experiment_registry.py`** contain internal
      engineering notes in Chinese, including a table of problems found and
      fixes made. They document the label-space protocol correction, which is
      scientifically relevant and disclosed in the paper. Keep or trim
      deliberately; the private IP addresses in them have already been
      replaced with `<private-ip>`.
- [ ] **`manuscript/text/*.md`** are the paper's drafts. Confirm that shipping
      the drafts alongside the code is intended. They are useful for
      transparency and harmless if the paper is published, but they will go
      stale.
- [ ] **`data/external_baselines/vlm/*.jsonl`** contain the models' verbose
      raw outputs. They carry no credentials, and they are the evidence behind
      the text-leakage claim, but they are the largest text files in the
      repository. Strip the `raw` field if repository size matters more than
      having the audit directly inspectable.
- [ ] **Manifest privacy.** The manifests contain observation URLs and the
      names of photographers and institutions. This is required for CC BY
      attribution and is already public on the source platforms. Confirm you
      are comfortable with it.
- [ ] **`data/species_data.json`** carries a `source` field crediting a
      Chinese plant atlas. Confirm that releasing the species list is fine, and
      decide whether the manuscript needs a formal citation for it.

## 5. Publish

```bash
cd github_ready/fern_benchmark_ecoinformatics
git init -b main
git add -A
git status                      # confirm no images, credentials or checkpoints
git commit -m "Fern identification benchmark: data, code and derived results"
git remote add origin git@github.com:<owner>/<repo>.git
git push -u origin main
```

- [ ] `git status` shows no `*.jpg` under `data/open_images/`, no `.env`, no
      `weights/`
- [ ] `.gitattributes` is present, so git does not normalise the CRLF CSV
      files
- [ ] Repository description and topics set
- [ ] `README.md` renders correctly on GitHub

## 6. After publication

- [ ] Insert the repository URL and the archive DOI into the manuscript's data
      availability statement and remove `[repository URL]` / `[DOI]`
- [ ] Archive a snapshot: GitHub's "release" plus Zenodo integration issues a
      DOI for the exact tagged commit, which is what the manuscript should
      cite
- [ ] Record the release date and any later corrections here

## Corrections log

Record any post-publication correction to the manifests or code here, so that a
reader can tell which version they have.

| Date | Version | Change |
|---|---|---|
| 2026-10-14 | 1.0.0 | Initial release |
