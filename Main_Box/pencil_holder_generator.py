#!/usr/bin/env python3
"""
Laser-cut pencil holder SVG generator.
Generates an SVG file for cutting a pencil holder from acrylic.
"""

import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

# === CONSTANTS (all in mm) ===
INCH_TO_MM = 25.4
MATERIAL_WIDTH = 18 * INCH_TO_MM   # 457.2
MATERIAL_HEIGHT = 12 * INCH_TO_MM  # 304.8
PIECE_GAP = 2

# Finger joints
TAB_WIDTH = 12
TAB_PROTRUSION = 3
POCKET_WIDTH = 11.7
POCKET_DEPTH = 2.7

# T-slots (nut slot: 1.5mm deep x 4.7mm along edge, inset from wall edge)
NUT_DEPTH = 1.5
NUT_WIDTH_ALONG_EDGE = 4.7
SHAFT_WIDTH = 2.2
HOLE_DIAMETER = 2.2
HOLE_OFFSET_FROM_EDGE = 1.5  # mm from edge (center of 3mm zone)
SHAFT_EXTENSION_PAST_NUT = 2.5  # shaft extends this far past the nut slot

# Bottom piece: extend length so pockets align with LEFT/RIGHT wall tabs
BOTTOM_EXTENSION_SIDE_MM = 3  # 3mm extra on left and right (6mm total)

# Divider slots
DIVIDER_SLOT_WIDTH = 2.7
DIVIDER_SLOT_OFFSET = 6  # slots are 6mm above bottom

# Engraving (0.1mm stroke for visibility; laser interprets as vector engrave)
ENGRAVING_STROKE = 0.1
TEXT_MARGIN = 10
FRACTAL_MARGIN = 5


def get_float(prompt, min_val=0.01):
    """Prompt for float input until valid."""
    while True:
        try:
            val = float(input(prompt))
            if val >= min_val:
                return val
            print("Input must be a positive number. Please try again.")
        except ValueError:
            print("Input must be a number (int or float). Please try again.")


def get_yn(prompt):
    """Prompt for y/n input until valid."""
    valid = {'y', 'Y', 'n', 'N'}
    while True:
        val = input(prompt).strip()
        if val in valid:
            return val.upper() == 'Y'
        print("Input must be one of: y, Y, n, N. Please try again.")


def get_dividers(prompt):
    """Prompt for divider count (0, 1, or 2)."""
    valid = {0, 1, 2}
    while True:
        try:
            val = int(input(prompt))
            if val in valid:
                return val
        except ValueError:
            pass
        print("Input must be 0, 1, or 2. Please try again.")


def get_inputs():
    """Collect all user inputs with validation. Returns dict with mm values."""
    length_in = get_float("Length (in): ")
    width_in = get_float("Width (in): ")
    height_in = get_float("Height (in): ")

    right_text = get_yn("Text on the RIGHT wall? (y/n): ")
    right_text_content = ""
    right_fractal = False
    if right_text:
        right_text_content = input("Right wall text content: ")
    else:
        right_fractal = get_yn("Fractal on RIGHT wall? (y/n): ")

    left_text = get_yn("Text on the LEFT wall? (y/n): ")
    left_text_content = ""
    left_fractal = False
    if left_text:
        left_text_content = input("Left wall text content: ")
    else:
        left_fractal = get_yn("Fractal on LEFT wall? (y/n): ")

    dividers = get_dividers("How many dividers? They will be equally spaced (0/1/2): ")

    return {
        'length': length_in * INCH_TO_MM,
        'width': width_in * INCH_TO_MM,
        'height': height_in * INCH_TO_MM,
        'right_text': right_text,
        'right_text_content': right_text_content,
        'right_fractal': right_fractal,
        'left_text': left_text,
        'left_text_content': left_text_content,
        'left_fractal': left_fractal,
        'dividers': dividers,
    }


def make_rect_path(x, y, w, h):
    """Create SVG path for rectangle."""
    return f"M{x},{y} h{w} v{h} h{-w} z"


def make_circle_path(cx, cy, r):
    """Create SVG path for circle."""
    return f"M{cx},{cy-r} A{r},{r} 0 0 1 {cx+r},{cy} A{r},{r} 0 0 1 {cx},{cy+r} A{r},{r} 0 0 1 {cx-r},{cy} A{r},{r} 0 0 1 {cx},{cy-r}"


