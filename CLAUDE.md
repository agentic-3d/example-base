# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Parametric CAD with build123d (Python, OpenCascade). The output is mm-precise parts exported as STL for 3D printing, previewed with macOS Quick Look (`open out/<name>.stl`). There is no STEP export, no test suite and no linter. Verification is the build/check/render loop below.

Before writing a model, follow `RULES.md` (requirements, feature order, FDM rules, plan block). API details are in `docs/build123d-notes.md`.

## Template and inheritance
This file and `RULES.md` come from the base template [agentic-3d/example-base](https://github.com/agentic-3d/example-base). They are generic on purpose: they name no model of the project they sit in.

| Files | Owner | In a derived project |
|---|---|---|
| `CLAUDE.md`, `RULES.md` | base | overwritten by `make sync-base`, never edited locally |
| `README.md`, `Makefile`, `models/*` | project | all project-specific facts live here |
| `tools/`, `docs/`, `models/common.py`, `pyproject.toml` | project | start as copies of base, may diverge, not synced |

- Project facts are not in this file. The model list, its order and the body counts are in `Makefile`. The model table is in `README.md`. Each model states its expected result in the `Expect:` line of its header comment. Read those first.
- Start a project: "Use this template" on GitHub, or `gh repo create <name> --template agentic-3d/example-base --clone`. Then run `uv sync`, delete the example models (`plate`, `bracket`, `assembly`) and their `out/` files, set `MODELS` in the `Makefile` and rewrite `README.md` for the project.
- Update a project: `make sync-base` downloads `CLAUDE.md` and `RULES.md` from the base `main` branch with `curl`. Review `git diff` before committing, because these files steer the agent.
- A rule or instruction that should change goes to the base repo first, then gets synced. A local edit is lost at the next sync.
- If a synced `RULES.md` names a constant that `models/common.py` does not define, add it to `models/common.py`.

## Commands
Always run from the project root (`models` imports and the `out/` paths are cwd-relative). Dependencies are managed with `uv`.

```bash
make                # build, check and render every model in MODELS
make <name>         # one model
make clean          # remove out/ (it is committed, so rebuild with `make` before committing)
make sync-base      # refresh CLAUDE.md and RULES.md from the base template
```

The loop behind `make <name>`, for one-off runs:

```bash
uv run python tools/build.py <name> && uv run python tools/check.py <name> && uv run python tools/render.py <name>
uv run python tools/check.py <name> --bodies 2     # expected body count other than 1
```

After changing a model, run `make` (it covers every model that imports the changed one). Then view `out/<name>.png` and compare it with the intended design. Commit the regenerated `out/` files together with the model change, so the committed STL and PNG never lag behind the source.

Success criteria: watertight = True, bodies = the intended count (default 1), bbox matches the `Expect:` line. `check.py` exits non-zero on failure, which stops `make`.

## Makefile
The `Makefile` is project-owned and is the list of what the project builds. Keep it in this shape:

```make
# Models bottom-up: a model comes after everything it imports.
MODELS := plate bracket assembly
# Expected body count where it is not 1.
BODIES_assembly := 2

BASE_REPO := agentic-3d/example-base
BASE_URL := https://raw.githubusercontent.com/$(BASE_REPO)/main
BASE_FILES := CLAUDE.md RULES.md

PY := uv run python

.PHONY: all clean sync-base $(MODELS)

all: $(MODELS)

$(MODELS):
	$(PY) tools/build.py $@
	$(PY) tools/check.py $@ --bodies $(or $(BODIES_$@),1)
	$(PY) tools/render.py $@

clean:
	rm -rf out

sync-base:
	@case "$$(git remote get-url origin 2>/dev/null)" in *$(BASE_REPO)*) echo "this is the base repo, nothing to sync"; exit 1;; esac
	@for f in $(BASE_FILES); do \
		curl -fsSL $(BASE_URL)/$$f -o $$f.tmp && mv $$f.tmp $$f && echo "synced $$f" || { rm -f $$f.tmp; echo "failed $$f"; exit 1; }; \
	done
	@git status --short $(BASE_FILES)
```

- `MODELS` has one entry per `models/<name>.py` that exposes `result`. Order it bottom-up, so the first failure is the root cause and not a dependent.
- Modules without a `result` (`common.py`, parameter-only modules) are not listed.
- A model whose `result` is a `Compound` of N separate parts gets `BODIES_<name> := N`.
- When you add, rename or delete a model, update `MODELS`, the `BODIES_` lines and the model table in `README.md` in the same change. Delete the `out/` files of a removed or renamed model.
- Recipe lines are indented with a tab. The file must work with GNU Make 3.81 (the macOS default).
- Only `MODELS` and the `BODIES_` lines differ between projects. Leave the targets alone.

## Architecture
- `models/<name>.py`: one model per file. Dimensions are named UPPER_CASE parameters at the top (mm, Z up). The file exposes `result`, and also `build(...)` with those constants as defaults when other models should reuse it with different dimensions. Models contain no export code.
- `models/common.py`: shared print constants (`CLEARANCE = 0.2`, `MIN_WALL = 1.2`, `HOLE_COMP = 0.2`, `BED_CHAMFER = 0.4`, `BED_MAX = 240`, `GLUE_GAP = 0.5`, `SOCKET_WALL = 2.4`, `SOCKET_FLOOR = 1.6`). Import these rather than redefining them. Every model has its origin at the bottom center.
- Models compose by importing each other: `insert(<other>.build(...))` reuses geometry with different dimensions, and reading `<other>.THICKNESS` positions parts, so a parameter change propagates. In the base template `bracket` builds its flange from `plate`, and `assembly` places both.
- A parameter set shared by several models goes into a module without a `result` (for example `models/<project>_params.py`), which every part imports. This avoids circular imports between a part and its assembly.
- `tools/build.py <name>` imports `models.<name>` dynamically (it puts the project root on `sys.path`) and writes `out/<name>.stl` with `tolerance=0.01, angular_tolerance=0.1`. `out/` is generated but committed (STL and PNG), so the results are visible on GitHub.
- `tools/check.py` loads the STL with trimesh and counts bodies with `mesh.split(only_watertight=False)`. It does not detect parts that overlap: overlapping solids still export as separate shells. Check a mating pair with `(a & b).volume`, which must be 0.
- `tools/render.py` is a numpy z-buffer orthographic rasterizer shown through matplotlib (Agg, no GPU). It draws a 2x2 grid (iso, top, front, side) with true-mm axes. It does not use matplotlib's 3D axes, because those mis-sort large triangles and produced visible artifacts.
- `docs/build123d-notes.md`: verified API notes, selector semantics and print recipes. Read it before writing build123d code. When you need the upstream docs, fetch the raw page source (`https://build123d.readthedocs.io/en/latest/_sources/<page>.rst.txt`), not the rendered HTML.

## Gotchas
- Printing rules: minimum wall 1.2 mm, fit clearance 0.2 mm per side, avoid overhangs above 45 degrees where possible.
- Check the build123d API against the installed version (`inspect.signature`, `help()`) instead of relying on memory, because the API changes between releases. The installed version is 0.13.0. For example, `add()` is deprecated in favor of `insert()`.
- `Hole(radius)` takes a radius, not a diameter.
- Builder-mode objects add themselves on creation, so use `Locations(...)` for placement rather than chaining `.moved()`.
- Multi-part models use `Compound([...])` and must keep a gap between parts. Parts that touch can fuse into one body in the STL, and `check.py` would then report the wrong body count.
- A `build()` argument of 0 can mean "skip this feature" (`corner_r=0` for square corners, `bed_chamfer=0` to leave the chamfer to the caller). Say so in a comment at the parameter.
