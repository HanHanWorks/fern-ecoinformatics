#!/usr/bin/env python3
"""Generate the elsarticle LaTeX submission from the Markdown source of truth.

The Markdown under ``text/`` is the single source of truth. This script is the
only way ``main.tex`` is produced; never edit ``main.tex`` by hand, because the
next run would silently discard the edit.

Structure produced
------------------
front matter  : title page, authors, affiliations, corresponding author,
                abstract, keywords, first-page abbreviation note
body          : Sections 2-12, converted from ``text/0N_*.md``
floats        : Tables 1-10 inlined from ``tables/tab*.md`` after their first
                textual reference; Figures 1-8 after their first reference
back matter   : CRediT, funding, competing interests, generative-AI
                declaration, data availability
references    : ``thebibliography`` with natbib author-year labels

Chinese working notes that live in ``text/00_*.md`` and ``text/97_*.md`` are
excluded here: those four files are read by dedicated builders that take only
the English fields. Sections 2-12 contain no Chinese.

Usage
-----
    python md_to_latex.py                # write main.tex
    python md_to_latex.py --check-only   # report what would be emitted
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUB = HERE.parent
TEXT = SUB / "text"
TABLES = SUB / "tables"
FIGDIR = SUB / "figures"
OUT = HERE / "main.tex"

BODY_FILES = [
    "01_introduction.md",
    "02_construction_pipeline.md",
    "03_model_recipe.md",
    "04_domain_source_shift.md",
    "05_geographic_shift.md",
    "06_baselines_vlm_audit.md",
    "07_error_structure.md",
    "08_open_set_rejection.md",
    "09_discussion.md",
    "12_conclusion.md",
    "11_data_code_availability.md",
]

TITLE = ("Two axes of distribution shift in automated fern identification: "
         "image domain and geography, quantified on a 5,969-image, "
         "152-species benchmark")

AUTHORS = [
    ("Zihao Huang", ["a", "b"], "2309392013@st.gxu.edu.cn", False),
    ("Yan Chen", ["a", "b"], "cy@gxu.edu.cn", False),
    ("Yeming You", ["c"], "youyeming@163.com", False),
    ("Qi Zhang", ["d"], "friendlyqi-work@foxmail.com", False),
    ("Kai Su", ["c"], "20210055@gxu.edu.cn", True),   # corresponding author
]

AFFILIATIONS = [
    ("a", "Guangxi Key Laboratory of Digital Infrastructure, Guangxi Zhuang "
          "Autonomous Region Information Center, Nanning 530000, China"),
    ("b", "School of Computer and Electronic Information, Guangxi University, "
          "Nanning 530000, China"),
    ("c", "Guangxi Colleges and Universities Key Laboratory for Cultivation and "
          "Utilization of Subtropical Forest Plantation, Key Laboratory of "
          "National Forestry and Grassland Administration on Cultivation of "
          "Fast-Growing Timber in Central South China, School of Forestry, "
          "Guangxi University, Nanning 530004, China"),
    ("d", "China Post Group Co., Ltd. Nanning Branch, Nanning 530000, China"),
]

CORRESPONDING_EMAIL = "20210055@gxu.edu.cn"

# ---------------------------------------------------------------------------
# Figure captions. Figures 1 and 2 follow the agreed design specification;
# Figures 3-8 are written here because no caption text exists for them in the
# Markdown source, and the manuscript cannot be assembled without them.
# ---------------------------------------------------------------------------
FIG_CAPTIONS = {
    1: ("From research benchmark to field-ready AI: a falsification framework "
        "for automated fern identification. The two image regimes of one "
        "species, *Cyrtomium macrophyllum* (Dryopteridaceae), are field "
        "photographs (CC BY, Cynthia Su) and herbarium sheets (CC0, US "
        "National Herbarium, Smithsonian Institution). A conventionally "
        "split benchmark reports 91.4 ± 0.7% over 5,969 images covering 152 "
        "species in 30 families. With both regimes represented during "
        "training the model reaches 0.9198 on sheets and 0.9250 on field "
        "photographs; separating the regimes between training and test drops "
        "accuracy to 0.4238–0.6538. Three hidden assumptions — image domain, "
        "geography and text leakage — are each tested by a controlled "
        "falsification test (T1–T3). Benchmark accuracy alone therefore does "
        "not make a model field-ready: the same model supports open-set "
        "rejection and selective acceptance, and a deployment decision "
        "pipeline routes field data through model inference and risk "
        "assessment to an accept, abstain, reject or review decision."),
    2: ("Benchmark construction. Records were retrieved from iNaturalist "
        "research-grade observations and from GBIF, including iDigBio-digitised "
        "herbarium sheets. The collected pool of 6,237 images was classified by "
        "licence, capped at 60 images per species and reduced to a working set of "
        "5,969 images covering 152 species in 30 families, annotated with image "
        "domain, data source and normalised country, and split by observation "
        "into 4,185 training, 882 validation and 902 test images. A separate set "
        "of 700 fern-like negatives is used for evaluation only and never enters "
        "training."),
    3: ("Species top-1 accuracy on the 902-image test split for eleven "
        "configurations of backbone, adaptation mode, input resolution and head "
        "design, with the frozen linear probe at 336 px shown first. The "
        "hierarchical head is the only configuration below the general-purpose "
        "self-supervised backbone. Error bars are the standard deviation over "
        "three seeds where available; single-seed configurations are marked."),
    4: ("Cost of transferring across image domain or data source, each measured "
        "against an in-domain baseline computed on the identical subset of test "
        "images, so the difference isolates the effect of the split rather than "
        "the difficulty of the subset. Crosses mark the values published under "
        "the earlier label-space protocol, which are superseded."),
    5: ("Leave-one-region-out geographic holdout. (a) Accuracy of the holdout "
        "model against the in-domain model scored on the same test images. "
        "(b) Absolute accuracy for each held-out region. (c) The accuracy drop "
        "against the share of the region's test species with at most five "
        "training images from outside that region. The association is positive "
        "but weak, and the aggregate point for the China region is shown "
        "separately."),
    6: ("Reliability diagram for the specialist classifier and for the "
        "Pl@ntNet service on the shared test images. The classifier is "
        "systematically under-confident: its stated confidence falls below its "
        "observed accuracy in every bin, and its most confident bin is correct "
        "on every image it contains."),
    7: ("Risk-coverage curve for the specialist classifier and for the two "
        "general-purpose vision--language models, with the same curves for the "
        "Pl@ntNet service. Coverage is the fraction of images accepted at a "
        "given confidence threshold; risk is the error rate among accepted "
        "images."),
    8: ("Error structure of the classifier and of the Pl@ntNet service. "
        "(a) Distribution of errors by taxonomic distance from the true species. "
        "(b) Per-family accuracy for the families with at least five test "
        "images. The classifier's remaining errors are confusions between "
        "congeneric species, whereas the service's errors frequently leave the "
        "family."),
}

FIG_FILES = {
    1: "Figure1_workflow.png",
    2: "Figure2_pipeline.png",
    3: "Figure3_main_results.png",
    4: "Figure4_transfer_drops.png",
    5: "Figure5_geographic_holdout.png",
    6: "Figure6_reliability.png",
    7: "Figure7_risk_coverage.png",
    8: "Figure8_error_structure.png",
}

NON_ASCII = {
    "\u2013": "--", "\u2014": "---", "\u00b1": r"$\pm$", "\u2212": r"$-$",
    "\u2264": r"$\leq$", "\u2265": r"$\geq$", "\u2248": r"$\approx$",
    "\u00d7": r"$\times$", "\u0394": r"$\Delta$", "\u03c1": r"$\rho$",
    "\u00a7": r"\S{}", "\u2020": r"\dag{}", "\u2192": r"$\rightarrow$",
    "\u2026": r"\ldots{}",
    "\u00e4": r'\"a', "\u00eb": r'\"e', "\u00f8": r"\o{}", "\u0107": r"\'c",
}

PLACEHOLDER = "\x00{}\x00"


# ---------------------------------------------------------------------------
# escaping and inline rendering
# ---------------------------------------------------------------------------
def escape_plain(text: str) -> str:
    """Escape TeX special characters in text that carries no markup."""
    out = text.replace("\\", r"\textbackslash{}")
    for ch, rep in (("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                    ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                    ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
                    ("<", r"\textless{}"), (">", r"\textgreater{}")):
        out = out.replace(ch, rep)
    return out


def stash(value: str, store: list[str]) -> str:
    """Park a rendered fragment so later escaping cannot touch it."""
    store.append(value)
    return PLACEHOLDER.format(len(store) - 1)


def esc_outside_placeholders(text: str) -> str:
    """Escape TeX specials everywhere except inside stashed fragments."""
    parts = re.split(r"(\x00\d+\x00)", text)
    return "".join(p if re.fullmatch(r"\x00\d+\x00", p) else escape_plain(p)
                   for p in parts)


class Inliner:
    """Renders Markdown inline markup to LaTeX, using placeholders throughout."""

    def __init__(self, cite_keys: dict[tuple[str, str], str]):
        self.cite_keys = cite_keys
        self.stats = {"citations": 0, "unmapped_citations": []}

    # -- citation ---------------------------------------------------------
    def key_for(self, surname: str, year: str) -> str | None:
        norm = self.norm_surname(surname)
        return self.cite_keys.get((norm, year))

    @staticmethod
    def norm_surname(surname: str) -> str:
        s = unicodedata.normalize("NFD", surname)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z]", "", s.lower())

    def render_citations(self, text: str, store: list[str]) -> str:
        # parenthetical: (Author et al., 2020; Other, 2019)
        def paren(m: re.Match) -> str:
            body = m.group(1)
            keys, missing = [], []
            for part in body.split(";"):
                part = part.strip().rstrip(".")
                mm = re.match(r"^(.*?)(?:,|\s+et al\.?|\s+and\s+[A-Z][a-z]+)?\s*"
                              r"(?:\(?)((?:19|20)\d{2}[a-z]?)\)?$", part)
                if not mm:
                    continue
                surname = re.split(r",|\bet al\.|\band\b|&", mm.group(1))[0].strip()
                year = mm.group(2)
                k = self.key_for(surname, year)
                if k:
                    keys.append(k)
                else:
                    missing.append(f"{surname} {year}")
            if not keys:
                return m.group(0)
            self.stats["citations"] += 1
            for m_ in missing:
                self.stats["unmapped_citations"].append(m_)
            return stash("\\citep{" + ",".join(keys) + "}", store)

        text = re.sub(
            r"\(([A-Z\u00c4\u00d6\u00dc][^()]{0,120}?"
            r"(?:19|20)\d{2}[a-z]?(?:\s*;\s*[^()]{0,80}?(?:19|20)\d{2}[a-z]?)*)\)",
            paren, text)

        # narrative: Author et al. (2020)
        def narr(m: re.Match) -> str:
            surname = m.group(1).replace(" et al.", "").replace(" and", "").strip()
            k = self.key_for(surname, m.group(2))
            if not k:
                self.stats["unmapped_citations"].append(
                    f"{surname} {m.group(2)} (narrative)")
                return m.group(0)
            self.stats["citations"] += 1
            return stash(f"\\citet{{{k}}}", store)

        text = re.sub(
            r"\b([A-Z\u00c4\u00d6\u00dc][a-z\u00e4\u00f6\u00fc'-]+)"
            r"(?: et al\.)?\s*\(((?:19|20)\d{2}[a-z]?)\)", narr, text)
        return text

    # -- cross references -------------------------------------------------
    @staticmethod
    def render_refs(text: str, store: list[str]) -> str:
        rules = [
            (r"\bTables (\d+) and (\d+)", r"Tables~\ref{tab:\1} and~\ref{tab:\2}"),
            (r"\bTables (\d+)--(\d+)", r"Tables~\ref{tab:\1}--\ref{tab:\2}"),
            (r"\bTable (\d+)", r"Table~\ref{tab:\1}"),
            (r"\bFigures (\d+) and (\d+)",
             r"Figures~\ref{fig:\1} and~\ref{fig:\2}"),
            (r"\bFigures (\d+)--(\d+)", r"Figures~\ref{fig:\1}--\ref{fig:\2}"),
            (r"\bFigure (\d+)", r"Figure~\ref{fig:\1}"),
            (r"\bSections (\d+) and (\d+)",
             r"Sections~\ref{sec:\1} and~\ref{sec:\2}"),
            (r"\bSections (\d+) to (\d+)",
             r"Sections~\ref{sec:\1} to~\ref{sec:\2}"),
            (r"\bSection (\d+(?:\.\d+)?)", r"Section~\ref{sec:\1}"),
        ]
        for pat, rep in rules:
            # The replacement contains backslashes and braces, so it has to be
            # stashed like any other rendered fragment. Inserting it directly
            # would let the escaping pass turn it into \ref{} spelled out.
            # Note: re.Match.expand must NOT be used here, because it reads
            # \r in the template as a carriage return and silently eats the
            # leading "r" of \ref.
            def repl(m, template=rep):
                out = template
                for i in range(1, (m.re.groups or 0) + 1):
                    out = out.replace("\\%d" % i, m.group(i) or "")
                return stash(out, store)
            text = re.sub(pat, repl, text)
        return text

    # -- inner pass: emphasis only ------------------------------------------
    def _inner(self, text: str, store: list[str]) -> str:
        # Escape once, up front. Emphasis markers are not TeX specials, so
        # they survive; the fragments already stashed do not.
        text = esc_outside_placeholders(text)
        text = re.sub(r"\*\*(.+?)\*\*",
                      lambda m: stash("\\textbf{" + m.group(1) + "}", store), text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)",
                      lambda m: stash("\\emph{" + m.group(1) + "}", store), text)
        return text

    # -- main entry -------------------------------------------------------
    def render(self, text: str) -> str:
        store: list[str] = []

        # 1. Citations and cross references run first, on the raw text, so
        #    that accented surnames (Goeau, Mader) are still intact when the
        #    reference keys are looked up. Everything they produce is stashed
        #    and therefore immune to the escaping that follows.
        text = self.render_citations(text, store)
        text = self.render_refs(text, store)

        # 2. non-ASCII to placeholders, so escaping cannot corrupt the accents
        for ch in NON_ASCII:
            if ch in text:
                text = text.replace(ch, stash(NON_ASCII[ch], store))

        # 3. code spans
        def code(m: re.Match) -> str:
            inner = escape_plain(m.group(1))
            inner = inner.replace("/", "/\\allowbreak{}").replace(".", ".\\allowbreak{}")
            return stash("\\texttt{" + inner + "}", store)
        text = re.sub(r"`([^`]+)`", code, text)

        # 4. inline math is left untouched by this manuscript, but guard it
        def math(m: re.Match) -> str:
            return stash(m.group(0), store)
        text = re.sub(r"\$[^$]+\$", math, text)

        # 5. bare URLs, before escaping so their punctuation survives
        def url(m: re.Match) -> str:
            u = m.group(0)
            trail = ""
            while u and u[-1] in ".,;:":
                trail = u[-1] + trail
                u = u[:-1]
            return stash("\\url{" + u + "}", store) + trail
        text = re.sub(r"https?://[^\s()<>]+", url, text)

        # 6. emphasis
        text = self._inner(text, store)

        # 7. double quotes to TeX quotes. _inner has already escaped the plain
        # text, and quote marks are not TeX specials, so this is safe to run
        # afterwards. Escaping again here would double-escape everything.
        text = re.sub(r'"([^"]*)"', lambda m: "``" + m.group(1) + "''", text)

        # 8. restore placeholders until stable
        for _ in range(8):
            if "\x00" not in text:
                break
            text = re.sub(
                PLACEHOLDER.format(r"(\d+)"),
                lambda m: store[int(m.group(1))], text)
        return text.strip()


# ---------------------------------------------------------------------------
# references
# ---------------------------------------------------------------------------
def parse_references() -> list[tuple[str, str, str]]:
    """Return (key, natbib label, body) for each reference in the Introduction."""
    text = (TEXT / "01_introduction.md").read_text(encoding="utf-8")
    if "## References" not in text:
        return []
    tail = text.split("## References", 1)[1]
    entries = [l.strip() for l in tail.splitlines()
               if l.strip() and re.match(r"^[A-Z\u00c4\u00d6\u00dc]", l.strip())]

    out, used = [], {}
    for entry in entries:
        m = re.search(r"\((\d{4}[a-z]?)\)\.\s*", entry)
        if not m:
            raise SystemExit(f"cannot find year in reference: {entry[:90]}")
        year = m.group(1)
        author_part = entry[:m.start()].rstrip(" .")
        body = entry[m.end():]

        surname_raw = author_part.split(",")[0].strip().rstrip(".")
        norm = Inliner.norm_surname(surname_raw)
        key = f"{norm}{year}"
        if key in used:                       # same author, same year
            used[key] += 1
            key = f"{key}{chr(ord('a') + used[key] - 1)}"
        else:
            used[key] = 0

        if "et al" in author_part or author_part.count(",") > 1 or "&" in author_part:
            label = f"{surname_raw} et al.({year})"
        elif author_part.count(",") == 1:
            second = author_part.split(",")[1].strip().split()[0].rstrip(".")
            label = f"{surname_raw} and {second}({year})"
        else:
            label = f"{surname_raw}({year})"
        out.append((key, label, body))
    return out


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
def parse_table(n: int) -> dict | None:
    """Find and parse the table file for Table n."""
    for path in sorted(TABLES.glob(f"tab{n}_*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        title, note, rows = "", "", []
        for line in lines:
            s = line.strip()
            if s.startswith("**Table"):
                title = s.strip("*").strip()
                title = re.sub(r"^Table \d+\.\s*", "", title)
            elif s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            elif s and not note and not s.startswith("|"):
                note = s
        if not rows:
            raise SystemExit(f"no table body found in {path}")
        return {"title": title, "note": note, "rows": rows,
                "path": path.name}
    return None


def visual_len(cell: str) -> str:
    """Strip LaTeX and math when measuring a cell's rendered width."""
    s = re.sub(r"\\[a-zA-Z]+\*?", "", cell)
    s = re.sub(r"\$[^$]*\$", "0" * 4, s)
    return s


