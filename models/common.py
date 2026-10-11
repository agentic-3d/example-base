# Shared print constants (mm). Import from any model: `from models.common import CLEARANCE, MIN_WALL`
CLEARANCE = 0.2  # fit clearance between mating parts, per side
MIN_WALL = 1.2  # minimum printable wall
HOLE_COMP = 0.2  # added to the diameter of holes (vertical holes print small)
BED_CHAMFER = 0.4  # elephant-foot relief on edges that touch the print bed
BED_MAX = 240  # design limit per part and per plate, on each axis (256 bed minus brim, purge line, excluded corner)
GLUE_GAP = 0.5  # extra socket depth behind a shouldered peg (room for glue and air)
SOCKET_WALL = 2.4  # minimum wall around a socket
SOCKET_FLOOR = 1.6  # minimum floor under a socket
