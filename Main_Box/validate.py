"""
validate.py — Simple mode
Validates raw user inputs and returns derived params in mm.
Divider convention A: dividerPos measured from LEFT inner wall (width axis),
dividers run along LENGTH, slots go in FRONT/BACK.
"""

from typing import Dict, List
import constants as C

WALLS = ("front", "back", "left", "right")

def inches_to_mm(x_in: float) -> float:
    return x_in * C.INCH_TO_MM

def build_wall_mode(inputs: dict) -> Dict[str, str]:
    wall_mode: Dict[str, str] = {}
    for wall in WALLS:
        tflag = bool(inputs.get(f"{wall}Text", False))
        fflag = bool(inputs.get(f"{wall}Fractal", False))
        if tflag and fflag:
            raise ValueError(f"{wall}: cannot have both text and fractal.")
        wall_mode[wall] = "text" if tflag else ("fractal" if fflag else "none")
    return wall_mode

def validate_inputs(inputs: dict) -> dict:
    # Dimensions
    for key in ("length", "width", "height"):
        if key not in inputs:
            raise ValueError(f"Missing required input: {key}")
        if float(inputs[key]) <= 0:
            raise ValueError(f"{key} must be > 0")

    L_out = inches_to_mm(float(inputs["length"]))
    W_out = inches_to_mm(float(inputs["width"]))
    H_out = inches_to_mm(float(inputs["height"]))

    kerf = float(inputs.get("kerf_mm", C.KERF_MM_DEFAULT))
    t = C.T_MM

    L_in = L_out - 2 * t
    W_in = W_out - 2 * t
    if L_in <= 0 or W_in <= 0:
        raise ValueError("Box too small: interior length/width must be positive after subtracting thickness.")

    # wall modes + text content
    wall_mode = build_wall_mode(inputs)
    wall_text: Dict[str, str] = {}
    for wall in WALLS:
        content_key = f"{wall}TextContent"
        content_val = str(inputs.get(content_key, "") or "")
        if wall_mode[wall] == "text" and not content_val.strip():
            raise ValueError(f"{wall}: text enabled but {content_key} is empty.")
        wall_text[wall] = content_val

    # Dividers
    num_dividers = int(inputs.get("numDividers", 0))
    if num_dividers not in (0, 1, 2):
        raise ValueError("numDividers must be 0, 1, or 2.")

    divider_positions: List[float] = []
    if num_dividers >= 1:
        if inputs.get("dividerPos1") is None:
            raise ValueError("dividerPos1 is required when numDividers >= 1.")
        divider_positions.append(inches_to_mm(float(inputs["dividerPos1"])))
    if num_dividers == 2:
        if inputs.get("dividerPos2") is None:
            raise ValueError("dividerPos2 is required when numDividers == 2.")
        divider_positions.append(inches_to_mm(float(inputs["dividerPos2"])))

    if num_dividers == 2 and not (divider_positions[0] < divider_positions[1]):
        raise ValueError("For 2 dividers, dividerPos1 must be < dividerPos2.")

    min_gap = C.DIVIDER_MIN_GAP_MM
    for p in divider_positions:
        if p < min_gap or p > (W_in - min_gap):
            raise ValueError("Divider too close to a wall (violates minimum gap).")
    if num_dividers == 2 and (divider_positions[1] - divider_positions[0]) < min_gap:
        raise ValueError("Dividers too close to each other (violates minimum gap).")

    return {
        "L_out": L_out, "W_out": W_out, "H_out": H_out,
        "L_in": L_in, "W_in": W_in,
        "t": t,
        "kerf": kerf,
        "wall_mode": wall_mode,
        "wall_text": wall_text,
        "num_dividers": num_dividers,
        "divider_positions": divider_positions,  # measured from left inner wall along WIDTH
    }