def table_latex(n: int, inliner: "Inliner") -> str:
    spec = parse_table(n)
    if spec is None:
        raise SystemExit(f"table {n} referenced in text but no file in tables/")
    rows, header, body = spec["rows"], spec["rows"][0], spec["rows"][1:]
    ncol = len(header)

    align_row = "l" * ncol
    widths = [max(len(visual_len(r[i])) for r in rows) for i in range(ncol)]
    total = sum(widths) + 3 * ncol

    # tabularx requires the \hsize factors of the X columns to add up to the
    # number of X columns. Getting that sum wrong silently squeezes every
    # column instead of raising an error, which is what produced the mangled
    # Table 1 in the first build.
    long_idx = [i for i in range(ncol) if widths[i] >= 26]
    use_tabularx = bool(long_idx) and ncol <= 4
    if use_tabularx:
        nx = len(long_idx)
        wsum = sum(widths[i] for i in long_idx)
        raw = {i: widths[i] / wsum * nx for i in long_idx}
        # Every X column gets at least an equal share; without that floor a
        # short-but-wide column like "Item" is squeezed to a fifth of the
        # table and every cell in it wraps to three lines.
        factors = {i: max(1.0, round(v, 1)) for i, v in raw.items()}
        drift = round(nx - sum(factors.values()), 1)
        while abs(drift) >= 0.05:
            widest = max(long_idx, key=lambda i: factors[i])
            factors[widest] = round(factors[widest] + drift, 1)
            drift = round(nx - sum(factors.values()), 1)
        cols = []
        for i in range(ncol):
            if i in long_idx:
                cols.append(">{\\raggedright\\arraybackslash\\hsize=%.1f\\hsize}X"
                            % factors[i])
            else:
                cols.append("l")
        begin = r"\begin{tabularx}{\linewidth}{" + " ".join(cols) + "}"
        end = r"\end{tabularx}"
    else:
        begin = r"\begin{tabular}{" + align_row + "}"
        end = r"\end{tabular}"

    def cells(row):
        return " & ".join(inliner.render(c) for c in row)

    lines = [begin, r"\toprule", cells(header) + r" \\", r"\midrule"]
    for r in body:
        lines.append(cells(r) + r" \\")
    lines += [r"\bottomrule", end]

    block = "\n".join(lines)
    scaled = not use_tabularx and (ncol >= 6 or total > 72)
    if scaled:
        block = "\\resizebox{\\linewidth}{!}{%\n" + block + "\n}"

    # threeparttable must not sit inside \resizebox: it needs vertical mode and
    # the combination makes TeX abort with "Missing \endgroup inserted". Wide
    # tables therefore carry their note as a plain paragraph instead.
    note_tex = ""
    if spec["note"]:
        if scaled:
            note_tex = ("\\par\\vspace{3pt}\n"
                        "\\noindent\\begin{minipage}{\\linewidth}\\footnotesize\n"
                        "Note. " + inliner.render(spec["note"]) + "\n"
                        "\\end{minipage}")
        else:
            note_tex = (r"\begin{tablenotes}\footnotesize" + "\n"
                        r"\item Note. " + inliner.render(spec["note"]) + "\n"
                        r"\end{tablenotes}")

    if scaled:
        return (
            "\\begin{table}[tbp]\n\\centering\n"
            f"\\caption{{{inliner.render(spec['title'])}}}\n"
            f"\\label{{tab:{n}}}\n"
            f"{block}\n"
            f"{note_tex}\n"
            "\\end{table}")

    return (
        "\\begin{table}[tbp]\n\\centering\n"
        "\\begin{threeparttable}\n"
        f"\\caption{{{inliner.render(spec['title'])}}}\n"
        f"\\label{{tab:{n}}}\n"
        f"{block}\n"
        f"{note_tex}\n"
        "\\end{threeparttable}\n"
        "\\end{table}")


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
def figure_latex(n: int, inliner: "Inliner") -> str:
    cap = inliner.render(FIG_CAPTIONS[n])
    fname = FIG_FILES[n]
    if fname is None:
        art = ("\\fbox{\\begin{minipage}{0.86\\linewidth}\\centering\\footnotesize\n"
               f"Figure {n} has not been drawn yet. The design specification is in "
               "\\texttt{figures/FIG1\\_FIG2\\_design\\_spec.md}.\n"
               "\\end{minipage}}")
        width = ""
    else:
        art = f"\\includegraphics[width=\\linewidth]{{figures/{Path(fname).stem}.pdf}}"
    return (
        "\\begin{figure}[tbp]\n\\centering\n"
        f"{art}\n"
        f"\\caption{{{cap}}}\n"
        f"\\label{{fig:{n}}}\n"
        "\\end{figure}")


