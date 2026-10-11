"""Usage: uv run python tools/sections.py <model> (--x V | --y V | --z V) [--out PNG]   (run from the project root)

Base-owned: edit in agentic-3d/example-base, then `make sync-base`.

Cross-section of out/<model>.stl through the plane X = V, Y = V or Z = V (model mm), drawn with true-mm axes. Shows what render.py
cannot: sockets, pockets, glue gaps, hollow parts and wall thickness. The section plane is viewed from the + side of its axis.
Default output: out/<model>.<axis><V>.png. Several planes: run it several times, or pass --x/--y/--z together.
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.collections import LineCollection

ap = argparse.ArgumentParser()
ap.add_argument("model")
for ax in "xyz":
    ap.add_argument(f"--{ax}", type=float, action="append", help=f"section at {ax.upper()} = V (mm)")
ap.add_argument("--out", help="output PNG (default out/<model>.<axis><V>.png), only with one plane")
a = ap.parse_args()
planes = [(i, v) for i, ax in enumerate("xyz") for v in (getattr(a, ax) or [])]
if not planes:
    ap.error("give at least one of --x, --y, --z")
if a.out and len(planes) > 1:
    ap.error("--out needs exactly one plane")

mesh = trimesh.load(f"out/{a.model}.stl", force="mesh")
tri = mesh.triangles  # (n, 3, 3)
for axis, value in planes:
    d = tri[:, :, axis] - value
    d[d == 0] = 1e-9  # a vertex exactly on the plane counts as the + side
    nxt, dn = np.roll(tri, -1, axis=1), np.roll(d, -1, axis=1)
    cross = d * dn < 0  # (n, 3): edge i -> i+1 crosses the plane
    t = np.where(cross, d / np.where(cross, d - dn, 1), 0)
    pts = tri + (nxt - tri) * t[..., None]  # crossing point on every edge (valid where `cross`)
    two = cross.sum(axis=1) == 2  # a triangle cut by the plane has exactly two crossing edges
    segs = pts[two][cross[two]].reshape(-1, 2, 3)
    h, v = [i for i in range(3) if i != axis]  # plane axes: horizontal, vertical (X -> Y, Z; Y -> X, Z; Z -> X, Y)
    xy = segs[:, :, [h, v]]
    names = "XYZ"
    name = f"{names[axis].lower()}{value:g}"
    flat = xy.reshape(-1, 2)
    lo, hi = (flat.min(axis=0), flat.max(axis=0)) if len(xy) else (np.zeros(2), np.ones(2))
    aspect = (hi[1] - lo[1] + 1) / (hi[0] - lo[0] + 1)  # figure follows the section, so it is not mostly white
    fig, ax = plt.subplots(figsize=(8, min(max(8 * aspect + 1.2, 3), 10)), dpi=100)
    ax.add_collection(LineCollection(xy, colors="C0", linewidths=1.0))
    if len(xy):
        pad = max(hi - lo) * 0.05 + 0.5
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_xlabel(f"{names[h]} mm")
    ax.set_ylabel(f"{names[v]} mm")
    ax.set_title(f"{a.model}: section {names[axis]} = {value:g} mm ({len(xy)} segments)")
    out = a.out or f"out/{a.model}.{name}.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}" + ("" if len(xy) else "  (plane misses the model)"))
