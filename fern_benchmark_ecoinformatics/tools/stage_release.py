"""Stage the public release of the fern benchmark into a GitHub-ready tree.

Copies a curated set of files from the working directories into this
repository, preserving the layout documented in README.md. Nothing is
copied from the source tree until you run this script, and nothing outside
this repository is ever modified or deleted.

Usage
-----
    python tools/stage_release.py --dry-run     # show what would be copied
    python tools/stage_release.py               # stage metadata and code
    python tools/stage_release.py --images      # also stage the 1,432
                                                # openly licensed images

Run this again before every commit: it keeps the repository in sync with
the working directories, which remain the single source of truth.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
REPO = Path(__file__).resolve().parents[1]

BIO = WORKSPACE / "bioclip_finetune"
EXP = WORKSPACE / "finetune_expansion"
SUB = WORKSPACE / "paper_analysis" / "ei_submission"

# --------------------------------------------------------------------------
# Sanitisation applied while copying. These run on the staged copy only; the
# working tree keeps its original content. Keeping them here rather than in
# the working tree means a re-run always produces a clean copy, so the fixes
# cannot be lost by re-staging.
# --------------------------------------------------------------------------

TEXT_SUFFIXES = {".py", ".sh", ".md", ".csv", ".json", ".jsonl", ".txt", ".cff"}

SANITISE_RULES: list[tuple[str, str, str]] = [
    # A personal contact address in the API User-Agent. Published code must
    # not carry the author's address, and every re-user should identify
    # themselves to the source platforms anyway.
    (r'"contact: [\w.+-]+@[\w.-]+\)"',
     '"contact: " + os.environ.get("API_CONTACT", "") + ")"',
     "personal contact address"),
    # Absolute paths on the author's machine.
    (r'"/home/[A-Za-z0-9._-]+/fern_bioclip"',
     'os.environ.get("FERN_ROOT", ".")',
     "absolute workspace path"),
    (r'/home/[A-Za-z0-9._-]+/fern_venv/bin/python',
     '${FERN_PYTHON:-python3}',
     "absolute interpreter path"),
    (r'/home/[A-Za-z0-9._-]+/models/',
     '<MODEL_DIR>/',
     "absolute model directory"),
    # Private network addresses recorded in internal notes.
    (r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b",
     "<private-ip>",
     "private network address"),
]


LAYOUT_RULES: list[tuple[str, str, str]] = [
    # ROOT was the directory holding results/, plantnet/, vlm/ and weights/
    # in the working tree. In this repository that role belongs to the
    # repository root, one level above where the scripts now live.
    (r"ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent",
     "ROOT = Path(__file__).resolve().parents[2]",
     "root anchor"),
    (r"\nREPO = ROOT\.parent",
     "\nREPO = ROOT",
     "second anchor collapsed into the first"),

    # Paths that crossed between the two sibling working directories.
    (r'REPO / "finetune_expansion/dataset/splits"', 'ROOT / "data/splits"', "splits"),
    (r'REPO / "finetune_expansion/dataset/testsets"', 'ROOT / "data/testsets"', "testsets"),
    (r'REPO / "finetune_expansion/images"', 'ROOT / "data/open_images"', "images"),
    (r'REPO / "ferns_dataset/species_data.json"',
     'ROOT / "data/species_data.json"', "species list"),
    (r'REPO / "paper_analysis/ei_submission/tables"',
     'ROOT / "manuscript/tables"', "default table output"),
    (r'REPO / "paper_analysis/ei_submission/figures"',
     'ROOT / "manuscript/figures"', "default figure output"),
    (r'Path\(__file__\)\.resolve\(\)\.parent\.parent\.parent / \\\n\s*"finetune_expansion/dataset/splits"',
     'Path(__file__).resolve().parents[2] / "data/splits"', "splits, third form"),

    # Baseline records moved under data/external_baselines/.
    (r'ROOT / "plantnet/raw_all_test\.jsonl"',
     'ROOT / "data/external_baselines/plantnet/raw_all_test.jsonl"', "plantnet records"),
    (r'ROOT / "vlm/text_ocr\.jsonl"',
     'ROOT / "data/external_baselines/vlm/text_ocr.jsonl"', "ocr audit"),
    (r'ROOT / "vlm"', 'ROOT / "data/external_baselines/vlm"', "vlm records"),

    # The dataset-building scripts were one level below the workspace root,
    # so their anchor needs one more step up in this layout.
    (r"ROOT = HERE\.parent\b", "ROOT = HERE.parents[1]",
     "root anchor, dataset scripts"),
    (r"ROOT = Path\(__file__\)\.resolve\(\)\.parents\[1\]  # workspace root",
     "ROOT = Path(__file__).resolve().parents[2]  # repository root",
     "root anchor, batch harvester"),
    (r'ROOT / "ferns_dataset" / "species_data\.json"',
     'ROOT / "data" / "species_data.json"', "species list, dataset scripts"),

    # build_testsets.py defined no anchor of its own, so these are resolved
    # from the file location directly.
    (r'HERE / "dataset/splits"',
     'Path(__file__).resolve().parents[2] / "data/splits"', "splits, testsets builder"),
    (r'HERE / "dataset/manifest_balanced\.csv"',
     'Path(__file__).resolve().parents[2] / "data/manifests/manifest_balanced.csv"',
     "balanced manifest, testsets builder"),
    (r'HERE / "dataset/testsets"',
     'Path(__file__).resolve().parents[2] / "data/testsets"', "testsets output"),
]


def adapt_layout(text: str, report: list[tuple[str, str]], rel: str) -> str:
    """Point the scripts at this repository's layout instead of the working
    tree's. Applied to Python only."""
    for pattern, repl, label in LAYOUT_RULES:
        new = re.sub(pattern, repl, text)
        if new != text:
            report.append((rel, f"layout: {label}"))
            text = new
    return text


