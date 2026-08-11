#!/usr/bin/env python3
"""Convert an approved flat-colour cartoon into a labelled MARD bead pattern."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageColor, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - environment-specific
    raise SystemExit("Pillow is required: install it in the Python environment used by this Skill.") from exc

try:
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
except ImportError:  # pragma: no cover - Pillow PDF fallback remains available
    HexColor = None
    pdf_canvas = None


SKILL_DIR = Path(__file__).resolve().parent.parent
PALETTE_PATH = SKILL_DIR / "references" / "mard-221.csv"
EMPTY = None
ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
SKIN_CODES = {"E1", "E11", "E14", "E15", "E16", "F1", "F14", "F16", "F17", "F20", "F21", "F22", "F23", "G1", "G2", "G3", "G4", "G9", "G12", "G16", "G18"}
COOL_CODES = {f"B{i}" for i in range(1, 33)} | {f"C{i}" for i in range(1, 30)}
PROTECTED_CODES = {"H7", "H16", "H1", "H2", "F5", "F8", "F12", "F15"}
MIN_GRID = 16
MAX_GRID = 256


@dataclass(frozen=True)
class Colour:
    code: str
    hex: str
    rgb: tuple[int, int, int]


def grid_size(value: str) -> int:
    parsed = int(value)
    if not MIN_GRID <= parsed <= MAX_GRID:
        raise argparse.ArgumentTypeError(f"grid must be between {MIN_GRID} and {MAX_GRID}; split larger work into multiple charts")
    return parsed


def nonnegative_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be 0 or greater")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Approved cartoon PNG or JPEG")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--grid", type=grid_size, default=72, metavar="N", help="Grid resolution from 16 to 256; 72 is a starting point and 120 is not a ceiling")
    parser.add_argument("--colors", type=int, default=22, choices=range(8, 41))
    parser.add_argument("--max-beads", type=nonnegative_integer, default=0, help="Optional user-requested bead ceiling; 0 keeps bead count informational")
    parser.add_argument("--background", choices=("auto", "white", "none"), default="auto")
    parser.add_argument("--background-tolerance", type=float, default=72.0)
    parser.add_argument("--foreground-threshold", type=int, default=42, choices=range(1, 256))
    parser.add_argument("--connect-gap", type=int, default=1, choices=range(0, 5), help="Only close tiny resize gaps; never draw long ugly bridges")
    parser.add_argument("--debug-exports", action="store_true", help="Also save SVG, CSV, pattern JSON, and report JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when pendant safety or an explicit bead budget fails")
    return parser.parse_args()


def load_palette(path: Path) -> list[Colour]:
    colours: list[Colour] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            colours.append(Colour(row["code"], row["hex"].upper(), ImageColor.getrgb(row["hex"])))
    if len(colours) != 221:
        raise ValueError(f"Expected 221 MARD colours, found {len(colours)}")
    return colours


def colour_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    mean_red = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return math.sqrt((2 + mean_red / 256) * dr * dr + 4 * dg * dg + (2 + (255 - mean_red) / 256) * db * db)


def border_reference(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    span = max(1, min(w, h) // 40)
    samples: list[tuple[int, int, int]] = []
    for x0, y0 in ((0, 0), (w - span, 0), (0, h - span), (w - span, h - span)):
        for y in range(y0, min(h, y0 + span)):
            for x in range(x0, min(w, x0 + span)):
                samples.append(rgb.getpixel((x, y)))
    channels = [sorted(pixel[i] for pixel in samples) for i in range(3)]
    mid = len(samples) // 2
    return tuple(channel[mid] for channel in channels)  # type: ignore[return-value]


def foreground_mask(image: Image.Image, mode: str, tolerance: float) -> Image.Image:
    rgba = image.convert("RGBA")
    w, h = rgba.size
    if mode == "none":
        return rgba.getchannel("A").point(lambda alpha: 255 if alpha > 8 else 0)
    reference = (255, 255, 255) if mode == "white" else border_reference(rgba)
    pixels = rgba.load()
    background = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()

    def eligible(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a < 8 or colour_distance((r, g, b), reference) <= tolerance

    for x in range(w):
        for y in (0, h - 1):
            index = y * w + x
            if not background[index] and eligible(x, y):
                background[index] = 1
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            index = y * w + x
            if not background[index] and eligible(x, y):
                background[index] = 1
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for dx, dy in ORTHOGONAL:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            index = ny * w + nx
            if background[index] or not eligible(nx, ny):
                continue
            background[index] = 1
            queue.append((nx, ny))

    mask = Image.new("L", (w, h), 255)
    mask.putdata([0 if background[i] else pixels[i % w, i // w][3] for i in range(w * h)])
    return mask


def crop_and_square(image: Image.Image, mask: Image.Image) -> tuple[Image.Image, Image.Image]:
    bbox = mask.getbbox()
    if not bbox:
        raise ValueError("No foreground found. Try --background none or a smaller background tolerance.")
    left, top, right, bottom = bbox
    width, height = right - left, bottom - top
    padding = max(2, round(max(width, height) * 0.04))
    left, top = max(0, left - padding), max(0, top - padding)
    right, bottom = min(image.width, right + padding), min(image.height, bottom + padding)
    cropped = image.convert("RGB").crop((left, top, right, bottom))
    cropped_mask = mask.crop((left, top, right, bottom))
    side = max(cropped.size)
    square = Image.new("RGB", (side, side), (255, 255, 255))
    square_mask = Image.new("L", (side, side), 0)
    offset = ((side - cropped.width) // 2, (side - cropped.height) // 2)
    square.paste(cropped, offset)
    square_mask.paste(cropped_mask, offset)
    return square, square_mask


def sample_grid(image: Image.Image, mask: Image.Image, grid: int, threshold: int) -> list[list[tuple[int, int, int] | None]]:
    rgb = image.resize((grid, grid), Image.Resampling.BOX)
    alpha = mask.resize((grid, grid), Image.Resampling.BOX)
    cells: list[list[tuple[int, int, int] | None]] = []
    for y in range(grid):
        row: list[tuple[int, int, int] | None] = []
        for x in range(grid):
            row.append(rgb.getpixel((x, y)) if alpha.getpixel((x, y)) >= threshold else EMPTY)
        cells.append(row)
    return cells


def nearest_colour(rgb: tuple[int, int, int], palette: Iterable[Colour]) -> Colour:
    return min(palette, key=lambda colour: colour_distance(rgb, colour.rgb))


def adaptive_palette(samples: list[tuple[int, int, int]], palette: list[Colour], limit: int) -> list[Colour]:
    nearest = [nearest_colour(sample, palette) for sample in samples]
    counts = Counter(colour.code for colour in nearest)
    by_code = {colour.code: colour for colour in palette}
    candidates = [by_code[code] for code, _ in counts.most_common()]
    if len(candidates) <= limit:
        return candidates
    selected = [candidates[0]]
    while len(selected) < limit:
        best = max(
            (colour for colour in candidates if colour not in selected),
            key=lambda colour: math.log2(counts[colour.code] + 1)
            * (1 + min(colour_distance(colour.rgb, item.rgb) for item in selected) / 70),
        )
        selected.append(best)
    return selected


def quantize(cells: list[list[tuple[int, int, int] | None]], palette: list[Colour]) -> list[list[Colour | None]]:
    return [[nearest_colour(cell, palette) if cell is not None else EMPTY for cell in row] for row in cells]


def neighbours8(cells: list[list[Colour | None]], x: int, y: int) -> list[Colour]:
    result: list[Colour] = []
    height, width = len(cells), len(cells[0])
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and cells[ny][nx] is not None:
                result.append(cells[ny][nx])  # type: ignore[arg-type]
    return result


def clean_speckles(cells: list[list[Colour | None]]) -> dict[str, int]:
    height, width = len(cells), len(cells[0])
    source = [row[:] for row in cells]
    green_skin = isolated = 0
    for y in range(height):
        for x in range(width):
            cell = source[y][x]
            if cell is None:
                continue
            nearby = neighbours8(source, x, y)
            counts = Counter(item.code for item in nearby)
            by_code = {item.code: item for item in nearby}
            skin_count = sum(count for code, count in counts.items() if code in SKIN_CODES)
            if cell.code in COOL_CODES and skin_count >= 5:
                replacement = max((code for code in counts if code in SKIN_CODES), key=counts.get)
                cells[y][x] = by_code[replacement]
                green_skin += 1
                continue
            if cell.code in PROTECTED_CODES or not counts:
                continue
            replacement, count = counts.most_common(1)[0]
            if replacement != cell.code and count >= 6:
                cells[y][x] = by_code[replacement]
                isolated += 1
    return {"green_skin_replaced": green_skin, "isolated_replaced": isolated}


def components(cells: list[list[Colour | None]]) -> list[list[tuple[int, int]]]:
    height, width = len(cells), len(cells[0])
    seen: set[tuple[int, int]] = set()
    groups: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if cells[y][x] is None or (x, y) in seen:
                continue
            group: list[tuple[int, int]] = []
            queue = deque([(x, y)])
            seen.add((x, y))
            while queue:
                cx, cy = queue.popleft()
                group.append((cx, cy))
                for dx, dy in ORTHOGONAL:
                    point = (cx + dx, cy + dy)
                    if 0 <= point[0] < width and 0 <= point[1] < height and point not in seen and cells[point[1]][point[0]] is not None:
                        seen.add(point)
                        queue.append(point)
            groups.append(group)
    return sorted(groups, key=len, reverse=True)


def close_tiny_gaps(cells: list[list[Colour | None]], max_gap: int) -> int:
    if max_gap <= 0:
        return 0
    added = 0
    for _ in range(max_gap):
        groups = [group for group in components(cells) if len(group) >= 4]
        if len(groups) <= 1:
            break
        main = set(groups[0])
        best: tuple[int, tuple[int, int], tuple[int, int]] | None = None
        for group in groups[1:]:
            for a in main:
                for b in group:
                    distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    if best is None or distance < best[0]:
                        best = (distance, a, b)
        if best is None or best[0] > max_gap + 1:
            break
        _, a, b = best
        x, y = a
        source = cells[y][x]
        while x != b[0]:
            x += 1 if b[0] > x else -1
            if cells[y][x] is None:
                cells[y][x] = source
                added += 1
        while y != b[1]:
            y += 1 if b[1] > y else -1
            if cells[y][x] is None:
                cells[y][x] = source
                added += 1
    return added


def critical_articulations(cells: list[list[Colour | None]], min_side: int = 10) -> int:
    occupied = {(x, y) for y, row in enumerate(cells) for x, cell in enumerate(row) if cell is not None}
    if not occupied:
        return 0
    discovery: dict[tuple[int, int], int] = {}
    low: dict[tuple[int, int], int] = {}
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}
    subtree: dict[tuple[int, int], int] = {}
    time = 0
    total = len(occupied)
    critical: set[tuple[int, int]] = set()

    sys.setrecursionlimit(max(10000, total * 2))

    def visit(point: tuple[int, int]) -> None:
        nonlocal time
        time += 1
        discovery[point] = low[point] = time
        subtree[point] = 1
        children = 0
        for dx, dy in ORTHOGONAL:
            nxt = (point[0] + dx, point[1] + dy)
            if nxt not in occupied:
                continue
            if nxt not in discovery:
                parent[nxt] = point
                children += 1
                visit(nxt)
                subtree[point] += subtree[nxt]
                low[point] = min(low[point], low[nxt])
                separated = subtree[nxt]
                remainder = total - separated - 1
                if parent.get(point) is not None and low[nxt] >= discovery[point] and separated >= min_side and remainder >= min_side:
                    critical.add(point)
            elif nxt != parent.get(point):
                low[point] = min(low[point], discovery[nxt])
        if parent.get(point) is None and children > 1:
            large_children = sum(1 for nxt in occupied if parent.get(nxt) == point and subtree[nxt] >= min_side)
            if large_children >= 2:
                critical.add(point)

    root = next(iter(occupied))
    parent[root] = None
    visit(root)
    return len(critical)


def readable_text(rgb: tuple[int, int, int]) -> str:
    luminance = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114
    return "#111111" if luminance > 165 else "#FFFFFF"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def used_colours(cells: list[list[Colour | None]]) -> list[Colour]:
    return sorted({cell.code: cell for row in cells for cell in row if cell is not None}.values(), key=lambda item: item.code)


def centred_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, fill: str) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    left, top, right, bottom = box
    draw.text(((left + right - width) / 2, (top + bottom - height) / 2 - bounds[1]), text, font=font, fill=fill)


def write_chart_png(cells: list[list[Colour | None]], counts: Counter[str], path: Path) -> None:
    grid = len(cells)
    colours = used_colours(cells)
    cell_size, margin_x, header = 36, 96, 126
    legend_columns, legend_row = 5, 54
    legend_height = math.ceil(len(colours) / legend_columns) * legend_row + 104
    width = grid * cell_size + margin_x * 2
    height = header + grid * cell_size + legend_height
    image = Image.new("RGB", (width, height), "#F8F5EE")
    draw = ImageDraw.Draw(image)
    title_font = load_font(30, bold=True)
    code_font = load_font(11, bold=True)
    legend_font = load_font(18)
    legend_title_font = load_font(22, bold=True)
    draw.text((margin_x, 42), f"MARD Fuse Bead Pattern - {grid} x {grid}", font=title_font, fill="#27221E")
    grid_top = header
    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            left, top = margin_x + x * cell_size, grid_top + y * cell_size
            box = (left, top, left + cell_size, top + cell_size)
            draw.rectangle(box, fill=cell.hex if cell is not None else "#FFFFFF", outline="#D6D0C7", width=1)
            if cell is not None:
                centred_text(draw, box, cell.code, code_font, readable_text(cell.rgb))
    legend_top = grid_top + grid * cell_size + 52
    draw.text((margin_x, legend_top), "MARD codes and bead counts", font=legend_title_font, fill="#27221E")
    column_width = (width - margin_x * 2) // legend_columns
    for index, colour in enumerate(colours):
        column, row = index % legend_columns, index // legend_columns
        x = margin_x + column * column_width
        y = legend_top + 48 + row * legend_row
        draw.rounded_rectangle((x, y, x + 34, y + 34), radius=5, fill=colour.hex, outline="#8F887F", width=1)
        draw.text((x + 46, y + 6), f"{colour.code} x {counts[colour.code]}", font=legend_font, fill="#27221E")
    image.save(path, optimize=True)


def write_pdf(cells: list[list[Colour | None]], counts: Counter[str], chart_png: Path, path: Path) -> None:
    if pdf_canvas is None or HexColor is None:
        with Image.open(chart_png) as image:
            image.convert("RGB").save(path, "PDF", resolution=300.0)
        return

    grid = len(cells)
    colours = used_colours(cells)
    cell_size, margin, header = 10.5, 38.0, 56.0
    legend_columns, legend_row = 5, 24.0
    legend_height = math.ceil(len(colours) / legend_columns) * legend_row + 62.0
    page_width = grid * cell_size + margin * 2
    page_height = header + grid * cell_size + legend_height + margin
    canvas = pdf_canvas.Canvas(str(path), pagesize=(page_width, page_height), pageCompression=1)
    canvas.setTitle(f"MARD Fuse Bead Pattern {grid}x{grid}")
    canvas.setFillColor(HexColor("#F8F5EE"))
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#27221E"))
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(margin, page_height - 34, f"MARD Fuse Bead Pattern - {grid} x {grid}")
    grid_bottom = legend_height + margin
    canvas.setLineWidth(0.22)
    canvas.setFont("Helvetica-Bold", 3.2)
    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            left = margin + x * cell_size
            bottom = grid_bottom + (grid - y - 1) * cell_size
            canvas.setFillColor(HexColor(cell.hex if cell is not None else "#FFFFFF"))
            canvas.setStrokeColor(HexColor("#D6D0C7"))
            canvas.rect(left, bottom, cell_size, cell_size, fill=1, stroke=1)
            if cell is not None:
                canvas.setFillColor(HexColor(readable_text(cell.rgb)))
                canvas.drawCentredString(left + cell_size / 2, bottom + cell_size * 0.36, cell.code)
    canvas.setFillColor(HexColor("#27221E"))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(margin, margin + legend_height - 20, "MARD codes and bead counts")
    column_width = (page_width - margin * 2) / legend_columns
    for index, colour in enumerate(colours):
        column, row = index % legend_columns, index // legend_columns
        x = margin + column * column_width
        y = margin + legend_height - 42 - row * legend_row
        canvas.setFillColor(HexColor(colour.hex))
        canvas.setStrokeColor(HexColor("#8F887F"))
        canvas.roundRect(x, y, 15, 15, 2, fill=1, stroke=1)
        canvas.setFillColor(HexColor("#27221E"))
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(x + 21, y + 4, f"{colour.code} x {counts[colour.code]}")
    canvas.showPage()
    canvas.save()


def escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_svg(cells: list[list[Colour | None]], counts: Counter[str], path: Path) -> None:
    grid = len(cells)
    cell_size, margin, legend_row = 28, 72, 32
    used = used_colours(cells)
    legend_height = math.ceil(len(used) / 6) * legend_row + 90
    width = grid * cell_size + margin * 2
    height = grid * cell_size + margin * 2 + legend_height
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8F5EE"/>',
        f'<text x="{margin}" y="42" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#27221E">MARD 拼豆图纸 · {grid}×{grid}</text>',
    ]
    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            sx, sy = margin + x * cell_size, margin + y * cell_size
            fill = cell.hex if cell is not None else "#FFFFFF"
            chunks.append(f'<rect x="{sx}" y="{sy}" width="{cell_size}" height="{cell_size}" fill="{fill}" stroke="#D6D0C7" stroke-width="0.7"/>')
            if cell is not None:
                chunks.append(f'<text x="{sx + cell_size / 2}" y="{sy + cell_size * .66}" text-anchor="middle" font-family="Arial,sans-serif" font-size="7.5" font-weight="700" fill="{readable_text(cell.rgb)}">{escape_xml(cell.code)}</text>')
    legend_y = margin + grid * cell_size + 46
    chunks.append(f'<text x="{margin}" y="{legend_y - 18}" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#27221E">色号与用量</text>')
    column_width = (width - margin * 2) / 6
    for index, colour in enumerate(used):
        column, row = index % 6, index // 6
        x, y = margin + column * column_width, legend_y + row * legend_row
        chunks.append(f'<rect x="{x}" y="{y - 16}" width="22" height="22" rx="4" fill="{colour.hex}" stroke="#8F887F"/>')
        chunks.append(f'<text x="{x + 30}" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#27221E">{escape_xml(colour.code)} × {counts[colour.code]}</text>')
    chunks.append("</svg>")
    path.write_text("\n".join(chunks), encoding="utf-8")


def write_outputs(cells: list[list[Colour | None]], output_dir: Path, report: dict, debug_exports: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter(cell.code for row in cells for cell in row if cell is not None)
    chart_png = output_dir / "chart.png"
    write_chart_png(cells, counts, chart_png)
    write_pdf(cells, counts, chart_png, output_dir / "chart.pdf")
    if not debug_exports:
        return
    write_svg(cells, counts, output_dir / "chart.svg")
    with (output_dir / "cells.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row/col", *range(1, len(cells) + 1)])
        for index, row in enumerate(cells, 1):
            writer.writerow([index, *[cell.code if cell is not None else "" for cell in row]])
    with (output_dir / "counts.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MARD色号", "HEX屏幕参考", "颗数"])
        used = {cell.code: cell for row in cells for cell in row if cell is not None}
        for code in sorted(counts):
            writer.writerow([code, used[code].hex, counts[code]])
    pattern = [[cell.code if cell is not None else None for cell in row] for row in cells]
    (output_dir / "pattern.json").write_text(json.dumps({"grid": len(cells), "cells": pattern}, ensure_ascii=False), encoding="utf-8")
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Input file not found: {args.input}")
    palette = load_palette(PALETTE_PATH)
    image = Image.open(args.input)
    mask = foreground_mask(image, args.background, args.background_tolerance)
    image, mask = crop_and_square(image, mask)
    sampled = sample_grid(image, mask, args.grid, args.foreground_threshold)
    rgb_samples = [cell for row in sampled for cell in row if cell is not None]
    if not rgb_samples:
        raise SystemExit("No occupied bead cells remained after sampling.")
    selected = adaptive_palette(rgb_samples, palette, args.colors)
    cells = quantize(sampled, selected)
    cleanup = clean_speckles(cells)
    bridge_cells = close_tiny_gaps(cells, args.connect_gap)
    groups = components(cells)
    significant = [group for group in groups if len(group) >= 4]
    articulations = critical_articulations(cells) if len(significant) == 1 else 0
    bead_count = sum(len(group) for group in groups)
    report = {
        "input": str(args.input.resolve()),
        "grid": args.grid,
        "requested_colors": args.colors,
        "used_colors": len({cell.code for row in cells for cell in row if cell is not None}),
        "palette_codes": sorted({cell.code for row in cells for cell in row if cell is not None}),
        "beads": bead_count,
        "components": len(significant),
        "tiny_components": len(groups) - len(significant),
        "critical_articulations": articulations,
        "bridge_cells_added": bridge_cells,
        **cleanup,
    }
    report["safe_for_pendant"] = report["components"] == 1 and report["critical_articulations"] == 0
    report["max_beads"] = args.max_beads
    report["bead_budget_enforced"] = args.max_beads > 0
    report["within_bead_budget"] = args.max_beads <= 0 or bead_count <= args.max_beads
    report["passes_quality_gate"] = report["safe_for_pendant"] and report["within_bead_budget"]
    report["warnings"] = []
    if report["components"] != 1:
        report["warnings"].append("人物主体没有连成一块；请让 AI 扩大头发、帽子或短肩膀的自然接触区域。")
    if report["critical_articulations"]:
        report["warnings"].append("检测到单豆承重位置；请把连接处加宽到至少两到三颗豆。")
    if not report["within_bead_budget"]:
        report["warnings"].append(f"总豆数 {bead_count} 超过上限 {args.max_beads}；请先减少衣服/帽子面积，再考虑降低格数。")
    write_outputs(cells, args.output_dir, report, args.debug_exports)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if args.strict and not report["passes_quality_gate"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
