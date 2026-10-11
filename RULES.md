# RULES.md: engineering-style design planning

Follow these steps in order **before** writing a model, and keep to them while editing. Engineering style means function and manufacturability first, appearance second. Every dimension has a reason, and every number has a name.

Toolchain and API details are in `CLAUDE.md` and `docs/build123d-notes.md`. The FDM numbers below are sized for a Bambu Lab P1/X1/A1 class printer (0.4 mm nozzle, PLA/PETG, no AMS). They are starting points. Tune them after the first test print.

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
- Default process: FDM, 0.4 mm nozzle, PLA/PETG, one material per print.
- Printer: build volume 256 x 256 x 256. Design limit per part and per plate is `BED_MAX` (240), which leaves room for a brim, the purge line and the excluded front-left corner on P1/X1.
- Pick the print orientation now, because it decides overhangs and strength.
  - The largest flat face goes on the bed. The bed face must be flat: a rod or sphere gets a flat instead of resting on a line or point.
  - Layer lines run perpendicular to the main load. Layers are weakest in tension across them.
  - Holes run along Z where possible. Vertical holes print rounder and need no support.
  - A part standing taller than 5 x its smallest bed-face width gets laid down or split.
- Supports are allowed (same material), but they are the last resort. For every overhang, try in this order:
  1. Rotate the part.
  2. Reshape it: 45 deg chamfer, teardrop or flat-roof hole, gusset down to the bed.
  3. Split it into parts (step 4).
  4. Support it, only where the support lands on and comes off a flat, hidden, non-mating face.
- Floating elements: any region whose lowest point is not on the bed or on earlier layers starts in mid-air. Each one needs one of the four answers above. List them in the `Risks` line of the plan.

## 3. Decompose
- List the printed parts. One printed part per file, modeled in its print orientation with the bed face at Z = 0. An assembly file places them. Reuse through `build(...)` rather than copying.
- Prefer identical parts (rotation, `PolarLocations`) over mirrored pairs, so one STL prints N times.
- For each part, list its features in this order: primary form, secondary forms, positioned features, details.
- Choose datums: one base face plus two axes (usually the centerlines). Dimension every feature from a datum, not from the previous feature, so tolerances do not stack up.
- Use symmetry (`mirror`) and patterns (`GridLocations`, `PolarLocations`) instead of placing repeated features by hand.

## 4. Split and join
Not every object prints as one part. Decide the split here, before any geometry.

**Split when** (any one is enough):
- No orientation fits `BED_MAX` (240).
- Sections need different orientations: a flat slab plus long slender members plus horizontal members.
- Sections need different layer directions for their loads.
- A slender member would stand taller than 5 x its width on the bed.
- Supports would land on a mating, functional or visible face, or could not be removed.

**Do not split when** a rotation, chamfer or teardrop already solves it, or when the cut would only save a little support on a hidden face. Use the fewest parts that satisfy the triggers.

**Where to cut:**
- At natural seams: where one member meets another, or at a change of section. Not across a smooth visible surface.
- So that each piece gains a large flat bed face.
- So that the joint is loaded in compression or shear, never in peel or tension across the glue line. Do not cut across the main load path.
- Not through thin walls. Around a socket keep wall >= `SOCKET_WALL` (2.4) and floor >= `SOCKET_FLOOR` (1.6).

**Default joint: glued peg-in-socket.**