# ---------------------------------------------------------------------------
# body conversion
# ---------------------------------------------------------------------------
def convert_body(inliner: "Inliner") -> tuple[str, dict]:
    emitted_tables: set[int] = set()
    emitted_figures: set[int] = set()
    chunks: list[str] = []
    # Subsection headings in the Markdown carry no trailing period
    # ("## 5.1 Transfer protocol"), so the period is optional.
    sec_re = re.compile(r"^#{1,3}\s+(\d+(?:\.\d+)?)\.?\s+(.*)$")

    for fname in BODY_FILES:
        raw = (TEXT / fname).read_text(encoding="utf-8")
        blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
        # The Introduction ends with a Markdown reference list. Those entries
        # are collected by parse_references() and emitted as thebibliography,
        # so everything from the heading onwards must be skipped here.
        in_references = False
        for block in blocks:
            lines = block.splitlines()

            # ---- references section -------------------------------------
            if lines[0].strip() == "## References":
                in_references = True
                continue
            if in_references:
                continue

            # ---- headings ------------------------------------------------
            m = sec_re.match(lines[0])
            if m and len(lines) == 1:
                num, text = m.group(1), m.group(2)
                label = f"sec:{num}"
                if "." not in num:
                    chunks.append(f"\\setcounter{{section}}{{{int(num) - 1}}}")
                    chunks.append(f"\\section{{{inliner.render(text)}}}"
                                  f"\\label{{{label}}}")
                else:
                    a, b = num.split(".")
                    # \subsection does not increment the section counter, so
                    # the section counter has to be set to the section itself,
                    # not to one less than it. Getting this wrong prints
                    # "9.5" for a subsection numbered 10.5.
                    chunks.append(f"\\setcounter{{section}}{{{int(a)}}}")
                    chunks.append(f"\\setcounter{{subsection}}{{{int(b) - 1}}}")
                    chunks.append(f"\\subsection{{{inliner.render(text)}}}"
                                  f"\\label{{{label}}}")
                continue

            # ---- pipe table (none expected in the body) -------------------
            if all(l.strip().startswith("|") for l in lines):
                continue

            # ---- block quote ---------------------------------------------
            if all(l.strip().startswith(">") for l in lines):
                inner = "\n".join(l.strip().lstrip(">").strip() for l in lines)
                chunks.append("\\begin{quote}\n" + inliner.render(inner)
                              + "\n\\end{quote}")
                continue

            # ---- lists ---------------------------------------------------
            if all(l.lstrip().startswith(("- ", "* ")) for l in lines):
                items = [inliner.render(re.sub(r"^\s*[-*]\s+", "", l))
                         for l in lines]
                chunks.append("\\begin{itemize}\n"
                              + "\n".join(f"\\item {i}" for i in items)
                              + "\n\\end{itemize}")
                continue
            if all(re.match(r"^\s*\d+\.\s", l) for l in lines):
                items = [inliner.render(re.sub(r"^\s*\d+\.\s+", "", l))
                         for l in lines]
                chunks.append("\\begin{enumerate}\n"
                              + "\n".join(f"\\item {i}" for i in items)
                              + "\n\\end{enumerate}")
                continue

            # ---- paragraph -----------------------------------------------
            para = inliner.render(" ".join(l.strip() for l in lines))
            if not para:
                continue
            chunks.append(para)

            # ---- floats, after the paragraph that first mentions them -----
            for t in sorted({int(x) for x in re.findall(r"Table (\d+)", block)}):
                if t not in emitted_tables and parse_table(t):
                    emitted_tables.add(t)
                    chunks.append(table_latex(t, inliner))
            for f in sorted({int(x) for x in re.findall(r"Figure (\d+)", block)}):
                if f not in emitted_figures:
                    emitted_figures.add(f)
                    chunks.append(figure_latex(f, inliner))

    missing = [t for t in range(1, 11) if t not in emitted_tables]
    missing_fig = [f for f in range(1, 9) if f not in emitted_figures]
    stats = {"tables_emitted": sorted(emitted_tables),
             "figures_emitted": sorted(emitted_figures),
             "tables_never_referenced": missing,
             "figures_never_referenced": missing_fig}
    return "\n\n".join(chunks), stats


