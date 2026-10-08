# 1:120 (TT) exterior model of the MAV 2-axle railbus trailer Bx 50 55 24-28 000 (Gyor, 1939). Exterior only, no seats.
# All parts are functions in this file; `result` is a Compound of 5 separate bodies (shell, roof, underframe, 2 wheelsets)
# with gaps >= CLEARANCE, so they print support-free except the curved roof (print it crown-down with supports, or in resin).
# Real-world drawing dimensions go through s(); everything else is model mm. Z = 0 is the lowest wheel point.
# Window/door positions are measured from the drawing (x from the body centre, real mm).
# Function:   scale model of the car; shell + roof + underframe + wheelsets are glued/clipped together
# Process:    FDM; shell floor-down open-top, roof crown-down, underframe flat, wheelsets axle-up
# Datums:     body centre X/Y, lowest wheel point Z=0
# Expect:     bodies=5, bbox 106.5 x 26.18 x 29.92, walls >= 1.6
# Risks:      roof needs supports (flat crown, 41 deg slope at the eaves); chimney only 0.5 mm proud (drawing: 3590.5 - 3531);
#             side window slots run up to the roof edge, so the roof edge is the lintel; no handrails/louvers (< 1 mm)
from build123d import Axis, Box, BuildPart, BuildSketch, Compound, Cylinder, Kind, Plane, Polygon, Pos, Rot, extrude, mirror, offset, revolve

from models.common import BED_CHAMFER, CLEARANCE, MIN_WALL

SCALE = 120


def s(mm):  # real-world mm of the drawing -> model mm
    return mm / SCALE


# --- Parameters (mm, Z up, X = length, Y = width) ---
BODY_L = s(11550)  # shell length (side view)
BODY_W = s(3080)  # shell width (front view)
END_W = s(2160)  # width of the end faces (plan view)
TAPER_L = s(1425)  # plan chamfer length at each end (plan view)
BUFFER_OVERHANG = s(615)  # buffer tip beyond the body end (12780 over buffers)
STEP_W = s(3142)  # width over the steps
WHEELBASE = s(7000)
FLOOR_Z = s(1175)  # floor plane above the rail
ROOF_Z = FLOOR_Z + s(2356)  # roof crown
TOP_Z = s(3590.5)  # ventilator top
EAVE_Z = FLOOR_Z + s(1785)  # roof edge at the side walls (measured from the side view)
BUFFER_Z = s(1065)
BUFFER_GAUGE = s(1750)
STEP_Z = s(540)  # step tread top
SILL = s(850)  # window sill above the floor (measured)
WINDOW_H = s(767)
DOOR_H = s(1570)  # door leaf height, kept below the shell rim on the tapered walls
DOOR_WIN_W = s(440)  # open window in each door leaf
DOOR_WIN_H = s(540)
GROOVE_W = 0.8  # engraved door outline (width x depth)
GROOVE_D = 0.5
WINDOWS = [(-3833, 630), (-2476, 621), (-1354, 750), (244, 750), (1739, 710), (3141, 621), (4041, 488)]  # (x, width) real mm
DOORS = [(-5146, 728), (5156, 710)]  # on the tapered end walls, one leaf per side wall (4 doors)
END_WINDOWS = [(-580, 420), (0, 340), (580, 420)]  # (y, width) real mm, 3 per end face (end view)
CHIMNEY_X = s(-673)
CHIMNEY_D = 2.4
WALL_T = 1.6
FLOOR_T = 1.6
ROOF_T = 1.6
ROOF_GAP = CLEARANCE  # shell rim to roof underside
# wheelset (TT: 12 mm gauge, 10.6 mm back to back)
BACK_TO_BACK = 10.6
WHEEL_R = s(850) / 2
WHEEL_W = 1.6
FLANGE_H = 0.4  # flange radial height and axial thickness
AXLE_D = 1.6
AXLE_CLEAR = 0.3  # axle slot clearance per side
AXLE_Z = WHEEL_R + FLANGE_H  # flange bottom touches Z = 0
# underframe
SB_T = 1.6  # solebar thickness (Y)
SB_H = 2.0  # solebar height (Z)
HEAD_T = 1.6  # headstock thickness (X)
CROSS_W = 3  # centre cross member
GUARD_W = 4  # axle guard width (X)
BUFFER_HEAD_R = s(340) / 2
BUFFER_SHAFT_R = 0.8
BUFFER_HEAD_T = 1
STEP_L = 5.5  # step tread length (X)
STEP_T = 1  # step tread thickness

