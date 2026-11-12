"""Full 2017 Specialized S-Works Shiv TT Size Small frameset assembly."""

from __future__ import annotations

import math

import build123d as bd
from cad import model

from lib.geometry import (
    BB_DROP,
    BB_HEIGHT,
    CHAIN_STAY_LENGTH,
    FORK_LENGTH,
    FORK_RAKE,
    FRONT_CENTER,
    HEAD_TUBE_ANGLE,
    HEAD_TUBE_LENGTH,
    HORIZONTAL_TOP_TUBE,
    REACH,
    SEAT_TUBE_ANGLE,
    SEAT_TUBE_LENGTH,
    STACK,
    STANDOVER,
    TRAIL,
    WHEELBASE,
    assert_geometry,
    hardpoints,
)
from cockpit import shiv_tt_cockpit_small
from fork import shiv_tt_fork_small
from frame import shiv_tt_frame_small


@model
def shiv_tt_frameset_small():
    """Photoreal Size Small Shiv TT frameset: frame + fork + cockpit."""
    hp = hardpoints()
    assert_geometry(hp)

    # Re-assert every official catalog number is present in this configuration.
    assert STACK == 502.0
    assert REACH == 390.0
    assert SEAT_TUBE_ANGLE == 74.5
    assert HEAD_TUBE_ANGLE == 72.0
    assert HEAD_TUBE_LENGTH == 100.0
    assert SEAT_TUBE_LENGTH == 565.0
    assert HORIZONTAL_TOP_TUBE == 529.0
    assert CHAIN_STAY_LENGTH == 390.0
    assert FRONT_CENTER == 587.0
    assert WHEELBASE == 965.0
    assert BB_DROP == 72.0
    assert BB_HEIGHT == 258.0
    assert FORK_LENGTH == 367.0
    assert FORK_RAKE == 50.0
    assert TRAIL == 55.0
    assert STANDOVER == 806.0

    frame = shiv_tt_frame_small().shape
    frame.label = "frame_asm"

    fork = shiv_tt_fork_small().shape
    fork.label = "fork_asm"

    cockpit = shiv_tt_cockpit_small().shape
    cockpit.label = "cockpit_asm"

    frameset = bd.Compound(
        children=[frame, fork, cockpit],
        label="shiv_tt_frameset_small",
    )

    # Bounding envelope must cover stack/reach and wheelbase hardpoints.
    bb = frameset.bounding_box()
    assert bb.min.X < hp.rear_axle[0] + 50
    assert bb.max.X > hp.ht_top[0]
    assert bb.max.Z >= STACK - 5.0
    assert abs(hp.wheelbase_actual - WHEELBASE) < 0.01
    assert abs(math.sqrt(sum(c * c for c in hp.st_top)) - SEAT_TUBE_LENGTH) < 0.01

    return frameset


if __name__ == "__main__":
    doc = shiv_tt_frameset_small()
    print(f"frameset id: {doc.id}")
    print(f"view: {doc.url}")