# ---------------------------------------------------------------------------
# front matter, abstract, back matter
# ---------------------------------------------------------------------------
def extract_abstract() -> tuple[str, str]:
    """Pull the abstract paragraph and the keyword line from 00_abstract.md."""
    raw = (TEXT / "00_abstract.md").read_text(encoding="utf-8")
    abstract = ""
    for block in re.split(r"\n\s*\n", raw):
        s = block.strip()
        if s.startswith("Automated species identification"):
            abstract = " ".join(s.splitlines())
            break
    kw = ""
    m = re.search(r"\*\*Keywords\*\*:\s*(.*?)(?:\n\n|\Z)", raw, re.S)
    if m:
        kw = " ".join(m.group(1).split())
    if not abstract or not kw:
        raise SystemExit("could not extract abstract or keywords")
    return abstract, kw


def extract_back_matter(inliner: "Inliner") -> list[tuple[str, str]]:
    """English declarations from 97_back_matter.md, as (heading, body)."""
    raw = (TEXT / "97_back_matter.md").read_text(encoding="utf-8")
    out, heading, buf = [], None, []

    def flush():
        if heading is None:
            return
        text = "\n".join(buf).strip()
        if text:
            out.append((heading, inliner.render(text)))

    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("## "):
            flush()
            heading, buf = s[3:].strip(), []
            # Chinese working-note headings, and the material under them, are
            # not manuscript content.
            if re.search(r"[\u4e00-\u9fff]", heading):
                heading, buf = None, []
            continue
        if heading is None or not s:
            continue
        if re.search(r"[\u4e00-\u9fff]", s):      # working note
            continue
        buf.append(s)
    flush()
    return out


