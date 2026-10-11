"""Overlay a model's silhouette on a drawing, scan or photo, to check it pixel by pixel.

Usage: uv run python tools/overlay.py <model> <drawing.png> <view> <px_x_per_mm> <px_y_per_mm> <origin_x_px> <origin_y_px> <out.png>
           [--crop x0 y0 x1 y1] [--zoom N] [--rotate DEG] [--shift DX DY DZ] [--edges MM]

Base-owned: edit in agentic-3d/example-base, then `make sync-base`. Needs only the packages of pyproject.toml.

<view> is `side` (model X, Z on the drawing), `front` (model Y, Z) or `top` (plan: model X, Y). The model origin (X or Y = 0,
Z = 0) is put at (origin_x_px, origin_y_px) of the drawing: the point that the model's datum corresponds to (a reference line,
a ground line or a centre mark). --shift moves the model first (model mm), for parts that are modelled in print orientation
and not in the coordinates of the drawing.
px per mm is the drawing scale per axis: drawing pixels per model mm (real mm / model scale / mm per pixel), because scans are
often stretched and each axis has its own scale. Calibrate each axis from two known dimensions on the drawing.
--rotate deskews the scan first (PIL angle, counter-clockwise positive).
The red outline is the silhouette of out/<model>.stl; ruler ticks are in drawing pixels. --edges MM also draws, in blue, every
depth step larger than MM (model mm) of the visible surface seen from the +Y / +X / +Z side: recesses, pockets and openings
that the silhouette does not show.
"""
import argparse

import numpy as np
import trimesh
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("drawing")
ap.add_argument("view", choices=["side", "front", "top"])
ap.add_argument("px_x_per_mm", type=float)
ap.add_argument("px_y_per_mm", type=float)
ap.add_argument("origin_x", type=float)
ap.add_argument("origin_y", type=float)
ap.add_argument("out")
ap.add_argument("--crop", type=int, nargs=4)
ap.add_argument("--zoom", type=int, default=4)
ap.add_argument("--rotate", type=float, default=0.0)
ap.add_argument("--shift", type=float, nargs=3, default=(0.0, 0.0, 0.0))
ap.add_argument("--edges", type=float, default=0.0)
a = ap.parse_args()

mesh = trimesh.load(f"out/{a.model}.stl", force="mesh")
mesh.apply_translation(a.shift)
img = Image.open(a.drawing).convert("RGB")
if a.rotate:
    img = img.rotate(a.rotate, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
x0, y0, x1, y1 = a.crop or (0, 0, *img.size)
z = a.zoom
w, h = (x1 - x0) * z, (y1 - y0) * z
u = mesh.triangles[:, :, 1 if a.view == "front" else 0]
v = mesh.triangles[:, :, 1 if a.view == "top" else 2]
px = (a.origin_x + u * a.px_x_per_mm - x0) * z
py = (a.origin_y - v * a.px_y_per_mm - y0) * z
mask = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(mask)
for xs, ys in zip(px, py):
    draw.polygon(list(zip(xs, ys)), fill=255)
m = np.array(mask) > 0
inner = m
for _ in range(2):  # one pixel erosion per pass, so the outline is 2 px wide
    prev = inner
    inner = prev.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        inner &= np.roll(np.roll(prev, dx, axis=1), dy, axis=0)
out = np.array(img.crop((x0, y0, x1, y1)).resize((w, h), Image.LANCZOS))
if a.edges:  # z-buffer (nearest surface towards +Y / +X / +Z), then the depth steps
    depth = mesh.triangles[:, :, {"side": 1, "front": 0, "top": 2}[a.view]]
    zb = np.full((h, w), float(depth.min() - 1))
    for (x_a, x_b, x_c), (y_a, y_b, y_c), (d_a, d_b, d_c) in zip(px, py, depth):
        x_lo, x_hi = int(max(min(x_a, x_b, x_c), 0)), int(min(max(x_a, x_b, x_c) + 1, w - 1))
        y_lo, y_hi = int(max(min(y_a, y_b, y_c), 0)), int(min(max(y_a, y_b, y_c) + 1, h - 1))
        det = (y_b - y_c) * (x_a - x_c) + (x_c - x_b) * (y_a - y_c)
        if x_hi < x_lo or y_hi < y_lo or abs(det) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x_lo, x_hi + 1) + 0.5, np.arange(y_lo, y_hi + 1) + 0.5)
        l_a = ((y_b - y_c) * (gx - x_c) + (x_c - x_b) * (gy - y_c)) / det
        l_b = ((y_c - y_a) * (gx - x_c) + (x_a - x_c) * (gy - y_c)) / det
        l_c = 1 - l_a - l_b
        inside = (l_a >= -1e-9) & (l_b >= -1e-9) & (l_c >= -1e-9)
        z_tri = np.where(inside, l_a * d_a + l_b * d_b + l_c * d_c, -1e9)
        sub = zb[y_lo:y_hi + 1, x_lo:x_hi + 1]
        np.maximum(sub, z_tri, out=sub)
    step = np.zeros((h, w), bool)
    step[:, 1:] |= np.abs(np.diff(zb, axis=1)) > a.edges
    step[1:, :] |= np.abs(np.diff(zb, axis=0)) > a.edges
    out[step] = (0, 0, 255)
out[m & ~inner] = (255, 0, 0)
res = Image.fromarray(out)
d = ImageDraw.Draw(res)
for x in range((x0 // 10 + 1) * 10, x1, 10):
    d.line([((x - x0) * z, 0), ((x - x0) * z, 8)], fill=(0, 0, 0))
    d.text(((x - x0) * z + 2, 8), str(x), fill=(0, 0, 0))
for y in range((y0 // 10 + 1) * 10, y1, 10):
    d.line([(0, (y - y0) * z), (8, (y - y0) * z)], fill=(0, 0, 0))
    d.text((10, (y - y0) * z - 5), str(y), fill=(0, 0, 0))
res.save(a.out)
print(f"wrote {a.out}")
