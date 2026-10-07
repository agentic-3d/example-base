# Stool (upright, as in the reference photos): seat, 4 splayed round legs, square ring of 4 stretchers. Origin: floor center.
# Everything is a ratio of HEIGHT, so one number rescales the stool. Legs are mirrored from one leg.
# Printed via stool_print (seat down). Stretchers bridge ~58 mm between the legs and need slicer supports.
# Expect: bodies=1, bbox ~93 x 93 x 120
from math import radians, tan

from build123d import Plane, Pos, Rot, mirror

from models import stool_leg, stool_seat, stool_stretcher

# --- Parameters (mm, Z up) ---
HEIGHT = 120
SEAT_W_RATIO = 0.70
SEAT_T_RATIO = 0.10
LEG_D_RATIO = 0.115
STRETCHER_D_RATIO = 0.075
STRETCHER_Z_RATIO = 0.32  # stretcher axis height above the floor
SPLAY_DEG = 5  # leg lean per axis
LEG_INSET = 12  # leg axis distance from the seat edge, at the seat underside
LEG_EMBED = 6  # leg depth into the seat
SEAT_CORNER_R = 8
SEAT_TOP_CHAMFER = 2
SEAT_BOTTOM_R = 3
FOOT_R = 2

SEAT_W = HEIGHT * SEAT_W_RATIO
SEAT_T = HEIGHT * SEAT_T_RATIO
LEG_D = HEIGHT * LEG_D_RATIO
STRETCHER_D = HEIGHT * STRETCHER_D_RATIO
STRETCHER_Z = HEIGHT * STRETCHER_Z_RATIO
STRETCHER_STOP = LEG_D / 4  # stretcher ends stop short of the leg axis, so perpendicular ones never meet

SEAT_Z = HEIGHT - SEAT_T
TAN = tan(radians(SPLAY_DEG))
LEG_TOP_X = SEAT_W / 2 - LEG_INSET  # leg axis at the seat underside
FOOT_X = LEG_TOP_X + TAN * SEAT_Z
STRETCHER_X = FOOT_X - TAN * STRETCHER_Z  # leg axis at the stretcher height
STRETCHER_L = 2 * (STRETCHER_X - STRETCHER_STOP)

assert LEG_INSET >= LEG_D / 2 + SEAT_BOTTOM_R  # leg clears the seat underside fillet
assert LEG_EMBED < SEAT_T  # leg does not poke through the seat top
assert min(LEG_D, STRETCHER_D) >= 3  # minimum pin size

seat = Pos(0, 0, SEAT_Z) * stool_seat.build(SEAT_W, SEAT_T, SEAT_CORNER_R, SEAT_TOP_CHAMFER, SEAT_BOTTOM_R)
leg = stool_leg.build(FOOT_X, FOOT_X, SEAT_Z + LEG_EMBED, SPLAY_DEG, LEG_D, FOOT_R)
legs = leg + mirror(leg, Plane.XZ)
legs = legs + mirror(legs, Plane.YZ)
rod = stool_stretcher.build(STRETCHER_L, STRETCHER_D)
stretchers = Pos(0, STRETCHER_X, STRETCHER_Z) * rod + Pos(0, -STRETCHER_X, STRETCHER_Z) * rod
stretchers = stretchers + Rot(0, 0, 90) * stretchers

result = seat + legs + stretchers
