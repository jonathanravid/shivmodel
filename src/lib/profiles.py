"""Truncated-airfoil (kammtail) and aero blade profiles for the Shiv TT."""

from __future__ import annotations

import math


def kammtail_points(
    chord: float,
    thickness: float,
    truncate: float = 0.78,
    n: int = 24,
) -> list[tuple[float, float]]:
    """Closed XY points for a truncated airfoil.

    Local frame: leading edge near x=0, trailing blunt face near x=chord*truncate,
    +Y lateral. Points are CCW for loft face normals.
    """
    c = max(chord, 1.0)
    half_t = thickness * 0.5
    # Parametric ellipse-like nose + parallel mid + blunt TE (stable, non-self-intersecting).
    pts: list[tuple[float, float]] = []
    nose_len = 0.28 * c * truncate
    te_x = truncate * c
    # Upper: nose arc -> mid -> TE corner
    for i in range(n // 3 + 1):
        a = math.pi * (1.0 - i / (n // 3))  # pi .. 0 half? use 0.5pi to 0
        a = math.pi / 2 * (1.0 - i / (n // 3))
        x = nose_len * (1.0 - math.sin(a))
        y = half_t * math.cos(a) if i < n // 3 else half_t
        # smoother: x = nose_len*(1-cos) style
        x = nose_len * (1.0 - math.cos(math.pi / 2 * i / (n // 3)))
        y = half_t * math.sin(math.pi / 2 * i / (n // 3)) if i > 0 else 0.0
        if i == 0:
            pts.append((0.0, 0.0))
        else:
            pts.append((x, y))
    # Force LE single point then upper from mid-nose
    pts = [(0.0, 0.0)]
    for i in range(1, n // 3 + 1):
        ang = math.pi / 2 * i / (n // 3)
        pts.append((nose_len * (1.0 - math.cos(ang)), half_t * math.sin(ang)))
    # Upper mid to TE
    for i in range(1, n // 3 + 1):
        t = i / (n // 3)
        x = nose_len + t * (te_x - nose_len)
        # slight taper toward TE
        y = half_t * (1.0 - 0.12 * t)
        pts.append((x, y))
    # Blunt TE face
    te_y = half_t * 0.88
    pts.append((te_x + 0.03 * c, te_y))
    pts.append((te_x + 0.03 * c, -te_y))
    # Lower TE to mid to nose (mirror)
    for i in range(n // 3, 0, -1):
        t = i / (n // 3)
        x = nose_len + t * (te_x - nose_len)
        y = half_t * (1.0 - 0.12 * t)
        pts.append((x, -y))
    for i in range(n // 3, 0, -1):
        ang = math.pi / 2 * i / (n // 3)
        pts.append((nose_len * (1.0 - math.cos(ang)), -half_t * math.sin(ang)))
    # Close
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    # Ensure CCW
    a = 0.0
    for i in range(len(pts) - 1):
        a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
    if a < 0:
        pts = list(reversed(pts))
    return pts


def flat_aero_points(
    depth: float,
    width: float,
    n: int = 20,
) -> list[tuple[float, float]]:
    """Shallower aero section for top tube / seat stays."""
    return kammtail_points(depth, width, truncate=0.82, n=n)


def blade_points(
    depth: float,
    width: float,
    n: int = 20,
) -> list[tuple[float, float]]:
    """Deep thin aero blade for fork legs and seat tube."""
    return kammtail_points(depth, width, truncate=0.80, n=n)
