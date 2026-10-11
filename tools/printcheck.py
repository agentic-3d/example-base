"""Usage: uv run python tools/printcheck.py <model> [--angle DEG] [--fail-over PCT]   (run from the project root)

Base-owned: edit in agentic-3d/example-base, then `make sync-base`.

FDM report from out/<model>.stl, printed as it stands (Z up, bed at the lowest Z): bed contact area, overhang area and the
largest overhang regions with their Z range, and extents against BED_MAX. A face is an overhang when it faces down and is
more than --angle degrees (default 45) off vertical. Faces lying on the bed are not overhangs. It cannot see that an overhang
rests on earlier layers, so read the regions, not only the percentage. Report only (exit 0), because supports are allowed as
a last resort; --fail-over PCT exits 1 when the overhang is more than PCT percent of the surface.
"""
import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, so `models` imports work

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--angle", type=float, default=45.0, help="overhang angle off vertical, degrees")
ap.add_argument("--fail-over", type=float, help="exit 1 when overhang area exceeds this percent of the surface")
ap.add_argument("--top", type=int, default=8, help="how many overhang regions to list")
ap.add_argument("--min-area", type=float, default=1.0, help="ignore overhang regions smaller than this many mm2 (tessellation noise)")
a = ap.parse_args()

mesh = trimesh.load(f"out/{a.model}.stl", force="mesh")
nz, area = mesh.face_normals[:, 2], mesh.area_faces
zmin = mesh.bounds[0][2]
on_bed = mesh.triangles[:, :, 2].max(axis=1) < zmin + 0.01  # all three vertices at the bed
over = (nz < -np.sin(np.radians(a.angle)) - 0.01) & ~on_bed  # 0.01 slack: a 45 deg chamfer is exactly at the limit
total = area.sum()
print(f"surface (mm2): {total:.1f}")
print(f"bed contact (mm2): {area[on_bed].sum():.1f}")
pct = 100 * area[over].sum() / total
print(f"overhang > {a.angle:g} deg (mm2): {area[over].sum():.1f} ({pct:.1f} percent of the surface)")

idx = np.flatnonzero(over)
if len(idx):  # connected regions of overhang faces: label propagation over the face adjacency
    where = -np.ones(len(nz), int)
    where[idx] = np.arange(len(idx))
    pair = mesh.face_adjacency
    pair = pair[over[pair[:, 0]] & over[pair[:, 1]]]
    u, v = where[pair[:, 0]], where[pair[:, 1]]
    lab = np.arange(len(idx))
    while True:
        m = np.minimum(lab[u], lab[v])
        new = lab.copy()
        np.minimum.at(new, u, m)
        np.minimum.at(new, v, m)
        new = new[new]  # pointer jumping
        if (new == lab).all():
            break
        lab = new
    regions = []
    for r in np.unique(lab):
        f = idx[lab == r]
        zs = mesh.triangles[f][:, :, 2]
        c = mesh.triangles[f].reshape(-1, 3)
        regions.append((area[f].sum(), zs.min(), zs.max(), c.min(axis=0), c.max(axis=0), -nz[f].mean()))
    regions.sort(key=lambda r: -r[0])
    big = [r for r in regions if r[0] >= a.min_area]
    print(f"overhang regions: {len(big)} of at least {a.min_area:g} mm2 ({len(regions) - len(big)} smaller ignored), largest first"
          " (area, Z range, X/Y span, flatness 1.0 = horizontal roof):")
    for s, z0, z1, lo, hi, flat in big[: a.top]:
        print(f"  {s:8.1f} mm2  Z {z0:7.2f} .. {z1:7.2f}  X {lo[0]:7.2f} .. {hi[0]:7.2f}  Y {lo[1]:7.2f} .. {hi[1]:7.2f}  {flat:.2f}")

x, y, z = mesh.extents
try:
    bed = importlib.import_module("models.common").BED_MAX
    print(f"extents (mm): {x:.2f} x {y:.2f} x {z:.2f}, BED_MAX {bed}: " + ("within" if max(x, y, z) <= bed else "OVER"))
except ImportError:
    print(f"extents (mm): {x:.2f} x {y:.2f} x {z:.2f}")

sys.exit(1 if a.fail_over is not None and pct > a.fail_over else 0)