# --- Derived ---
SHELL_Z0 = FLOOR_Z - FLOOR_T  # shell bottom
ROOF_RISE = ROOF_Z - EAVE_Z
ROOF_R = ((BODY_W / 2) ** 2 + ROOF_RISE**2) / (2 * ROOF_RISE)  # outer arc radius
ARC_Z = ROOF_Z - ROOF_R  # arc centre height
WHEEL_IN = BACK_TO_BACK / 2
WHEEL_OUT = WHEEL_IN + WHEEL_W
SB_Y0 = WHEEL_OUT + 0.4  # solebar inner face, clear of the wheels
SB_Y1 = SB_Y0 + SB_T
SB_TOP = SHELL_Z0 - CLEARANCE
SB_BOT = SB_TOP - SB_H
HEAD_X0 = BODY_L / 2 + CLEARANCE  # headstock inner face, clear of the shell end
HEAD_X1 = HEAD_X0 + HEAD_T
TIP_X = BODY_L / 2 + BUFFER_OVERHANG
SLOT_R = AXLE_D / 2 + AXLE_CLEAR
GUARD_BOT = AXLE_Z - 1

assert min(WALL_T, FLOOR_T, ROOF_T) >= 1.5 and max(WALL_T, FLOOR_T, ROOF_T) <= 2.5 and WALL_T >= MIN_WALL
assert SHELL_Z0 - (AXLE_Z + WHEEL_R + FLANGE_H) >= CLEARANCE  # wheels clear the floor
assert SB_Y1 < STEP_W / 2  # steps stick out past the solebars


# --- helpers ---
def cuboid(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xcyl(r, x0, x1, y, z):  # cylinder along X
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, abs(x1 - x0))


def plan_prism(inset, z0, z1):  # hexagonal plan (full width in the middle, tapering to END_W), optionally inset
    w, e, x, t = BODY_W / 2, END_W / 2, BODY_L / 2, TAPER_L
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(z0)):
            Polygon((-x, -e), (-x + t, -w), (x - t, -w), (x, -e), (x, e), (x - t, w), (-x + t, w), (-x, e), align=None)
            if inset:
                offset(amount=-inset, kind=Kind.INTERSECTION)
        extrude(amount=z1 - z0)
    return p.part


def arch(r, dz=0):  # cylinder along X with the roof arc centre, optionally moved down
    return Pos(0, 0, ARC_Z - dz) * Rot(0, 90, 0) * Cylinder(r, BODY_L + 2)


def slot(x, w, z0):  # opening cut through both side walls, open to the top
    return cuboid(x - w / 2, x + w / 2, -BODY_W, BODY_W, z0, ROOF_Z + 1)


# --- parts ---
def shell():
    body = arch(ROOF_R - ROOF_T - ROOF_GAP) & plan_prism(0, SHELL_Z0, ROOF_Z)  # floor + walls up to the roof underside
    body -= plan_prism(WALL_T, FLOOR_Z, ROOF_Z + 1)  # hollow, open top
    for x, w in WINDOWS:
        body -= slot(s(x), s(w), FLOOR_Z + SILL)
    for y, w in END_WINDOWS:  # through both end faces
        body -= cuboid(-BODY_L, BODY_L, s(y - w / 2), s(y + w / 2), FLOOR_Z + SILL, FLOOR_Z + SILL + WINDOW_H)
    skin = plan_prism(0, FLOOR_Z, ROOF_Z) - plan_prism(GROOVE_D, FLOOR_Z - 1, ROOF_Z + 1)  # outer layer for engraving
    for x, w in DOORS:  # door leaves: engraved outline, open window
        x, w = s(x), s(w)
        z0, z1 = FLOOR_Z + GROOVE_W,FLOOR_Z + DOOR_H
        ring = cuboid(x - w / 2, x + w / 2, -BODY_W, BODY_W, z0, z1) - cuboid(x - w / 2 + GROOVE_W, x + w / 2 - GROOVE_W, -BODY_W, BODY_W, z0 + GROOVE_W, z1 - GROOVE_W)
        body -= ring & skin
        body -= cuboid(x - DOOR_WIN_W / 2, x + DOOR_WIN_W / 2, -BODY_W, BODY_W, FLOOR_Z + SILL, FLOOR_Z + SILL + DOOR_WIN_H)
    return body.chamfer(BED_CHAMFER, None, body.faces().sort_by(Axis.Z)[0].edges())


