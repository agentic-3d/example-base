# build123d notes

Checked against build123d **0.13.0** and the `/en/latest` docs on 2026-10-07. Code snippets were run against 0.13.0. If the installed version differs, verify with `inspect.signature` / `help()` first.

## Doc map (https://build123d.readthedocs.io/en/latest/)
When fetching a page, read the raw source instead of the rendered HTML: `https://build123d.readthedocs.io/en/latest/_sources/<page>.rst.txt` (e.g. `_sources/index.rst.txt`, whose toctree lists the pages).

- `cheat_sheet.html`: every object, operation, selector and enum on one page
- `key_concepts_builder.html`, `key_concepts_algebra.html`: the two modes
- `topology_selection.html`, `tutorial_selectors.html`: selecting vertices/edges/faces
- `objects.html`, `operations.html`, `builders.html`: reference with parameters
- `joints.html`, `assemblies.html`: multi-part designs
- `tips.html`, `import_export.html`, `builder_api_reference.html`

## Modes (project style = builder, compact)
```python
with BuildPart() as p:                  # result: p.part
    Box(60, 40, 10)
    with Locations((10, 0, 5)):         # placement context
        Cylinder(3, 4, mode=Mode.SUBTRACT)
```
- `Mode`: `ADD` (default), `SUBTRACT` (holes/pockets), `INTERSECT`, `REPLACE`, `PRIVATE` (build without adding).
- Objects add themselves on creation, so `Cylinder(1, 2).moved(...)` does nothing. Use `Locations(...)` before creating.
- Sketch to solid: `with BuildSketch(Plane.XY): Rectangle(w, h)` then `extrude(amount=t)` inside `BuildPart`.
- Builders work in local `Plane.XY` and are placed afterwards. Nested builders do not inherit the parent's placement, and selection inside a sketch uses local coordinates.
- Algebra mode: `Box(80, 60, 10) - Pos(0, 0, 0) * Cylinder(11, 10)`. Operators are `+ - &`, and `Plane/Pos/Rot * obj` places. Mixing is fine: `base.part - bore.part`.

## Objects and operations
- 3D: `Box, Cylinder, Cone, Sphere, Torus, Wedge, Hole, CounterBoreHole, CounterSinkHole, ConvexPolyhedron`
- 2D: `Rectangle, RectangleRounded, Circle, Ellipse, Polygon, RegularPolygon, SlotOverall, SlotCenterToCenter, Trapezoid, Triangle, Text`
- 1D: `Line, Polyline, FilletPolyline, CenterArc, ThreePointArc, RadiusArc, TangentArc, Spline, Bezier, Helix`
- Ops: `extrude, revolve, loft, sweep, fillet, chamfer, offset, mirror, scale, split, thicken, draft, make_face`
- Location contexts: `Locations(*points)`, `GridLocations`, `PolarLocations`, `HexLocations`

## Signatures (0.13.0)
```
Hole(radius, depth=None, mode=SUBTRACT)                     # RADIUS, not diameter; through-all if depth None
CounterBoreHole(radius, counter_bore_radius, counter_bore_depth, depth=None)
CounterSinkHole(radius, counter_sink_radius, depth=None, counter_sink_angle=82, mode)
pack(objects, padding, align_z=False)                        # print-bed layout
Box(length, width, height, rotation, align=(CENTER,CENTER,CENTER), mode)   # centered by default
extrude(to_extrude=None, amount, dir, until, target, both=False, taper=0, clean=True, mode)
fillet(objects, radius)    chamfer(objects, length, length2=None, angle=None, reference=None)
GridLocations(x_spacing, y_spacing, x_count, y_count, align=(CENTER,CENTER))
PolarLocations(radius, count, start_angle=0, angular_range=360, rotate=True)
offset(objects, amount, openings, kind=ARC, side=BOTH, closed=True, min_edge_length, mode=REPLACE)
export_stl(shape, path, tolerance=0.001, angular_tolerance=0.1, ascii_format=False)
```