def ensure_os_import(text: str) -> str:
    """Add `import os` when a substitution introduced `os.environ`.

    The insertion point is the end of the existing import block. It must
    come after `from __future__ import ...`, which has to remain the first
    statement in the file.
    """
    if "os.environ" not in text:
        return text
    if re.search(r"^\s*import os\b", text, re.M):
        return text

    lines = text.split("\n")
    first = next((i for i, l in enumerate(lines)
                  if re.match(r"^(?:import|from) \w", l)), None)
    if first is None:
        return "import os\n" + text

    end, i = first, first
    while i < len(lines):
        if re.match(r"^(?:import|from) \w", lines[i]):
            end, i = i + 1, i + 1
        elif lines[i].strip() == "" and i == first + 1:
            i += 1          # the blank line after `from __future__ import`
        else:
            break
    lines.insert(end, "import os")
    return "\n".join(lines)


def verify(quiet: bool = False) -> int:
    """Parse every staged Python file and shell script.

    Compiling in memory rather than with py_compile keeps the staged tree
    free of __pycache__ directories.
    """
    failures: list[str] = []
    pys = sorted(REPO.rglob("*.py"))
    for p in pys:
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except SyntaxError as exc:
            failures.append(f"{p.relative_to(REPO)}:{exc.lineno}: {exc.msg}")

    shs = sorted(REPO.rglob("*.sh"))
    for p in shs:
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"{p.relative_to(REPO)}: {r.stderr.strip().splitlines()[0]}")

    if not quiet:
        print(f"\n  syntax check: {len(pys)} python, {len(shs)} shell files")
        for f in failures:
            print(f"    FAIL {f}")
        if not failures:
            print("    all files parse")
    return len(failures)


def sanitise(text: str, suffix: str, rel: str,
             report: list[tuple[str, str]]) -> str:
    """Apply every rule to one file's text and record what changed."""
    for pattern, repl, label in SANITISE_RULES:
        if "${FERN_PYTHON" in repl and suffix != ".sh":
            repl = "python3"          # shell syntax is not valid Python
        new = re.sub(pattern, repl, text)
        if new != text:
            report.append((rel, label))
            text = new
    if suffix == ".py":
        text = adapt_layout(text, report, rel)
        text = ensure_os_import(text)
    return text


