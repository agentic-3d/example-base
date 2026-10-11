"""Usage: uv run python tools/overlaps.py <model> [--near MM]   (run from the project root)

Base-owned: edit in agentic-3d/example-base, then `make sync-base`.

Finds solids of a model's `result` that overlap each other. check.py does not see them: overlapping solids still export as
separate shells. Prints every pair with an intersection volume above 1e-6 mm3 and exits non-zero if there is one.
--near MM also lists the pairs that do not overlap but are closer than MM (a joint gap). A gap below CLEARANCE (models/common.py,
the fit clearance per side) is marked `tight` and also fails the run.
"""
import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, so `models` imports work

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--near", type=float, default=0.0, help="also list pairs closer than this many mm")
a = ap.parse_args()

solids = importlib.import_module(f"models.{a.model}").result.solids()
boxes = [(b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z) for b in (s.bounding_box() for s in solids)]  # lo xyz, hi xyz
min_gap = importlib.import_module("models.common").CLEARANCE - 0.01  # below this a gap is tighter than the fit rule
overlap = tight = near = 0
for i in range(len(solids)):
    for j in range(i + 1, len(solids)):
        p, q = boxes[i], boxes[j]
        if any(p[k + 3] + a.near < q[k] or q[k + 3] + a.near < p[k] for k in range(3)):
            continue  # bounding boxes are further apart than the reach
        common = solids[i] & solids[j]  # None when they do not meet
        v = common.volume if common else 0.0
        if v > 1e-6:
            print(f"overlap solids {i} and {j}: {v:.4f} mm3")
            overlap += 1
        elif a.near and (d := solids[i].distance_to(solids[j])) < a.near:
            print(f"near    solids {i} and {j}: gap {d:.3f} mm" + ("  tight" if d < min_gap else ""))
            near += 1
            tight += d < min_gap
print(f"solids: {len(solids)}, overlapping pairs: {overlap}" + (f", within {a.near} mm: {near} ({tight} tight)" if a.near else ""))
sys.exit(1 if overlap or tight else 0)
