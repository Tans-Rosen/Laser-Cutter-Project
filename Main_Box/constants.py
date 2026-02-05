"""
constants.py — Simple mode

Key idea:
- Internal cutouts (slots, holes, pockets) end up LARGER by ~kerf.
  => draw_size = target_physical - kerf
- External parts (tabs, outer sizes) end up SMALLER by ~kerf.
  => draw_size = target_physical + kerf

You will calibrate:
- KERF_MM (if you want)
- NUT_POCKET_CLEARANCE_MM (to prevent jiggle)
- DIVIDER_SLOT_CLEARANCE_MM (for smooth slip fit)
- SCREW_HOLE_DIAMETER_MM (clearance for 2-56 screw)
"""

INCH_TO_MM = 25.4

# Fixed material
T_MM = 3.0

# Default kerf (you will calibrate)
KERF_MM_DEFAULT = 0.10

# Sheet size (one sheet per box)
SHEET_W_MM = 12.0 * INCH_TO_MM
SHEET_H_MM = 18.0 * INCH_TO_MM

# Packing gap between parts on sheet
PART_GAP_MM = 2.0

# Safety margins
MIN_EDGE_MARGIN_MM = max(2 * T_MM, 6.0)

# Engraving safe margin inside each wall
ENGRAVE_MARGIN_MM = max(2 * T_MM, 6.0)

# Divider rules
DIVIDER_MIN_GAP_MM = max(2 * T_MM, 6.0)

# --------------------------
# Fit tuning (PHYSICAL targets)
# --------------------------
# Divider slots: slip fit for 3mm divider. Start at +0.08mm and tune from test strip.
DIVIDER_SLOT_CLEARANCE_MM = 0.08

# Nut pocket: should NOT spin; should have minimal wiggle.
# Start at +0.05mm and tune from test strip.
NUT_POCKET_CLEARANCE_MM = 0.05

# Screw hole diameter (clearance). Start at 2.50mm and tune if needed.
SCREW_HOLE_DIAMETER_MM = 2.50

# --------------------------
# Hardware (square nut) saved specs
# --------------------------
NUT_WIDTH_IN = 0.188
NUT_WIDTH_MM = NUT_WIDTH_IN * INCH_TO_MM

# --------------------------
# Helper conversions for kerf-aware drawing
# --------------------------
def internal_cut_draw_dim(target_physical_mm: float, kerf_mm: float) -> float:
    """For holes/slots/pockets (internal voids)."""
    return target_physical_mm - kerf_mm

def external_cut_draw_dim(target_physical_mm: float, kerf_mm: float) -> float:
    """For external features (tabs, tongues) if you add them later."""
    return target_physical_mm + kerf_mm

def divider_slot_target_physical(kerf_mm: float) -> float:
    """Desired physical slot width for a 3mm divider slip fit."""
    return T_MM + DIVIDER_SLOT_CLEARANCE_MM

def divider_slot_draw_w(kerf_mm: float) -> float:
    return internal_cut_draw_dim(divider_slot_target_physical(kerf_mm), kerf_mm)

def nut_pocket_target_physical() -> float:
    """Desired physical pocket width (square)."""
    return NUT_WIDTH_MM + NUT_POCKET_CLEARANCE_MM

def nut_pocket_draw_w(kerf_mm: float) -> float:
    return internal_cut_draw_dim(nut_pocket_target_physical(), kerf_mm)

def screw_hole_draw_d(kerf_mm: float) -> float:
    return internal_cut_draw_dim(SCREW_HOLE_DIAMETER_MM, kerf_mm)

# --------------------------
# Corner finger-joint placeholders (box-style)
# --------------------------
# These control the small “foam-mat style” corner joints between adjacent faces.
# Tune JOINT_CLEARANCE_MM later using test strips.
JOINT_CLEARANCE_MM = 0.10  # general tab/slot clearance (physical)

# How far male tabs protrude beyond the nominal panel outline (physical). Usually = thickness.
FINGER_DEPTH_MM = T_MM

# Width of each finger feature along an edge (physical).
FINGER_WIDTH_MM = 12.0

def finger_depth_draw(kerf_mm: float) -> float:
    # External protrusion: add kerf so physical ends up right.
    return external_cut_draw_dim(FINGER_DEPTH_MM, kerf_mm)

def finger_slot_depth_draw(kerf_mm: float) -> float:
    # Internal indentation depth: subtract kerf so physical ends up right.
    return internal_cut_draw_dim(FINGER_DEPTH_MM, kerf_mm)

def finger_slot_width_draw(kerf_mm: float) -> float:
    # Internal slot width: thickness + clearance, then kerf-aware.
    return internal_cut_draw_dim(T_MM + JOINT_CLEARANCE_MM, kerf_mm)

def finger_width_draw(kerf_mm: float) -> float:
    # Feature width is along the perimeter; keep as design intent.
    return FINGER_WIDTH_MM

# --------------------------
# T-slot captive nut placeholders
# --------------------------
# T-slot stem: screw shank can slide in; cross captures square nut (anti-rotation).
T_SLOT_STEM_LENGTH_MM = 10.0

# Divider slot vertical geometry (standardized)
DIVIDER_SLOT_TOP_CAP_MM = MIN_EDGE_MARGIN_MM
DIVIDER_SLOT_BOTTOM_MARGIN_MM = MIN_EDGE_MARGIN_MM

# Engraving defaults
TEXT_FONT_FAMILY = "Arial"
TEXT_FONT_SIZE_MM = 6.0
TEXT_ANCHOR = "middle"
