# L-bracket, printed base-down (upright rises along Z). Origin: bottom center.
# The base/wall joint is filleted because a load on the upright pulls across layer lines there.
# The wall hole is a teardrop (45 deg point up) so it prints without support.
# Expect: bodies=1, bbox 40 x 30 x 29
from math import cos, radians, sin, sqrt

from build123d import Axis, BuildPart, BuildSketch, Box, Circle, Locations, Mode, Plane, Polygon, chamfer, extrude, fillet, insert

from models import plate
from models.common import BED_CHAMFER, HOLE_COMP, MIN_WALL

# --- Parameters (mm, Z up) ---
BASE_L = 40  # X
BASE_W = 30  # Y
BASE_T = 4  # base flange thickness
WALL_T = 3  # upright wall thickness
WALL_H = 25  # upright wall height above the base
CORNER_R = 2  # rounding of the two front corners (the wall side stays square)
JOINT_R = 1.5  # fillet where the upright meets the base
HOLE_D = 4  # base mounting hole diameter
HOLE_INSET = 9  # base hole center distance from edges
WALL_HOLE_D = 6  # hole through the upright wall
EPS = 0.01  # selector tolerance

assert WALL_T >= MIN_WALL
assert WALL_T + JOINT_R + MIN_WALL <= HOLE_INSET - (HOLE_D + HOLE_COMP) / 2  # joint fillet clears the base holes

wall_y = -BASE_W / 2 + WALL_T / 2
wall_z = BASE_T + WALL_H / 2
r_wall = (WALL_HOLE_D + HOLE_COMP) / 2

with BuildPart() as part:
    # the base flange reuses the plate model with different dimensions and square corners
    insert(plate.build(BASE_L, BASE_W, BASE_T, corner_r=0, hole_d=HOLE_D, hole_inset=HOLE_INSET, bed_chamfer=0))
    front_corners = part.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, BASE_W / 2 - EPS, BASE_W / 2 + EPS)
    fillet(front_corners, CORNER_R)
    with Locations((0, wall_y, wall_z)):
        Box(BASE_L, WALL_T, WALL_H)
    joint_y = -BASE_W / 2 + WALL_T
    joint = part.edges().filter_by(Axis.X).filter_by_position(Axis.Y, joint_y - EPS, joint_y + EPS).filter_by_position(Axis.Z, BASE_T - EPS, BASE_T + EPS)
    fillet(joint, JOINT_R)
    # teardrop: circle plus a 45 deg point on top; sketch plane XZ is offset (along -Y) to the wall center
    with BuildSketch(Plane.XZ.offset(-wall_y)):
        with Locations((0, wall_z)):
            Circle(r_wall)
            Polygon((r_wall * cos(radians(45)), r_wall * sin(radians(45))), (0, r_wall * sqrt(2)), (-r_wall * cos(radians(45)), r_wall * sin(radians(45))))
    extrude(amount=WALL_T, both=True, mode=Mode.SUBTRACT)
    chamfer((part.faces() << Axis.Z).edges(), BED_CHAMFER)

result = part.part