def chimney():
    return Pos(CHIMNEY_X, 0, (ROOF_Z - ROOF_T + TOP_Z) / 2) * Cylinder(CHIMNEY_D / 2, TOP_Z - ROOF_Z + ROOF_T)


def roof():
    ring = (arch(ROOF_R) - arch(ROOF_R - ROOF_T)) & plan_prism(0, ARC_Z, ROOF_Z + 1)
    return ring + chimney()


def buffers():
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            y = sy * BUFFER_GAUGE / 2
            parts += [xcyl(BUFFER_SHAFT_R, sx * (HEAD_X1 - 0.5), sx * (TIP_X - BUFFER_HEAD_T), y, BUFFER_Z), xcyl(BUFFER_HEAD_R, sx * (TIP_X - BUFFER_HEAD_T), sx * TIP_X, y, BUFFER_Z)]
    return parts


def steps():  # one tread under each door, hanging from the solebar
    parts = []
    for x, _ in DOORS:
        for sy in (-1, 1):
            x0, x1 = s(x) - STEP_L / 2, s(x) + STEP_L / 2
            parts += [cuboid(x0, x1, *sorted((sy * SB_Y0, sy * STEP_W / 2)), STEP_Z - STEP_T, STEP_Z), cuboid(x0, x1, *sorted((sy * SB_Y0, sy * SB_Y1)), STEP_Z - STEP_T, SB_BOT + 0.5)]
    return parts


def axle_guards():  # plates below the solebars, with a bottom-open slot for the axle
    return [cuboid(ax - GUARD_W / 2, ax + GUARD_W / 2, *sorted((sy * SB_Y0, sy * SB_Y1)), GUARD_BOT, SB_BOT + 0.5) for ax in (-WHEELBASE / 2, WHEELBASE / 2) for sy in (-1, 1)]


def axle_slots():
    slots = []
    for ax in (-WHEELBASE / 2, WHEELBASE / 2):
        slots += [Pos(ax, 0, AXLE_Z) * Rot(90, 0, 0) * Cylinder(SLOT_R, 2 * SB_Y1 + 2), cuboid(ax - SLOT_R, ax + SLOT_R, -SB_Y1 - 1, SB_Y1 + 1, GUARD_BOT - 1, AXLE_Z)]
    return slots


def underframe():
    head_top = BUFFER_Z + BUFFER_HEAD_R + 0.4
    frame = cuboid(-HEAD_X1, HEAD_X1, SB_Y0, SB_Y1, SB_BOT, SB_TOP) + cuboid(-HEAD_X1, HEAD_X1, -SB_Y1, -SB_Y0, SB_BOT, SB_TOP)
    frame += cuboid(-CROSS_W / 2, CROSS_W / 2, -SB_Y1, SB_Y1, SB_BOT, SB_TOP)
    for sx in (-1, 1):
        frame += cuboid(*sorted((sx * HEAD_X0, sx * HEAD_X1)), -SB_Y1, SB_Y1, SB_BOT, head_top)
    for part in buffers() + steps() + axle_guards():
        frame += part
    for cut in axle_slots():
        frame -= cut
    return frame


def wheelset():  # axle along Y, centred at the origin
    with BuildPart() as p:
        with BuildSketch(Plane.XY):  # profile (radius, axial) revolved about Y: flange on the inner face, chamfer to the tread
            Polygon((0, WHEEL_IN), (WHEEL_R + FLANGE_H, WHEEL_IN), (WHEEL_R + FLANGE_H, WHEEL_IN + FLANGE_H), (WHEEL_R, WHEEL_IN + 2 * FLANGE_H), (WHEEL_R, WHEEL_OUT), (0, WHEEL_OUT), align=None)
        revolve(axis=Axis.Y)
        mirror(about=Plane.XZ)
        Cylinder(AXLE_D / 2, 2 * (SB_Y1 - 0.2), rotation=(90, 0, 0))
    return p.part


def assemble():
    return Compound([shell(), roof(), underframe(), *(Pos(x, 0, AXLE_Z) * wheelset() for x in (-WHEELBASE / 2, WHEELBASE / 2))])


result = assemble()
