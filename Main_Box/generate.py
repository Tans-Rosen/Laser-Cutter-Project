"""
generate.py — Joint-based fasteners + simple finger joints

Key design rules (matches your reference intent):
- T-slots (nut traps + stem) live on the TAB piece.
- Clearance holes live on the MATING (non-tab) piece.
- Nothing tries to put both features on the same face.

Box axes (confirmed by you):
- length: left↔right span of front wall
- width:  front↔back depth
- height: bottom↔top

Dividers:
- Divider panels run FRONT→BACK (span interior width W_in).
- Divider positions are measured along interior LENGTH from left inner wall.
- Slots are cut into FRONT/BACK walls and the FLOOR.
"""

from typing import List, Optional
import constants as C
from fractal_sierpinski import Rect as FractalRect, sierpinski_paths_clipped_by_keepouts

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
# Top-level API
# -------------------------
def generate_svg(params: dict) -> str:
    pieces = build_pieces(params)
    placements = shelf_pack(pieces, C.SHEET_W_MM, C.SHEET_H_MM, C.PART_GAP_MM)
    if placements is None:
        raise ValueError("Parts do not fit on one 12x18 sheet (packing failed).")
    return to_svg(pieces, placements, C.SHEET_W_MM, C.SHEET_H_MM)

# -------------------------
# Piece construction
# -------------------------
def build_pieces(params: dict) -> List[dict]:
    L_out, W_out, H_out = params["L_out"], params["W_out"], params["H_out"]
    L_in, W_in = params["L_in"], params["W_in"]
    kerf = params["kerf"]

    pieces: List[dict] = []

    # Walls:
    # - We keep the "base rectangle" as the true nominal size.
    # - We enlarge the piece bounding box to include protruding tabs (right + bottom).
    pieces.append(_new_wall_piece("wall_front", base_w=L_out, base_h=H_out, kerf=kerf))
    pieces.append(_new_wall_piece("wall_back",  base_w=L_out, base_h=H_out, kerf=kerf))
    pieces.append(_new_wall_piece("wall_left",  base_w=W_out, base_h=H_out, kerf=kerf))
    pieces.append(_new_wall_piece("wall_right", base_w=W_out, base_h=H_out, kerf=kerf))

    # Floor: base footprint is L_out x W_out (no protruding tabs on floor, only pockets/cuts)
    pieces.append(_new_floor_piece("floor", base_w=L_out, base_h=W_out))

    # Dividers run FRONT→BACK (span W_in)
    for i in range(params["num_dividers"]):
        pieces.append(_new_piece(f"divider_{i+1}", w=W_in, h=H_out - C.T_MM))

    # Geometry
    _add_finger_joint_outlines(pieces, params)

    # Divider slots
    _add_divider_slots_front_to_back(pieces, params)

    # Joint-based fasteners (this is the big change)
    _add_joint_based_fasteners(pieces, params)

    # Engraving (placeholder)
    _add_standard_engraving(pieces, params)

    return pieces

def _new_piece(name: str, w: float, h: float) -> dict:
    return {"name": name, "w": w, "h": h, "base_w": w, "base_h": h,
            "outline": {"type": "rect", "x": 0.0, "y": 0.0, "w": w, "h": h, "stroke": "red", "sw": 0.1}, "cuts": [], "engraves": []}

def _new_wall_piece(name: str, base_w: float, base_h: float, kerf: float) -> dict:
    tab_d = C.finger_tab_depth_draw(kerf)
    # Right-edge tabs protrude to +x, bottom tabs protrude to +y
    w = base_w + tab_d
    h = base_h + tab_d
    return {"name": name, "w": w, "h": h, "base_w": base_w, "base_h": base_h,
            "outline": {"type": "rect"}, "cuts": [], "engraves": []}

def _new_floor_piece(name: str, base_w: float, base_h: float) -> dict:
    return {"name": name, "w": base_w, "h": base_h, "base_w": base_w, "base_h": base_h,
            "outline": {"type": "rect"}, "cuts": [], "engraves": []}

def _find_piece(pieces: List[dict], name: str) -> dict:
    for p in pieces:
        if p["name"] == name:
            return p
    raise KeyError(f"Missing piece: {name}")

# -------------------------
# Finger joints (simple: 2 features per vertical edge + 2 bottom tabs)
# -------------------------
def _corner_centers(edge_len: float, feature_w: float, margin: float) -> List[float]:
    a = margin + feature_w / 2
    b = edge_len - (margin + feature_w / 2)
    return [a, b]

