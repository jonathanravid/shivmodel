"""2017 S-Works Shiv TT Size Small main frame (monocoque aero tubes)."""

from __future__ import annotations

import math

import build123d as bd
from bd_materials import plastics
from cad import model

from lib.geometry import (
    BB_DROP,
    HEAD_TUBE_LENGTH,
    HORIZONTAL_TOP_TUBE,
    OSBB_BORE,
    OSBB_OD,
    OSBB_WIDTH,
    REACH,
    SEAT_TUBE_LENGTH,
    STACK,
    WALL_THICKNESS,
    WHEEL_RADIUS,
    assert_geometry,
    hardpoints,
)
from lib.profiles import blade_points, flat_aero_points, kammtail_points
from lib.tubes import aero_tube, fuse_all, hollow_solid, loft_tube


PAINT = "#A9BFCE"  # light metallic blue/silver
BLACK = "#151515"
DECAL = "#F4F7FA"
REAR_HALF = 65.0


def _lerp(a, b, t: float):
    return (
        a[0] + t * (b[0] - a[0]),
        a[1] + t * (b[1] - a[1]),
        a[2] + t * (b[2] - a[2]),
    )


def _paint_cfrp(part: bd.Solid, color: str = PAINT) -> bd.Solid:
    mat = plastics.cfrp()
    mat.pbr = mat.pbr.override(
        metalness=0.62,
        roughness=0.18,
        clearcoat=1.0,
        clearcoat_roughness=0.06,
        anisotropy=0.4,
    )
    part.material = mat
    part.color = color
    return part


def _safe_fillet(solid: bd.Solid, radius: float, z_lo: float, z_hi: float) -> bd.Solid:
    try:
        edges = [
            e
            for e in solid.edges()
            if z_lo <= e.center().Z <= z_hi and 2.0 < e.length < 90.0
        ][:18]
        if edges:
            return bd.fillet(edges, radius)
    except Exception:
        pass
    return solid


def _as_solid_list(shape) -> list[bd.Solid]:
    if shape is None:
        return []
    if hasattr(shape, "solids"):
        return list(shape.solids())
    return [shape]