def front_matter(inliner: "Inliner") -> str:
    abstract, keywords = extract_abstract()
    refs = parse_references()

    lines = [
        r"\documentclass[preprint,12pt,authoryear]{elsarticle}",
        r"\usepackage{amsmath,amssymb,booktabs,graphicx,textcomp,url}",
        r"\usepackage{tabularx,array,threeparttable}",
        r"\usepackage[most]{tcolorbox}",
        "",
        r"% Elsevier applies its own reference style after acceptance; at",
        r"% submission the format only has to be internally consistent.",
        r"\biboptions{round,authoryear}",
        r"\graphicspath{{figures/}{../figures/}}",
        "",
        r"% Float placement: without this the figures and tables drift to the",
        r"% end of the document and every \ref{} in the text points at a",
        r"\renewcommand{\topfraction}{0.9}",
        r"\renewcommand{\bottomfraction}{0.7}",
        r"\renewcommand{\textfraction}{0.07}",
        r"\renewcommand{\floatpagefraction}{0.85}",
        r"\setcounter{topnumber}{3}",
        r"\setcounter{bottomnumber}{2}",
        r"\setcounter{totalnumber}{5}",
        "",
        r"\journal{Ecological Informatics}",
        "",
        r"\begin{document}",
        r"\begin{frontmatter}",
        "",
        r"\title{" + inliner.render(TITLE) + r"\tnotemark[1]}",
        "",
    ]
    for entry in AUTHORS:
        name, affs, email, corr = entry
        # The corresponding author carries the corref marker on the name; the
        # e-mail itself comes from the same \ead as everyone else's, so it
        # must not be repeated after \cortext.
        mark = r"\corref{cor1}" if corr else ""
        lines.append(f"\\author[{','.join(affs)}]{{{name}{mark}}}")
        lines.append(f"\\ead{{{email}}}")
    lines += [
        "",
        r"\cortext[cor1]{Corresponding author.}",
        "",
    ]
    for tag, text in AFFILIATIONS:
        lines.append(f"\\address[{tag}]{{{inliner.render(text)}}}")
    lines += [
        "",
        r"\tnotetext[1]{Abbreviations: API, application programming interface; "
        r"CC0 / CC BY / CC BY-NC, Creative Commons licences; CI, confidence "
        r"interval; ECE, expected calibration error; GBIF, Global Biodiversity "
        r"Information Facility; iDigBio, Integrated Digitized Biocollections; "
        r"OCR, optical character recognition; pp, percentage points; PPG I, "
        r"the Pteridophyte Phylogeny Group classification; VLM, "
        r"vision--language model.}",
        "",
        r"\begin{abstract}",
        inliner.render(abstract),
        r"\end{abstract}",
        "",
        r"\begin{keyword}",
        inliner.render(keywords),
        r"\end{keyword}",
        r"\end{frontmatter}",
        "",
    ]
    return "\n".join(lines)