def _wall_outline(base_w: float, base_h: float, kerf: float) -> dict:
    """
    Wall outline:
    - Top edge: plain.
    - Left edge: 2 female pockets (indent inward).
    - Right edge: 2 male tabs (protrude outward).
    - Bottom edge: 2 male tabs (protrude downward).
    """
    m = C.MIN_EDGE_MARGIN_MM
    fw = C.finger_feature_w_draw(kerf)
    tab_d = C.finger_tab_depth_draw(kerf)
    pocket_d = C.finger_pocket_depth_draw(kerf)

    ys = _corner_centers(base_h, fw, m)
    y1, y2 = ys[0], ys[1]
    a1, b1 = y1 - fw/2, y1 + fw/2
    a2, b2 = y2 - fw/2, y2 + fw/2

    xs = _corner_centers(base_w, fw, m)
    x1, x2 = xs[0], xs[1]
    c1, d1 = x1 - fw/2, x1 + fw/2
    c2, d2 = x2 - fw/2, x2 + fw/2

    x0, xB = 0.0, base_w
    y0, yB = 0.0, base_h

    d = []
    d.append(f"M {x0:.4f} {y0:.4f}")
    d.append(f"L {xB:.4f} {y0:.4f}")

    # Right edge with 2 outward tabs
    d.append(f"L {xB:.4f} {a2:.4f}")
    d.append(f"L {xB+tab_d:.4f} {a2:.4f}")
    d.append(f"L {xB+tab_d:.4f} {b2:.4f}")
    d.append(f"L {xB:.4f} {b2:.4f}")

    d.append(f"L {xB:.4f} {a1:.4f}")
    d.append(f"L {xB+tab_d:.4f} {a1:.4f}")
    d.append(f"L {xB+tab_d:.4f} {b1:.4f}")
    d.append(f"L {xB:.4f} {b1:.4f}")

    d.append(f"L {xB:.4f} {yB:.4f}")

    # Bottom edge with 2 downward tabs
    d.append(f"L {d2:.4f} {yB:.4f}")
    d.append(f"L {d2:.4f} {yB+tab_d:.4f}")
    d.append(f"L {c2:.4f} {yB+tab_d:.4f}")
    d.append(f"L {c2:.4f} {yB:.4f}")

    d.append(f"L {d1:.4f} {yB:.4f}")
    d.append(f"L {d1:.4f} {yB+tab_d:.4f}")
    d.append(f"L {c1:.4f} {yB+tab_d:.4f}")
    d.append(f"L {c1:.4f} {yB:.4f}")

    d.append(f"L {x0:.4f} {yB:.4f}")

    # Left edge with 2 inward pockets
    d.append(f"L {x0:.4f} {b1:.4f}")
    d.append(f"L {x0+pocket_d:.4f} {b1:.4f}")
    d.append(f"L {x0+pocket_d:.4f} {a1:.4f}")
    d.append(f"L {x0:.4f} {a1:.4f}")

    d.append(f"L {x0:.4f} {b2:.4f}")
    d.append(f"L {x0+pocket_d:.4f} {b2:.4f}")
    d.append(f"L {x0+pocket_d:.4f} {a2:.4f}")
    d.append(f"L {x0:.4f} {a2:.4f}")

    d.append(f"L {x0:.4f} {y0:.4f}")
    d.append("Z")

    return {"type": "path", "d": " ".join(d), "stroke": "red", "sw": 0.1}

