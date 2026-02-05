"""
generate.py — Simple mode
Kerf-aware internal features (slots/holes/pockets).
Divider convention A implemented: slots in FRONT/BACK walls based on dividerPos from left inner wall.
"""

from typing import List, Dict, Optional
import constants as C

# -------------------------
# Packing (simple shelf pack)
# -------------------------
def shelf_pack(pieces: List[dict], sheet_w: float, sheet_h: float, gap: float) -> Optional[List[dict]]:
    items = sorted(pieces, key=lambda p: p["h"], reverse=True)
    x = gap
    y = gap
    row_h = 0.0
    placed = []

    for p in items:
        w, h = p["w"], p["h"]
        if x + w + gap > sheet_w:
            x = gap
            y += row_h + gap
            row_h = 0.0

        if y + h + gap > sheet_h:
            return None

        placed.append({"name": p["name"], "x": x, "y": y, "rot": 0})
        x += w + gap
        row_h = max(row_h, h)

    return placed

# -------------------------
# Piece construction
# -------------------------
def generate_svg(params: dict) -> str:
    pieces = build_pieces(params)
    placements = shelf_pack(pieces, C.SHEET_W_MM, C.SHEET_H_MM, C.PART_GAP_MM)
    if placements is None:
        raise ValueError("Parts do not fit on one 12x18 sheet (packing failed).")
    return to_svg(pieces, placements, C.SHEET_W_MM, C.SHEET_H_MM)

def build_pieces(params: dict) -> List[dict]:
    L_out, W_out, H_out = params["L_out"], params["W_out"], params["H_out"]
    L_in, W_in = params["L_in"], params["W_in"]
    t, kerf = params["t"], params["kerf"]

    pieces: List[dict] = []
    pieces.append(_new_piece("wall_front", L_out, H_out))
    pieces.append(_new_piece("wall_back",  L_out, H_out))
    pieces.append(_new_piece("wall_left",  W_out, H_out))
    pieces.append(_new_piece("wall_right", W_out, H_out))

    # IMPORTANT: floor uses outer footprint so wall↔floor corner joints can line up.
    pieces.append(_new_piece("floor",      L_out,  W_out))

    for i in range(params["num_dividers"]):
        pieces.append(_new_piece(f"divider_{i+1}", L_in, H_out - t))  # divider runs along LENGTH

    _add_corner_finger_joints(pieces, params)

    _add_divider_slots_convention_A(pieces, params)
    _add_captive_hardware_placeholders(pieces, params)
    _add_standard_engraving(pieces, params)

    return pieces

def _new_piece(name: str, w: float, h: float) -> dict:
    return {"name": name, "w": w, "h": h, "outline": {"type": "rect"}, "cuts": [], "engraves": []}

def _find_piece(pieces: List[dict], name: str) -> dict:
    for p in pieces:
        if p["name"] == name:
            return p
    raise KeyError(f"Missing piece: {name}")

# -------------------------
# Corner finger joints (minimal, box-style)
# -------------------------
def _corner_positions(edge_len: float, feature_w: float, margin: float) -> tuple[float, float]:
    """Return two feature center positions near the ends of an edge."""
    bottom = margin + feature_w / 2
    top = edge_len - (margin + feature_w / 2)
    return bottom, top

def _wall_outline_with_corner_joints(w: float, h: float, kerf: float) -> dict:
    """
    Wall outline:
    - Top edge: plain (no lid).
    - Left vertical edge: two FEMALE pockets (indent inward).
    - Right vertical edge: two MALE tabs (protrude outward).
    """
    m = C.MIN_EDGE_MARGIN_MM
    fw = C.finger_width_draw(kerf)
    tab_d = C.finger_depth_draw(kerf)
    slot_d = C.finger_slot_depth_draw(kerf)

    y1, y2 = _corner_positions(h, fw, m)

    # Convert centers to [start,end] for each finger
    a1, b1 = y1 - fw / 2, y1 + fw / 2
    a2, b2 = y2 - fw / 2, y2 + fw / 2

    # Build path clockwise starting at bottom-left (0,h)
    x0, x1 = 0.0, w
    d = []
    d.append(f"M {x0:.4f} {h:.4f}")
    d.append(f"L {x1:.4f} {h:.4f}")

    # RIGHT edge upward with 2 outward tabs
    d.append(f"L {x1:.4f} {a1:.4f}")
    d.append(f"L {x1 + tab_d:.4f} {a1:.4f}")
    d.append(f"L {x1 + tab_d:.4f} {b1:.4f}")
    d.append(f"L {x1:.4f} {b1:.4f}")

    d.append(f"L {x1:.4f} {a2:.4f}")
    d.append(f"L {x1 + tab_d:.4f} {a2:.4f}")
    d.append(f"L {x1 + tab_d:.4f} {b2:.4f}")
    d.append(f"L {x1:.4f} {b2:.4f}")

    d.append(f"L {x1:.4f} {0.0:.4f}")
    d.append(f"L {x0:.4f} {0.0:.4f}")

    # LEFT edge downward with 2 inward pockets
    d.append(f"L {x0:.4f} {b2:.4f}")
    d.append(f"L {x0 + slot_d:.4f} {b2:.4f}")
    d.append(f"L {x0 + slot_d:.4f} {a2:.4f}")
    d.append(f"L {x0:.4f} {a2:.4f}")

    d.append(f"L {x0:.4f} {b1:.4f}")
    d.append(f"L {x0 + slot_d:.4f} {b1:.4f}")
    d.append(f"L {x0 + slot_d:.4f} {a1:.4f}")
    d.append(f"L {x0:.4f} {a1:.4f}")

    d.append(f"L {x0:.4f} {h:.4f}")
    d.append("Z")

    return {"type": "path", "d": " ".join(d), "stroke": "red", "sw": 0.1}

