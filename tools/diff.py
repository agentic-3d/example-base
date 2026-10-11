"""Usage: uv run python tools/diff.py <model> [--ref REV]   (run from the project root, inside the git repository)

Base-owned: edit in agentic-3d/example-base, then `make sync-base`.

Compares the working out/<model>.stl with the one committed at REV (default HEAD): bbox, volume, surface area, bodies and
centroid. Run it after `make` and before committing, to see how far a parameter change travelled through the models that
import each other. Report only (exit 0). A model without a committed STL is reported as new.
"""
import argparse
import io
import subprocess

import trimesh

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--ref", default="HEAD", help="git revision that holds the old out/<model>.stl")
a = ap.parse_args()

path = f"out/{a.model}.stl"
new = trimesh.load(path, force="mesh")
old = None
try:
    blob = subprocess.run(["git", "show", f"{a.ref}:{path}"], check=True, capture_output=True).stdout
    old = trimesh.load(io.BytesIO(blob), file_type="stl", force="mesh")
except subprocess.CalledProcessError:
    print(f"{path} is not in {a.ref}: new model")


def metrics(m):
    x, y, z = m.extents
    cx, cy, cz = m.centroid
    return {
        "bbox X": x, "bbox Y": y, "bbox Z": z, "volume mm3": m.volume, "area mm2": m.area,
        "bodies": len(m.split(only_watertight=False)), "centroid X": cx, "centroid Y": cy, "centroid Z": cz,
    }


n = metrics(new)
o = metrics(old) if old is not None else None
print(f"{'':12}{'new':>12}" + (f"{'old':>12}{'delta':>12}" if o else ""))
changed = False
for k, v in n.items():
    if o is None:
        print(f"{k:12}{v:12.3f}")
        continue
    d = v - o[k]
    changed |= abs(d) > 1e-3
    print(f"{k:12}{v:12.3f}{o[k]:12.3f}{d:+12.3f}{'  *' if abs(d) > 1e-3 else ''}")
if o is not None:
    print("changed" if changed else f"unchanged against {a.ref}")