def _floor_outline(base_w: float, base_h: float, kerf: float) -> dict:
    """
    Floor outline with 2 pockets per edge near corners (accepts wall bottom tabs).
    """
    m = C.MIN_EDGE_MARGIN_MM
    fw = C.finger_feature_w_draw(kerf)
    pocket_d = C.finger_pocket_depth_draw(kerf)

    w, h = base_w, base_h

    xL0 = m
    xL1 = m + fw
    xR0 = w - m - fw
    xR1 = w - m

    yT0 = m
    yT1 = m + fw
    yB0 = h - m - fw
    yB1 = h - m

    d = []
    d.append(f"M {0.0:.4f} {0.0:.4f}")

    # Top pockets (indent down)
    d.append(f"L {xL0:.4f} {0.0:.4f}")
    d.append(f"L {xL0:.4f} {pocket_d:.4f}")
    d.append(f"L {xL1:.4f} {pocket_d:.4f}")
    d.append(f"L {xL1:.4f} {0.0:.4f}")

    d.append(f"L {xR0:.4f} {0.0:.4f}")
    d.append(f"L {xR0:.4f} {pocket_d:.4f}")
    d.append(f"L {xR1:.4f} {pocket_d:.4f}")
    d.append(f"L {xR1:.4f} {0.0:.4f}")
    d.append(f"L {w:.4f} {0.0:.4f}")

    # Right pockets (indent left)
    d.append(f"L {w:.4f} {yT0:.4f}")
    d.append(f"L {w-pocket_d:.4f} {yT0:.4f}")
    d.append(f"L {w-pocket_d:.4f} {yT1:.4f}")
    d.append(f"L {w:.4f} {yT1:.4f}")

    d.append(f"L {w:.4f} {yB0:.4f}")
    d.append(f"L {w-pocket_d:.4f} {yB0:.4f}")
    d.append(f"L {w-pocket_d:.4f} {yB1:.4f}")
    d.append(f"L {w:.4f} {yB1:.4f}")
    d.append(f"L {w:.4f} {h:.4f}")

    # Bottom pockets (indent up)
    d.append(f"L {xR1:.4f} {h:.4f}")
    d.append(f"L {xR1:.4f} {h-pocket_d:.4f}")
    d.append(f"L {xR0:.4f} {h-pocket_d:.4f}")
    d.append(f"L {xR0:.4f} {h:.4f}")

    d.append(f"L {xL1:.4f} {h:.4f}")
    d.append(f"L {xL1:.4f} {h-pocket_d:.4f}")
    d.append(f"L {xL0:.4f} {h-pocket_d:.4f}")
    d.append(f"L {xL0:.4f} {h:.4f}")
    d.append(f"L {0.0:.4f} {h:.4f}")

    # Left pockets (indent right)
    d.append(f"L {0.0:.4f} {yB1:.4f}")
    d.append(f"L {pocket_d:.4f} {yB1:.4f}")
    d.append(f"L {pocket_d:.4f} {yB0:.4f}")
    d.append(f"L {0.0:.4f} {yB0:.4f}")

    d.append(f"L {0.0:.4f} {yT1:.4f}")
    d.append(f"L {pocket_d:.4f} {yT1:.4f}")
    d.append(f"L {pocket_d:.4f} {yT0:.4f}")
    d.append(f"L {0.0:.4f} {yT0:.4f}")

    d.append("Z")
    return {"type": "path", "d": " ".join(d), "stroke": "red", "sw": 0.1}

def _add_finger_joint_outlines(pieces: List[dict], params: dict) -> None:
    kerf = params["kerf"]
    for name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        p = _find_piece(pieces, name)
        p["outline"] = _wall_outline(p["base_w"], p["base_h"], kerf)

    floor = _find_piece(pieces, "floor")
    floor["outline"] = _floor_outline(floor["base_w"], floor["base_h"], kerf)
    
    # Dividers are simple rectangles (no finger joints)
    for p in pieces:
        if p["name"].startswith("divider_"):
            p["outline"] = {"type": "rect", "x": 0.0, "y": 0.0, "w": p["base_w"], "h": p["base_h"], "stroke": "red", "sw": 0.1}

# -------------------------
# Divider slots (FRONT→BACK dividers)
# -------------------------
def _add_divider_slots_front_to_back(pieces: List[dict], params: dict) -> None:
    kerf = params["kerf"]
    t = params["t"]
    W_in = params["W_in"]
    divider_positions = params["divider_positions"]

    slot_w = C.divider_slot_draw_w(kerf)

    y0 = C.DIVIDER_SLOT_BOTTOM_MARGIN_MM
    y1 = params["H_out"] - C.DIVIDER_SLOT_TOP_CAP_MM
    slot_h = max(0.0, y1 - y0)

    front = _find_piece(pieces, "wall_front")
    back  = _find_piece(pieces, "wall_back")
    floor = _find_piece(pieces, "floor")

    for pos in divider_positions:
        x_center = t + pos
        x_wall = x_center - slot_w / 2
        front["cuts"].append(svg_rect(x_wall, y0, slot_w, slot_h))
        back["cuts"].append(svg_rect(x_wall, y0, slot_w, slot_h))

        # Floor slit across interior width
        x_floor = x_center - slot_w / 2
        y_floor = t
        floor["cuts"].append(svg_rect(x_floor, y_floor, slot_w, W_in))