def _floor_outline_with_corner_pockets(w: float, h: float, kerf: float) -> dict:
    """
    Floor outline (outer footprint):
    - Rectangle w x h
    - Two FEMALE pockets near each corner on each edge, so each wall can have
      a bottom indexing feature near each end that inserts into the floor.
    """
    m = C.MIN_EDGE_MARGIN_MM
    fw = C.finger_width_draw(kerf)
    pocket_d = C.finger_slot_depth_draw(kerf)

    xL0 = m
    xL1 = m + fw
    xR1 = w - m
    xR0 = w - m - fw

    yT0 = m
    yT1 = m + fw
    yB1 = h - m
    yB0 = h - m - fw

    d = []
    d.append(f"M {0.0:.4f} {0.0:.4f}")

    # Top edge pockets
    d.append(f"L {xL0:.4f} {0.0:.4f}")
    d.append(f"L {xL0:.4f} {pocket_d:.4f}")
    d.append(f"L {xL1:.4f} {pocket_d:.4f}")
    d.append(f"L {xL1:.4f} {0.0:.4f}")

    d.append(f"L {xR0:.4f} {0.0:.4f}")
    d.append(f"L {xR0:.4f} {pocket_d:.4f}")
    d.append(f"L {xR1:.4f} {pocket_d:.4f}")
    d.append(f"L {xR1:.4f} {0.0:.4f}")
    d.append(f"L {w:.4f} {0.0:.4f}")

    # Right edge pockets
    d.append(f"L {w:.4f} {yT0:.4f}")
    d.append(f"L {w - pocket_d:.4f} {yT0:.4f}")
    d.append(f"L {w - pocket_d:.4f} {yT1:.4f}")
    d.append(f"L {w:.4f} {yT1:.4f}")

    d.append(f"L {w:.4f} {yB0:.4f}")
    d.append(f"L {w - pocket_d:.4f} {yB0:.4f}")
    d.append(f"L {w - pocket_d:.4f} {yB1:.4f}")
    d.append(f"L {w:.4f} {yB1:.4f}")
    d.append(f"L {w:.4f} {h:.4f}")

    # Bottom edge pockets
    d.append(f"L {xR1:.4f} {h:.4f}")
    d.append(f"L {xR1:.4f} {h - pocket_d:.4f}")
    d.append(f"L {xR0:.4f} {h - pocket_d:.4f}")
    d.append(f"L {xR0:.4f} {h:.4f}")

    d.append(f"L {xL1:.4f} {h:.4f}")
    d.append(f"L {xL1:.4f} {h - pocket_d:.4f}")
    d.append(f"L {xL0:.4f} {h - pocket_d:.4f}")
    d.append(f"L {xL0:.4f} {h:.4f}")
    d.append(f"L {0.0:.4f} {h:.4f}")

    # Left edge pockets
    d.append(f"L {0.0:.4f} {yB1:.4f}")
    d.append(f"L {pocket_d:.4f} {yB1:.4f}")
    d.append(f"L {pocket_d:.4f} {yB0:.4f}")
    d.append(f"L {0.0:.4f} {yB0:.4f}")

    d.append(f"L {0.0:.4f} {yT1:.4f}")
    d.append(f"L {pocket_d:.4f} {yT1:.4f}")
    d.append(f"L {pocket_d:.4f} {yT0:.4f}")
    d.append(f"L {0.0:.4f} {yT0:.4f}")

    d.append(f"L {0.0:.4f} {0.0:.4f}")
    d.append("Z")

    return {"type": "path", "d": " ".join(d), "stroke": "red", "sw": 0.1}