def copy_file(src: Path, dst: Path, report: list[tuple[str, str]]) -> None:
    """Copy one file, sanitising text in transit.

    Newlines are preserved exactly rather than translated. The table
    generator writes CSV with CRLF line endings, so translating them here
    would make the staged files differ from a fresh run of the released
    scripts, which is the one thing the release has to avoid.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in TEXT_SUFFIXES:
        with open(src, encoding="utf-8", errors="ignore", newline="") as fh:
            text = fh.read()
        cleaned = sanitise(text, src.suffix.lower(),
                           dst.relative_to(REPO).as_posix(), report)
        with open(dst, "w", encoding="utf-8", newline="") as fh:
            fh.write(cleaned)
    else:
        shutil.copy2(src, dst)

# --------------------------------------------------------------------------
# Curated file lists. Each entry is (source, destination relative to REPO).
# Directory sources expand to every file directly inside them.
# --------------------------------------------------------------------------

DATASET_SCRIPTS = [
    "build_dataset.py",
    "build_testsets.py",
    "download_dual.py",
    "download_gbif_bulk.py",
    "download_expansion_batch.py",
    "download_negatives.py",
    "fill_gaps.py",
    "run_bulk_resilient.py",
]

MODEL_SCRIPTS = [
    "train_fern.py",
    "eval_full.py",
    "openset_eval.py",
    "zeroshot_bioclip.py",
    "probe_models.py",
]

ANALYSIS_SCRIPTS = [
    "paired_significance.py",
    "confusion_analysis.py",
    "summarize_runs.py",
    "build_experiment_registry.py",
]

BASELINE_SCRIPTS = [
    "plantnet_eval.py",
    "plantnet_score.py",
    "plantnet_error_analysis.py",
    "vlm_eval.py",
    "vlm_score.py",
    "vlm_leakage.py",
    "vlm_local_eval.py",
    "text_leakage.py",
]

ARTIFACT_SCRIPTS = [
    "make_paper_tables.py",
    "make_figures.py",
]

RUN_SCRIPTS = [
    "run_experiments.sh",
    "run_experiments2.sh",
    "run_experiments3.sh",
    "run_experiments4.sh",
    "run_geo_experiments.sh",
    "run_seed_experiments.sh",
    "retry_ft_seeds.sh",
]


def build_plan() -> list[tuple[Path, Path]]:
    """Return every (source, destination) pair to be staged."""
    plan: list[tuple[Path, Path]] = []

    def add(src: Path, dst: str) -> None:
        plan.append((src, REPO / dst))

    def add_dir(src_dir: Path, dst_dir: str, patterns: tuple[str, ...] = ("*",)) -> None:
        if not src_dir.is_dir():
            return
        for pat in patterns:
            for f in sorted(src_dir.glob(pat)):
                if f.is_file():
                    add(f, f"{dst_dir}/{f.name}")

    # ---- data: manifests, splits, testsets -------------------------------
    ds = EXP / "dataset"
    add(ds / "manifest_full.csv", "data/manifests/manifest_full.csv")
    add(ds / "manifest_balanced.csv", "data/manifests/manifest_balanced.csv")
    add(ds / "release_manifest.csv", "data/manifests/release_manifest.csv")
    add(EXP / "negative_expansion" / "manifest_negatives.csv",
        "data/manifests/manifest_negatives.csv")
    add_dir(ds / "splits", "data/splits", ("*.csv",))
    add_dir(ds / "testsets", "data/testsets", ("*.csv", "*.md",))
    add(WORKSPACE / "ferns_dataset" / "species_data.json",
        "data/species_data.json")

    # ---- data: the two photographs embedded in Fig 1 ----------------------
    # Both are redistributable (CC0 / CC BY) and both ship so that all eight
    # figures regenerate byte-identically inside this repository. Attribution
    # is recorded in CREDITS.md and repeated in the figure caption.
    for sid in ("EXP_01736", "EXP_01734"):
        src = WORKSPACE / "finetune_expansion" / "images" / f"{sid}.jpg"
        add(src, f"data/figure_photos/{sid}.jpg")
    add(Path(__file__).resolve().parent / "PHOTO_CREDITS.md",
        "data/figure_photos/CREDITS.md")

    # ---- data: external baseline records ---------------------------------
    add(BIO / "plantnet" / "raw_all_test.jsonl",
        "data/external_baselines/plantnet/raw_all_test.jsonl")
    add_dir(BIO / "vlm", "data/external_baselines/vlm", ("*.jsonl",))

    # ---- code ------------------------------------------------------------
    for name in DATASET_SCRIPTS:
        add(EXP / name, f"code/dataset/{name}")
    add(BIO / "code" / "clean_country.py", "code/dataset/clean_country.py")
    for name in MODEL_SCRIPTS:
        add(BIO / "code" / name, f"code/models/{name}")
    for name in ANALYSIS_SCRIPTS:
        add(BIO / "code" / name, f"code/analysis/{name}")
    for name in BASELINE_SCRIPTS:
        add(BIO / "code" / name, f"code/baselines/{name}")
    for name in ARTIFACT_SCRIPTS:
        add(BIO / "code" / name, f"code/paper_artifacts/{name}")
    for name in RUN_SCRIPTS:
        add(BIO / "code" / name, f"code/scripts/{name}")

    # ---- results: per-run records ----------------------------------------
    results = BIO / "results"
    if results.is_dir():
        # The registry is the run → configuration → accuracy index that the
        # table and figure scripts read, so it must be present.
        add(results / "registry.csv", "results/registry.csv")
        for run in sorted(results.iterdir()):
            if not run.is_dir() or run.name == "analysis":
                continue
            for f in sorted(run.iterdir()):
                if f.is_file() and f.suffix in {".json", ".jsonl"}:
                    add(f, f"results/{run.name}/{f.name}")
        add_dir(results / "analysis", "results/analysis", ("*.csv", "*.json", "*.md"))
    add(BIO / "EXPERIMENT_LOG.md", "results/EXPERIMENT_LOG.md")

    # ---- manuscript artefacts -------------------------------------------
    add_dir(SUB / "tables", "manuscript/tables", ("*.csv", "*.md"))
    add_dir(SUB / "figures", "manuscript/figures", ("*.png", "*.svg", "*.md"))
    add_dir(SUB / "text", "manuscript/text", ("*.md",))

    # ---- the LaTeX submission -------------------------------------------
    # The .tex is the format actually submitted to the journal, so it ships
    # with the release. Figures 1-2 are authored as PPTX masters (shipped in
    # figure_masters/) and converted by make_fig12_pptx.py; Figures 3-8 are
    # matplotlib renders. Both paths are scripted, so every figure
    # regenerates from this repository.
    add(SUB / "latex" / "main.tex", "manuscript/latex/main.tex")
    for pdf in sorted((SUB / "latex" / "figures").glob("*.pdf")):
        if "mockup" not in pdf.name:
            add(pdf, f"manuscript/latex/figures/{pdf.name}")
    for master in sorted((SUB / "figures").glob("*.pptx")):
        add(master, f"figure_masters/{master.name}")
    for tool in ("md_to_latex.py", "make_figure_pdfs.py",
                 "make_fig12_pptx.py",
                 "check_fig12_numbers.py",
                 "verify_latex.py", "build_latex.sh"):
        src = SUB / "latex" / tool
        if src.exists():
            add(src, f"code/latex/{tool}")

    return plan


def is_excluded(dst: Path) -> bool:
    """Working documents that must not ship with the public release.

    Nothing is excluded at present. The mechanism is kept because the material
    under `manuscript/text/` will grow to include submission paperwork — cover
    letter, reviewer responses, editor correspondence — which should not reach
    the public repository.

    Note on the title page and the back matter: they carry the authors' e-mail
    addresses. That is deliberate. EI publishes the corresponding author's
    address, the author list is supplied by the authors, and the same
    addresses appear in the published article. `tools/privacy_scan.py` reports
    them at INFO level rather than blocking, so they stay visible.
    """
    excluded: set[str] = set()
    try:
        return dst.relative_to(REPO).as_posix() in excluded
    except ValueError:
        return False


def stage_images(dry_run: bool) -> None:
    """Copy the 1,432 openly licensed images and write their licence file."""
    manifest = EXP / "dataset" / "release_manifest.csv"
    if not manifest.exists():
        print(f"  ! release manifest not found: {manifest}")
        return
    rows = [r for r in csv.DictReader(open(manifest, encoding="utf-8"))
            if r.get("releasable") == "yes"]

    out_dir = REPO / "data" / "open_images"
    copied = missing = 0
    licence_rows = []
    for r in rows:
        src = WORKSPACE / r["image_path"]
        dst = out_dir / f"{r['sample_id']}.jpg"
        if src.exists():
            copied += 1
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        else:
            missing += 1
        licence_rows.append({
            "file": f"{r['sample_id']}.jpg",
            "sample_id": r["sample_id"],
            "species": r["species_latin_project"],
            "image_domain": r["image_domain"],
            "source": r["source"],
            "license": r["license"],
            "rights_holder": r["rights_holder"],
            "source_url": r["occurrence_url"] or r["observation_url"],
        })

    if not dry_run and licence_rows:
        out_dir.mkdir(parents=True, exist_ok=True)
        lic = out_dir / "LICENCES.csv"
        with open(lic, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(licence_rows[0].keys()))
            w.writeheader()
            w.writerows(licence_rows)

    print(f"  images: {copied} copied, {missing} not found on disk"
          f"{' (dry run)' if dry_run else ''}")
    if licence_rows:
        print(f"  licence file: data/open_images/LICENCES.csv "
              f"({len(licence_rows)} rows)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="list the copy plan without writing anything")
    ap.add_argument("--images", action="store_true",
                    help="also stage the 1,432 openly licensed images")
    args = ap.parse_args()

    plan = [(s, d) for s, d in build_plan() if not is_excluded(d)]
    skipped = [d for _, d in build_plan() if is_excluded(d)]
    missing = [(s, d) for s, d in plan if not s.exists()]
    ready = [(s, d) for s, d in plan if s.exists()]

    total = sum(s.stat().st_size for s, _ in ready)
    print(f"staging {len(ready)} files ({total / 1e6:.1f} MB) into {REPO.name}/")

    buckets: dict[str, int] = {}
    for _, d in ready:
        top = d.relative_to(REPO).parts[0]
        buckets[top] = buckets.get(top, 0) + 1
    for k, v in sorted(buckets.items()):
        print(f"  {k + '/':<12} {v:4d} files")

    if args.dry_run:
        for s, d in ready:
            print(f"  {s.relative_to(WORKSPACE)}  ->  {d.relative_to(REPO)}")
    else:
        changes: list[tuple[str, str]] = []
        for s, d in ready:
            copy_file(s, d, changes)
        print(f"copied {len(ready)} files")
        if changes:
            by_label: dict[str, set[str]] = {}
            for rel, label in changes:
                by_label.setdefault(label, set()).add(rel)
            print("\n  sanitised while copying:")
            for label, files in sorted(by_label.items()):
                print(f"    {label}: {len(files)} file(s)")
                for f in sorted(files)[:6]:
                    print(f"      {f}")

    if skipped:
        print(f"\n  {len(skipped)} file(s) held back (submission paperwork):")
        for d in skipped:
            print(f"    {d.relative_to(REPO)}")

    if missing:
        print(f"\n  {len(missing)} source file(s) not found:")
        for s, _ in missing:
            print(f"    {s.relative_to(WORKSPACE)}")

    if args.images:
        print("\nstaging openly licensed images:")
        stage_images(args.dry_run)

    if args.dry_run:
        return 0

    # The staged tree is only worth committing if it parses and carries no
    # private material, so both gates run here rather than being left to the
    # author to remember.
    failures = verify()

    print("\n  privacy scan:")
    scan = subprocess.run(
        [sys.executable, str(REPO / "tools" / "privacy_scan.py")],
        capture_output=True, text=True)
    for line in scan.stdout.splitlines():
        print(f"  {line}")
    if scan.returncode != 0:
        failures += 1

    if failures:
        print(f"\n  {failures} blocking problem(s); do not commit yet")
        return 1
    print("\n  release is clean and ready to commit")
    return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