# -------------------------
# Joint-based fasteners (MATCHES YOUR REFERENCE INTENT)
# -------------------------
def _add_tslot_on_right_edge(wall: dict, kerf: float, y: float) -> None:
    """
    Add a T-slot on the RIGHT edge region of a wall:
    - Cross pocket (square) is slightly inside the base rectangle.
    - Stem goes out to the RIGHTmost outer edge so you can slide the nut in.
    """
    bw = wall["base_w"]
    tab_d = C.finger_tab_depth_draw(kerf)

    nut_w = C.nut_pocket_draw_w(kerf)
    stem_w = C.screw_hole_draw_d(kerf)  # use screw diameter as stem width
    stem_len = C.T_SLOT_STEM_LENGTH_MM

    # Place pocket center just inside the base rectangle (so it has material around it)
    cx = bw - (nut_w / 2 + 0.8)
    cy = y

    # Cross pocket
    wall["cuts"].append(svg_rect(cx - nut_w/2, cy - nut_w/2, nut_w, nut_w))

    # Stem: from pocket center toward outer edge
    x0 = cx
    x1 = bw + tab_d  # outermost edge
    # ensure stem reaches the edge; clamp length by available space
    if x1 - x0 < stem_len:
        stem_len_eff = max(0.0, x1 - x0)
    else:
        stem_len_eff = stem_len
    wall["cuts"].append(svg_rect(x1 - stem_len_eff, cy - stem_w/2, stem_len_eff, stem_w))

def _add_clearance_holes_on_left_edge(wall: dict, kerf: float, y: float) -> None:
    """
    Add a clearance hole on the LEFT edge region of the mating wall.
    Visually matches the reference: holes near the edge, aligned to the T-slots.
    """
    hole_d = C.screw_hole_draw_d(kerf)
    pocket_d = C.finger_pocket_depth_draw(kerf)

    cx = pocket_d + hole_d/2 + 0.8
    cy = y
    wall["cuts"].append(svg_circle(cx, cy, hole_d/2))

def _add_joint_based_fasteners(pieces: List[dict], params: dict) -> None:
    kerf = params["kerf"]

    fw = C.finger_feature_w_draw(kerf)
    m  = C.MIN_EDGE_MARGIN_MM

    # Two fasteners per corner (top/bottom), using same y's as finger features
    def y_positions(bh: float) -> List[float]:
        return _corner_centers(bh, fw, m)

    # Corner chain around the box:
    # right edge of A mates to left edge of B
    chain = [("wall_front", "wall_right"),
             ("wall_right", "wall_back"),
             ("wall_back", "wall_left"),
             ("wall_left", "wall_front")]

    for tab_wall_name, mate_wall_name in chain:
        tab_wall  = _find_piece(pieces, tab_wall_name)
        mate_wall = _find_piece(pieces, mate_wall_name)

        ys = y_positions(min(tab_wall["base_h"], mate_wall["base_h"]))
        for y in ys:
            _add_tslot_on_right_edge(tab_wall, kerf, y)
            _add_clearance_holes_on_left_edge(mate_wall, kerf, y)

    # Wall↔Floor: 2 per wall (8 total)
    # - Floor gets T-slots near its perimeter (nut trap lives on the "tab piece" conceptually here = floor)
    # - Walls get clearance holes in their BOTTOM tabs

    floor = _find_piece(pieces, "floor")
    fw_floor = floor["base_w"]
    fh_floor = floor["base_h"]

    # Floor T-slot placements: 2 near each side midpoint-ish, but kept near corners for symmetry
    # We'll place 2 per edge near corners (matching the bottom tab x locations of walls)
    # For floor: use same corner-centers along each edge
    xs_floor = _corner_centers(fw_floor, fw, m)
    ys_floor = _corner_centers(fh_floor, fw, m)

    # Add T-slots near the floor perimeter, stems pointing outward to the nearest edge
    # Top edge (stem opens upward): approximate by rotating is hard in this minimal SVG;
    # so we implement "right-opening" stems but place them near edges—still works visually & for nut insertion from side.
    # (If you want true directional stems per edge, we can do that next.)
    for x in xs_floor:
        # near top
        _add_floor_tslot(floor, kerf, x, m + fw/2)
        # near bottom
        _add_floor_tslot(floor, kerf, x, fh_floor - (m + fw/2))
    for y in ys_floor:
        # near left
        _add_floor_tslot(floor, kerf, m + fw/2, y)
        # near right
        _add_floor_tslot(floor, kerf, fw_floor - (m + fw/2), y)

    # Wall bottom-tab clearance holes (2 per wall)
    tab_d = C.finger_tab_depth_draw(kerf)
    hole_d = C.screw_hole_draw_d(kerf)
    for wall_name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        w = _find_piece(pieces, wall_name)
        bw, bh = w["base_w"], w["base_h"]
        xs = _corner_centers(bw, fw, m)
        cy = bh + tab_d/2  # center of bottom tab protrusion
        for x in xs:
            w["cuts"].append(svg_circle(x, cy, hole_d/2))

