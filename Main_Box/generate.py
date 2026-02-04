"""generate.py — Simple mode

What this generates:
- Wall rectangles (with internal cutouts)
- Floor OUTLINE as a tabbed perimeter (SVG path) + optional internal cutouts

Kerf-aware internal features (slots/holes/pockets).
Divider convention A implemented: slots in FRONT/BACK walls based on dividerPos from left inner wall.

Tab system (new):
- Floor has outward tabs on all 4 edges.
- Each wall has matching bottom slots.
- All fit tuning is controlled in constants.py:
  - TAB_SLOT_CLEARANCE_MM, TAB_WIDTH_MM, TAB_COUNT_LONG_EDGE, TAB_COUNT_SHORT_EDGE
"""

from typing import List, Dict, Optional, Tuple
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

    # Floor bounding box includes tab protrusions on all sides.
    tab_len_draw = C.floor_tab_len_draw(kerf)
    floor_w = L_in + 2 * tab_len_draw
    floor_h = W_in + 2 * tab_len_draw
    pieces.append(_new_piece("floor", floor_w, floor_h))

    for i in range(params["num_dividers"]):
        pieces.append(_new_piece(f"divider_{i+1}", L_in, H_out - t))  # divider runs along LENGTH

    _add_floor_tabs_and_wall_bottom_slots(pieces, params)
    _add_divider_slots_convention_A(pieces, params)
    _add_captive_hardware_placeholders(pieces, params)
    _add_standard_engraving(pieces, params)

    return pieces

def _new_piece(name: str, w: float, h: float) -> dict:
    # outline: either a rect (default) or a path (used by the floor tabs)
    return {"name": name, "w": w, "h": h, "outline": {"type": "rect"}, "cuts": [], "engraves": []}

def _find_piece(pieces: List[dict], name: str) -> dict:
    for p in pieces:
        if p["name"] == name:
            return p
    raise KeyError(f"Missing piece: {name}")

# -------------------------
# Floor tabs + wall bottom slots
# -------------------------
def _tab_centers(edge_len: float, count: int, margin: float) -> List[float]:
    """Return `count` tab centers spanning edge_len, staying inside [margin, edge_len - margin]."""
    if count <= 0:
        return []
    if count == 1:
        return [edge_len / 2]

    usable = edge_len - 2 * margin
    if usable <= 0:
        # Degenerate: just place them at the midpoint to avoid crashes.
        return [edge_len / 2 for _ in range(count)]

    step = usable / (count + 1)
    return [margin + step * (i + 1) for i in range(count)]


def _tab_intervals(edge_len: float, centers: List[float], tab_w: float, margin: float) -> List[Tuple[float, float]]:
    """Convert centers -> [start,end] intervals, clamped to avoid corners and each other."""
    intervals: List[Tuple[float, float]] = []
    half = tab_w / 2
    for c in centers:
        start = max(margin, c - half)
        end = min(edge_len - margin, c + half)
        if end > start:
            intervals.append((start, end))
    intervals.sort()
    return intervals


def _floor_tabbed_outline_path(base_x: float, base_y: float, base_w: float, base_h: float,
                              tab_len: float, tab_w: float,
                              n_long: int, n_short: int, margin: float) -> str:
    """Build an SVG path for a rectangle with outward tabs on all 4 edges."""

    # Along the top/bottom edges (length direction)
    top_centers = _tab_centers(base_w, n_long, margin)
    top_tabs = _tab_intervals(base_w, top_centers, tab_w, margin)
    # Along the left/right edges (width direction)
    side_centers = _tab_centers(base_h, n_short, margin)
    side_tabs = _tab_intervals(base_h, side_centers, tab_w, margin)

    x0, y0 = base_x, base_y
    x1, y1 = base_x + base_w, base_y + base_h

    d: List[str] = []
    d.append(f"M {x0:.4f} {y0:.4f}")

    # TOP edge: (x0,y0) -> (x1,y0), tabs go upward to y0 - tab_len
    cur_x = x0
    for a, b in top_tabs:
        xa = x0 + a
        xb = x0 + b
        d.append(f"L {xa:.4f} {y0:.4f}")
        d.append(f"L {xa:.4f} {y0 - tab_len:.4f}")
        d.append(f"L {xb:.4f} {y0 - tab_len:.4f}")
        d.append(f"L {xb:.4f} {y0:.4f}")
        cur_x = xb
    d.append(f"L {x1:.4f} {y0:.4f}")

    # RIGHT edge: (x1,y0) -> (x1,y1), tabs go right to x1 + tab_len
    for a, b in side_tabs:
        ya = y0 + a
        yb = y0 + b
        d.append(f"L {x1:.4f} {ya:.4f}")
        d.append(f"L {x1 + tab_len:.4f} {ya:.4f}")
        d.append(f"L {x1 + tab_len:.4f} {yb:.4f}")
        d.append(f"L {x1:.4f} {yb:.4f}")
    d.append(f"L {x1:.4f} {y1:.4f}")

    # BOTTOM edge: (x1,y1) -> (x0,y1), tabs go downward to y1 + tab_len
    for a, b in reversed(top_tabs):
        xa = x0 + a
        xb = x0 + b
        d.append(f"L {xb:.4f} {y1:.4f}")
        d.append(f"L {xb:.4f} {y1 + tab_len:.4f}")
        d.append(f"L {xa:.4f} {y1 + tab_len:.4f}")
        d.append(f"L {xa:.4f} {y1:.4f}")
    d.append(f"L {x0:.4f} {y1:.4f}")

    # LEFT edge: (x0,y1) -> (x0,y0), tabs go left to x0 - tab_len
    for a, b in reversed(side_tabs):
        ya = y0 + a
        yb = y0 + b
        d.append(f"L {x0:.4f} {yb:.4f}")
        d.append(f"L {x0 - tab_len:.4f} {yb:.4f}")
        d.append(f"L {x0 - tab_len:.4f} {ya:.4f}")
        d.append(f"L {x0:.4f} {ya:.4f}")
    d.append(f"L {x0:.4f} {y0:.4f}")
    d.append("Z")

    return " ".join(d)