def finger_pocket_positions(dim):
    """Return center positions for pockets/tabs at 25% and 75%."""
    return (0.25 * dim, 0.75 * dim)


def build_left_wall_outline(width, height):
    """Build LEFT wall outline with pockets on vertical edges, tabs on bottom."""
    p25, p75 = finger_pocket_positions(height)
    half_pocket = POCKET_WIDTH / 2

    # Trace outline: top-left, down left edge with pockets, bottom with tabs, up right edge with pockets
    path = f"M0,0 "
    path += f"L0,{p25 - half_pocket} "
    path += f"L{POCKET_DEPTH},{p25 - half_pocket} L{POCKET_DEPTH},{p25 + half_pocket} L0,{p25 + half_pocket} "
    path += f"L0,{p75 - half_pocket} "
    path += f"L{POCKET_DEPTH},{p75 - half_pocket} L{POCKET_DEPTH},{p75 + half_pocket} L0,{p75 + half_pocket} "
    path += f"L0,{height} "

    # Bottom edge with tabs
    w25, w75 = finger_pocket_positions(width)
    half_tab = TAB_WIDTH / 2
    path += f"L{w25 - half_tab},{height} "
    path += f"L{w25 - half_tab},{height + TAB_PROTRUSION} L{w25 + half_tab},{height + TAB_PROTRUSION} L{w25 + half_tab},{height} "
    path += f"L{w75 - half_tab},{height} "
    path += f"L{w75 - half_tab},{height + TAB_PROTRUSION} L{w75 + half_tab},{height + TAB_PROTRUSION} L{w75 + half_tab},{height} "
    path += f"L{width},{height} "

    # Right edge with pockets
    path += f"L{width},{p75 + half_pocket} "
    path += f"L{width - POCKET_DEPTH},{p75 + half_pocket} L{width - POCKET_DEPTH},{p75 - half_pocket} L{width},{p75 - half_pocket} "
    path += f"L{width},{p25 + half_pocket} "
    path += f"L{width - POCKET_DEPTH},{p25 + half_pocket} L{width - POCKET_DEPTH},{p25 - half_pocket} L{width},{p25 - half_pocket} "
    path += f"L{width},0 L0,0 z"
    return path


def build_right_wall_outline(width, height):
    """RIGHT wall same as LEFT."""
    return build_left_wall_outline(width, height)


def build_front_wall_outline(length, height):
    """Build FRONT wall with tabs on vertical edges and bottom."""
    p25, p75 = finger_pocket_positions(height)
    half_tab = TAB_WIDTH / 2

    path = f"M0,0 "
    # Left edge with tabs (tabs protrude left, so we start from -TAB_PROTRUSION)
    path += f"L0,{p25 - half_tab} "
    path += f"L{-TAB_PROTRUSION},{p25 - half_tab} L{-TAB_PROTRUSION},{p25 + half_tab} L0,{p25 + half_tab} "
    path += f"L0,{p75 - half_tab} "
    path += f"L{-TAB_PROTRUSION},{p75 - half_tab} L{-TAB_PROTRUSION},{p75 + half_tab} L0,{p75 + half_tab} "
    path += f"L0,{height} "

    # Bottom edge with tabs
    l25, l75 = finger_pocket_positions(length)
    path += f"L{l25 - half_tab},{height} "
    path += f"L{l25 - half_tab},{height + TAB_PROTRUSION} L{l25 + half_tab},{height + TAB_PROTRUSION} L{l25 + half_tab},{height} "
    path += f"L{l75 - half_tab},{height} "
    path += f"L{l75 - half_tab},{height + TAB_PROTRUSION} L{l75 + half_tab},{height + TAB_PROTRUSION} L{l75 + half_tab},{height} "
    path += f"L{length},{height} "

    # Right edge with tabs
    path += f"L{length},{p75 + half_tab} "
    path += f"L{length + TAB_PROTRUSION},{p75 + half_tab} L{length + TAB_PROTRUSION},{p75 - half_tab} L{length},{p75 - half_tab} "
    path += f"L{length},{p25 + half_tab} "
    path += f"L{length + TAB_PROTRUSION},{p25 + half_tab} L{length + TAB_PROTRUSION},{p25 - half_tab} L{length},{p25 - half_tab} "
    path += f"L{length},0 L0,0 z"
    return path


def build_back_wall_outline(length, height):
    """BACK wall same as FRONT."""
    return build_front_wall_outline(length, height)