def _add_floor_tslot(floor: dict, kerf: float, x: float, y: float) -> None:
    """
    A compact T-slot for the floor at (x,y) center.
    For now: stem opens to +x (right). This keeps the SVG clean and non-overlapping.
    """
    nut_w = C.nut_pocket_draw_w(kerf)
    stem_w = C.screw_hole_draw_d(kerf)
    stem_len = C.T_SLOT_STEM_LENGTH_MM

    # Cross pocket
    floor["cuts"].append(svg_rect(x - nut_w/2, y - nut_w/2, nut_w, nut_w))
    # Stem to +x
    floor["cuts"].append(svg_rect(x + nut_w/2, y - stem_w/2, stem_len, stem_w))

# -------------------------
# Engraving (text + fractal)
# -------------------------
def _calculate_engraving_safe_bounds(piece_name: str, piece: dict, params: dict) -> tuple[float, float, float, float]:
    """
    Calculate safe engraving bounds, accounting for:
    - Edge margins
    - T-slot and clearance hole positions (which we avoid by expanding margins)
    - Extra buffer for rotated text to prevent overflow
    
    Returns (x_min, y_min, x_max, y_max) of the safe region.
    """
    bw, bh = piece["base_w"], piece["base_h"]
    kerf = params["kerf"]
    
    # Base margins from edges - more aggressive for safety
    margin = C.ENGRAVE_MARGIN_MM
    
    # Account for fastener positions
    # Finger features are at _corner_centers with feature width fw
    fw = C.finger_feature_w_draw(kerf)
    m = C.MIN_EDGE_MARGIN_MM
    
    # Calculate fastener y-positions (for vertical edges)
    ys_fastener = _corner_centers(bh, fw, m)
    
    # Fastener size (nut pocket is roughly fw x fw) with buffer for safety
    fastener_size = fw + 6.0  # Increased clearance buffer to prevent overflow
    
    # Start with base margins
    x_min = margin
    y_min = margin
    x_max = bw - margin
    y_max = bh - margin
    
    # For vertical walls (front/back/left/right), top and bottom have fasteners
    # Avoid tall vertical strip near top and bottom by reducing y range
    if piece_name in ("wall_front", "wall_back", "wall_left", "wall_right"):
        # Fasteners at top and bottom edges
        y_top_fastener = ys_fastener[0]
        y_bot_fastener = ys_fastener[1]
        
        # Expand these positions vertically by half fastener size + extra buffer for text
        y_top_max = y_top_fastener + fastener_size / 2 + 2.0  # Extra buffer
        y_bot_min = y_bot_fastener - fastener_size / 2 - 2.0  # Extra buffer
        
        # Safe region is between top and bottom fastener areas, with additional margin
        y_min = y_top_max + 6.0  # Increased margin
        y_max = y_bot_min - 6.0  # Increased margin
        
        # Also ensure we don't get too close to the edges for rotated text
        # Add extra horizontal margin for side walls to prevent overflow when rotated
        if piece_name in ("wall_left", "wall_right"):
            x_min = margin + 3.0  # Extra safety margin for rotated text
            x_max = bw - margin - 3.0
    
    return (x_min, y_min, x_max, y_max)


def _calculate_text_box_size(safe_width: float, safe_height: float) -> tuple[float, float]:
    """
    Calculate text box dimensions as a percentage of the safe zone.
    The text box is a fixed proportion of the wall that scales with wall size.
    
    Args:
        safe_width: Available width for engraving (mm)
        safe_height: Available height for engraving (mm)
    
    Returns:
        (box_width, box_height) in mm
    """
    # Text box uses 75% of safe width and 50% of safe height
    box_width = safe_width * 0.75
    box_height = safe_height * 0.50
    return (box_width, box_height)