def build_main_triangle(hp) -> bd.Solid | bd.Compound:
    """Downtube, toptube, seat tube with scallop, head tube, OSBB, stays."""
    parts: list[bd.Solid] = []

    # --- OSBB shell ---
    bb_shell = bd.Cylinder(OSBB_OD / 2, OSBB_WIDTH, align=bd.Align.CENTER)
    bb_shell = bd.Rot(0, 90, 0) * bb_shell
    fair = bd.Sphere(radius=38)
    fair = fair.scale((1.55, 0.95, 1.15))
    parts.extend(_as_solid_list(fuse_all([bb_shell, fair])))

    # --- Downtube: deepest kammtail (overlap HT and BB) ---
    dt0 = _lerp(hp.ht_bottom, hp.ht_top, 0.15)  # into HT
    dt1 = _lerp(hp.ht_bottom, hp.bb, 0.50)
    dt2 = (0.0, 0.0, 8.0)  # into BB fairing
    dt = aero_tube(
        dt0,
        dt2,
        chord0=105.0,
        thick0=40.0,
        chord1=118.0,
        thick1=56.0,
        mid=dt1,
        chord_mid=110.0,
        thick_mid=44.0,
        truncate=0.74,
        chord_hint=(0.15, 0.0, -1.0),
        kind="kamm",
    )
    parts.append(dt)

    # --- Head tube (full length + slight overshoot for unions) ---
    ht_stations = []
    for t, chord, thick in (
        (-0.05, 70.0, 52.0),
        (0.5, 60.0, 44.0),
        (1.05, 54.0, 38.0),
    ):
        o = _lerp(hp.ht_bottom, hp.ht_top, t)
        ht_stations.append((o, hp.ht_dir, kammtail_points(chord, thick, truncate=0.70)))
    ht = loft_tube(ht_stations, ruled=True, chord_hint=(-1.0, 0.0, 0.0))
    parts.append(ht)

    # Stem interface stub (flush with top tube, forward of HT)
    stem = aero_tube(
        _lerp(hp.ht_bottom, hp.ht_top, 0.85),
        (hp.ht_top[0] + 62.0, 0.0, hp.ht_top[2] - 5.0),
        chord0=50.0,
        thick0=34.0,
        chord1=40.0,
        thick1=26.0,
        kind="flat",
        chord_hint=(0.0, 0.0, -1.0),
    )
    parts.append(stem)

    # --- Horizontal top tube (overlap HT and ST) ---
    tt = aero_tube(
        (hp.tt_front[0] + 15.0, 0.0, hp.tt_front[2]),
        (hp.tt_rear[0] - 20.0, 0.0, hp.tt_rear[2]),
        chord0=44.0,
        thick0=24.0,
        chord1=48.0,
        thick1=26.0,
        kind="flat",
        chord_hint=(0.0, 0.0, -1.0),
    )
    parts.append(tt)

    # --- Seat tube: deep blade, then gentle rear scallop ---
    st0 = (0.0, 0.0, 5.0)  # into BB
    st1 = _lerp(hp.bb, hp.st_top, 0.42)
    st2 = _lerp(hp.bb, hp.st_top, 0.78)
    st3 = _lerp(hp.bb, hp.st_top, 1.02)  # past TT junction
    st_lo = aero_tube(
        st0,
        st1,
        chord0=92.0,
        thick0=42.0,
        chord1=86.0,
        thick1=36.0,
        kind="blade",
        chord_hint=(-1.0, 0.0, 0.0),
    )
    st_mid = aero_tube(
        st1,
        st2,
        chord0=86.0,
        thick0=36.0,
        chord1=72.0,
        thick1=32.0,
        kind="blade",
        chord_hint=(-1.0, 0.0, 0.0),
    )
    st_hi = aero_tube(
        st2,
        st3,
        chord0=72.0,
        thick0=32.0,
        chord1=58.0,
        thick1=28.0,
        kind="blade",
        chord_hint=(-1.0, 0.0, 0.0),
    )
    seat = fuse_all([st_lo, st_mid, st_hi])
    seat_solids = _as_solid_list(seat)
    seat = seat_solids[0] if len(seat_solids) == 1 else fuse_all(seat_solids)

    # Scallop: wheel cylinder ∩ box only behind seat-tube midplane so we
    # never erase the leading edge / open triangle wall.
    wheel = bd.Cylinder(WHEEL_RADIUS + 4.0, 160.0, align=bd.Align.CENTER)
    wheel = bd.Rot(90, 0, 0) * wheel
    wheel = bd.Pos(hp.rear_axle[0], 0.0, hp.rear_axle[2]) * wheel
    st_center_x = 0.5 * (st1[0] + st2[0]) - 25.0
    cut_box = bd.Box(500.0, 200.0, 700.0, align=bd.Align.CENTER)
    cut_box = bd.Pos(st_center_x - 250.0, 0.0, 280.0) * cut_box
    try:
        cutter = wheel & cut_box
        if cutter is not None and cutter.solids():
            base_vol = sum(s.volume for s in _as_solid_list(seat))
            seat2 = seat - cutter.solids()[0]
            new_solids = _as_solid_list(seat2)
            if new_solids and sum(s.volume for s in new_solids) > 0.35 * base_vol:
                seat = new_solids[0] if len(new_solids) == 1 else fuse_all(new_solids)
    except Exception:
        pass
    parts.extend(_as_solid_list(seat))

    # --- Dropped seat stays ---
    stay_t = 0.62
    stay_root = _lerp(hp.bb, hp.st_top, stay_t)
    for sign in (-1.0, 1.0):
        s0 = (stay_root[0] - 18.0, sign * 14.0, stay_root[2] - 5.0)
        s1 = (hp.rear_axle[0] + 20.0, sign * REAR_HALF, hp.rear_axle[2] + 4.0)
        ss = aero_tube(
            s0,
            s1,
            chord0=30.0,
            thick0=12.0,
            chord1=22.0,
            thick1=10.0,
            kind="flat",
            chord_hint=(-1.0, 0.0, 0.0),
        )
        parts.append(ss)

    # --- Chainstays ---
    for sign in (-1.0, 1.0):
        c0 = (30.0, sign * 20.0, 8.0)
        c1 = (
            0.5 * (c0[0] + hp.rear_axle[0]),
            sign * (20.0 + 0.45 * (REAR_HALF - 20.0)),
            18.0,
        )
        c2 = (hp.rear_axle[0] + 14.0, sign * REAR_HALF, hp.rear_axle[2])
        cs = aero_tube(
            c0,
            c2,
            chord0=52.0,
            thick0=24.0,
            chord1=30.0,
            thick1=14.0,
            mid=c1,
            chord_mid=40.0,
            thick_mid=18.0,
            kind="blade",
            chord_hint=(0.0, 0.0, -1.0),
        )
        # Light upper scallop (visual cue from Shiv chainstay)
        scallop = bd.Sphere(radius=12)
        scallop = bd.Pos(c1[0], c1[1], c1[2] + 12.0) * scallop
        try:
            cs2 = cs - scallop
            if cs2.solids():
                cs = cs2.solids()[0]
        except Exception:
            pass
        parts.append(cs)

    # --- Horizontal rear dropouts ---
    for sign in (-1.0, 1.0):
        do = bd.Box(46.0, 9.0, 30.0, align=bd.Align.CENTER)
        slot = bd.Box(30.0, 12.0, 10.0, align=bd.Align.CENTER)
        do = do - bd.Pos(-2, 0, 0) * slot
        do = bd.Pos(hp.rear_axle[0], sign * REAR_HALF, hp.rear_axle[2]) * do
        parts.append(do.solids()[0])

    # --- Rear brake fairing under BB / ahead of CS ---
    brake = bd.Box(36.0, 28.0, 22.0, align=bd.Align.CENTER)
    brake = bd.Pos(-40.0, 0.0, -8.0) * brake
    parts.append(brake)

    frame = fuse_all(parts)
    frame_solids = _as_solid_list(frame)

    def _cut_all(solids: list[bd.Solid], tool: bd.Solid) -> list[bd.Solid]:
        out: list[bd.Solid] = []
        for s in solids:
            try:
                cut = s - tool
                out.extend(_as_solid_list(cut) or [s])
            except Exception:
                out.append(s)
        return out

    # Steerer bore
    steerer = bd.Cylinder(12.5, HEAD_TUBE_LENGTH + 50.0, align=bd.Align.CENTER)
    z = bd.Vector(0, 0, 1)
    d = bd.Vector(*hp.ht_dir).normalized()
    axis = z.cross(d)
    if axis.length > 1e-9:
        ang = math.degrees(math.acos(max(-1.0, min(1.0, z.dot(d)))))
        steerer = steerer.rotate(bd.Axis((0, 0, 0), axis), ang)
    mid_ht = _lerp(hp.ht_bottom, hp.ht_top, 0.5)
    steerer = bd.Pos(*mid_ht) * steerer
    frame_solids = _cut_all(frame_solids, steerer)

    # OSBB bore
    bb_bore = bd.Cylinder(OSBB_BORE / 2, OSBB_WIDTH + 6.0, align=bd.Align.CENTER)
    bb_bore = bd.Rot(0, 90, 0) * bb_bore
    frame_solids = _cut_all(frame_solids, bb_bore)

    # Cable exit ports (clean routing cues)
    for y in (-14.0, 14.0):
        port = bd.Cylinder(3.0, 40.0, align=bd.Align.CENTER)
        port = bd.Rot(0, 90, 0) * port
        port = bd.Pos(hp.tt_front[0] - 25.0, y, hp.tt_front[2] - 8.0) * port
        frame_solids = _cut_all(frame_solids, port)

    framed: list[bd.Solid] = []
    for s in frame_solids:
        s = _safe_fillet(s, 5.0, -30.0, 140.0)
        s = hollow_solid(s, WALL_THICKNESS)
        framed.append(s)

    if len(framed) == 1:
        return framed[0]
    return bd.Compound(children=framed)