def build_bottom_outline(length, width):
    """Build BOTTOM with 8 pockets on all 4 edges. Length is extended by 6mm (3mm each side)
    so left/right pockets align with LEFT and RIGHT wall tabs; pockets/holes keep same
    distance from edges."""
    shift = BOTTOM_EXTENSION_SIDE_MM
    extended_length = length + 2 * shift
    # Pocket centers along length: same spacing as inner span, shifted right by shift
    l25 = shift + length * 0.25
    l75 = shift + length * 0.75
    w25, w75 = finger_pocket_positions(width)
    half_pocket = POCKET_WIDTH / 2

    # Trace clockwise from top-left. Left edge at 0, right at extended_length.
    path = f"M0,0 "
    # Top: 3mm strip then pockets at l25, l75
    path += f"L{shift},0 "
    path += f"L{l25 - half_pocket},0 "
    path += f"L{l25 - half_pocket},{POCKET_DEPTH} L{l25 + half_pocket},{POCKET_DEPTH} L{l25 + half_pocket},0 "
    path += f"L{l75 - half_pocket},0 "
    path += f"L{l75 - half_pocket},{POCKET_DEPTH} L{l75 + half_pocket},{POCKET_DEPTH} L{l75 + half_pocket},0 "
    path += f"L{extended_length},0 "

    # Right edge: pockets indent leftward
    path += f"L{extended_length},{w25 - half_pocket} "
    path += f"L{extended_length - POCKET_DEPTH},{w25 - half_pocket} L{extended_length - POCKET_DEPTH},{w25 + half_pocket} L{extended_length},{w25 + half_pocket} "
    path += f"L{extended_length},{w75 - half_pocket} "
    path += f"L{extended_length - POCKET_DEPTH},{w75 - half_pocket} L{extended_length - POCKET_DEPTH},{w75 + half_pocket} L{extended_length},{w75 + half_pocket} "
    path += f"L{extended_length},{width} "

    # Bottom edge: pockets indent upward
    path += f"L{l75 + half_pocket},{width} "
    path += f"L{l75 + half_pocket},{width - POCKET_DEPTH} L{l75 - half_pocket},{width - POCKET_DEPTH} L{l75 - half_pocket},{width} "
    path += f"L{l25 + half_pocket},{width} "
    path += f"L{l25 + half_pocket},{width - POCKET_DEPTH} L{l25 - half_pocket},{width - POCKET_DEPTH} L{l25 - half_pocket},{width} "
    path += f"L{shift},{width} "
    path += f"L0,{width} "

    # Left edge: pockets indent rightward (same distance from edge 0)
    path += f"L0,{w75 + half_pocket} "
    path += f"L{POCKET_DEPTH},{w75 + half_pocket} L{POCKET_DEPTH},{w75 - half_pocket} L0,{w75 - half_pocket} "
    path += f"L0,{w25 + half_pocket} "
    path += f"L{POCKET_DEPTH},{w25 + half_pocket} L{POCKET_DEPTH},{w25 - half_pocket} L0,{w25 - half_pocket} "
    path += "z"
    return path


def build_divider_outline(width, div_height):
    """Simple rectangle for divider."""
    return make_rect_path(0, 0, width, div_height)


def add_tslot_nut_shaft(svg_group, cx, cy, edge_direction):
    """
    Add T-slot: nut pocket (1.5mm x 4.7mm, inset from edge) and shaft (extends to edge,
    then 2-3mm past the nut so screw can pass through).
    Nut does not touch the wall edge - shaft connects them.
    """
    nut_to_edge = NUT_DEPTH + SHAFT_EXTENSION_PAST_NUT
    shaft_len = nut_to_edge + SHAFT_EXTENSION_PAST_NUT
    half_nut_w = NUT_WIDTH_ALONG_EDGE / 2
    half_shaft = SHAFT_WIDTH / 2

    if edge_direction == 'bottom':
        shaft_rect = (cx - half_shaft, cy - shaft_len, SHAFT_WIDTH, shaft_len)
        nut_rect = (cx - half_nut_w, cy - nut_to_edge, NUT_WIDTH_ALONG_EDGE, NUT_DEPTH)
    elif edge_direction == 'top':
        shaft_rect = (cx - half_shaft, cy, SHAFT_WIDTH, shaft_len)
        nut_rect = (cx - half_nut_w, cy + nut_to_edge - NUT_DEPTH, NUT_WIDTH_ALONG_EDGE, NUT_DEPTH)
    elif edge_direction == 'right':
        shaft_rect = (cx - shaft_len, cy - half_shaft, shaft_len, SHAFT_WIDTH)
        nut_rect = (cx - nut_to_edge, cy - half_nut_w, NUT_DEPTH, NUT_WIDTH_ALONG_EDGE)
    elif edge_direction == 'left':
        shaft_rect = (cx, cy - half_shaft, shaft_len, SHAFT_WIDTH)
        nut_rect = (cx + nut_to_edge - NUT_DEPTH, cy - half_nut_w, NUT_DEPTH, NUT_WIDTH_ALONG_EDGE)
    else:
        return

    for rect in (shaft_rect, nut_rect):
        x, y, w, h = rect
        p = make_rect_path(x, y, w, h)
        ET.SubElement(svg_group, 'path', {'d': p, 'fill': 'none', 'stroke': '#000', 'stroke-width': '0.1'})


