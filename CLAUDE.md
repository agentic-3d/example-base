# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Parametric CAD with build123d (Python, OpenCascade). The output is mm-precise parts exported as STL for 3D printing, previewed with macOS Quick Look (`open out/<name>.stl`). There is no STEP export, no test suite and no linter. Verification is the build/check/render loop below.

Before writing a model, follow `RULES.md` (requirements, feature order, FDM rules, plan block). API details are in `docs/build123d-notes.md`.

## Commands
Always run from the project root (`models` imports and the `out/` paths are cwd-relative). Dependencies are managed with `uv`.

```bash
uv run python tools/build.py <name> && uv run python tools/check.py <name> && uv run python tools/render.py <name>
uv run python tools/check.py assembly --bodies 2     # expected body count other than 1
```

After changing a model, run the loop for it and for every model that imports it (`plate` is imported by `bracket`, and both are imported by `assembly`; `stool_seat`, `stool_leg` and `stool_stretcher` are imported by `stool`, which is imported by `stool_print`). Then view `out/<name>.png` and compare it with the intended design.

Success criteria: watertight = True, bodies = the intended count (default 1), bbox matches the expected size. `check.py` exits non-zero on failure.

## Architecture
- `models/<name>.py`: one model per file. Dimensions are named UPPER_CASE parameters at the top (mm, Z up). The file exposes `result`, and also `build(...)` with those constants as defaults when other models should reuse it with different dimensions. Models contain no export code.
- `models/common.py`: shared print constants (`CLEARANCE = 0.2`, `MIN_WALL = 1.2`, `HOLE_COMP = 0.2`, `BED_CHAMFER = 0.4`). Import these rather than redefining them. Every model has its origin at the bottom center.
- Models compose by importing each other. `bracket.py` calls `insert(plate.build(...))` for its base flange, and `assembly.py` reads `plate.THICKNESS` to position the parts, so changing a plate parameter propagates.
- `models/plaque.py` raises a stepped brightness relief of `assets/photo.webp` and text on a plate. It flood-fills the near-white background from the image border for the figure mask, splits the figure into `LEVELS` equal-area brightness bands, traces each band with `contourpy`, and extrudes one `STEP` per level. Tuning knobs are `BG_MIN`, `BLUR_PX`, `TONE_BLUR_PX`, `LEVELS` and `SIMPLIFY`.
- `tools/build.py <name>` imports `models.<name>` dynamically (it puts the project root on `sys.path`) and writes `out/<name>.stl` with `tolerance=0.01, angular_tolerance=0.1`. `out/` is generated and git-ignored.
- `tools/check.py` loads the STL with trimesh and counts bodies with `mesh.split(only_watertight=False)`.
- `tools/render.py` is a numpy z-buffer orthographic rasterizer shown through matplotlib (Agg, no GPU). It draws a 2x2 grid (iso, top, front, side) with true-mm axes. It does not use matplotlib's 3D axes, because those mis-sort large triangles and produced visible artifacts.
- `docs/build123d-notes.md`: verified API notes, selector semantics and print recipes. Read it before writing build123d code. When you need the upstream docs, fetch the raw page source (`https://build123d.readthedocs.io/en/latest/_sources/<page>.rst.txt`), not the rendered HTML.

## Gotchas
- Printing rules: minimum wall 1.2 mm, fit clearance 0.2 mm, avoid overhangs above 45 degrees where possible.
- Check the build123d API against the installed version (`inspect.signature`, `help()`) instead of relying on memory, because the API changes between releases. The installed version is 0.13.0. For example, `add()` is deprecated in favor of `insert()`.
- `Hole(radius)` takes a radius, not a diameter.
- Builder-mode objects add themselves on creation, so use `Locations(...)` for placement rather than chaining `.moved()`.
- Multi-part files such as `assembly.py` use `Compound([...])` and must keep a gap between parts. Parts that touch can fuse into one body in the STL, and `check.py` would then report the wrong body count.
- `plate.build(corner_r=0)` means square corners (the fillet is skipped). `bracket.py` relies on this to round only its two front corners.
