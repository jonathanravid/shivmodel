"""Integrated aero stem, basebar, extensions and armrests for the Shiv TT."""

from __future__ import annotations

import build123d as bd
from bd_materials import plastics
from cad import model

from lib.geometry import REACH, STACK, hardpoints
from lib.tubes import aero_tube, fuse_all


PAINT = "#A9BFCE"
PAD = "#1E1E1E"


def _paint(part: bd.Solid, color: str = PAINT, rough: float = 0.2) -> bd.Solid:
    mat = plastics.cfrp()
    mat.pbr = mat.pbr.override(
        metalness=0.55,
        roughness=rough,
        clearcoat=0.95,
        clearcoat_roughness=0.08,
    )
    part.material = mat
    part.color = color
    return part


def build_cockpit(hp) -> bd.Compound:
    stem_front = (hp.ht_top[0] + 78.0, 0.0, hp.ht_top[2] - 8.0)
    carbon: list[bd.Solid] = []

    stem = aero_tube(
        (hp.ht_top[0] + 15.0, 0.0, hp.ht_top[2] - 2.0),
        stem_front,
        chord0=46.0,
        thick0=32.0,
        chord1=40.0,
        thick1=28.0,
        kind="flat",
        chord_hint=(0.0, 0.0, -1.0),
    )
    carbon.append(stem)

    # Basebar center
    center = bd.Box(48.0, 100.0, 26.0, align=bd.Align.CENTER)
    center = bd.Pos(*stem_front) * center
    carbon.append(center)

    # Explicit full-span aero wings (boxes lofted via taper) — guaranteed ±200 mm
    bar_half = 200.0
    pads: list[bd.Solid] = []
    for sign in (-1.0, 1.0):
        # Tapered wing as a wedge solid from root to tip
        root = bd.Box(44.0, 30.0, 24.0, align=bd.Align.CENTER)
        root = bd.Pos(stem_front[0], sign * 55.0, stem_front[2]) * root
        tip = bd.Box(28.0, 24.0, 16.0, align=bd.Align.CENTER)
        tip = bd.Pos(
            stem_front[0] - 35.0,
            sign * bar_half,
            stem_front[2] - 55.0,
        ) * tip
        # Connect with lofted aero tube for the mid span
        wing = aero_tube(
            (stem_front[0], sign * 50.0, stem_front[2]),
            (stem_front[0] - 35.0, sign * bar_half, stem_front[2] - 55.0),
            chord0=42.0,
            thick0=22.0,
            chord1=26.0,
            thick1=14.0,
            kind="flat",
            chord_hint=(0.0, 0.0, -1.0),
        )
        carbon.extend([root, tip, wing])

        lever = bd.Cylinder(7.5, 50.0, align=bd.Align.MIN)
        lever = bd.Rot(0, 20, 0) * lever
        lever = bd.Pos(
            stem_front[0] - 40.0, sign * bar_half, stem_front[2] - 60.0
        ) * lever
        carbon.append(lever)

        riser = bd.Cylinder(8.5, 95.0, align=bd.Align.MIN)
        riser = bd.Pos(stem_front[0] + 8.0, sign * 60.0, stem_front[2] + 10.0) * riser
        carbon.append(riser)

        ext0 = (stem_front[0] + 8.0, sign * 60.0, stem_front[2] + 100.0)
        ext1 = (stem_front[0] + 95.0, sign * 60.0, stem_front[2] + 108.0)
        ext2 = (stem_front[0] + 175.0, sign * 60.0, stem_front[2] + 78.0)
        carbon.append(
            aero_tube(ext0, ext1, chord0=24.0, thick0=18.0, kind="flat", chord_hint=(0, 0, -1))
        )
        carbon.append(
            aero_tube(
                ext1,
                ext2,
                chord0=24.0,
                thick0=18.0,
                chord1=20.0,
                thick1=16.0,
                kind="flat",
                chord_hint=(0, 0, -1),
            )
        )

        pad = bd.Box(95.0, 58.0, 20.0, align=bd.Align.CENTER)
        try:
            pad = bd.fillet(pad.edges().group_by(bd.Axis.Z)[-1], 10.0)
        except Exception:
            pass
        pad = bd.Pos(stem_front[0] + 40.0, sign * 60.0, stem_front[2] + 112.0) * pad
        pad = _paint(pad, PAD, rough=0.7)
        pad.label = "armrest"
        pads.append(pad)

    fused = fuse_all(carbon)
    body_parts = []
    solids = list(fused.solids()) if hasattr(fused, "solids") else [fused]
    for i, s in enumerate(solids):
        s = _paint(s, PAINT)
        s.label = "cockpit_carbon" if i == 0 else f"cockpit_carbon_{i}"
        body_parts.append(s)
    return bd.Compound(children=[*body_parts, *pads], label="cockpit")


@model
def shiv_tt_cockpit_small():
    hp = hardpoints()
    assert abs(hp.ht_top[0] - REACH) < 0.01
    assert abs(hp.ht_top[2] - STACK) < 0.01
    return build_cockpit(hp)


if __name__ == "__main__":
    shiv_tt_cockpit_small()
