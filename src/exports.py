"""Standing deliverables for the Size Small Shiv TT frameset."""

from pathlib import Path

from assembly import shiv_tt_frameset_small
from cad import model
from cockpit import shiv_tt_cockpit_small
from fork import shiv_tt_fork_small
from frame import shiv_tt_frame_small


ROOT = Path(__file__).resolve().parents[1]


def main():
    frameset = shiv_tt_frameset_small()
    frame = shiv_tt_frame_small()
    fork = shiv_tt_fork_small()
    cockpit = shiv_tt_cockpit_small()

    (ROOT / "STEP").mkdir(exist_ok=True)
    (ROOT / "STL").mkdir(exist_ok=True)
    (ROOT / "GLB").mkdir(exist_ok=True)

    model.export(frameset, ROOT / "STEP" / "shiv_tt_frameset_small.step")
    model.export(frameset, ROOT / "STL" / "shiv_tt_frameset_small.stl")
    model.export(frameset, ROOT / "GLB" / "shiv_tt_frameset_small.glb")
    model.export(frame, ROOT / "STEP" / "shiv_tt_frame_small.step")
    model.export(fork, ROOT / "STEP" / "shiv_tt_fork_small.step")
    model.export(cockpit, ROOT / "STEP" / "shiv_tt_cockpit_small.step")
    print("exports written under STEP/, STL/, GLB/")


if __name__ == "__main__":
    main()
