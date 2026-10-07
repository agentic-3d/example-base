# example-3d

Parametric CAD with [build123d](https://build123d.readthedocs.io/) (Python, OpenCascade). Parts are mm-precise and exported as STL for FDM 3D printing (0.4 mm nozzle, PLA/PETG).

## Models

| Model | Description | Expected bbox (mm) |
|---|---|---|
| `plate` | Mounting plate with four corner holes | 60 x 40 x 10 |
| `bracket` | L-bracket with filleted joint and teardrop wall hole; reuses `plate` for its base | 40 x 30 x 29 |
| `assembly` | Exploded view of `plate` and `bracket` (2 bodies, gap between them) | 60 x 40 x 44 |
| `stool` | 120 mm scale-model stool, upright, sized from the reference photos by ratios of `HEIGHT`; one fused body | 92.4 x 92.4 x 120 |
| `stool_print` | `stool` flipped for printing, seat on the bed; stretchers need slicer supports | 92.4 x 92.4 x 120 |
| `stool_seat`, `stool_leg`, `stool_stretcher` | Sub-components of `stool` | 84 x 84 x 12, 23.6 x 23.6 x 114.8, 58 x 9 x 9 |

## Setup

Requires Python >= 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

Run everything from the project root. The loop for a model is build, check, render:

```bash
uv run python tools/build.py plate && uv run python tools/check.py plate && uv run python tools/render.py plate
uv run python tools/check.py assembly --bodies 2   # expected body count other than 1
open out/plate.stl                                 # preview with macOS Quick Look
```

- `tools/build.py <name>` writes `out/<name>.stl`.
- `tools/check.py <name>` verifies the mesh is watertight, has the expected body count (default 1) and prints the bbox. It exits non-zero on failure.
- `tools/render.py <name>` writes `out/<name>.png`, a 2x2 view grid (iso, top, front, side) with true-mm axes.

After changing a model, re-run the loop for it and for every model that imports it (`plate` -> `bracket` -> `assembly`; `stool_seat`, `stool_leg`, `stool_stretcher` -> `stool` -> `stool_print`).

## Layout

```
models/
  common.py     shared print constants (CLEARANCE, MIN_WALL, HOLE_COMP, BED_CHAMFER)
  plate.py      one model per file; UPPER_CASE parameters at the top, exposes `result` and `build(...)`
  bracket.py
  assembly.py
  stool_seat.py, stool_leg.py, stool_stretcher.py, stool.py, stool_print.py
tools/          build, check and render scripts
docs/           build123d API notes and print recipes
out/            generated STL/PNG output (git-ignored)
RULES.md        design planning rules (requirements, feature order, FDM rules)
CLAUDE.md       guidance for Claude Code
```

## Adding a model

1. Follow [RULES.md](RULES.md) and read [docs/build123d-notes.md](docs/build123d-notes.md) first.
2. Create `models/<name>.py` with named parameters (mm, Z up, origin at bottom center), a `build(...)` function and a `result`.
3. Run the build, check and render loop and compare `out/<name>.png` with the intended design.

## Print rules

Minimum wall 1.2 mm, fit clearance 0.2 mm per side, overhangs at most 45 degrees from vertical. Constants live in `models/common.py`, so import them rather than redefining them.
