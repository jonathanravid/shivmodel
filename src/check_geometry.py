"""Assert Size Small catalog hardpoints and assembly envelope."""

from __future__ import annotations

import math
import sys

from assembly import shiv_tt_frameset_small
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
    hardpoints,
)


def main() -> int:
    hp = hardpoints()
    assert hp.ht_top == (REACH, 0.0, STACK)
    assert abs(hp.front_axle[0] - FRONT_CENTER) < 1e-9
    assert abs(hp.front_axle[2] - BB_DROP) < 1e-9
    assert abs(hp.wheelbase_actual - WHEELBASE) < 1e-9
    assert abs(math.sqrt(sum(c * c for c in hp.st_top)) - SEAT_TUBE_LENGTH) < 1e-6
    assert abs(abs(hp.tt_front[0] - hp.tt_rear[0]) - HORIZONTAL_TOP_TUBE) < 5.0
    ht_len = math.dist(hp.ht_top, hp.ht_bottom)
    assert abs(ht_len - HEAD_TUBE_LENGTH) < 1e-6

    # Catalog constants present
    assert (STACK, REACH, SEAT_TUBE_ANGLE, HEAD_TUBE_ANGLE) == (502.0, 390.0, 74.5, 72.0)
    assert (BB_DROP, BB_HEIGHT, FORK_LENGTH, FORK_RAKE, TRAIL, STANDOVER) == (
        72.0,
        258.0,
        367.0,
        50.0,
        55.0,
        806.0,
    )
    assert CHAIN_STAY_LENGTH == 390.0

    doc = shiv_tt_frameset_small()
    shape = doc.shape
    bb = shape.bounding_box()
    assert bb.max.Z >= STACK - 1.0
    assert bb.max.X > FRONT_CENTER - 50.0
    assert bb.min.X < hp.rear_axle[0] + 30.0
    print("geometry OK")
    print(f"  stack/reach hardpoint: {hp.ht_top}")
    print(f"  htt dx: {abs(hp.tt_front[0] - hp.tt_rear[0]):.2f} (catalog {HORIZONTAL_TOP_TUBE})")
    print(f"  wheelbase: {hp.wheelbase_actual}")
    print(f"  assembly bounds: {bb.size}")
    print(f"  id: {doc.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