def _add_corner_finger_joints(pieces: List[dict], params: dict) -> None:
    kerf = params["kerf"]

    for wall_name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        wall = _find_piece(pieces, wall_name)
        wall["outline"] = _wall_outline_with_corner_joints(wall["w"], wall["h"], kerf)

    floor = _find_piece(pieces, "floor")
    floor["outline"] = _floor_outline_with_corner_pockets(floor["w"], floor["h"], kerf)

# -------------------------
# Divider slots (Convention A)
# -------------------------
def _add_divider_slots_convention_A(pieces: List[dict], params: dict) -> None:
    """
    Convention A:
    - dividerPos measured from LEFT inner wall along WIDTH (W_in axis)
    - divider runs along LENGTH (L_in) splitting width into sections
    => slots on FRONT/BACK walls at x-position corresponding to dividerPos
    """
    if params["num_dividers"] == 0:
        return

    kerf = params["kerf"]
    slot_w_draw = C.divider_slot_draw_w(kerf)

    top_cap = C.DIVIDER_SLOT_TOP_CAP_MM
    bottom_margin = C.DIVIDER_SLOT_BOTTOM_MARGIN_MM
    slot_h = params["H_out"] - top_cap - bottom_margin

    front = _find_piece(pieces, "wall_front")
    back  = _find_piece(pieces, "wall_back")
    floor = _find_piece(pieces, "floor")

    for p_mm in params["divider_positions"]:
        x = p_mm
        y = bottom_margin

        # slots in front/back walls
        front["cuts"].append(svg_rect(x, y, slot_w_draw, slot_h, stroke="red"))
        back["cuts"].append(svg_rect(x, y, slot_w_draw, slot_h, stroke="red"))

        # floor slots must be offset by wall thickness (inner origin is at x=t)
        floor_slot_h_draw = C.internal_cut_draw_dim(params["t"], kerf)
        fy = (floor["h"] - floor_slot_h_draw) / 2
        floor["cuts"].append(svg_rect(params["t"] + x, fy, slot_w_draw, floor_slot_h_draw, stroke="red"))

# -------------------------
# Captive nut + screw channel (T-slot)
# -------------------------
def _add_captive_hardware_placeholders(pieces: List[dict], params: dict) -> None:
    """
    T-slot captive nut + screw channel.

    - Cross: square pocket capturing the square nut (anti-rotation).
    - Stem: rectangular slot leading to the edge; screw shank aligns along the stem.

    This is still placeholder placement; the sizes are kerf-aware and clearance-ready.
    """
    kerf = params["kerf"]
    hole_d_draw = C.screw_hole_draw_d(kerf)

    pocket_w_draw = C.nut_pocket_draw_w(kerf)
    stem_w_draw = hole_d_draw
    stem_len_draw = C.internal_cut_draw_dim(C.T_SLOT_STEM_LENGTH_MM, kerf)

    H = params["H_out"]
    ys = [frac * H for frac in (0.25, 0.75)]

    for wall_name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        wall = _find_piece(pieces, wall_name)

        for side in ("left", "right"):
            edge_x = 0.0 if side == "left" else wall["w"]
            x_center = (stem_len_draw + pocket_w_draw / 2) if side == "left" else (wall["w"] - (stem_len_draw + pocket_w_draw / 2))

            for y in ys:
                wall["cuts"].append(svg_rect(
                    x_center - pocket_w_draw / 2,
                    y - pocket_w_draw / 2,
                    pocket_w_draw,
                    pocket_w_draw,
                    stroke="red",
                ))

                if side == "left":
                    x0, x1 = edge_x, x_center - pocket_w_draw / 2
                else:
                    x0, x1 = x_center + pocket_w_draw / 2, edge_x
                stem_x = min(x0, x1)
                stem_w = abs(x1 - x0)
                wall["cuts"].append(svg_rect(
                    stem_x,
                    y - stem_w_draw / 2,
                    stem_w,
                    stem_w_draw,
                    stroke="red",
                ))

                wall["cuts"].append(svg_circle(x_center, y, hole_d_draw / 2, stroke="red"))

# -------------------------
# Engraving (standardized)
# -------------------------
def _add_standard_engraving(pieces: List[dict], params: dict) -> None:
    wall_mode = params["wall_mode"]
    wall_text = params["wall_text"]

    mapping = {
        "front": "wall_front",
        "back":  "wall_back",
        "left":  "wall_left",
        "right": "wall_right",
    }

    for wall_key, piece_name in mapping.items():
        mode = wall_mode[wall_key]
        if mode == "none":
            continue

        piece = _find_piece(pieces, piece_name)

        m = C.ENGRAVE_MARGIN_MM
        safe_x = m
        safe_y = m
        safe_w = max(0.0, piece["w"] - 2*m)
        safe_h = max(0.0, piece["h"] - 2*m)

        cx = safe_x + safe_w / 2
        cy = safe_y + safe_h / 2

        if mode == "text":
            piece["engraves"].append(svg_text(cx, cy, wall_text[wall_key]))
        elif mode == "fractal":
            piece["engraves"].append(svg_rect(safe_x, safe_y, safe_w, safe_h, stroke="black"))