def add_tslot_hole(svg_group, cx, cy):
    """Add circular hole for screw shaft (absolute coords in SVG)."""
    r = HOLE_DIAMETER / 2
    path = make_circle_path(cx, cy, r)
    ET.SubElement(svg_group, 'path', {'d': path, 'fill': 'none', 'stroke': '#000', 'stroke-width': '0.1'})


def add_divider_slot(svg_group, start_x, start_y, slot_w, slot_h):
    """Add divider slot (absolute coords). Slots run from top down to 6mm above bottom."""
    path = make_rect_path(start_x, start_y, slot_w, slot_h)
    ET.SubElement(svg_group, 'path', {'d': path, 'fill': 'none', 'stroke': '#000', 'stroke-width': '0.1'})


def get_sierpinski_path(depth, size):
    """Generate Sierpinski triangle as SVG path. Equilateral triangle, recursively subdivided."""
    h = size * math.sqrt(3) / 2
    cx = size / 2
    cy = h / 2

    def triangle(x, y, s, d):
        if d <= 0:
            h = s * math.sqrt(3) / 2
            return f"M{x},{y + h/2} L{x - s/2},{y - h/2} L{x + s/2},{y - h/2} z"
        else:
            h = s * math.sqrt(3) / 2
            paths = []
            # Top
            paths.append(triangle(x, y - h/4, s/2, d - 1))
            # Bottom left
            paths.append(triangle(x - s/4, y + h/4, s/2, d - 1))
            # Bottom right
            paths.append(triangle(x + s/4, y + h/4, s/2, d - 1))
            return " ".join(paths)

    return triangle(cx, cy, size, depth)


def estimate_text_size(text, max_width):
    """Return largest font size (mm) so text fits within max_width. ~0.55 font-size per char for Times New Roman."""
    if not text:
        return 10
    max_font = (max_width / (len(text) * 0.55)) * 0.95
    return max(4, min(28, int(max_font)))


def build_all_components(params):
    """Build all piece geometries. Returns list of (piece_id, path, bounds, ptype, params)."""
    length = params['length']
    width = params['width']
    height = params['height']
    div_count = params['dividers']

    pieces = []
    pieces.append(('left', build_left_wall_outline(width, height), (0, 0, width, height + TAB_PROTRUSION), 'left', params))
    pieces.append(('right', build_right_wall_outline(width, height), (0, 0, width, height + TAB_PROTRUSION), 'right', params))
    pieces.append(('front', build_front_wall_outline(length, height), (-TAB_PROTRUSION, 0, length + TAB_PROTRUSION, height + TAB_PROTRUSION), 'front', params))
    pieces.append(('back', build_back_wall_outline(length, height), (-TAB_PROTRUSION, 0, length + TAB_PROTRUSION, height + TAB_PROTRUSION), 'back', params))
    bottom_length = length + 2 * BOTTOM_EXTENSION_SIDE_MM
    pieces.append(('bottom', build_bottom_outline(length, width), (0, 0, bottom_length, width), 'bottom', params))

    div_height = height - DIVIDER_SLOT_OFFSET
    for i in range(div_count):
        pieces.append((f'div{i+1}', build_divider_outline(width, div_height), (0, 0, width, div_height), f'div{i+1}', params))

    return pieces


