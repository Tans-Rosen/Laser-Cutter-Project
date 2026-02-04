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
# Tabs + wall bottom slots (placeholder tuning)
# --------------------------
# These parameters control the tabbed floor + matching slots on the bottom of each wall.
# You can dial in TAB_SLOT_CLEARANCE_MM later using a small test strip.

# Physical clearance added to the tab thickness when computing the SLOT width.
# (Tabs are material thickness; slots are cutouts.)
TAB_SLOT_CLEARANCE_MM = 0.10

# Design intent: how wide each tab is along the edge.
TAB_WIDTH_MM = 12.0

# How many tabs per edge.
# Long edges correspond to L_in/L_out direction (front/back), short edges correspond to W_in/W_out (left/right).
TAB_COUNT_LONG_EDGE = 3
TAB_COUNT_SHORT_EDGE = 2

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
# Tab / slot helpers (kerf-aware)
# --------------------------
def tab_slot_target_physical() -> float:
    """Desired physical slot width for a floor tab (slot is an internal cutout)."""
    return T_MM + TAB_SLOT_CLEARANCE_MM

def tab_slot_draw_w(kerf_mm: float) -> float:
    """Drawn slot width (kerf-aware) for the wall bottom slots."""
    return internal_cut_draw_dim(tab_slot_target_physical(), kerf_mm)

def wall_bottom_slot_draw_depth(kerf_mm: float) -> float:
    """Drawn slot depth upward from the wall bottom edge."""
    return internal_cut_draw_dim(T_MM, kerf_mm)

def floor_tab_len_draw(kerf_mm: float) -> float:
    """Drawn tab length protruding from the floor base outline."""
    return external_cut_draw_dim(T_MM, kerf_mm)

# Divider slot vertical geometry (standardized)
DIVIDER_SLOT_TOP_CAP_MM = MIN_EDGE_MARGIN_MM
DIVIDER_SLOT_BOTTOM_MARGIN_MM = MIN_EDGE_MARGIN_MM

# Engraving defaults
TEXT_FONT_FAMILY = "Arial"
TEXT_FONT_SIZE_MM = 6.0
TEXT_ANCHOR = "middle"

# --------------------------
# Fractal engraving (Sierpinski)
# --------------------------
# Recursion depth: 4–6 is usually good for 3mm acrylic + typical laser spot sizes.
FRACTAL_SIERPINSKI_DEPTH = 5

# Extra inset INSIDE the engraving-safe region (in addition to ENGRAVE_MARGIN_MM)
# so the pattern doesn’t touch the “safe box” edges.
FRACTAL_INSET_MM = 2.0

# Avoid engraving too close to cutouts (slots/pockets/holes). This is extra padding.
FRACTAL_KEEPOUT_PAD_MM = 1.0

# Stroke width for vector engraving lines
FRACTAL_STROKE_WIDTH_MM = 0.12
