# example-base

Template repository for agentic parametric CAD: an AI coding agent (Claude Code) plans and writes [build123d](https://build123d.readthedocs.io/) models (Python, OpenCascade), then verifies them with a build, check and render loop. Parts are mm-precise and exported as STL for FDM 3D printing (0.4 mm nozzle, PLA/PETG).

The template is deliberately minimal. It carries the rules, the tooling and three small example models. A real project is created from it and replaces the examples.

Derived example: [example-stool](https://github.com/agentic-3d/example-stool), a scale-model stool split into glued printed parts.

## How it works

Claude Code writes and edits the model script. The `make` loop (Python runner scripts) builds, checks and renders it, and Claude reads the results and iterates until the part matches the design.

```mermaid
flowchart LR
    you(["You: describe the part"]) --> claude

    claude["<b>Claude Code</b><br/>follows RULES.md + CLAUDE.md<br/>reads docs/build123d-notes.md"]
    model["<b>models/&lt;name&gt;.py</b><br/>build123d model<br/>UPPER_CASE params, build(), result"]

    subgraph loop ["make &lt;name&gt; (Python runner scripts)"]
        direction TB
        build["<b>tools/build.py</b><br/>import model, export STL"]
        check["<b>tools/check.py</b><br/>watertight, body count, bbox"]
        render["<b>tools/render.py</b><br/>2x2 view grid (iso, top, front, side)"]
        build --> check --> render
    end

    stl[("out/&lt;name&gt;.stl")]
    png[("out/&lt;name&gt;.png")]
    print(["Quick Look, slicer, 3D print"])

    claude -- "writes / edits" --> model
    model -- "result" --> build
    build --> stl
    render --> png
    stl --> print
    check -. "exit code + metrics" .-> claude
    png -. "Claude views image,<br/>compares with design" .-> claude
```

Solid arrows are data flow, dashed arrows are feedback to Claude. `models/*` is the only thing Claude edits; `tools/` and `make` are fixed runners.

## What you get

| File | Purpose |
|---|---|
| `RULES.md` | Design planning rules for the agent: requirements, orientation, splitting and joints, feature order, FDM rules, plan block, verification |
| `CLAUDE.md` | Guidance for Claude Code: commands, architecture, gotchas, how the template inheritance works |
| `Makefile` | Builds, checks and renders every model, and syncs the two files above from this repo |
| `tools/` | `build.py` (STL export), `check.py` (watertight, body count, bbox), `render.py` (2x2 view grid as PNG) |
| `docs/build123d-notes.md` | Verified build123d API notes and print recipes |
| `models/` | `common.py` (shared print constants) and the example models |

## Start a project from this template

1. Create the repository: "Use this template" on GitHub, or

   ```bash
   gh repo create my-part --template agentic-3d/example-base --clone
   ```

2. Install the dependencies (Python >= 3.12 and [uv](https://docs.astral.sh/uv/)) and build the examples once:

   ```bash
   uv sync
   ```

   ```bash
   make
   ```

3. Delete the example models (`models/plate.py`, `models/bracket.py`, `models/assembly.py`) and their files in `out/`, add your own and list them in `MODELS` in the `Makefile`.
4. Rewrite `README.md` for your project. Leave `CLAUDE.md` and `RULES.md` untouched.

## Who owns which file

| Files | Owner | In a derived project |
|---|---|---|
| `CLAUDE.md`, `RULES.md` | base | overwritten by `make sync-base`, never edited locally |
| `README.md`, `Makefile`, `models/*` | project | all project-specific facts live here |
| `tools/`, `docs/`, `models/common.py`, `pyproject.toml` | project | start as copies of base, may diverge, not synced |

To pull the current rules into a derived project:

```bash
make sync-base
```

It downloads both files from the `main` branch of this repository with `curl`. Review `git diff` before committing. A rule that should change is changed here first, then synced.

## Example models

| Model | Description | Expected bbox (mm) |
|---|---|---|
| `plate` | Mounting plate with four corner holes | 60 x 40 x 10 |
| `bracket` | L-bracket with filleted joint and rectangular wall hole; reuses `plate` for its base | 40 x 30 x 29 |
| `assembly` | Exploded view of `plate` and `bracket` (2 bodies, gap between them) | 60 x 40 x 44 |

They show the three patterns a project needs: a parametric part with `build(...)`, a part that reuses another one, and a multi-body compound.

![assembly](out/assembly.png)

## Usage

Run everything from the project root.

```bash
make                # build, check and render every model
make plate          # one model
make clean          # remove out/ (rebuild with make before committing)
open out/plate.stl  # preview with macOS Quick Look
```

`make <name>` runs the loop for one model:

- `tools/build.py <name>` writes `out/<name>.stl`.
- `tools/check.py <name> [--bodies N]` verifies the mesh is watertight, has the expected body count (default 1) and prints the bbox. It exits non-zero on failure.
- `tools/render.py <name>` writes `out/<name>.png`, a 2x2 view grid (iso, top, front, side) with true-mm axes.

After changing a model, run `make`, so every model that imports it is rebuilt too (`plate` -> `bracket` -> `assembly`). `out/` is committed: commit the regenerated STL and PNG files together with the model.

## Layout

```
models/
  common.py     shared print constants (CLEARANCE, MIN_WALL, HOLE_COMP, BED_CHAMFER, BED_MAX, ...)
  plate.py      one model per file; UPPER_CASE parameters at the top, exposes `result` and `build(...)`
  bracket.py
  assembly.py
tools/          build, check and render scripts
docs/           build123d API notes and print recipes
out/            generated STL/PNG output (committed, so GitHub shows the results)
Makefile        model list and targets
RULES.md        design planning rules (base-owned)
CLAUDE.md       guidance for Claude Code (base-owned)
```

## Adding a model

1. Follow [RULES.md](RULES.md) and read [docs/build123d-notes.md](docs/build123d-notes.md) first.
2. Create `models/<name>.py` with named parameters (mm, Z up, origin at bottom center), a `build(...)` function and a `result`.
3. Add `<name>` to `MODELS` in the `Makefile`, after the models it imports. Set `BODIES_<name>` if it is a compound of several parts.
4. Run `make <name>` and compare `out/<name>.png` with the intended design.

## Print rules

Minimum wall 1.2 mm, fit clearance 0.2 mm per side, overhangs at most 45 degrees from vertical. Constants live in `models/common.py`, so import them rather than redefining them.