| Item | Rule |
|---|---|
| Who gets what | The slender part gets longer and becomes the peg. The bulky part gets the socket. Never model a joint as two overlapping solids. |
| Diameter | `SOCKET_D = PEG_D + 2 * CLEARANCE` (0.2 per side). Always say "per side". Integral pegs >= 5 mm. |
| Depth | `JOINT_DEPTH` >= 0.5 x `PEG_D`, target 1 to 1.5 x. If the host is too thin, add a boss around the socket. |
| Stop | Exactly one: a shoulder on the peg, or the socket floor. With a shoulder stop the socket is `GLUE_GAP` (0.5) deeper than the peg. With a floor stop the peg carries a flat or groove, so glue and air can escape. |
| Lead-in | Chamfer the peg tip 0.5 to 1.0 and the socket mouth 0.5. Fillet a shouldered peg root >= 1, and let the mouth chamfer clear it. |
| Rotation | A single round peg locates position only. If orientation matters, key it: D-flat, square peg or two pegs. Make wrong assembly impossible rather than relying on labels. |
| Flat-face joints | Two halves meeting on a plane need >= 2 pegs spaced wide apart, or one non-round key. Glue alone is not a joint. |
| Socket direction | Sockets open along Z in the host's print orientation (round, support-free). Tilted sockets stay within 45 deg of Z. A horizontal socket needs a teardrop or flat roof and loses fit accuracy. No support inside a socket. |
| Peg strength | Layers should run along the peg. A peg printed standing snaps at its root in bending. For a loaded joint use a separate dowel printed lying down, a metal pin, or an M3 screw into a heat-set insert through the joint. |
| Glue | PLA/PETG: CA (medium or gel) or two-part epoxy. No solvent cement. Dry-fit first. |
| Coupon | For a new peg diameter or filament, print a short peg and a socket slice at 0.15 / 0.2 / 0.3 per side before the full plate. |
| Look-alikes | Parts that look the same but are not interchangeable get an engraved mark on the mating face. |

**Modeling a multi-part object:**
- One side owns the joint dimensions and the other derives them: `SOCKET_D = <peg part>.DIAMETER + 2 * CLEARANCE`.
- The assembled model is a `Compound` of the parts in their final position. Keep a `CLEARANCE` (0.2) gap at the stop face too, so the bodies do not fuse in the STL. Check it with `--bodies N`.
- The plate model holds every part in print orientation at Z = 0, laid out with `pack(parts, padding=5, align_z=True)`. Check it with `--bodies N` and bbox <= `BED_MAX`. If it does not fit, make a second plate model.

## 5. Parameters
- Every number is a named UPPER_CASE constant at the top of the file.
- Derived values are expressions, never retyped numbers: `SOCKET_D = PEG_D + 2 * CLEARANCE`.
- Import the shared print constants from `models.common` (`CLEARANCE`, `MIN_WALL`, `HOLE_COMP`, `BED_CHAMFER`, `BED_MAX`, `GLUE_GAP`, `SOCKET_WALL`, `SOCKET_FLOOR`). Do not redefine them.
- Dependent models read the other model's constants (`<other>.THICKNESS`), so a change propagates.

## 6. Feature order
1. **Base solid** from the simplest sketch that gives the primary form (box, extrude, revolve).
2. **Secondary forms**: bosses, ribs, pockets, steps.
3. **Positioned features**: holes, slots, cutouts, placed with `Locations`/`GridLocations`/`PolarLocations`.
4. **Details last**: fillet first, then chamfer.

- Reference the base solid, not geometry that a later fillet will change.
- Keep each sketch simple. Two simple sketches beat one complicated one.
- Select by property, not by index: `faces() >> Axis.Z`, `edges().filter_by(GeomType.CIRCLE)`.
- Add only what the requirements ask for. No decorative features.

