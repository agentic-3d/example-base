"""Usage: uv run python tools/check.py <model> [--bodies N]   (N defaults to 1; run from the project root)

Base-owned: edit in agentic-3d/example-base, then `make sync-base`.

Fails (exit 1) unless the mesh is watertight and has N bodies. It also reads the `Expect:` line of the model's header comment
(models/<name>.py, a dotted name `a.b` is models/a/b.py): the bbox must match `bbox X x Y x Z` within 0.1 mm, and when the line
names BED_MAX no extent may exceed it. A missing or unparsable Expect line is only a warning.
"""
import argparse
import re
import sys
from pathlib import Path

import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, so `models` imports work
BBOX_TOL = 0.1  # mm, Expect values are rounded to 0.01 to 0.1

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--bodies", type=int, default=1, help="expected number of bodies")
args = ap.parse_args()

mesh = trimesh.load(f"out/{args.name}.stl", force="mesh")
bodies = len(mesh.split(only_watertight=False))
x, y, z = mesh.extents

print(f"bbox (mm): {x:.3f} x {y:.3f} x {z:.3f}")
print(f"volume (mm3): {mesh.volume:.2f}")
print(f"watertight: {mesh.is_watertight}")
print(f"bodies: {bodies}")

ok = mesh.is_watertight and bodies == args.bodies
src = Path("models", *args.name.split(".")).with_suffix(".py")
line = next((l for l in src.read_text().splitlines() if "Expect:" in l), None) if src.exists() else None
if line is None:
    print(f"expect: no `Expect:` line in {src}")
else:
    line = line.split("Expect:", 1)[1]
    m = re.search(r"bbox\s+([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)", line)
    if m:
        want = [float(v) for v in m.groups()]
        off = [f"{got:.2f} instead of {w}" for got, w in zip((x, y, z), want) if abs(got - w) > BBOX_TOL]
        print(f"expect bbox: {'ok' if not off else 'MISMATCH, ' + ', '.join(off)}")
        ok &= not off
    else:
        print("expect bbox: not parsable, skipped")
    m = re.search(r"bodies\s*=\s*(\d+)", line)
    if m and int(m.group(1)) != args.bodies:
        print(f"expect bodies: Expect line says {m.group(1)}, --bodies is {args.bodies} (Makefile BODIES_ and the header differ)")
    if "BED_MAX" in line:
        from models.common import BED_MAX

        over = [f"{v:.2f}" for v in (x, y, z) if v > BED_MAX]
        print(f"bed: {'within BED_MAX ' + str(BED_MAX) if not over else 'OVER BED_MAX ' + str(BED_MAX) + ': ' + ', '.join(over)}")
        ok &= not over

sys.exit(0 if ok else 1)
