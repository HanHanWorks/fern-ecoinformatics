"""Scan the staged release tree for anything that must not be published.

Run this after staging and before the first `git add`. It looks for the
classes of content that leaked into research repositories in the past:
server addresses, credentials, absolute paths from the author's machine,
and files that carry no scientific value.

    python tools/privacy_scan.py
    python tools/privacy_scan.py --fix      # redact absolute paths in .md/.py

Exit code is 1 if any BLOCK-level finding is present, so the scan can be
used as a pre-commit gate.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {".md", ".py", ".sh", ".csv", ".json", ".jsonl", ".txt", ".cff", ".yml", ".yaml"}
SKIP_DIRS = {".git", "__pycache__", ".venv"}

# (level, label, pattern, note)
CHECKS: list[tuple[str, str, str, str]] = [
    ("BLOCK", "private IP address",
     r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b",
     "internal network address"),
    ("BLOCK", "ssh target",
     r"\b[a-z_][a-z0-9_-]{1,30}@(?:\d{1,3}\.){3}\d{1,3}\b",
     "username plus internal host"),
    ("BLOCK", "api key literal",
     r"\b(?:sk|rk)-[A-Za-z0-9]{16,}\b",
     "provider credential"),
    ("BLOCK", "credential assignment",
     r"(?:API_KEY|SECRET|TOKEN|PASSWORD)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']",
     "hard-coded credential"),
    ("BLOCK", "email address",
     r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b",
     "personal contact detail"),
    ("BLOCK", "dotenv file",
     r"^\.env",
     "environment file present"),
    ("WARN", "absolute home path",
     r"/(?:Users|home)/[A-Za-z0-9._-]+/",
     "reveals local directory layout"),
    ("WARN", "absolute volume path",
     r"/Volumes/[A-Za-z0-9._-]+/",
     "reveals local directory layout"),
    ("WARN", "windows path",
     r"[A-Za-z]:\\\\?Users\\\\?[A-Za-z0-9._-]+",
     "reveals local directory layout"),
    ("WARN", "todo marker",
     r"(?:#|//)\s*(?:TODO|FIXME|XXX|HACK)\b|\b(?:TODO|FIXME)\s*:",
     "unfinished marker in released code"),
]

SKIP_FILES = {"tools/privacy_scan.py"}   # this file documents the patterns

# Byline contact addresses. EI publishes the corresponding author's e-mail and
# the author list is supplied by the authors themselves, so addresses in these
# files are intentional rather than leaked. They are reported at INFO level
# instead of being suppressed, so whoever runs the scan can see exactly which
# personal addresses the release will make public.
BYLINE_FILES = {
    "manuscript/text/00_title_page.md",
    "manuscript/text/97_back_matter.md",
    # The LaTeX generator carries the byline as data, because that is where
    # the title page is assembled from.
    "code/latex/md_to_latex.py",
}

# Documentation needs to show example values, and RFC 2606 reserves these
# domains for exactly that. A real address will never match them.
ALLOW_PATTERNS = [
    r"@example\.(?:com|org|net)\b",
    r"@(?:your|my|some)domain\.",
    r"git@github\.com\b",                     # the standard SSH remote form
    r"<(?:owner|repo|user|host)>",
    r"\b(?:you|your|user|name|me|someone)@",
]


def scan_file(path: Path) -> list[tuple[str, str, int, str, str]]:
    findings = []
    rel = path.relative_to(REPO).as_posix()
    if rel in SKIP_FILES:
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        if any(re.search(a, line) for a in ALLOW_PATTERNS):
            continue
        for level, label, pattern, note in CHECKS:
            m = re.search(pattern, line)
            if m:
                if rel in BYLINE_FILES and label == "email address":
                    level = "INFO"        # intentional byline, see above
                excerpt = line.strip()[:110]
                findings.append((level, label, lineno, excerpt, rel))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                    help="redact absolute local paths in text files")
    args = ap.parse_args()

    files = [p for p in REPO.rglob("*")
             if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES
             and not any(part in SKIP_DIRS for part in p.parts)]

    print(f"scanning {len(files)} text files under {REPO.name}/")

    all_findings = []
    for p in files:
        all_findings.extend(scan_file(p))

    if not all_findings:
        print("  clean: no findings")
        return 0

    blocks = [f for f in all_findings if f[0] == "BLOCK"]
    warns = [f for f in all_findings if f[0] == "WARN"]
    infos = [f for f in all_findings if f[0] == "INFO"]

    for level, label, lineno, excerpt, rel in sorted(all_findings, key=lambda x: (x[0], x[4], x[2])):
        print(f"  {level:<5} {label:<22} {rel}:{lineno}  {excerpt}")

    print(f"\n  {len(blocks)} blocking, {len(warns)} warning, {len(infos)} informational")
    if infos:
        print("  informational = byline contact addresses, published with the paper")
        print("  and supplied by the authors; not suppressed so they stay visible")

    if args.fix:
        patterns = [p for lvl, _, p, _ in CHECKS
                    if lvl == "WARN" and "path" in _]
        changed = 0
        for p in files:
            t = orig = p.read_text(encoding="utf-8", errors="ignore")
            t = re.sub(r"/(?:Users|home)/[A-Za-z0-9._-]+/", "<WORKSPACE>/", t)
            t = re.sub(r"/Volumes/[A-Za-z0-9._-]+/", "<VOLUME>/", t)
            if t != orig:
                p.write_text(t, encoding="utf-8")
                changed += 1
        print(f"  redacted local paths in {changed} file(s)")

    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
