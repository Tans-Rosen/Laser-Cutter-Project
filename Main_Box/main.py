"""
main.py — Simple mode CLI
"""

import constants as C
from validate import validate_inputs
from generate import generate_svg

def prompt_bool(prompt: str) -> bool:
    s = input(prompt + " (y/n): ").strip().lower()
    return s in ("y", "yes", "true", "1")

def prompt_float(prompt: str) -> float:
    return float(input(prompt + ": ").strip())

def prompt_int(prompt: str) -> int:
    return int(input(prompt + ": ").strip())

def main():
    print("Laser-cut Acrylic Pencil Holder (simple mode, kerf-aware)")

    inputs = {}
    inputs["length"] = prompt_float("Length (in)")
    inputs["width"]  = prompt_float("Width  (in)")
    inputs["height"] = prompt_float("Height (in)")

    for wall in ("front", "back", "left", "right"):
        inputs[f"{wall}Text"] = prompt_bool(f"{wall}Text")
        inputs[f"{wall}Fractal"] = prompt_bool(f"{wall}Fractal")
        inputs[f"{wall}TextContent"] = input(f"{wall}TextContent: ") if inputs[f"{wall}Text"] else ""

    inputs["numDividers"] = prompt_int("numDividers (0/1/2)")
    if inputs["numDividers"] >= 1:
        inputs["dividerPos1"] = prompt_float("dividerPos1 from left inner wall (in)")
    if inputs["numDividers"] == 2:
        inputs["dividerPos2"] = prompt_float("dividerPos2 from left inner wall (in)")

    # Use default kerf for now; you can expose this later if you want
    inputs["kerf_mm"] = C.KERF_MM_DEFAULT

    params = validate_inputs(inputs)
    svg = generate_svg(params)

    out_path = "output.svg"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