def _add_floor_tabs_and_wall_bottom_slots(pieces: List[dict], params: dict) -> None:
    """Adds a tabbed floor outline (path) and matching bottom slots to each wall."""
    kerf = params["kerf"]
    t = params["t"]

    tab_len_draw = C.floor_tab_len_draw(kerf)
    tab_w = C.TAB_WIDTH_MM
    slot_w_draw = C.tab_slot_draw_w(kerf)
    slot_depth_draw = C.wall_bottom_slot_draw_depth(kerf)

    floor = _find_piece(pieces, "floor")

    # Base floor rectangle (the portion inside the walls) is L_in x W_in,
    # centered inside the floor bounding box with a tab_len_draw margin.
    base_x = tab_len_draw
    base_y = tab_len_draw
    base_w = params["L_in"]
    base_h = params["W_in"]

    # Create floor outline path
    # Use a conservative margin so we don't generate tabs too close to corners.
    edge_margin = C.MIN_EDGE_MARGIN_MM
    d = _floor_tabbed_outline_path(
        base_x=base_x,
        base_y=base_y,
        base_w=base_w,
        base_h=base_h,
        tab_len=tab_len_draw,
        tab_w=tab_w,
        n_long=C.TAB_COUNT_LONG_EDGE,
        n_short=C.TAB_COUNT_SHORT_EDGE,
        margin=edge_margin,
    )
    floor["outline"] = svg_path(d, stroke="red")

    # Add matching slots along the bottom edge of each wall.
    # NOTE: Wall coordinate convention in this file is unchanged (x=0..w for the panel).
    # Slots are placed relative to the wall's full width, inside a margin.
    for wall_name in ("wall_front", "wall_back"):
        wall = _find_piece(pieces, wall_name)
        centers = _tab_centers(wall["w"], C.TAB_COUNT_LONG_EDGE, edge_margin)
        intervals = _tab_intervals(wall["w"], centers, slot_w_draw, edge_margin)
        for a, b in intervals:
            x = a
            w = b - a
            y = wall["h"] - slot_depth_draw
            wall["cuts"].append(svg_rect(x, y, w, slot_depth_draw, stroke="red"))

    for wall_name in ("wall_left", "wall_right"):
        wall = _find_piece(pieces, wall_name)
        centers = _tab_centers(wall["w"], C.TAB_COUNT_SHORT_EDGE, edge_margin)
        intervals = _tab_intervals(wall["w"], centers, slot_w_draw, edge_margin)
        for a, b in intervals:
            x = a
            w = b - a
            y = wall["h"] - slot_depth_draw
            wall["cuts"].append(svg_rect(x, y, w, slot_depth_draw, stroke="red"))

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

    # Floor base origin is offset by the floor tab margin.
    tab_len_draw = C.floor_tab_len_draw(kerf)

    # Map dividerPos (from left inner wall) to x on FRONT/BACK panels.
    # Standard choice:
    # - wall panel local x=0 is aligned with left INNER wall line.
    # This keeps the mental model consistent with dividerPos definition.
    # If you later change coordinate convention, adjust this mapping only.
    for p_mm in params["divider_positions"]:
        x = p_mm
        y = bottom_margin

        # slots in front/back walls
        front["cuts"].append(svg_rect(x, y, slot_w_draw, slot_h, stroke="red"))
        back["cuts"].append(svg_rect(x, y, slot_w_draw, slot_h, stroke="red"))

        # optional floor slot (short slot for stiffness)
        floor_slot_h_draw = C.internal_cut_draw_dim(params["t"], kerf)  # through slot height == thickness
        fy = (floor["h"] - floor_slot_h_draw) / 2
        floor["cuts"].append(svg_rect(tab_len_draw + x, fy, slot_w_draw, floor_slot_h_draw, stroke="red"))

# -------------------------
# Captive nut anti-spin (placeholder geometry)
# -------------------------
def _add_captive_hardware_placeholders(pieces: List[dict], params: dict) -> None:
    """
    You said: nut must not spin or jiggle loose.
    A square pocket prevents spin; clearance controls jiggle.

    This skeleton places hole + square pocket centered together.
    Later, when you implement real internal tabs, you'll move the pocket
    into the tab region. The sizing here is already kerf-aware.
    """
    kerf = params["kerf"]
    hole_d_draw = C.screw_hole_draw_d(kerf)
    pocket_w_draw = C.nut_pocket_draw_w(kerf)

    H = params["H_out"]
    ys = [frac * H for frac in (0.25, 0.75)]

    for wall_name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        wall = _find_piece(pieces, wall_name)
        x_left = C.MIN_EDGE_MARGIN_MM
        x_right = wall["w"] - C.MIN_EDGE_MARGIN_MM

        for y in ys:
            wall["cuts"].append(svg_circle(x_left, y, hole_d_draw/2, stroke="red"))
            wall["cuts"].append(svg_circle(x_right, y, hole_d_draw/2, stroke="red"))

            wall["cuts"].append(svg_rect(x_left - pocket_w_draw/2, y - pocket_w_draw/2, pocket_w_draw, pocket_w_draw, stroke="red"))
            wall["cuts"].append(svg_rect(x_right - pocket_w_draw/2, y - pocket_w_draw/2, pocket_w_draw, pocket_w_draw, stroke="red"))

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

        # Outline (either a rect or a path)
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
