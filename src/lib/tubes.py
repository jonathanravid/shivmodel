"""Loft helpers that place kammtail sections along bicycle tube centerlines."""

from __future__ import annotations

import math

import build123d as bd

from lib.profiles import blade_points, flat_aero_points, kammtail_points


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    n = math.sqrt(x * x + y * y + z * z)
    if n < 1e-12:
        return (0.0, 0.0, 1.0)
    return (x / n, y / n, z / n)


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def section_plane(
    origin: tuple[float, float, float],
    tangent: tuple[float, float, float],
    up_hint: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> bd.Plane:
    """Plane whose +Z is along the tube tangent and +X aligns with chord aft.

    Local profile: +X = trailing (chord), +Y = lateral. We map profile +X onto the
    world direction that is the projection of -forward (or up_hint) into the plane.
    """
    z_dir = bd.Vector(*_normalize(tangent))
    # Prefer mapping chord aft roughly opposite to global +X (rearward on DT/ST),
    # falling back to up_hint when the tube is near horizontal forward.
    hint = bd.Vector(*up_hint)
    x_dir = hint - z_dir * hint.dot(z_dir)
    if x_dir.length < 1e-8:
        hint = bd.Vector(-1.0, 0.0, 0.0)
        x_dir = hint - z_dir * hint.dot(z_dir)
    x_dir = x_dir.normalized()
    y_dir = z_dir.cross(x_dir).normalized()
    # Re-orthogonalize x
    x_dir = y_dir.cross(z_dir).normalized()
    return bd.Plane(origin=bd.Vector(*origin), x_dir=x_dir, z_dir=z_dir)


def profile_face(
    plane: bd.Plane,
    points_xy: list[tuple[float, float]],
    scale: float = 1.0,
) -> bd.Face:
    """Make a planar face from local XY profile points on the given plane."""
    pts = [bd.Vector(scale * x, scale * y, 0.0) for x, y in points_xy[:-1]]
    with bd.BuildSketch(plane) as sk:
        bd.Polygon(*pts, align=None)
    return sk.sketch.faces()[0]


def loft_tube(
    stations: list[tuple[tuple[float, float, float], tuple[float, float, float], list[tuple[float, float]]]],
    *,
    ruled: bool = True,
    chord_hint: tuple[float, float, float] = (-1.0, 0.0, 0.0),
) -> bd.Solid:
    """Loft a solid tube from (origin, tangent, profile_points) stations."""
    faces = []
    for origin, tangent, pts in stations:
        pl = section_plane(origin, tangent, up_hint=chord_hint)
        faces.append(profile_face(pl, pts))
    # build123d 0.13: Solid.make_loft wants wires; bd.loft accepts faces/sketches.
    result = bd.loft(faces, ruled=ruled)
    solids = result.solids() if hasattr(result, "solids") else []
    if not solids:
        raise RuntimeError("loft produced no solid")
    return solids[0]


def aero_tube(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    *,
    chord0: float,
    thick0: float,
    chord1: float | None = None,
    thick1: float | None = None,
    truncate: float = 0.72,
    mid: tuple[float, float, float] | None = None,
    chord_mid: float | None = None,
    thick_mid: float | None = None,
    chord_hint: tuple[float, float, float] = (-1.0, 0.0, 0.0),
    kind: str = "kamm",
) -> bd.Solid:
    """Convenience loft between two (optionally three) aero sections."""
    chord1 = chord0 if chord1 is None else chord1
    thick1 = thick0 if thick1 is None else thick1

    def pts(c, t):
        if kind == "flat":
            return flat_aero_points(c, t)
        if kind == "blade":
            return blade_points(c, t)
        return kammtail_points(c, t, truncate=truncate)

    tangent = _normalize(
        (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    )
    stations = [(start, tangent, pts(chord0, thick0))]
    if mid is not None:
        cm = chord_mid if chord_mid is not None else 0.5 * (chord0 + chord1)
        tm = thick_mid if thick_mid is not None else 0.5 * (thick0 + thick1)
        stations.append((mid, tangent, pts(cm, tm)))
    stations.append((end, tangent, pts(chord1, thick1)))
    # Smooth loft reads more like molded carbon; fall back to ruled if refused.
    try:
        return loft_tube(stations, ruled=False, chord_hint=chord_hint)
    except Exception:
        return loft_tube(stations, ruled=True, chord_hint=chord_hint)


def hollow_solid(solid: bd.Solid, wall: float) -> bd.Solid:
    """Attempt inward shell; fall back to the solid outer if offset fails."""
    # Prefer shelling through planar openings when present (BB / steerer bores).
    openings = []
    try:
        for face in solid.faces():
            if face.area < 80.0:
                continue
            # Small-ish planar faces are typical bore ends.
            try:
                if face.geom_type == bd.Geom.PLANE and 80.0 <= face.area <= 3500.0:
                    openings.append(face)
            except Exception:
                pass
        openings = openings[:6]
        kwargs = {"openings": openings} if openings else {}
        shelled = bd.offset(solid, -wall, **kwargs)
        if shelled is not None and shelled.solids():
            s = shelled.solids()[0]
            if s.is_valid and 0 < s.volume < 0.92 * solid.volume:
                return s
    except Exception:
        pass
    try:
        shelled = bd.offset(solid, -wall)
        if shelled is not None and shelled.solids():
            s = shelled.solids()[0]
            if s.is_valid and 0 < s.volume < 0.92 * solid.volume:
                return s
    except Exception:
        pass
    # Fallback: watertight outer solid (STEP-ready B-rep).
    return solid


def fuse_all(parts: list[bd.Solid]) -> bd.Solid | bd.Compound:
    """Boolean-fuse solids, never dropping disjoint members.

    OCCT union of non-overlapping solids yields a multi-solid compound. Taking
    only ``solids()[0]`` silently deletes the rest (top tube, head tube, ...).
    """
    if not parts:
        raise ValueError("fuse_all: no parts")
    body: bd.Shape = parts[0]
    for p in parts[1:]:
        try:
            body = body + p
        except Exception:
            # Fall back to a compound so geometry is never discarded.
            prev = list(body.solids()) if hasattr(body, "solids") else [body]
            body = bd.Compound(children=[*prev, p])
    solids = list(body.solids()) if hasattr(body, "solids") else [body]
    if len(solids) == 1:
        return solids[0]
    # Keep every solid; caller may still fillet / shell the primary body.
    return bd.Compound(children=solids)
