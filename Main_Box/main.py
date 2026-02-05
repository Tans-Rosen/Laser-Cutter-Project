"""
main.py — Simple mode CLI
"""

import constants as C
from validate import validate_inputs
from generate import generate_svg, build_pieces, shelf_pack

WALLS = ("front", "back", "left", "right")

def prompt_yes_no(prompt: str) -> bool:
    while True:
        s = input(prompt + " (y/n): ").strip()
        if s in ("y", "Y"):
            return True
        if s in ("n", "N"):
            return False
        print("Please enter 'y' or 'n'.")

def prompt_float(prompt: str) -> float:
    while True:
        s = input(prompt + ": ").strip()
        try:
            return float(s)
        except ValueError:
            print("Please enter a number (int or float).")

def prompt_int_from_set(prompt: str, allowed: set[int]) -> int:
    while True:
        s = input(prompt + ": ").strip()
        try:
            val = int(s)
        except ValueError:
            print(f"Please enter one of: {sorted(allowed)}.")
            continue
        if val in allowed:
            return val
        print(f"Please enter one of: {sorted(allowed)}.")

def prompt_non_empty_text(prompt: str) -> str:
    while True:
        s = input(prompt + ": ")
        if s.strip():
            return s
        print("Please enter non-empty text.")

def _build_base_inputs(length_in: float, width_in: float, height_in: float, num_dividers: int, divider_positions: list[float]) -> dict:
    inputs: dict = {
        "length": length_in,
        "width": width_in,
        "height": height_in,
        "numDividers": num_dividers,
        "kerf_mm": C.KERF_MM_DEFAULT,
    }
    if num_dividers >= 1:
        inputs["dividerPos1"] = divider_positions[0]
    if num_dividers == 2:
        inputs["dividerPos2"] = divider_positions[1]

    # Pre-fill wall flags so validate_inputs can run before we ask for text/fractal
    for wall in WALLS:
        inputs[f"{wall}Text"] = False
        inputs[f"{wall}Fractal"] = False
        inputs[f"{wall}TextContent"] = ""
    return inputs

def main():
    print("Laser-cut Acrylic Pencil Holder (simple mode, kerf-aware)")
    while True:
        # Dimensions
        length_in = prompt_float("Length (in)")
        width_in = prompt_float("Width  (in)")
        height_in = prompt_float("Height (in)")

        # Dividers (prompt right after height)
        num_dividers = prompt_int_from_set("numDividers (0/1/2)", {0, 1, 2})
        divider_positions: list[float] = []
        if num_dividers >= 1:
            divider_positions.append(prompt_float("dividerPos1 from LEFT inner wall (in)"))
        if num_dividers == 2:
            divider_positions.append(prompt_float("dividerPos2 from LEFT inner wall (in)"))

        # Pre-validate and fit check before text prompts
        base_inputs = _build_base_inputs(length_in, width_in, height_in, num_dividers, divider_positions)
        try:
            base_params = validate_inputs(base_inputs)
            pieces = build_pieces(base_params)
            placements = shelf_pack(pieces, C.SHEET_W_MM, C.SHEET_H_MM, C.PART_GAP_MM)
            if placements is None:
                print("Error: Parts do not fit on one 12x18 sheet. Please re-enter dimensions.")
                continue
        except ValueError as e:
            print(f"Error: {e}")
            print("Please re-enter dimensions and divider positions.")
            continue

        # Wall decorations (after fit check)
        inputs = dict(base_inputs)
        for wall in WALLS:
            wants_text = prompt_yes_no(f"{wall}Text")
            inputs[f"{wall}Text"] = wants_text
            if wants_text:
                inputs[f"{wall}TextContent"] = prompt_non_empty_text(f"{wall}TextContent")
                inputs[f"{wall}Fractal"] = False
            else:
                wants_fractal = prompt_yes_no(f"{wall}Fractal")
                inputs[f"{wall}Fractal"] = wants_fractal
                inputs[f"{wall}TextContent"] = ""

        # Final validation + generate
        try:
            params = validate_inputs(inputs)
            svg = generate_svg(params)
        except ValueError as e:
            print(f"Error: {e}")
            print("Please re-enter inputs.")
            continue

        out_path = "output.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)

        print(f"Wrote {out_path}")
        break

if __name__ == "__main__":
    main()
