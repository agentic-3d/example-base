"""Usage: uv run python tools/render.py <model>  ->  out/<model>.png"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

# (title, elevation, azimuth) in degrees; Z is up
VIEWS = [("iso", 30, -55), ("top", 90, -90), ("front", 0, -90), ("side", 0, 0)]
RES = 600
BASE = np.array([0.35, 0.55, 0.85])

name = sys.argv[1]
mesh = trimesh.load(f"out/{name}.stl", force="mesh")
tris, normals = mesh.triangles, mesh.face_normals
lo, hi = mesh.bounds
center, half = (lo + hi) / 2, np.linalg.norm(hi - lo) / 2 * 1.05  # bounding-sphere radius: no view clips


def rasterize(elev, azim):
    """Orthographic z-buffer render, shaded by face normals. Returns RGB image."""
    e, a = np.radians(elev), np.radians(azim)
    cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.array([-np.sin(a), np.cos(a), 0.0])
    up = np.cross(cam, right)
    light = cam + 0.6 * up - 0.5 * right
    light /= np.linalg.norm(light)
    shade = 0.3 + 0.7 * np.clip(normals @ light, 0, 1)

    p = tris - center
    sx = (p @ right / half + 1) / 2 * (RES - 1)
    sy = (1 - (p @ up / half + 1) / 2) * (RES - 1)
    sz = p @ cam
    img = np.ones((RES, RES, 3))
    zbuf = np.full((RES, RES), -np.inf)
    for i in range(len(tris)):
        if normals[i] @ cam < -1e-9:  # back-face cull
            continue
        x, y, z = sx[i], sy[i], sz[i]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), RES - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), RES - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        depth = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = zbuf[y0 : y1 + 1, x0 : x1 + 1]
        win = inside & (depth > sub)
        sub[win] = depth[win]
        img[y0 : y1 + 1, x0 : x1 + 1][win] = np.clip(BASE * shade[i], 0, 1)
    return img, right, up


fig, axes = plt.subplots(2, 2, figsize=(12, 12), dpi=100)
for ax, (title, elev, azim) in zip(axes.flat, VIEWS):
    img, right, up = rasterize(elev, azim)
    cx, cy = center @ right, center @ up  # extent in true model coordinates
    ax.imshow(img, extent=(cx - half, cx + half, cy - half, cy + half), interpolation="bilinear")
    names = "XYZ"
    h, v = names[int(np.argmax(np.abs(right)))], names[int(np.argmax(np.abs(up)))]
    ax.set_title(title)
    if title != "iso":  # orthographic: axes are true model mm
        ax.set_xlabel(f"{h} mm (screen right)")
        ax.set_ylabel(f"{v} mm (screen up)")
        ax.grid(alpha=0.3)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
fig.suptitle(f"{name}: bbox {mesh.extents[0]:.1f} x {mesh.extents[1]:.1f} x {mesh.extents[2]:.1f} mm", fontsize=11)
fig.tight_layout()
fig.savefig(f"out/{name}.png")
print(f"wrote out/{name}.png")
