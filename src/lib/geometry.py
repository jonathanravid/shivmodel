"""Official 2017 Specialized S-Works Shiv TT Size Small geometry hardpoints.

Coordinate frame: BB center at origin, +X forward, +Y left, +Z up.
Wheel axles sit at z = BB_DROP so BB drop matches catalog (72 mm).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# --- Official Size Small numbers (mm / degrees) ---
STACK = 502.0
REACH = 390.0
SEAT_TUBE_ANGLE = 74.5
HEAD_TUBE_ANGLE = 72.0
HEAD_TUBE_LENGTH = 100.0
SEAT_TUBE_LENGTH = 565.0  # center BB to top of seat tube / clamp area
HORIZONTAL_TOP_TUBE = 529.0
CHAIN_STAY_LENGTH = 390.0
FRONT_CENTER = 587.0
WHEELBASE = 965.0
BB_DROP = 72.0
BB_HEIGHT = 258.0
FORK_LENGTH = 367.0  # full axle-to-crown along steerer + rake geometry
FORK_RAKE = 50.0
TRAIL = 55.0
STANDOVER = 806.0

# Modeling constants (visual match to Shiv TT aero sections, mm)
WALL_THICKNESS = 3.0
OSBB_BORE = 46.0  # PF30 / OSBB shell ID
OSBB_WIDTH = 68.0
OSBB_OD = 56.0
WHEEL_RADIUS = 335.0  # ~700c tire OD / 2 for cutout reference
REAR_SPACING = 130.0  # classic rim-brake TT spacing
FORK_CROWN_WIDTH = 58.0
DROPOUT_SLOT = 10.0


def _unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    n = math.sqrt(x * x + y * y + z * z)
    return (x / n, y / n, z / n)


def _add(a, b, s: float = 1.0):
    return (a[0] + s * b[0], a[1] + s * b[1], a[2] + s * b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass(frozen=True)
class Hardpoints:
    """Derived Size Small hardpoints used by every tube loft."""

    bb: tuple[float, float, float]
    rear_axle: tuple[float, float, float]
    front_axle: tuple[float, float, float]
    ht_top: tuple[float, float, float]
    ht_bottom: tuple[float, float, float]
    ht_dir: tuple[float, float, float]  # bottom -> top along steerer
    st_top: tuple[float, float, float]
    st_dir: tuple[float, float, float]  # BB -> seat tube top
    tt_front: tuple[float, float, float]
    tt_rear: tuple[float, float, float]
    fork_crown: tuple[float, float, float]
    cs_horizontal: float
    wheelbase_actual: float


def hardpoints() -> Hardpoints:
    """Compute all frame hardpoints from the official Size Small table."""
    bb = (0.0, 0.0, 0.0)

    # Catalog wheelbase / front-center place the axles; CS length is the stay length.
    cs_horizontal = math.sqrt(max(CHAIN_STAY_LENGTH**2 - BB_DROP**2, 0.0))
    # Prefer catalog wheelbase for axle spacing; CS length still drives stay loft length.
    rear_axle = (-(WHEELBASE - FRONT_CENTER), 0.0, BB_DROP)
    front_axle = (FRONT_CENTER, 0.0, BB_DROP)

    # Stack / reach define the top of the head tube (steerer centerline).
    ht_top = (REACH, 0.0, STACK)
    from_vert = math.radians(90.0 - HEAD_TUBE_ANGLE)
    # Up the steerer: rearward and up.
    ht_dir = _unit((-math.sin(from_vert), 0.0, math.cos(from_vert)))
    ht_bottom = _add(ht_top, ht_dir, -HEAD_TUBE_LENGTH)

    # Seat tube: STA measured from horizontal; leans slightly rearward.
    sta = math.radians(SEAT_TUBE_ANGLE)
    st_dir = _unit((-math.cos(sta), 0.0, math.sin(sta)))
    st_top = _add(bb, st_dir, SEAT_TUBE_LENGTH)

    # Horizontal top tube: level line at stack height between HT top and ST.
    # Catalog HTT is effective length; place ends on the tube centerlines.
    tt_z = STACK - 8.0  # top tube center slightly below HT top face
    # Front TT end near HT / stem interface
    # Parametric intersection of horizontal line with HT axis near top:
    # ht_bottom + t * ht_dir has z = tt_z
    t_tt = (tt_z - ht_bottom[2]) / ht_dir[2]
    tt_front = _add(ht_bottom, ht_dir, t_tt)
    # Rear TT end on seat tube at same height
    t_st = (tt_z - bb[2]) / st_dir[2]
    tt_rear = _add(bb, st_dir, t_st)

    # Fork crown: axle projected back along steerer by fork length, plus rake.
    # Axle = crown_along_axis + rake * perpendicular (forward of steerer).
    # Perpendicular in XZ pointing "forward" relative to steerer:
    # steerer dir S = ht_dir; forward-perp P = rotate S by +90° in XZ toward +X ground.
    sx, _, sz = ht_dir
    # Perp that points roughly forward (positive X component): (sz, 0, -sx) or opposite
    p = _unit((sz, 0.0, -sx))
    if p[0] < 0:
        p = (-p[0], 0.0, -p[2])
    # front_axle = crown + FORK_LENGTH * (-ht_dir) wait: crown is above axle along steerer
    # crown = front_axle - rake * p + (distance along steerer).
    # Standard: axle = (crown_race point) + rake_forward, crown race is FORK_LENGTH along
    # steerer above a virtual point. Approximate:
    # Point on steerer at crown: from axle, go up steerer and back by rake.
    crown = _add(_add(front_axle, p, -FORK_RAKE), ht_dir, FORK_LENGTH * 0.55)
    # Better geometric placement: crown sits just under HT bottom, integrated.
    crown = _add(ht_bottom, ht_dir, -18.0)

    return Hardpoints(
        bb=bb,
        rear_axle=rear_axle,
        front_axle=front_axle,
        ht_top=ht_top,
        ht_bottom=ht_bottom,
        ht_dir=ht_dir,
        st_top=st_top,
        st_dir=st_dir,
        tt_front=tt_front,
        tt_rear=tt_rear,
        fork_crown=crown,
        cs_horizontal=cs_horizontal,
        wheelbase_actual=front_axle[0] - rear_axle[0],
    )


def assert_geometry(hp: Hardpoints) -> None:
    """Enforce catalog numbers inside the model body."""
    assert abs(hp.ht_top[0] - REACH) < 0.01
    assert abs(hp.ht_top[2] - STACK) < 0.01
    assert abs(hp.front_axle[0] - FRONT_CENTER) < 0.01
    assert abs(hp.front_axle[2] - BB_DROP) < 0.01
    assert abs(hp.rear_axle[2] - BB_DROP) < 0.01
    assert abs(hp.wheelbase_actual - WHEELBASE) < 0.01
    st_len = math.sqrt(sum(c * c for c in hp.st_top))
    assert abs(st_len - SEAT_TUBE_LENGTH) < 0.01
    ht_len = math.sqrt(sum((a - b) ** 2 for a, b in zip(hp.ht_top, hp.ht_bottom)))
    assert abs(ht_len - HEAD_TUBE_LENGTH) < 0.01