def shelf_pack(pieces):
    """
    Pack pieces using shelf packing. Each piece is (id, path, bounds, ptype, params).
    bounds: (minx, miny, maxx, maxy). Place so piece origin (0,0) maps to correct position.
    Returns: list of (id, path, px, py, type, params) and total bounds (w, h).
    """
    packed = []
    shelf_y = 0
    shelf_x = 0
    shelf_max_h = 0
    total_width = 0
    total_height = 0

    for p in pieces:
        pid, path, bounds, ptype, params = p
        minx, miny, maxx, maxy = bounds
        w = maxx - minx
        h = maxy - miny
        pw = w + PIECE_GAP
        ph = h + PIECE_GAP

        if shelf_x + pw > MATERIAL_WIDTH and shelf_x > 0:
            shelf_y += shelf_max_h + PIECE_GAP
            shelf_x = 0
            shelf_max_h = 0

        place_x = shelf_x - minx
        place_y = shelf_y - miny

        packed.append((pid, path, place_x, place_y, ptype, params))

        shelf_x += pw
        shelf_max_h = max(shelf_max_h, ph)
        total_width = max(total_width, shelf_x)
        total_height = max(total_height, shelf_y + shelf_max_h)

    return packed, (total_width, total_height)


def generate_svg(packed_pieces, total_bounds):
    """Generate full SVG with layers in correct order."""
    width_svg = max(total_bounds[0], 100)
    height_svg = max(total_bounds[1], 100)

    svg = ET.Element('svg', {
        'xmlns': 'http://www.w3.org/2000/svg',
        'width': f'{width_svg}mm',
        'height': f'{height_svg}mm',
        'viewBox': f'0 0 {width_svg} {height_svg}',
        'unit': 'mm'
    })

    # Layers (drawn in order; engravings last so they render on top for visibility)
    g_tslot = ET.SubElement(svg, 'g', {'id': 'tslots'})
    g_divslot = ET.SubElement(svg, 'g', {'id': 'divider_slots'})
    g_outline = ET.SubElement(svg, 'g', {'id': 'outlines'})
    g_engrave = ET.SubElement(svg, 'g', {'id': 'engravings'})

    for pid, path, px, py, ptype, params in packed_pieces:
        transform = f'translate({px},{py})'

        length = params['length']
        width = params['width']
        height = params['height']
        div_count = params['dividers']

        # Wall outline (always)
        g_piece = ET.SubElement(g_outline, 'g', {'id': pid, 'transform': transform})
        ET.SubElement(g_piece, 'path', {'d': path, 'fill': 'none', 'stroke': '#000', 'stroke-width': '0.1'})

        # T-slots, divider slots, engravings per piece type
        if ptype == 'left':
            # Holes centered in first 3mm of left/right edges
            add_tslot_hole(g_tslot, px + HOLE_OFFSET_FROM_EDGE, py + height / 2)
            add_tslot_hole(g_tslot, px + width - HOLE_OFFSET_FROM_EDGE, py + height / 2)
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), width / 2, height, 'bottom')
            if params['left_text'] and params['left_text_content']:
                fs = estimate_text_size(params['left_text_content'], width - TEXT_MARGIN)
                txt = ET.SubElement(g_engrave, 'text', {
                    'x': str(px + width / 2), 'y': str(py + height / 2),
                    'text-anchor': 'middle', 'dominant-baseline': 'middle',
                    'font-family': 'Times New Roman, Arial, serif', 'font-size': str(fs),
                    'fill': 'none', 'stroke': '#000', 'stroke-width': str(ENGRAVING_STROKE)
                })
                txt.text = params['left_text_content']
            elif params['left_fractal']:
                sz = min(width, height) - 2 * FRACTAL_MARGIN
                h_tri = sz * math.sqrt(3) / 2
                tx = (width - sz) / 2
                ty = (height - h_tri) / 2
                spath = get_sierpinski_path(5, sz)
                g_f = ET.SubElement(g_engrave, 'g', {'transform': f'{transform} translate({tx},{ty})'})
                ET.SubElement(g_f, 'path', {'d': spath, 'fill': 'none', 'stroke': '#000', 'stroke-width': str(ENGRAVING_STROKE)})

        elif ptype == 'right':
            add_tslot_hole(g_tslot, px + HOLE_OFFSET_FROM_EDGE, py + height / 2)
            add_tslot_hole(g_tslot, px + width - HOLE_OFFSET_FROM_EDGE, py + height / 2)
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), width / 2, height, 'bottom')
            if params['right_text'] and params['right_text_content']:
                fs = estimate_text_size(params['right_text_content'], width - TEXT_MARGIN)
                txt = ET.SubElement(g_engrave, 'text', {
                    'x': str(px + width / 2), 'y': str(py + height / 2),
                    'text-anchor': 'middle', 'dominant-baseline': 'middle',
                    'font-family': 'Times New Roman, Arial, serif', 'font-size': str(fs),
                    'fill': 'none', 'stroke': '#000', 'stroke-width': str(ENGRAVING_STROKE)
                })
                txt.text = params['right_text_content']
            elif params['right_fractal']:
                sz = min(width, height) - 2 * FRACTAL_MARGIN
                h_tri = sz * math.sqrt(3) / 2
                tx = (width - sz) / 2
                ty = (height - h_tri) / 2
                spath = get_sierpinski_path(5, sz)
                g_f = ET.SubElement(g_engrave, 'g', {'transform': f'{transform} translate({tx},{ty})'})
                ET.SubElement(g_f, 'path', {'d': spath, 'fill': 'none', 'stroke': '#000', 'stroke-width': str(ENGRAVING_STROKE)})

        elif ptype == 'front':
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), 0, height / 2, 'left')
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), length, height / 2, 'right')
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), length / 2, height, 'bottom')
            slot_h = height - DIVIDER_SLOT_OFFSET
            if div_count == 1:
                x1 = length / 3 - DIVIDER_SLOT_WIDTH / 2
                add_divider_slot(g_divslot, px + x1, py, DIVIDER_SLOT_WIDTH, slot_h)
            elif div_count == 2:
                x1 = length / 3 - DIVIDER_SLOT_WIDTH / 2
                x2 = 2 * length / 3 - DIVIDER_SLOT_WIDTH / 2
                add_divider_slot(g_divslot, px + x1, py, DIVIDER_SLOT_WIDTH, slot_h)
                add_divider_slot(g_divslot, px + x2, py, DIVIDER_SLOT_WIDTH, slot_h)

        elif ptype == 'back':
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), 0, height / 2, 'left')
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), length, height / 2, 'right')
            add_tslot_nut_shaft(ET.SubElement(g_tslot, 'g', {'transform': transform}), length / 2, height, 'bottom')
            slot_h = height - DIVIDER_SLOT_OFFSET
            if div_count == 1:
                x1 = length / 3 - DIVIDER_SLOT_WIDTH / 2
                add_divider_slot(g_divslot, px + x1, py, DIVIDER_SLOT_WIDTH, slot_h)
            elif div_count == 2:
                x1 = length / 3 - DIVIDER_SLOT_WIDTH / 2
                x2 = 2 * length / 3 - DIVIDER_SLOT_WIDTH / 2
                add_divider_slot(g_divslot, px + x1, py, DIVIDER_SLOT_WIDTH, slot_h)
                add_divider_slot(g_divslot, px + x2, py, DIVIDER_SLOT_WIDTH, slot_h)

        elif ptype == 'bottom':
            # Bottom length is extended by 6mm (3mm each side); holes keep same distance from edges
            bottom_length = length + 2 * BOTTOM_EXTENSION_SIDE_MM
            half_l = bottom_length / 2  # center of extended piece
            half_w = width / 2
            add_tslot_hole(g_tslot, px + half_l, py + HOLE_OFFSET_FROM_EDGE)
            add_tslot_hole(g_tslot, px + half_l, py + width - HOLE_OFFSET_FROM_EDGE)
            add_tslot_hole(g_tslot, px + HOLE_OFFSET_FROM_EDGE, py + half_w)
            add_tslot_hole(g_tslot, px + bottom_length - HOLE_OFFSET_FROM_EDGE, py + half_w)

    return svg


def prettify(elem):
    """Return a pretty-printed XML string."""
    rough = ET.tostring(elem, encoding='unicode')
    return minidom.parseString(rough).toprettyxml(indent="  ")


def main():
    while True:
        params = get_inputs()
        pieces = build_all_components(params)
        packed, (tw, th) = shelf_pack(pieces)

        if tw > MATERIAL_WIDTH or th > MATERIAL_HEIGHT:
            print(f"\nThe pieces do not fit on an 18\" x 12\" sheet. Required area: {tw:.1f}mm x {th:.1f}mm")
            print("Please enter smaller dimensions.\n")
            continue

        svg = generate_svg(packed, (tw, th))
        with open('pencil_holder.svg', 'w') as f:
            f.write(prettify(svg))
        print("\nSaved pencil_holder.svg")
        break


if __name__ == '__main__':
    main()
