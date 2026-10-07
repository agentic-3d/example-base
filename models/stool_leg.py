# Stool leg for the (+,+) corner, placed in world coordinates (Z up, floor at Z=0).
# The axis leans inward by SPLAY_DEG per axis going up; the foot is cut flat at Z=0 and its edge filleted.
# Expect: bodies=1, z from 0 to Z_TOP
from math import radians, sqrt, tan

from build123d import Align, Axis, BuildPart, Cylinder, Keep, Location, Plane, Pos, fillet, split

# --- Parameters (mm, Z up) ---
FOOT_X = 39.45  # axis position at the floor
FOOT_Y = 39.45
Z_TOP = 114  # top end of the leg (inside the seat)
SPLAY_DEG = 5  # lean per axis
DIAMETER = 13.8
FOOT_R = 2  # foot edge fillet
EXTRA = 5  # axis length below the floor, removed by the flat cut


def build(foot_x=FOOT_X, foot_y=FOOT_Y, z_top=Z_TOP, splay_deg=SPLAY_DEG, d=DIAMETER, foot_r=FOOT_R):
    t = tan(radians(splay_deg))
    length = z_top * sqrt(1 + 2 * t * t) + EXTRA  # along the axis, from EXTRA below the floor
    rod = Pos(0, 0, -EXTRA) * Cylinder(d / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rod = Location(Plane(origin=(foot_x, foot_y, 0), z_dir=(-t, -t, 1))) * rod
    with BuildPart() as part:
        split(rod, bisect_by=Plane.XY, keep=Keep.TOP)
        fillet((part.faces() << Axis.Z).edges(), foot_r)
    return part.part


result = build()
