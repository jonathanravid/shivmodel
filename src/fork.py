"""Shiv TT integrated aero fork for Size Small."""

from __future__ import annotations

import math

import build123d as bd
from bd_materials import plastics
from cad import model

from lib.geometry import BB_DROP, FORK_RAKE, FRONT_CENTER, WALL_THICKNESS, hardpoints
from lib.tubes import aero_tube, fuse_all, hollow_solid


PAINT = "#A9BFCE"
ACCENT = "#E8EEF2"


def _paint(part: bd.Solid, color: str = PAINT) -> bd.Solid:
    mat = plastics.cfrp()
    mat.pbr = mat.pbr.override(
        metalness=0.6,
        roughness=0.2,
        clearcoat=1.0,
        clearcoat_roughness=0.07,
        anisotropy=0.35,
    )
    part.material = mat
    part.color = color
    return part


def _lerp(a, b, t):
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2]))


def build_fork(hp) -> bd.Solid:
    crown = hp.fork_crown
    axle = hp.front_axle
    parts = []

    # Crown nesting under HT / DT junction
    crown_body = aero_tube(
        _lerp(hp.ht_bottom, crown, 0.2),
        _lerp(crown, axle, 0.12),
        chord0=78.0,
        thick0=54.0,
        chord1=90.0,
        thick1=60.0,
        kind="kamm",
        chord_hint=(-1.0, 0.0, 0.0),
    )
    parts.append(crown_body)

    # Integrated front rim-brake fairing behind crown
    brake = bd.Box(30.0, 22.0, 42.0, align=bd.Align.CENTER)
    brake = bd.Pos(crown[0] - 22.0, 0.0, crown[2] - 40.0) * brake
    parts.append(brake)

    for sign in (-1.0, 1.0):
        top = (crown[0] - 8.0, sign * 16.0, crown[2] - 20.0)
        mid = (
            axle[0] * 0.4 + crown[0] * 0.6,
            sign * 38.0,
            axle[2] * 0.5 + crown[2] * 0.5,
        )
        bot = (axle[0] + 2.0, sign * 50.0, axle[2])
        blade = aero_tube(
            top,
            bot,
            chord0=62.0,
            thick0=16.0,
            chord1=34.0,
            thick1=12.0,
            mid=mid,
            chord_mid=52.0,
            thick_mid=14.0,
            kind="blade",
            chord_hint=(-1.0, 0.0, 0.0),
        )
        parts.append(blade)

        do = bd.Box(32.0, 8.0, 26.0, align=bd.Align.CENTER)
        slot = bd.Box(20.0, 10.0, 9.0, align=bd.Align.CENTER)
        do = do - bd.Pos(4, 0, 0) * slot
        do = bd.Pos(axle[0], sign * 50.0, axle[2]) * do
        parts.append(do.solids()[0])

    fork = fuse_all(parts)

    # Steerer upward into HT
    steerer = bd.Cylinder(12.5, 145.0, align=bd.Align.MIN)
    z = bd.Vector(0, 0, 1)
    d = bd.Vector(*hp.ht_dir).normalized()
    axis = z.cross(d)
    if axis.length > 1e-9:
        ang = math.degrees(math.acos(max(-1.0, min(1.0, z.dot(d)))))
        steerer = steerer.rotate(bd.Axis((0, 0, 0), axis), ang)
    steerer = bd.Pos(*_lerp(crown, hp.ht_bottom, 0.5)) * steerer
    fork = fuse_all([fork, steerer])
    return hollow_solid(fork, WALL_THICKNESS)


@model
def shiv_tt_fork_small():
    hp = hardpoints()
    assert abs(hp.front_axle[0] - FRONT_CENTER) < 0.01
    assert abs(hp.front_axle[2] - BB_DROP) < 0.01
    assert FORK_RAKE == 50.0

    fork = _paint(build_fork(hp), PAINT)
    fork.label = "fork"

    accents = []
    for sign in (-1.0, 1.0):
        strip = bd.Box(45.0, 0.6, 140.0, align=bd.Align.CENTER)
        strip = bd.Pos(
            0.55 * hp.fork_crown[0] + 0.45 * hp.front_axle[0],
            sign * 32.0,
            0.55 * hp.fork_crown[2] + 0.45 * hp.front_axle[2],
        ) * strip
        strip = _paint(strip, ACCENT)
        strip.label = "fork_accent"
        accents.append(strip)

    return bd.Compound(children=[fork, *accents], label="shiv_tt_fork_small")


if __name__ == "__main__":
    shiv_tt_fork_small()