def build_black_seatpost_tip(hp) -> bd.Solid:
    """Black upper seatpost continuing the aero mast above the TT junction."""
    start = _lerp(hp.bb, hp.st_top, 0.93)
    end = _lerp(hp.bb, hp.st_top, 1.14)
    tip = aero_tube(
        start,
        end,
        chord0=56.0,
        thick0=27.0,
        chord1=42.0,
        thick1=22.0,
        kind="blade",
        chord_hint=(-1.0, 0.0, 0.0),
    )
    # Slight overlap into the silver mast so it reads continuous
    return tip


def build_decal_plates(hp) -> list[bd.Solid]:
    """Raised branding plates: S-WORKS on DT, SHIV TT near ST/TT junction."""
    plates = []
    dt_mid = _lerp(hp.ht_bottom, hp.bb, 0.42)
    # Downtube side plate (S-WORKS area)
    p1 = bd.Box(110.0, 0.7, 22.0, align=bd.Align.CENTER)
    # Align roughly with downtube angle
    ang = math.degrees(math.atan2(hp.ht_bottom[2] - 0.0, hp.ht_bottom[0] - 0.0))
    p1 = bd.Rot(0, -(90 - ang), 0) * p1
    p1 = bd.Pos(dt_mid[0] + 8.0, 23.0, dt_mid[2] + 8.0) * p1
    plates.append(p1)
    # SHIV TT near seat tube / top tube
    p2 = bd.Box(60.0, 0.7, 12.0, align=bd.Align.CENTER)
    p2 = bd.Pos(hp.tt_rear[0] + 55.0, 14.0, hp.tt_rear[2] + 2.0) * p2
    plates.append(p2)
    return plates


@model
def shiv_tt_frame_small():
    hp = hardpoints()
    assert_geometry(hp)
    htt = abs(hp.tt_front[0] - hp.tt_rear[0])
    assert abs(htt - HORIZONTAL_TOP_TUBE) < 5.0

    frame = build_main_triangle(hp)
    frame_children = []
    for i, s in enumerate(_as_solid_list(frame)):
        s = _paint_cfrp(s, PAINT)
        s.label = "frame" if i == 0 else f"frame_{i}"
        frame_children.append(s)

    tip = build_black_seatpost_tip(hp)
    tip = _paint_cfrp(tip, BLACK)
    tip.label = "seatpost_black"

    decals = []
    for i, p in enumerate(build_decal_plates(hp)):
        p = _paint_cfrp(p, DECAL)
        p.label = f"decal_{i}"
        decals.append(p)

    assert abs(hp.ht_top[0] - REACH) < 0.01
    assert abs(hp.ht_top[2] - STACK) < 0.01
    assert abs(math.sqrt(sum(c * c for c in hp.st_top)) - SEAT_TUBE_LENGTH) < 0.01
    assert HEAD_TUBE_LENGTH == 100.0
    assert BB_DROP == 72.0

    return bd.Compound(
        children=[*frame_children, tip, *decals],
        label="shiv_tt_frame_small",
    )


if __name__ == "__main__":
    shiv_tt_frame_small()