## 7. FDM rules
| Topic | Rule |
|---|---|
| Size | Every part and every plate <= `BED_MAX` (240) on each axis, in print orientation. |
| Wall | >= `MIN_WALL` (1.2). Default 1.6. Load-bearing 2.4 to 3.2. Use multiples of 0.4. |
| Smallest feature | >= 1 mm. No knife edges or thin spikes. |
| Overhang | Design to <= 45 deg from vertical. 45 to 60 deg is acceptable on hidden faces. Above 60: chamfer, teardrop hole, split or support (step 2 order). |
| Bridge | <= 20 mm unsupported span, straight, between two supports. <= 10 mm where the underside is dimensioned or visible. |
| Supports | Same material only. A supported face comes out rough and about 0.2 off, so never a mating, functional or visible face. Supports must be reachable for removal: no enclosed cavities. |
| Slender | Standing height <= 5 x the smallest bed-face width. Cross-sections under 5 x 5 high above the bed overheat at this printer's speeds: thicken them or lay the part down. |
| Warp | Bed-face corners R >= 3 on parts longer than 150 mm. Keep the wall thickness uniform. |
| Fit | Sliding or glued: `CLEARANCE` (0.2) per side. Free-moving: 0.3. Press: 0.1, and only after a coupon. |
| Holes | Vertical holes print slightly small: size them diameter + `HOLE_COMP` (0.2). Horizontal holes above 6 mm get a teardrop or flat roof. A counterbore facing the bed needs a sacrificial layer, or goes on the top side. M3 clearance 3.4. M3 heat-set pilot 4.0 with boss OD >= 6.5. No printed threads below M6: use a heat-set insert. Remember `Hole(radius)` takes a radius. |
| Pins, columns | >= 2 to 3 mm diameter, with a fillet at the base. Pins under 5 mm are weak, so use a metal pin in a hole. |
| Corners | Fillet inside corners (stress). Chamfer `BED_CHAMFER` (0.4) to 1.0 on edges touching the bed (elephant foot). Fillet radius about the wall thickness. |
| Text | Emboss 0.8 wide x 0.5 high. Engrave 1.0 wide x 0.5 deep. |
| Assemblies | Keep a gap >= `CLEARANCE` (0.2) between parts, or they fuse into one body in the STL. Joints follow step 4. |

Fit vocabulary (ISO 286, hole-basis): clearance fit = always a gap, transition = gap or overlap, interference = always an overlap. Give tight tolerances only to functional interfaces, never to the rest of the part.

## 8. Plan before code
Write this block in the reply (or a comment at the top of the model) before the first line of code:

```
Function:      <one sentence>
Printer:       256^3, BED_MAX 240, no AMS
Process:       FDM, <orientation per part>
Parameters:    <table from step 1>
Parts:         <name: features in order>
Split:         <trigger, cut location>                                  (or "none")
Joints:        <peg D, depth, clearance per side, stop, key>            (or "none")
Plates:        <part x count, orientation, supports: none | where and why>
Datums:        <base face, axes>
Expect:        bodies=<n> per plate, bbox=<x> x <y> x <z>, walls >= <n>
Risks:         <overhangs, floating elements, thin walls, tight fits>
```

The `Expect` line is what step 9 checks against.

## 9. Verify
- Run build, check and render from `CLAUDE.md` for the model and every model that imports it.
- Compare the result to the `Expect` line and the requirements table, not to "looks fine":
  - watertight and body count (`--bodies N` when it is not 1)
  - bbox equals the values derived from the parameters, and is <= `BED_MAX` (240) in print orientation
  - walls >= `MIN_WALL`, and no overhang above 45 deg unless intended
  - assembly gaps >= `CLEARANCE`
- For a multi-part object also check:
  - the assembled model and the plate model both report bodies = part count
  - socket wall >= 2.4 and floor >= 1.6, socket axis within 45 deg of Z on the plate
  - the supports actually needed match the `Plates` line
- Open `out/<name>.png` and look at every view.
- On failure read the error, find the single cause, change that one thing, rebuild. Do not rewrite the model.

## 10. Anti-patterns
**Modeling:**
- Magic numbers in the middle of the code.
- Dimensioning from an edge that a later fillet or chamfer removes.
- Index-based selectors (`edges()[3]`).
- Chaining `.moved()` in builder mode.
- Touching parts in an assembly.
- Moving a hole to fix a fit instead of changing the parameter.
- Fixing a failed build by deleting the check.
- Skipping the plan block because "it is a small part".