## Selectors (verified on 0.13.0)
```python
p.faces() > Axis.Z          # sort_by, ascending  -> [-1] is topmost
p.faces() < Axis.Z          # sort_by, descending -> [0] is topmost
p.faces() >> Axis.Z         # group_by, LAST group  = top face(s)
p.faces() << Axis.Z         # group_by, FIRST group = bottom face(s)
p.faces() | Axis.Z          # filter_by(Axis.Z): faces whose normal is Z
p.edges().filter_by(GeomType.CIRCLE)
p.edges().filter_by_position(Axis.Z, 4, 6)       # min/max along axis
p.faces().group_by(Axis.Z)                       # list of groups
p.edges().sort_by(SortBy.LENGTH)
```
Select a high-level feature first, then drill down: `(p.faces() >> Axis.Z).edges().filter_by(GeomType.CIRCLE)`. The docs page text describing these operators is ambiguous, so trust the table above.

## Printing recipes (apply CLAUDE.md rules: wall >= 1.2, clearance 0.2)
```python
# Fillet top edges, chamfer bottom edges (first-layer / elephant-foot relief)
with BuildPart() as p:
    Box(30, 30, 10)
    fillet((p.faces() >> Axis.Z).edges(), radius=1)
    chamfer((p.faces() << Axis.Z).edges(), length=0.4)

# Chamfer the rim of a blind hole
with BuildPart() as p:
    Box(30, 30, 10)
    with Locations((0, 0, 5)):
        Hole(4, depth=3)
    chamfer((p.faces() >> Axis.Z).edges().filter_by(GeomType.CIRCLE), length=0.8)

# Clearance fit: socket diameter = peg + 2 * clearance (named parameters!)
PEG, CLEAR = 10, 0.2
with BuildPart() as sock:
    Box(20, 20, 8)
    with Locations((0, 0, 4)):
        Cylinder((PEG + 2 * CLEAR) / 2, 5, mode=Mode.SUBTRACT)

# Hole patterns
with BuildPart() as p:
    Box(60, 40, 10)
    with GridLocations(40, 20, 2, 2): Hole(2.5)
    with PolarLocations(10, 6): CounterBoreHole(1.5, 3, 2)

# Revolve a profile
with BuildPart() as p:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline((0, 0), (10, 0), (10, 5), (5, 10), (0, 10), close=True)
        make_face()
    revolve(axis=Axis.Z)
```

## Tips and gotchas
- 2D before 3D: sketch then extrude/revolve. It is more robust than stacking boxes.
- Fillets and chamfers go last. They fail on complex topology, so reduce the radius or select fewer edges.
- Avoid self-touching solids. They produce invalid topology even when `is_valid` says True, so split them into sections.
- Repeated parts (screws, pins): use shallow copies. `pack(parts, padding=2, align_z=True)` lays parts out for the print bed.
- `from build123d import *` is the accepted style in model scripts.
- "Can't get there from here": if `sweep` fails, try `loft`, or restructure the profile.
- Check the result: `p.part.bounding_box().size`, `p.part.volume`. The `tools/check.py` loop covers watertight and body count.

## Multiple models and reuse
- Files in `models/` import each other (`from models import plate`), which works because tools run from the project root.
- Wrap geometry in `build(...)` with the file's constants as defaults, so another model can reuse it with different dimensions: `insert(plate.build(40, 30, 4, hole_d=4))` inside a `BuildPart` (see `models/bracket.py`).
- Builder mode: `insert(part)` merges an existing part into the current `BuildPart`. Algebra mode: `Pos(x, y, z) * part` places it.
- Separate bodies: `Compound([a, Pos(0, 0, z) * b])` stays two bodies, so check with `--bodies 2` (see `models/assembly.py`). Parts that share a surface or vertex can fuse into one body in the STL, so leave a gap.

## Export (STL only)
`tools/build.py <name>` calls `export_stl(result, "out/<name>.stl", tolerance=0.01, angular_tolerance=0.1)`, which writes binary STL. `Mesher` handles 3MF (with metadata) if it is ever needed. The project does not export STEP.
