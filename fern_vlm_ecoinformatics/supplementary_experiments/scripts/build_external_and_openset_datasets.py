#!/usr/bin/env python3
"""Build external validation and open-set datasets from iNaturalist/GBIF."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper_analysis"
SUPP = PAPER / "supplementary_experiments"
EXT_DIR = SUPP / "datasets" / "external_validation"
OPEN_DIR = SUPP / "datasets" / "open_set"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"
SPECIES = ROOT / "ferns_dataset" / "species_data.json"
TEXT_MASKED_MANIFEST = PAPER / "text_masked_dataset" / "manifest.csv"

USER_AGENT = "CFern-VLM-Supplementary-Experiment/1.0 (research dataset builder)"
ALLOWED_LICENSE_HINTS = ["cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "publicdomain"]
PAPER_FIGURE_LICENSE_HINTS = ["cc0", "cc-by/4.0", "cc-by-4.0", "cc by 4.0"]
MIN_SIDE = 512


OPEN_NEGATIVE_QUERIES = {
    "candidate_out_fern": [
        "Selaginella tamariscina",
        "Selaginella kraussiana",
        "Equisetum arvense",
        "Equisetum hyemale",
        "Cyathea cooperi",
        "Dicksonia antarctica",
    ],
    "angiosperm": [
        "Rosa chinensis",
        "Taraxacum officinale",
        "Camellia sinensis",
        "Acer palmatum",
        "Plantago asiatica",
        "Iris japonica",
    ],
    "gymnosperm_cycad": [
        "Cycas revoluta",
        "Ginkgo biloba",
        "Pinus massoniana",
        "Taxus wallichiana",
        "Juniperus chinensis",
        "Cycas panzhihuaensis",
    ],
    "bryophyte_liverwort": [
        "Marchantia polymorpha",
        "Polytrichum commune",
        "Sphagnum palustre",
        "Bryum argenteum",
        "Funaria hygrometrica",
        "Conocephalum conicum",
    ],
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def request_json(url: str, retries: int = 3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            last = exc
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"request failed: {url}: {last}")


def normalize_license(text: str) -> str:
    return str(text or "").strip().lower()


def allowed_license(text: str) -> bool:
    low = normalize_license(text)
    return any(hint in low for hint in ALLOWED_LICENSE_HINTS)


def paper_safe_license(text: str) -> bool:
    low = normalize_license(text)
    return any(hint in low for hint in PAPER_FIGURE_LICENSE_HINTS)


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", str(text).strip())
    return slug.strip("_") or "unknown"


def image_ext_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if ext == ".jpeg" else ext
    guessed = mimetypes.guess_extension("image/jpeg") or ".jpg"
    return guessed


def unlink_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def download_image(url: str, out_path: Path) -> tuple[bool, str, int, int, str]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=45) as response:
            data = response.read()
        if len(data) < 1024:
            return False, "download_too_small", 0, 0, ""
        tmp.write_bytes(data)
        with Image.open(tmp) as img:
            w, h = img.size
            if min(w, h) < MIN_SIDE:
                unlink_if_exists(tmp)
                return False, f"min_side_lt_{MIN_SIDE}", w, h, ""
            rgb = img.convert("RGB")
            rgb.save(out_path, "JPEG", quality=92)
        unlink_if_exists(tmp)
        digest = hashlib.sha1(out_path.read_bytes()).hexdigest()
        return True, "", w, h, digest
    except Exception as exc:
        unlink_if_exists(tmp)
        return False, str(exc)[:200], 0, 0, ""


def inat_taxon_id(query: str) -> int | None:
    url = "https://api.inaturalist.org/v1/taxa?" + urllib.parse.urlencode({"q": query, "per_page": 5})
    data = request_json(url)
    results = data.get("results", [])
    if not results:
        return None
    exact = [t for t in results if str(t.get("name", "")).lower() == query.lower()]
    taxon = exact[0] if exact else results[0]
    return taxon.get("id")


def inat_observations(query: str, per_page: int = 30) -> list[dict]:
    taxon_id = inat_taxon_id(query)
    if not taxon_id:
        return []
    params = {
        "taxon_id": taxon_id,
        "photos": "true",
        "quality_grade": "research",
        "per_page": per_page,
        "order_by": "created_at",
        "order": "desc",
    }
    url = "https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode(params)
    data = request_json(url)
    rows = []
    for obs in data.get("results", []):
        tax = obs.get("taxon") or {}
        for photo in obs.get("photos") or []:
            license_code = photo.get("license_code") or obs.get("license_code") or ""
            attribution = photo.get("attribution") or ""
            if not allowed_license(license_code) and not allowed_license(attribution):
                continue
            square_url = photo.get("url") or ""
            if not square_url:
                continue
            image_url = square_url.replace("/square.", "/original.").replace("/small.", "/original.")
            rows.append({
                "source": "iNaturalist",
                "source_record_id": str(obs.get("id", "")),
                "source_photo_id": str(photo.get("id", "")),
                "source_url": obs.get("uri", ""),
                "image_url": image_url,
                "taxon_name": tax.get("name", ""),
                "taxon_rank": tax.get("rank", ""),
                "license": license_code,
                "rights_holder": attribution,
                "image_context": "field_or_living",
            })
    return rows


def gbif_taxon_key(query: str) -> int | None:
    url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": query})
    data = request_json(url)
    return data.get("usageKey")


def gbif_occurrences(query: str, per_page: int = 30) -> list[dict]:
    key = gbif_taxon_key(query)
    if not key:
        return []
    params = {"taxonKey": key, "mediaType": "StillImage", "limit": per_page}
    url = "https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode(params)
    data = request_json(url)
    rows = []
    for occ in data.get("results", []):
        for media in occ.get("media") or []:
            image_url = media.get("identifier") or ""
            if not image_url.startswith("http"):
                continue
            license_text = media.get("license") or occ.get("license") or ""
            if not allowed_license(license_text):
                continue
            rows.append({
                "source": "GBIF",
                "source_record_id": str(occ.get("gbifID") or occ.get("key") or ""),
                "source_photo_id": str(media.get("references") or image_url),
                "source_url": occ.get("references") or media.get("references") or "",
                "image_url": image_url,
                "taxon_name": occ.get("scientificName") or occ.get("species") or occ.get("genus") or "",
                "taxon_rank": occ.get("taxonRank", ""),
                "license": license_text,
                "rights_holder": occ.get("rightsHolder") or media.get("rightsHolder") or "",
                "image_context": "field_or_living" if occ.get("basisOfRecord") == "HUMAN_OBSERVATION" else "external_record",
            })
    return rows


def source_candidates(query: str, per_source: int = 30) -> list[dict]:
    rows = []
    try:
        rows.extend(inat_observations(query, per_source))
    except Exception as exc:
        print(f"  iNat failed for {query}: {exc}")
    try:
        rows.extend(gbif_occurrences(query, per_source))
    except Exception as exc:
        print(f"  GBIF failed for {query}: {exc}")
    return rows


def representative_queries_by_family(species_data: list[dict]) -> dict[str, list[str]]:
    by_family = defaultdict(list)
    for sp in species_data:
        latin = sp["latin_name"]
        genus = latin.split()[0] if latin else ""
        for q in [latin, genus]:
            if q and q not in by_family[sp["family"]]:
                by_family[sp["family"]].append(q)
    return by_family


def existing_key(row: dict) -> tuple[str, str]:
    return row.get("source", ""), row.get("source_record_id", "") + "::" + row.get("source_photo_id", "")


def build_external(args) -> list[dict]:
    config = load_json(CONFIG)
    species_data = load_json(SPECIES)["species"]
    families = config["canonical_families"]
    by_family = representative_queries_by_family(species_data)
    manifest_path = EXT_DIR / "manifest.csv"
    rows = read_csv(manifest_path)
    seen_urls = {r.get("image_url", "") for r in rows}
    seen_hashes = {r.get("sha1", "") for r in rows if r.get("sha1")}
    next_index = len(rows) + 1

    for fam in families:
        current = [r for r in rows if r.get("family") == fam]
        if len(current) >= args.external_per_family:
            continue
        print(f"\nExternal family {fam}: have {len(current)}/{args.external_per_family}")
        queries = by_family.get(fam, [])
        fill_reason = ""
        for query in queries:
            if len([r for r in rows if r.get("family") == fam]) >= args.external_per_family:
                break
            print(f"  query {query}")
            candidates = source_candidates(query, args.candidates_per_query)
            for cand in candidates:
                if len([r for r in rows if r.get("family") == fam]) >= args.external_per_family:
                    break
                if cand["image_url"] in seen_urls:
                    continue
                ext = image_ext_from_url(cand["image_url"])
                sample_id = f"EXT_{next_index:03d}"
                out_rel = f"paper_analysis/supplementary_experiments/datasets/external_validation/images/{sample_id}.jpg"
                out_path = ROOT / out_rel
                ok, error, width, height, digest = download_image(cand["image_url"], out_path)
                if not ok:
                    continue
                if digest in seen_hashes:
                    unlink_if_exists(out_path)
                    continue
                row = {
                    "sample_id": sample_id,
                    "species_id": sample_id,
                    "dataset": "external_validation",
                    "family": fam,
                    "family_latin_project": next((sp["family_latin"] for sp in species_data if sp["family"] == fam), ""),
                    "query_taxon": query,
                    "taxon_name": cand["taxon_name"],
                    "taxon_rank": cand["taxon_rank"],
                    "source": cand["source"],
                    "source_record_id": cand["source_record_id"],
                    "source_photo_id": cand["source_photo_id"],
                    "source_url": cand["source_url"],
                    "image_url": cand["image_url"],
                    "image_path": out_rel,
                    "license": cand["license"],
                    "rights_holder": cand["rights_holder"],
                    "paper_figure_safe": int(paper_safe_license(cand["license"]) or paper_safe_license(cand["rights_holder"])),
                    "image_context": cand["image_context"],
                    "width": width,
                    "height": height,
                    "sha1": digest,
                    "fill_reason": fill_reason,
                }
                rows.append(row)
                seen_urls.add(cand["image_url"])
                seen_hashes.add(digest)
                next_index += 1
                print(f"    saved {sample_id} {cand['source']} {cand['taxon_name']} {width}x{height}")
        if len([r for r in rows if r.get("family") == fam]) < args.external_per_family:
            print(f"  WARNING: still short for {fam}")
        write_csv(manifest_path, rows, EXTERNAL_HEADERS)
    write_csv(manifest_path, rows, EXTERNAL_HEADERS)
    return rows


def build_open_set(args) -> list[dict]:
    manifest_path = OPEN_DIR / "manifest.csv"
    rows = read_csv(manifest_path)
    seen_urls = {r.get("image_url", "") for r in rows}
    seen_hashes = {r.get("sha1", "") for r in rows if r.get("sha1")}
    next_index = 1 + max([int(r["sample_id"].split("_")[-1]) for r in rows if r.get("sample_id", "").startswith("OPEN_")] or [0])

    # Positive rows are reused local text-masked images and do not need external licenses.
    positives = [r for r in rows if r.get("open_set_label") == "positive_in_scope"]
    if len(positives) < 60:
        masked_rows = list(csv.DictReader(TEXT_MASKED_MANIFEST.open(encoding="utf-8")))
        rows = [r for r in rows if r.get("open_set_label") != "positive_in_scope"]
        for m in masked_rows:
            rows.append({
                "sample_id": f"OPEN_POS_{m['species_id']}",
                "species_id": m["species_id"],
                "dataset": "open_set",
                "open_set_label": "positive_in_scope",
                "negative_group": "",
                "expected_decision": "in_scope",
                "family": m["family"],
                "family_latin_project": m["family_latin"],
                "query_taxon": m["latin_name"],
                "taxon_name": m["latin_name"],
                "taxon_rank": "species",
                "source": "local_text_masked",
                "source_record_id": m["species_id"],
                "source_photo_id": "",
                "source_url": m["source_image"],
                "image_url": "",
                "image_path": m["masked_image"],
                "license": "local_research_dataset",
                "rights_holder": "",
                "paper_figure_safe": 0,
                "image_context": m["source_type"],
                "width": "",
                "height": "",
                "sha1": "",
                "fill_reason": "positive_control_from_text_masked_dataset",
            })
        write_csv(manifest_path, rows, OPEN_HEADERS)

    for group, queries in OPEN_NEGATIVE_QUERIES.items():
        have = len([r for r in rows if r.get("negative_group") == group])
        target = args.open_negative_per_group
        if have >= target:
            continue
        print(f"\nOpen negative group {group}: have {have}/{target}")
        for query in queries:
            if len([r for r in rows if r.get("negative_group") == group]) >= target:
                break
            print(f"  query {query}")
            for cand in source_candidates(query, args.candidates_per_query):
                if len([r for r in rows if r.get("negative_group") == group]) >= target:
                    break
                if cand["image_url"] in seen_urls:
                    continue
                sample_id = f"OPEN_{next_index:03d}"
                out_rel = f"paper_analysis/supplementary_experiments/datasets/open_set/images/{sample_id}.jpg"
                out_path = ROOT / out_rel
                ok, error, width, height, digest = download_image(cand["image_url"], out_path)
                if not ok:
                    continue
                if digest in seen_hashes:
                    unlink_if_exists(out_path)
                    continue
                rows.append({
                    "sample_id": sample_id,
                    "species_id": sample_id,
                    "dataset": "open_set",
                    "open_set_label": "negative_out_of_scope",
                    "negative_group": group,
                    "expected_decision": "none_of_the_above",
                    "family": "",
                    "family_latin_project": "",
                    "query_taxon": query,
                    "taxon_name": cand["taxon_name"],
                    "taxon_rank": cand["taxon_rank"],
                    "source": cand["source"],
                    "source_record_id": cand["source_record_id"],
                    "source_photo_id": cand["source_photo_id"],
                    "source_url": cand["source_url"],
                    "image_url": cand["image_url"],
                    "image_path": out_rel,
                    "license": cand["license"],
                    "rights_holder": cand["rights_holder"],
                    "paper_figure_safe": int(paper_safe_license(cand["license"]) or paper_safe_license(cand["rights_holder"])),
                    "image_context": cand["image_context"],
                    "width": width,
                    "height": height,
                    "sha1": digest,
                    "fill_reason": "",
                })
                seen_urls.add(cand["image_url"])
                seen_hashes.add(digest)
                next_index += 1
                print(f"    saved {sample_id} {cand['source']} {cand['taxon_name']} {width}x{height}")
        write_csv(manifest_path, rows, OPEN_HEADERS)
    write_csv(manifest_path, rows, OPEN_HEADERS)
    return rows


EXTERNAL_HEADERS = [
    "sample_id", "species_id", "dataset", "family", "family_latin_project",
    "query_taxon", "taxon_name", "taxon_rank", "source", "source_record_id",
    "source_photo_id", "source_url", "image_url", "image_path", "license",
    "rights_holder", "paper_figure_safe", "image_context", "width", "height",
    "sha1", "fill_reason",
]

OPEN_HEADERS = [
    "sample_id", "species_id", "dataset", "open_set_label", "negative_group",
    "expected_decision", "family", "family_latin_project", "query_taxon",
    "taxon_name", "taxon_rank", "source", "source_record_id", "source_photo_id",
    "source_url", "image_url", "image_path", "license", "rights_holder",
    "paper_figure_safe", "image_context", "width", "height", "sha1",
    "fill_reason",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external-per-family", type=int, default=3)
    parser.add_argument("--open-negative-per-group", type=int, default=15)
    parser.add_argument("--candidates-per-query", type=int, default=35)
    parser.add_argument("--only", choices=["all", "external", "open"], default="all")
    args = parser.parse_args()
    (EXT_DIR / "images").mkdir(parents=True, exist_ok=True)
    (OPEN_DIR / "images").mkdir(parents=True, exist_ok=True)
    if args.only in {"all", "external"}:
        rows = build_external(args)
        print(f"External rows: {len(rows)}")
    if args.only in {"all", "open"}:
        rows = build_open_set(args)
        pos = sum(1 for r in rows if r.get("open_set_label") == "positive_in_scope")
        neg = sum(1 for r in rows if r.get("open_set_label") == "negative_out_of_scope")
        print(f"Open-set rows: {len(rows)} positive={pos} negative={neg}")


if __name__ == "__main__":
    main()
