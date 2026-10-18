#!/usr/bin/env python3
"""Create a representative text-masked fern image subset from existing data."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "ferns_dataset"
SPECIES_JSON = DATASET / "species_data.json"
OUT = ROOT / "paper_analysis" / "text_masked_dataset"
ORIGINAL_DIR = OUT / "original"
MASKED_DIR = OUT / "masked"
PREVIEW_DIR = OUT / "preview"
META_DIR = OUT / "metadata"


def load_species() -> list[dict]:
    return json.load(open(SPECIES_JSON, encoding="utf-8"))["species"]


def select_representative_subset(species: list[dict], target_n: int = 60) -> list[dict]:
    """Stratified subset: all families plus extra samples for large families."""
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in species:
        by_family[row["family"]].append(row)

    selected = []
    selected_ids = set()

    def sort_key(row: dict) -> tuple[int, int]:
        ref = row.get("image_refs", [""])[0]
        # Prefer already-cropped plant photographs for the masked-image subset;
        # full pages are still included when they are the only available family representative.
        is_full = 1 if "_full" in Path(ref).name else 0
        return is_full, int(row["species_id"].split("_")[1])

    # First pass: one sample per family.
    for family in sorted(by_family):
        row = sorted(by_family[family], key=sort_key)[0]
        selected.append(row)
        selected_ids.add(row["species_id"])

    # Remaining quota allocated proportional to sqrt family size.
    remaining = max(0, target_n - len(selected))
    weights = {family: math.sqrt(len(rows)) for family, rows in by_family.items()}
    total_w = sum(weights.values())
    quotas = {family: int(remaining * weights[family] / total_w) for family in by_family}
    while sum(quotas.values()) < remaining:
        family = max(by_family, key=lambda f: weights[f] - quotas[f])
        quotas[family] += 1

    for family in sorted(by_family):
        count = 0
        for row in sorted(by_family[family], key=sort_key):
            if count >= quotas[family]:
                break
            if row["species_id"] not in selected_ids:
                selected.append(row)
                selected_ids.add(row["species_id"])
                count += 1

    return sorted(selected, key=lambda x: int(x["species_id"].split("_")[1]))


def run_tesseract_hocr(image_path: Path) -> str:
    cmd = ["tesseract", str(image_path), "stdout", "-l", "chi_sim+eng", "hocr", "--psm", "11"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        # Retry English only; many botanical labels are Latin.
        cmd = ["tesseract", str(image_path), "stdout", "-l", "eng", "hocr", "--psm", "11"]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def parse_hocr_boxes(hocr: str, width: int, height: int) -> list[dict]:
    if not hocr.strip():
        return []
    boxes = []
    try:
        root = ET.fromstring(hocr)
    except ET.ParseError:
        return []
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    words = root.findall(".//x:span[@class='ocrx_word']", ns)
    if not words:
        words = root.findall(".//span[@class='ocrx_word']")
    for word in words:
        title = word.attrib.get("title", "")
        text = "".join(word.itertext()).strip()
        if not text:
            continue
        parts = title.split(";")
        bbox_part = next((p.strip() for p in parts if p.strip().startswith("bbox ")), "")
        conf_part = next((p.strip() for p in parts if p.strip().startswith("x_wconf ")), "")
        if not bbox_part:
            continue
        nums = bbox_part.replace("bbox", "").strip().split()
        if len(nums) != 4:
            continue
        x1, y1, x2, y2 = [int(float(n)) for n in nums]
        conf = 0
        if conf_part:
            try:
                conf = int(float(conf_part.replace("x_wconf", "").strip()))
            except ValueError:
                conf = 0
        w = x2 - x1
        h = y2 - y1
        if w < 4 or h < 4:
            continue
        if conf < 35:
            continue
        # Avoid masking large plant structures wrongly detected as text.
        if w > width * 0.65 or h > height * 0.12:
            continue
        pad = max(2, int(min(width, height) * 0.004))
        boxes.append({
            "text": text,
            "conf": conf,
            "bbox": [
                max(0, x1 - pad),
                max(0, y1 - pad),
                min(width, x2 + pad),
                min(height, y2 + pad),
            ],
        })
    return boxes


def mask_image(image_path: Path, out_path: Path, preview_path: Path) -> list[dict]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    hocr = run_tesseract_hocr(image_path)
    boxes = parse_hocr_boxes(hocr, width, height)

    masked = image.copy()
    draw = ImageDraw.Draw(masked)
    for box in boxes:
        draw.rectangle(box["bbox"], fill=(245, 245, 245))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    masked.save(out_path, quality=95)

    preview = image.copy()
    pdraw = ImageDraw.Draw(preview)
    for box in boxes:
        pdraw.rectangle(box["bbox"], outline=(255, 0, 0), width=3)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(preview_path, quality=90)
    return boxes


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for d in [ORIGINAL_DIR, MASKED_DIR, PREVIEW_DIR, META_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    species = load_species()
    subset = select_representative_subset(species, target_n=60)
    rows = []
    subset_species = []
    family_counts = Counter()

    for row in subset:
        src = DATASET / row["image_refs"][0]
        ext = src.suffix.lower() or ".jpg"
        name = f"{row['species_id']}{ext}"
        original_out = ORIGINAL_DIR / name
        masked_out = MASKED_DIR / name
        preview_out = PREVIEW_DIR / name
        Image.open(src).convert("RGB").save(original_out, quality=95)
        boxes = mask_image(src, masked_out, preview_out)
        family_counts[row["family"]] += 1
        item = {
            "species_id": row["species_id"],
            "chinese_name": row["chinese_name"],
            "latin_name": row["latin_name"],
            "family": row["family"],
            "family_latin": row["family_latin"],
            "source_image": str(src.relative_to(ROOT)),
            "source_type": "full_page" if "_full" in src.name else "cropped_photo",
            "original_image": str(original_out.relative_to(ROOT)),
            "masked_image": str(masked_out.relative_to(ROOT)),
            "preview_image": str(preview_out.relative_to(ROOT)),
            "text_boxes": len(boxes),
            "masked_area_ratio": round(sum((b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1]) for b in boxes) / (Image.open(src).width * Image.open(src).height), 5),
        }
        rows.append(item)
        subset_species.append({**row, "image_refs": [str(masked_out.relative_to(DATASET.parent))]})
        with (META_DIR / f"{row['species_id']}_boxes.json").open("w", encoding="utf-8") as f:
            json.dump(boxes, f, ensure_ascii=False, indent=2)

    write_csv(OUT / "manifest.csv", rows, [
        "species_id", "chinese_name", "latin_name", "family", "family_latin",
        "source_image", "source_type", "original_image", "masked_image", "preview_image",
        "text_boxes", "masked_area_ratio",
    ])
    with (OUT / "species_data_text_masked_subset.json").open("w", encoding="utf-8") as f:
        json.dump({
            "dataset": "ferns_text_masked_subset",
            "source": "Derived from ferns_dataset/species_data.json and ferns_dataset/images",
            "selection": "Stratified subset: all 30 families plus proportional extra samples, target n=60",
            "total_species": len(subset_species),
            "family_counts": dict(sorted(family_counts.items())),
            "species": subset_species,
        }, f, ensure_ascii=False, indent=2)

    # Contact sheet for quick visual QA.
    thumbs = []
    for item in rows[:24]:
        im = Image.open(ROOT / item["masked_image"]).convert("RGB")
        im.thumbnail((180, 180))
        canvas = Image.new("RGB", (200, 220), "white")
        canvas.paste(im, ((200 - im.width) // 2, 5))
        d = ImageDraw.Draw(canvas)
        d.text((8, 190), item["species_id"], fill="black")
        d.text((8, 205), str(item["text_boxes"]) + " boxes", fill="black")
        thumbs.append(canvas)
    sheet = Image.new("RGB", (200 * 6, 220 * 4), "white")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % 6) * 200, (i // 6) * 220))
    sheet.save(OUT / "masked_contact_sheet.jpg", quality=90)

    print(f"Wrote {OUT}")
    print(f"n={len(rows)} families={len(family_counts)}")


if __name__ == "__main__":
    main()
