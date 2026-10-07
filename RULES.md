# RULES.md: engineering-style design planning

Follow these steps in order **before** writing a model, and keep to them while editing. Engineering style means function and manufacturability first, appearance second. Every dimension has a reason, and every number has a name.

Toolchain and API details are in `CLAUDE.md` and `docs/build123d-notes.md`. FDM numbers below are public-guide starting points. Tune them after the first test print.

## 1. Requirements (no code yet)
- State the function in one sentence.
- List the interfaces: mating parts, screws, shafts, other models in `models/`.
- State the load direction and the environment (heat, moisture, outdoor) if they matter.
- Extract every number from the request into a table with a status:

  | Name | Value | Status |
  |---|---|---|
  | `PLATE_W` | 40 | given |
  | `HOLE_D` | 3.4 | derived (M3 clearance) |
  | `THICKNESS` | 4 | assumed |

- Statuses are *given*, *derived* or *assumed*. Ask the user about anything missing that changes the design. If the answer is cheap to change later, assume it and say so. Never invent silently.
- Units are mm, Z up. Put the origin on a meaningful datum (bottom center or the main mounting face).

## 2. Process and orientation
- Default process: FDM, 0.4 mm nozzle, PLA/PETG.
- Pick the print orientation now, because it decides overhangs and strength.
  - The largest flat face goes on the bed.
  - Layer lines run perpendicular to the main load. Layers are weakest in tension across them.
  - Holes run along Z where possible. Vertical holes print rounder and need no support.
  - Parts that cannot print support-free get split into separate parts.

## 3. Decompose
- List the parts. One part per file. Reuse through `build(...)` rather than copying.
- For each part, list its features in this order: primary form, secondary forms, positioned features, details.
- Choose datums: one base face plus two axes (usually the centerlines). Dimension every feature from a datum, not from the previous feature, so tolerances do not stack up.
- Use symmetry (`mirror`) and patterns (`GridLocations`, `PolarLocations`) instead of placing repeated features by hand.

## 4. Parameters
- Every number is a named UPPER_CASE constant at the top of the file.
- Derived values are expressions, never retyped numbers: `SOCKET_D = PEG_D + 2 * CLEARANCE`.
- Import `CLEARANCE` and `MIN_WALL` from `models.common`. Do not redefine them.
- Dependent models read the other model's constants (`plate.THICKNESS`), so a change propagates.

## 5. Feature order
1. **Base solid** from the simplest sketch that gives the primary form (box, extrude, revolve).
2. **Secondary forms**: bosses, ribs, pockets, steps.
3. **Positioned features**: holes, slots, cutouts, placed with `Locations`/`GridLocations`/`PolarLocations`.
4. **Details last**: fillet first, then chamfer.

- Reference the base solid, not geometry that a later fillet will change.
- Keep each sketch simple. Two simple sketches beat one complicated one.
- Select by property, not by index: `faces() >> Axis.Z`, `edges().filter_by(GeomType.CIRCLE)`.
- Add only what the requirements ask for. No decorative features.

## 6. FDM rules
| Topic | Rule |
|---|---|
| Wall | >= `MIN_WALL` (1.2). Default 1.6. Load-bearing 2.4 to 3.2. Use multiples of 0.4. |
| Smallest feature | >= 1 mm. No knife edges or thin spikes. |
| Overhang | <= 45 deg from vertical. Otherwise chamfer, use a teardrop hole, or split the part. |
| Bridge | <= 5 mm unsupported span. |
| Fit | Sliding or press: `CLEARANCE` (0.2) per side. Loose or moving parts: 0.3 to 0.4. Interference needs flex, about 0.5, and only on purpose. |
| Holes | Vertical holes print slightly small: size them diameter + `HOLE_COMP` (0.2). M3 clearance 3.4. M3 heat-set pilot 4.0 with boss OD >= 6.5. Remember `Hole(radius)` takes a radius. |
| Pins, columns | >= 2 to 3 mm diameter, with a fillet at the base. Pins under 5 mm are weak, so use a metal pin in a hole. |
| Corners | Fillet inside corners (stress). Chamfer `BED_CHAMFER` (0.4) to 1.0 on edges touching the bed (elephant foot). Fillet radius about the wall thickness. |
| Text | Emboss 0.8 wide x 0.5 high. Engrave 1.0 wide x 0.5 deep. |
| Assemblies | Keep a gap >= `CLEARANCE` between parts, or they fuse into one body in the STL. |

Fit vocabulary (ISO 286, hole-basis): clearance fit = always a gap, transition = gap or overlap, interference = always an overlap. Give tight tolerances only to functional interfaces, never to the rest of the part.

## 7. Plan before code
Write this block in the reply (or a comment at the top of the model) before the first line of code:

```
Function:      <one sentence>
Process:       FDM, <orientation>
Parameters:    <table from step 1>
Parts:         <name: features in order>
Datums:        <base face, axes>
Expect:        bodies=<n>, bbox=<x> x <y> x <z>, walls >= <n>
Risks:         <overhangs, thin walls, tight fits>
```

The `Expect` line is what step 8 checks against.

## 8. Verify
- Run build, check and render from `CLAUDE.md` for the model and every model that imports it.
- Compare the result to the `Expect` line and the requirements table, not to "looks fine":
  - watertight and body count (`--bodies N` when it is not 1)
  - bbox equals the values derived from the parameters
  - walls >= `MIN_WALL`, and no overhang above 45 deg unless intended
  - assembly gaps >= `CLEARANCE`
- Open `out/<name>.png` and look at every view.
- On failure read the error, find the single cause, change that one thing, rebuild. Do not rewrite the model.

## 9. Anti-patterns
- Magic numbers in the middle of the code.
- Dimensioning from an edge that a later fillet or chamfer removes.
- Index-based selectors (`edges()[3]`).
- Chaining `.moved()` in builder mode.
- Touching parts in an assembly.
- Moving a hole to fix a fit instead of changing the parameter.
- Fixing a failed build by deleting the check.
- Skipping the plan block because "it is a small part".

## Sources
- Onshape: [What makes a parametric modeler tick](https://www.onshape.com/en/blog/what-makes-a-parametric-modeler-tick), [Mastering 3D Modeling](https://onshape.com/global-assets/ebooks/mastering-3d-modeling/mastering-3d-modeling-ebook.pdf) (design intent, feature order, stable references)
- FDM guides: [Wevolver](https://www.wevolver.com/article/fdm-3d-printing-design-tips-best-practices-and-techniques-for-stronger-prints), [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/), [GrabCAD](https://grabcad.com/tutorials/3d-printing-design-guidelines) (walls, overhangs, bridges, holes, clearance)
- [Heat-set insert bosses](https://www.sovol3d.com/blogs/news/3d-printing-with-heat-set-inserts-design-strong-screw-bosses-that-last), [Engineering fits](https://jlccnc.com/blog/engineering-fits) (ISO 286)
- [Text2CAD-Bench](https://arxiv.org/pdf/2605.18430): decomposition, explicit dimension extraction, structured intermediate spec, error-feedback loop