def _calculate_auto_font_size(text_content: str, box_width: float, box_height: float, max_font_size: float = 10.0, min_font_size: float = 3.0) -> float:
    """
    Iteratively find the largest font size that fits text within the text box.
    
    Args:
        text_content: The text to render
        box_width: Text box width (mm)
        box_height: Text box height (mm)
        max_font_size: Starting/maximum font size (mm)
        min_font_size: Minimum acceptable font size (mm)
    
    Returns:
        Font size (mm) that fits the text in the box
    """
    if not text_content or len(text_content) == 0:
        return max_font_size
    
    # Character width estimate: each char is roughly (font_size * 0.55) wide in Arial
    # Height estimate: font_size * 1.2 (with ascenders/descenders)
    char_width_ratio = 0.55
    height_ratio = 1.2
    
    # Start with max font size and decrease until text fits
    font_size = max_font_size
    step = 0.5  # Decrease by 0.5mm each iteration
    
    while font_size >= min_font_size:
        # Calculate text dimensions at this font size
        text_width = len(text_content) * font_size * char_width_ratio
        text_height = font_size * height_ratio
        
        # Check if text fits in the box
        if text_width <= box_width and text_height <= box_height:
            return font_size
        
        # Decrease font size and try again
        font_size -= step
    
    # If we get here, use minimum font size
    return min_font_size


def _add_standard_engraving(pieces: List[dict], params: dict) -> None:
    wall_mode = params["wall_mode"]
    wall_text = params["wall_text"]

    for wall_key, piece_name in (
        ("front", "wall_front"),
        ("back",  "wall_back"),
        ("left",  "wall_left"),
        ("right", "wall_right"),
    ):
        mode = wall_mode[wall_key]
        if mode == "none":
            continue

        piece = _find_piece(pieces, piece_name)
        
        # Get safe engraving bounds that avoid fasteners
        x_min, y_min, x_max, y_max = _calculate_engraving_safe_bounds(piece_name, piece, params)
        safe_w = max(0.0, x_max - x_min)
        safe_h = max(0.0, y_max - y_min)
        
        if safe_w <= 0 or safe_h <= 0:
            continue  # No room to engrave
        
        if mode == "text":
            # Text oriented with bottom closest to floor
            # For front/back walls: text reads normally, bottom at y_max
            # For left/right walls: text reads from the floor up
            text_content = wall_text[wall_key]
            
            # Determine rotation based on wall
            rotation = 0
            if wall_key == "left":
                rotation = 90
            elif wall_key == "right":
                rotation = -90
            
            # For rotated text, swap width/height for text box calculation
            # Rotated text needs height to accommodate text width, and width to accommodate text height
            if rotation != 0:
                calc_w, calc_h = safe_h, safe_w  # Swap for rotated case
            else:
                calc_w, calc_h = safe_w, safe_h
            
            # Calculate text box size (scales with wall dimensions)
            box_width, box_height = _calculate_text_box_size(calc_w, calc_h)
            
            # Find font size that fits text within the text box
            font_size = _calculate_auto_font_size(text_content, box_width, box_height, max_font_size=10.0, min_font_size=3.0)
            
            # Position text in safe zone
            # SVG text with text-anchor="middle" and dominant-baseline="middle" is centered at (x,y)
            # For rotated text, we need to account for the text bounds when rotated
            if rotation == 0:
                # Front/back walls: normal horizontal centering, bottom-aligned
                cx = x_min + safe_w / 2
                cy = y_max - (font_size * 0.3)
            elif rotation == 90:
                # Left wall: rotated 90° clockwise
                # When rotated 90°, text width becomes vertical extent, height becomes horizontal
                # Position so text is centered in the safe zone area
                cx = x_min + (safe_w / 2)
                cy = y_min + (safe_h / 2)
            else:  # rotation == -90
                # Right wall: rotated -90° (counterclockwise)
                # Same logic as left wall
                cx = x_min + (safe_w / 2)
                cy = y_min + (safe_h / 2)
            
            piece["engraves"].append(svg_text(cx, cy, text_content, font_size=font_size, rotation=rotation))
            
        elif mode == "fractal":
            # Generate Sierpinski fractal in safe region
            depth = 4
            inset = C.T_MM
            keepouts: List[FractalRect] = []
            rect = FractalRect(x_min, y_min, safe_w, safe_h)
            paths = sierpinski_paths_clipped_by_keepouts(rect, depth=depth, inset=inset, keepouts=keepouts)
            for d in paths:
                piece["engraves"].append(svg_path(d, stroke="black"))

