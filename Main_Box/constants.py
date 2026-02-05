"""
constants.py — Simple mode

Kerf conventions used throughout this project:
- Internal cutouts (slots/holes/pockets) end up LARGER by ~kerf.
  => draw_size = target_physical - kerf
- External protrusions (tabs) end up SMALLER by ~kerf.
  => draw_size = target_physical + kerf

Calibrated from your clearance tests (2026-02-04):
- Divider slot test: best labeled "2.80"  => DIVIDER_SLOT_CLEARANCE_MM = -0.10 (with kerf=0.10, T=3.0)
- Nut socket test: best labeled "-0.08"  => NUT_POCKET_CLEARANCE_MM  = -0.08
"""

INCH_TO_MM = 25.4

# Fixed material thickness
T_MM = 3.0

# Default kerf (can be exposed as an input later)
KERF_MM_DEFAULT = 0.10

# Sheet size (one sheet per box)
SHEET_W_MM = 12.0 * INCH_TO_MM
SHEET_H_MM = 18.0 * INCH_TO_MM

# Packing gap between parts on sheet
PART_GAP_MM = 2.0

# Safety margins
MIN_EDGE_MARGIN_MM = max(2 * T_MM, 6.0)

# Engraving safe margin inside each wall (keeps away from edges, tabs, pockets)
ENGRAVE_MARGIN_MM = max(2 * T_MM, 6.0)

# Divider rules
DIVIDER_MIN_GAP_MM = max(2 * T_MM, 6.0)

# --------------------------
# Fit tuning (PHYSICAL targets)
# --------------------------
# Divider slots: calibrated so the DRAWN width label "2.80" is correct with kerf=0.10 and T=3.0
DIVIDER_SLOT_CLEARANCE_MM = -0.10

# Nut pocket: calibrated best = -0.08mm
NUT_POCKET_CLEARANCE_MM = -0.08

# Screw hole diameter (clearance). Start at 2.50mm and tune if needed.
SCREW_HOLE_DIAMETER_MM = 2.50

# --------------------------
# Hardware (square nut) saved specs
# --------------------------
NUT_WIDTH_IN = 0.188
NUT_WIDTH_MM = NUT_WIDTH_IN * INCH_TO_MM

# --------------------------
# Kerf-aware sizing helpers
# --------------------------
def internal_cut_draw_dim(target_physical_mm: float, kerf_mm: float) -> float:
    """For holes/slots/pockets (internal voids)."""
    return target_physical_mm - kerf_mm

def external_cut_draw_dim(target_physical_mm: float, kerf_mm: float) -> float:
    """For external protrusions (tabs/tongues)."""
    return target_physical_mm + kerf_mm

def divider_slot_target_physical() -> float:
    """Desired physical slot width for a 3mm divider fit."""
    return T_MM + DIVIDER_SLOT_CLEARANCE_MM

def divider_slot_draw_w(kerf_mm: float) -> float:
    return internal_cut_draw_dim(divider_slot_target_physical(), kerf_mm)

def nut_pocket_target_physical() -> float:
    """Desired physical pocket width (square)."""
    return NUT_WIDTH_MM + NUT_POCKET_CLEARANCE_MM

def nut_pocket_draw_w(kerf_mm: float) -> float:
    return internal_cut_draw_dim(nut_pocket_target_physical(), kerf_mm)

def screw_hole_draw_d(kerf_mm: float) -> float:
    return internal_cut_draw_dim(SCREW_HOLE_DIAMETER_MM, kerf_mm)

# --------------------------
# Corner finger joints (box-style, minimal)
# --------------------------
# General tab/slot clearance for wall-to-wall joints (physical). Tune later if needed.
JOINT_CLEARANCE_MM = 0.10

# How far tabs protrude beyond a panel edge (physical). Usually thickness.
FINGER_DEPTH_MM = T_MM

# Width of each finger feature along an edge (physical).
FINGER_WIDTH_MM = 12.0

def finger_tab_depth_draw(kerf_mm: float) -> float:
    # External protrusion: add kerf so physical ends up ~FINGER_DEPTH_MM
    return external_cut_draw_dim(FINGER_DEPTH_MM, kerf_mm)

def finger_pocket_depth_draw(kerf_mm: float) -> float:
    # Internal indentation depth: subtract kerf so physical ends up ~FINGER_DEPTH_MM
    return internal_cut_draw_dim(FINGER_DEPTH_MM, kerf_mm)

def finger_feature_w_draw(kerf_mm: float) -> float:
    # Feature width is along the perimeter; keep as design intent.
    return FINGER_WIDTH_MM

# --------------------------
# Divider slot vertical geometry (standardized)
# --------------------------
DIVIDER_SLOT_TOP_CAP_MM = MIN_EDGE_MARGIN_MM
DIVIDER_SLOT_BOTTOM_MARGIN_MM = MIN_EDGE_MARGIN_MM

# --------------------------
# Engraving defaults
# --------------------------
TEXT_FONT_FAMILY = "Arial"
TEXT_FONT_SIZE_MM = 6.0
TEXT_ANCHOR = "middle"

# --------------------------
# T-slot captive nut placeholders
# --------------------------
# Stem length along which the screw shank can slide.
T_SLOT_STEM_LENGTH_MM = 10.0