# -------------------------
# SVG primitives + export
# -------------------------
def svg_rect(x, y, w, h, stroke="red", stroke_width=0.1) -> dict:
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h, "stroke": stroke, "sw": stroke_width}

def svg_circle(cx, cy, r, stroke="red", stroke_width=0.1) -> dict:
    return {"type": "circle", "cx": cx, "cy": cy, "r": r, "stroke": stroke, "sw": stroke_width}

def svg_path(d: str, stroke="red", stroke_width=0.1) -> dict:
    return {"type": "path", "d": d, "stroke": stroke, "sw": stroke_width}

def svg_text(x, y, text: str) -> dict:
    return {
        "type": "text",
        "x": x, "y": y, "text": text,
        "font": C.TEXT_FONT_FAMILY,
        "size": C.TEXT_FONT_SIZE_MM,
        "anchor": C.TEXT_ANCHOR
    }

def to_svg(pieces: List[dict], placements: List[dict], sheet_w: float, sheet_h: float) -> str:
    place_by_name = {p["name"]: p for p in placements}

    def el(tag: str, attrs: Dict[str, str], self_close=True, text=None) -> str:
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        if text is not None:
            return f"<{tag} {a}>{text}</{tag}>"
        return f"<{tag} {a} />" if self_close else f"<{tag} {a}>"

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w}mm" height="{sheet_h}mm" viewBox="0 0 {sheet_w} {sheet_h}">')

    out.append('<g id="CUT" stroke="red" fill="none" stroke-width="0.1">')
    for piece in pieces:
        pl = place_by_name[piece["name"]]
        ox, oy = pl["x"], pl["y"]

        outline = piece.get("outline", {"type": "rect"})
        if outline.get("type") == "path":
            out.append(el("path", {
                "d": outline["d"],
                "fill": "none",
                "stroke": outline.get("stroke", "red"),
                "stroke-width": str(outline.get("sw", 0.1)),
                "transform": f"translate({ox} {oy})",
            }))
        else:
            out.append(el("rect", {
                "x": str(ox), "y": str(oy),
                "width": str(piece["w"]), "height": str(piece["h"]),
                "fill": "none", "stroke": "red", "stroke-width": "0.1",
            }))

        for c in piece["cuts"]:
            if c["type"] == "rect":
                out.append(el("rect", {
                    "x": str(ox + c["x"]), "y": str(oy + c["y"]),
                    "width": str(c["w"]), "height": str(c["h"]),
                    "fill": "none", "stroke": c["stroke"], "stroke-width": str(c["sw"]),
                }))
            elif c["type"] == "circle":
                out.append(el("circle", {
                    "cx": str(ox + c["cx"]), "cy": str(oy + c["cy"]),
                    "r": str(c["r"]),
                    "fill": "none", "stroke": c["stroke"], "stroke-width": str(c["sw"]),
                }))
            elif c["type"] == "path":
                out.append(el("path", {
                    "d": c["d"],
                    "fill": "none",
                    "stroke": c["stroke"],
                    "stroke-width": str(c["sw"]),
                    "transform": f"translate({ox} {oy})",
                }))
    out.append("</g>")

    out.append('<g id="ENGRAVE" stroke="black" fill="none" stroke-width="0.1">')
    for piece in pieces:
        pl = place_by_name[piece["name"]]
        ox, oy = pl["x"], pl["y"]
        for e in piece["engraves"]:
            if e["type"] == "rect":
                out.append(el("rect", {
                    "x": str(ox + e["x"]), "y": str(oy + e["y"]),
                    "width": str(e["w"]), "height": str(e["h"]),
                    "fill": "none", "stroke": e["stroke"], "stroke-width": str(e["sw"]),
                }))
            elif e["type"] == "text":
                out.append(el("text", {
                    "x": str(ox + e["x"]),
                    "y": str(oy + e["y"]),
                    "fill": "black",
                    "font-family": e["font"],
                    "font-size": str(e["size"]),
                    "text-anchor": e["anchor"],
                    "dominant-baseline": "middle",
                }, self_close=False, text=e["text"]))
    out.append("</g>")

    out.append("</svg>")
    return "\n".join(out)