def assemble(body: str, inliner: "Inliner") -> str:
    head = front_matter(inliner)
    refs = parse_references()

    parts = [head, body, "", r"\section*{Declarations}"]
    for title, text in extract_back_matter(inliner):
        parts.append(f"\\subsection*{{{inliner.render(title)}}}")
        parts.append(text)
    parts += [
        "",
        "% Elsevier places the reference list after the declarations.",
        r"\begin{thebibliography}{99}",
    ]
    for key, label, body_text in refs:
        parts.append(f"\\bibitem[{label}]{{{key}}} {inliner.render(body_text)}")
    parts += [
        r"\end{thebibliography}",
        "",
        r"\end{document}",
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    cite_keys = {}
    for key, _label, _body in parse_references():
        m = re.match(r"^([a-z]+?)(\d{4})$", key)
        if m:
            cite_keys[(m.group(1), m.group(2))] = key

    inliner = Inliner(cite_keys)
    body, stats = convert_body(inliner)
    tex = assemble(body, inliner)

    print("=== conversion statistics ===")
    print(f"  citations rendered      : {inliner.stats['citations']}")
    unmapped = sorted(set(inliner.stats["unmapped_citations"]))
    print(f"  unmapped citations      : {len(unmapped)}")
    for u in unmapped:
        print(f"      ! {u}")
    print(f"  references emitted      : {len(parse_references())}")
    print(f"  tables emitted          : {stats['tables_emitted']}")
    print(f"  figures emitted         : {stats['figures_emitted']}")
    print(f"  tables never referenced : {stats['tables_never_referenced'] or 'none'}")
    print(f"  figures never referenced: {stats['figures_never_referenced'] or 'none'}")
    print(f"  main.tex size           : {len(tex)} characters")

    if args.check_only:
        return 0
    OUT.write_text(tex, encoding="utf-8")
    print(f"\n  wrote {OUT}")
    return 1 if unmapped else 0


if __name__ == "__main__":
    sys.exit(main())
