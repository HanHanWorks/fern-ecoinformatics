#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR.parent / "paper_ready"

FIGURES = [
    "figure_02_main_performance_forest_v2.html",
    "figure_03_imbalance_heatmap_v2.html",
    "figure_04_robustness_slope_strip_v2.html",
    "figure_05_external_validation_dumbbell_v2.html",
    "figure_06_open_set_tilematrix_v2.html",
    "figure_07_taxonomic_rank_ladder_v2.html",
    "figure_08_confidence_reliability_mosaic_v2.html",
]

MODEL_PATTERNS = [
    (r"Qwen3\.5 Plus / 397B", "Qwen3.5-397B-A17B"),
    (r"Qwen397B", "Qwen3.5-397B-A17B"),
    (r"Qwen3\.5 Plus\b", "Qwen3.5-397B-A17B"),
    (r"Qwen3\.5-35B / qwen3\.5-flash", "Qwen3.5-35B-A3B"),
    (r"Qwen3\.5-35B / flash", "Qwen3.5-35B-A3B"),
    (r"Qwen35/flash", "Qwen3.5-35B-A3B"),
    (r"(?<!-A3B)Qwen3\.5-35B(?!-A3B)", "Qwen3.5-35B-A3B"),
]

FAMILY_REPLACEMENTS = {
    "鳞毛蕨科": "Dryopteridaceae",
    "水龙骨科": "Polypodiaceae",
    "石松科": "Lycopodiaceae",
    "乌毛蕨科": "Blechnaceae",
    "凤尾蕨科": "Pteridaceae",
    "蘋科": "Marsileaceae",
    "膜蕨科": "Hymenophyllaceae",
    "松叶蕨科": "Psilotaceae",
    "里白科": "Gleicheniaceae",
    "叉蕨科": "Tectariaceae",
    "合囊蕨科": "Marattiaceae",
    "爬树蕨科": "Arthropteridaceae",
    "紫萁科": "Osmundaceae",
    "翼盖蕨科": "Didymochlaenaceae",
    "肿足蕨科": "Hypodematiaceae",
    "蹄盖蕨科": "Athyriaceae",
    "卷柏科": "Selaginellaceae",
    "瓶尔小草科": "Ophioglossaceae",
}


def extract_svg(html: str) -> str:
    match = re.search(r"(<svg\b.*?</svg>)", html, flags=re.S)
    if not match:
        raise ValueError("SVG block not found")
    return match.group(1)


def apply_text_normalization(svg: str) -> str:
    for pattern, repl in MODEL_PATTERNS:
        svg = re.sub(pattern, repl, svg)
    for src, dst in FAMILY_REPLACEMENTS.items():
        svg = svg.replace(src, dst)
    svg = svg.replace("Qwen3.5-35B-A3B-A3B", "Qwen3.5-35B-A3B")
    svg = svg.replace("Qwen3.5-397B-A17B-A17B", "Qwen3.5-397B-A17B")
    return svg


def with_export_style(svg: str, figure_name: str) -> str:
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ')
    svg = svg.replace(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" ",
        (
            "<svg xmlns=\"http://www.w3.org/2000/svg\" "
            "style=\"display:block;background:#ffffff;font-family:-apple-system,"
            "BlinkMacSystemFont,'Segoe UI',Arial,sans-serif\" "
        ),
        1,
    )
    svg = apply_text_normalization(svg)
    return svg


def render_png(svg_path: Path, png_path: Path) -> None:
    subprocess.run(
        [
            "rsvg-convert",
            "-f",
            "png",
            "-o",
            str(png_path),
            "-w",
            "2400",
            "-b",
            "#ffffff",
            str(svg_path),
        ],
        check=True,
    )


def render_jpg(png_path: Path, jpg_path: Path) -> None:
    image = Image.open(png_path).convert("RGB")
    image.save(jpg_path, format="JPEG", quality=95, optimize=True, dpi=(300, 300))


def main() -> None:
    EXPORT_DIR.mkdir(exist_ok=True)
    for filename in FIGURES:
        html_path = BASE_DIR / filename
        figure_stem = html_path.stem
        svg_path = EXPORT_DIR / f"{figure_stem}.svg"
        png_path = EXPORT_DIR / f"{figure_stem}.png"
        jpg_path = EXPORT_DIR / f"{figure_stem}.jpg"

        html = html_path.read_text(encoding="utf-8")
        svg = with_export_style(extract_svg(html), figure_stem)
        svg_path.write_text(svg, encoding="utf-8")
        render_png(svg_path, png_path)
        render_jpg(png_path, jpg_path)


if __name__ == "__main__":
    main()