# -------------------------
# SVG primitives + export
# -------------------------
def svg_rect(x, y, w, h, stroke="red", stroke_width=0.1) -> dict:
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h, "stroke": stroke, "sw": stroke_width}

def svg_circle(cx, cy, r, stroke="red", stroke_width=0.1) -> dict:
    return {"type": "circle", "cx": cx, "cy": cy, "r": r, "stroke": stroke, "sw": stroke_width}

def svg_text(x, y, text: str, font_size: float = None, rotation: int = 0) -> dict:
    if font_size is None:
        font_size = C.TEXT_FONT_SIZE_MM
    return {
        "type": "text",
        "x": x,
        "y": y,
        "text": text,
        "font": C.TEXT_FONT_FAMILY,
        "size": font_size,
        "anchor": C.TEXT_ANCHOR,
        "rotation": rotation,
        "stroke": "black",
        "sw": 0.1,
    }

def svg_path(d: str, stroke: str = "red", stroke_width: float = 0.1) -> dict:
    return {"type": "path", "d": d, "stroke": stroke, "sw": stroke_width}

def _render_shape(shape: dict, dx: float, dy: float) -> str:
    t = shape["type"]
    if t == "rect":
        x = shape["x"] + dx
        y = shape["y"] + dy
        return (
            f"<rect x=\"{x:.4f}\" y=\"{y:.4f}\" width=\"{shape['w']:.4f}\" height=\"{shape['h']:.4f}\" "
            f"fill=\"none\" stroke=\"{shape['stroke']}\" stroke-width=\"{shape['sw']}\" />"
        )
    if t == "circle":
        cx = shape["cx"] + dx
        cy = shape["cy"] + dy
        return (
            f"<circle cx=\"{cx:.4f}\" cy=\"{cy:.4f}\" r=\"{shape['r']:.4f}\" "
            f"fill=\"none\" stroke=\"{shape['stroke']}\" stroke-width=\"{shape['sw']}\" />"
        )
    if t == "text":
        x = shape["x"] + dx
        y = shape["y"] + dy
        text = _escape_xml(shape["text"])
        rotation = shape.get("rotation", 0)
        if rotation != 0:
            return (
                f"<g transform=\"translate({x:.4f},{y:.4f}) rotate({rotation})\">"
                f"<text x=\"0\" y=\"0\" font-family=\"{shape['font']}\" font-size=\"{shape['size']:.4f}mm\" "
                f"text-anchor=\"{shape['anchor']}\" dominant-baseline=\"middle\" fill=\"none\" stroke=\"{shape['stroke']}\" stroke-width=\"{shape['sw']}\">{text}</text>"
                f"</g>"
            )
        else:
            return (
                f"<text x=\"{x:.4f}\" y=\"{y:.4f}\" font-family=\"{shape['font']}\" font-size=\"{shape['size']:.4f}mm\" "
                f"text-anchor=\"{shape['anchor']}\" dominant-baseline=\"middle\" fill=\"none\" stroke=\"{shape['stroke']}\" stroke-width=\"{shape['sw']}\">{text}</text>"
            )
    if t == "path":
        return (
            f"<g transform=\"translate({dx:.4f},{dy:.4f})\">"
            f"<path d=\"{shape['d']}\" fill=\"none\" stroke=\"{shape['stroke']}\" stroke-width=\"{shape['sw']}\" />"
            f"</g>"
        )
    raise ValueError(f"Unknown shape type: {t}")

def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )

def to_svg(pieces: List[dict], placements: List[dict], sheet_w: float, sheet_h: float) -> str:
    header = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{sheet_w:.4f}mm\" height=\"{sheet_h:.4f}mm\" viewBox=\"0 0 {sheet_w:.4f} {sheet_h:.4f}\">\n"
    )
    body = []
    body.append("<rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"white\" />")

    place_map = {pl["name"]: pl for pl in placements}

    for p in pieces:
        pl = place_map[p["name"]]
        dx, dy = pl["x"], pl["y"]

        body.append(_render_shape(p["outline"], dx, dy))
        for c in p["cuts"]:
            body.append(_render_shape(c, dx, dy))
        for e in p["engraves"]:
            body.append(_render_shape(e, dx, dy))

    footer = "\n</svg>\n"
    return header + "\n".join(body) + footer
