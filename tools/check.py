"""Usage: uv run python tools/check.py <model> [--bodies N]   (N defaults to 1)"""
import argparse
import sys
import trimesh

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

sys.exit(0 if mesh.is_watertight and bodies == args.bodies else 1)
