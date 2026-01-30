#!/usr/bin/env python3
"""
rectangle_svg.py
Input: rectangle width/height in inches
Output: SVG in millimeters, with kerf compensation and a margin offset.
"""

from pathlib import Path

MAX_WIDTH_IN = 2.0
MAX_HEIGHT_IN = 2.0
MIN_IN = 0.1

INCH_TO_MM = 25.4       # 1 inch = 25.4 mm
KERF_MM = 0.1           # assuming: 0.1mm kerf
MARGIN_MM = 5.0         # keep cut away from canvas edge
STROKE_WIDTH_MM = 0.1   # display stroke; not the kerf


def read_in(prompt: str) -> float:
    """Read a float in inches from user input."""
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number (example: 4 or 4.25).")


def validate_input_inches(w_in: float, h_in: float) -> None:
    """Validate against limits in INCHES (before kerf compensation)."""
    if w_in < MIN_IN or h_in < MIN_IN:
        raise ValueError(f"Dimensions must be at least {MIN_IN} inches.")
    if w_in > MAX_WIDTH_IN:
        raise ValueError(f"Width exceeds max of {MAX_WIDTH_IN} inches.")
    if h_in > MAX_HEIGHT_IN:
        raise ValueError(f"Height exceeds max of {MAX_HEIGHT_IN} inches.")


def make_svg(width_mm: float, height_mm: float, margin_mm: float) -> str:
    """
    Create SVG where 1 unit in viewBox = 1 mm.
    Rectangle is placed at (margin, margin).
    Canvas size includes margin on all sides.
    """
    canvas_w = width_mm + 2 * margin_mm
    canvas_h = height_mm + 2 * margin_mm

    x = margin_mm
    y = margin_mm

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{canvas_w}mm" height="{canvas_h}mm"
     viewBox="0 0 {canvas_w} {canvas_h}">
  <rect x="{x}" y="{y}"
        width="{width_mm}" height="{height_mm}"
        fill="none" stroke="black" stroke-width="{STROKE_WIDTH_MM}" />
</svg>
"""


def main() -> None:
    print("Rectangle → SVG generator (input: inches, output: mm)")
    print(f"Input limits: {MAX_WIDTH_IN}in x {MAX_HEIGHT_IN}in (min {MIN_IN}in)")
    print(f"Kerf compensation: +{KERF_MM}mm to width and height")
    print(f"Margin: {MARGIN_MM}mm\n")

    w_in = read_in("Enter rectangle width (in): ")
    h_in = read_in("Enter rectangle height (in): ")
    
    file_name_in = input('Enter file name (optional): ').strip()
    if not file_name_in:
        file_name_in = "rectangle"

    output_file = (Path(__file__).resolve().parent / "SVGs" / Path(file_name_in).name).with_suffix(".svg")


    try:
        validate_input_inches(w_in, h_in)
    except ValueError as e:
        print(f"\nError: {e}\nNo file created.")
        return

    # Convert inches -> mm
    w_mm = w_in * INCH_TO_MM
    h_mm = h_in * INCH_TO_MM

    # Kerf compensation: expand geometry so the cut result matches intended size
    w_mm_comp = w_mm + KERF_MM
    h_mm_comp = h_mm + KERF_MM

    svg_text = make_svg(w_mm_comp, h_mm_comp, MARGIN_MM)
    
    print("\n--- SVG Content ---")
    print(svg_text)
    print("-------------------\n")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(svg_text, encoding="utf-8")

    print(f"\nWrote SVG to: {output_file.resolve()}")
    print(f"Input: {w_in}in x {h_in}in")
    print(f"Converted: {w_mm:.3f}mm x {h_mm:.3f}mm")
    print(f"Compensated: {w_mm_comp:.3f}mm x {h_mm_comp:.3f}mm")


if __name__ == "__main__":
    main()
