# 2017 Specialized S-Works Shiv TT — Size Small

Parametric build123d CAD model of the S-Works Shiv TT frameset, scaled to the
official Size Small geometry table.

## Geometry (Size Small)

| Spec | Value |
| --- | --- |
| Stack | 502 mm |
| Reach | 390 mm |
| Seat tube angle | 74.5° |
| Head tube angle | 72° |
| Head tube length | 100 mm |
| Seat tube length (c-t) | 565 mm |
| Horizontal top tube | 529 mm |
| Chain stay length | 390 mm |
| Front center | 587 mm |
| Wheelbase | 965 mm |
| BB drop | 72 mm |
| BB height | 258 mm |
| Fork length | 367 mm |
| Fork rake | 50 mm |
| Trail | 55 mm |
| Standover | 806 mm |

## Layout

```
src/
  lib/geometry.py   # hardpoints from the Size Small table
  lib/profiles.py   # truncated-airfoil (kammtail) sections
  lib/tubes.py      # loft / fuse / shell helpers
  frame.py          # main triangle + stays + OSBB
  fork.py           # aero fork
  cockpit.py        # stem / basebar / extensions
  assembly.py       # full frameset
  exports.py        # STEP / STL / GLB writers
assets/shiv-tt-reference.png
STEP/ STL/ GLB/
```

## Build

```bash
cad run src/assembly.py
cad run src/exports.py
```

Finish: glossy metallic light blue/silver CFRP (`#A9BFCE`) with black integrated
seatpost tip and light branding plates (S-WORKS / SHIV TT areas).