**Printing (what not to do):**
- One fused body with members pointing in three directions, left to slicer supports. Split it.
- A feature that starts in mid-air with no plan for it.
- Supports inside sockets or holes, on mating faces, or in cavities they cannot leave.
- A flat butt joint held by glue only. Add pegs or a key.
- A joint modeled as two overlapping solids instead of a peg and a socket.
- Zero-clearance pegs. Trapped glue stops the peg from seating.
- A clearance number without "per side".
- Two stops in one direction (shoulder and floor both touching).
- A single round peg where orientation matters.
- An integral peg or clip printed standing, with layer lines across its root.
- A cut through a thin wall, across the load path, or across a smooth visible face.
- Mirrored look-alike parts with no key or mark.
- Printing a full plate of joints before a fit coupon.
- Walls thinner than the nozzle (0.4), or not a multiple of it. The slicer drops them or leaves gaps.
- Sharp 90 deg corners on the bed face of a large part (they lift), and sharp inside corners (they crack).
- A tall thin part standing on a small footprint.
- A rod or sphere resting on the bed on a line or point.
- Large horizontal holes left round. Counterbores facing the bed.
- Printed threads below M6. Screws driven into thin walls without a boss.
- The main load pulling layers apart.
- A part that fills the bed to the last millimetre.

## Sources
- Onshape: [What makes a parametric modeler tick](https://www.onshape.com/en/blog/what-makes-a-parametric-modeler-tick), [Mastering 3D Modeling](https://onshape.com/global-assets/ebooks/mastering-3d-modeling/mastering-3d-modeling-ebook.pdf) (design intent, feature order, stable references)
- FDM guides: [Wevolver](https://www.wevolver.com/article/fdm-3d-printing-design-tips-best-practices-and-techniques-for-stronger-prints), [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/), [GrabCAD](https://grabcad.com/tutorials/3d-printing-design-guidelines) (walls, overhangs, bridges, holes, clearance)
- [Heat-set insert bosses](https://www.sovol3d.com/blogs/news/3d-printing-with-heat-set-inserts-design-strong-screw-bosses-that-last), [Engineering fits](https://jlccnc.com/blog/engineering-fits) (ISO 286)
- [Text2CAD-Bench](https://arxiv.org/pdf/2605.18430): decomposition, explicit dimension extraction, structured intermediate spec, error-feedback loop
- Splitting and joining: [Digi-Key](https://www.digikey.com/en/maker/blogs/2024/how-to-split-and-join-large-3d-prints), [Sovol: keys, glue, assembly](https://www.sovol3d.com/blogs/news/3d-printing-large-models-in-multiple-pieces-keys-glue-and-assembly-tips), [Sovol: splitting for FDM](https://www.sovol3d.com/blogs/news/how-to-split-large-3d-models), [JLC3DP](https://jlc3dp.com/blog/how-to-split-large-3d-prints-for-better-quality-and-asembly), [University of Melbourne](https://ms-kb.msd.unimelb.edu.au/next-lab/3d-printing/key-techniques/split-models-rhino-3d-and-physical-joining), [Bambu Studio cut tool](https://wiki.bambulab.com/en/software/bambu-studio/cut-tool) (cut placement, joint types, glue, clearance)
- What not to do: [Craftcloud](https://blog.craftcloud3d.com/7-common-3d-modeling-mistakes-that-lead-to-print-failure/), [Markforged: warping](https://markforged.com/blog/3d-printed-part-warping), [JLC3DP design guideline](https://jlc3dp.com/help/article/3d-printing-design-guideline), [SelfCAD: threads](https://www.selfcad.com/blog/3d-printing-threads-and-screws-key-settings-and-tips), [Bambu forum: tall thin parts](https://forum.bambulab.com/t/how-to-fix-layer-wobble-for-tall-and-skinny-parts/56301)
- Printer class (measured on P1S, X1C, A1): [Fab Academy Charlotte](https://fabacademy.org/2026/labs/charlotte/assignments/week05-Adult/), [MIT group test](https://fab.cba.mit.edu/classes/863.25/Architecture/week-3.html), [UAL CCI: clearance per side](https://wiki.cci.arts.ac.uk/books/digital-fabrication-lab/page/design-the-clearance-and-tolerance) (overhang, bridge, clearance)
