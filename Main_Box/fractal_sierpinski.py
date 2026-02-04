# fractal_sierpinski.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import math

Point = Tuple[float, float]


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def inset(self, m: float) -> "Rect":
        w2 = max(0.0, self.w - 2 * m)
        h2 = max(0.0, self.h - 2 * m)
        return Rect(self.x + m, self.y + m, w2, h2)


def rects_intersect(a: Rect, b: Rect) -> bool:
    return not (
        a.x + a.w <= b.x or
        b.x + b.w <= a.x or
        a.y + a.h <= b.y or
        b.y + b.h <= a.y
    )


def _mid(p: Point, q: Point) -> Point:
    return ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)


def _triangle_bbox(a: Point, b: Point, c: Point) -> Rect:
    xs = (a[0], b[0], c[0])
    ys = (a[1], b[1], c[1])
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return Rect(x0, y0, x1 - x0, y1 - y0)


def _triangle_to_path(a: Point, b: Point, c: Point) -> str:
    return f"M {a[0]:.4f},{a[1]:.4f} L {b[0]:.4f},{b[1]:.4f} L {c[0]:.4f},{c[1]:.4f} Z"


def _equilateral_triangle_in_rect(rect: Rect) -> Tuple[Point, Point, Point]:
    """
    Fit an equilateral triangle inside rect, centered.
    Returns (A,B,C) with A=top, B=bottom-left, C=bottom-right.
    """
    if rect.w <= 0 or rect.h <= 0:
        p = (rect.x, rect.y)
        return p, p, p

    side_by_width = rect.w
    side_by_height = rect.h * 2.0 / math.sqrt(3.0)
    side = min(side_by_width, side_by_height)
    tri_h = side * math.sqrt(3.0) / 2.0

    cx = rect.x + rect.w / 2.0
    cy = rect.y + rect.h / 2.0

    left = cx - side / 2.0
    right = cx + side / 2.0
    top = cy - tri_h / 2.0
    bottom = cy + tri_h / 2.0

    A = (cx, top)
    B = (left, bottom)
    C = (right, bottom)
    return A, B, C


def sierpinski_leaf_triangles(rect: Rect, depth: int, inset: float) -> List[Tuple[Point, Point, Point]]:
    """
    Returns leaf triangles for a Sierpinski triangle fitted to `rect` (after an additional `inset`).
    """
    r = rect.inset(inset)
    A, B, C = _equilateral_triangle_in_rect(r)

    tris: List[Tuple[Point, Point, Point]] = []

    def rec(a: Point, b: Point, c: Point, d: int) -> None:
        if d <= 0:
            tris.append((a, b, c))
            return
        ab = _mid(a, b)
        ac = _mid(a, c)
        bc = _mid(b, c)
        rec(a, ab, ac, d - 1)
        rec(ab, b, bc, d - 1)
        rec(ac, bc, c, d - 1)

    rec(A, B, C, depth)
    return tris


def sierpinski_paths_clipped_by_keepouts(
    rect: Rect,
    depth: int,
    inset: float,
    keepouts: List[Rect],
) -> List[str]:
    """
    Generate Sierpinski leaf triangles and DROP any triangle whose bbox intersects a keepout.
    keepouts should already include any desired padding (expanded areas).
    """
    leaf = sierpinski_leaf_triangles(rect, depth=depth, inset=inset)

    out: List[str] = []
    for (a, b, c) in leaf:
        bb = _triangle_bbox(a, b, c)
        if any(rects_intersect(bb, k) for k in keepouts):
            continue
        out.append(_triangle_to_path(a, b, c))

    return out
