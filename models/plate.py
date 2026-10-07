# Mounting plate, bottom on the print bed. Origin: bottom center.
# Expect: bodies=1, bbox 60 x 40 x 10
from build123d import Align, Axis, BuildPart, Box, Hole, Locations, chamfer, fillet

from models.common import BED_CHAMFER, HOLE_COMP, MIN_WALL

# --- Parameters (mm, Z up) ---
LENGTH = 60  # X
WIDTH = 40  # Y
THICKNESS = 10  # Z
CORNER_R = 3  # vertical edge fillet radius
HOLE_D = 5  # mounting hole diameter
HOLE_INSET = 6  # hole center distance from plate edges


def build(length=LENGTH, width=WIDTH, thickness=THICKNESS, corner_r=CORNER_R, hole_d=HOLE_D, hole_inset=HOLE_INSET, bed_chamfer=BED_CHAMFER):
    assert hole_inset - hole_d / 2 >= MIN_WALL
    with BuildPart() as part:
        Box(length, width, thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        if corner_r:  # 0 = square corners
            fillet(part.edges().filter_by(Axis.Z), corner_r)
        hx, hy = length / 2 - hole_inset, width / 2 - hole_inset
        with Locations((hx, hy), (-hx, hy), (hx, -hy), (-hx, -hy)):
            Hole((hole_d + HOLE_COMP) / 2)
        if bed_chamfer:  # 0 = leave to the caller
            chamfer((part.faces() << Axis.Z).edges(), bed_chamfer)
    return part.part


result = build()
