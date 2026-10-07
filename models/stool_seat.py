# Stool seat: square slab, bottom at Z=0 (upright). Origin: bottom center.
# Printed seat-down, so the top edge (bed side) is a 45 deg chamfer and the underside edge a fillet.
# Expect: bodies=1, bbox 84 x 84 x 12
from build123d import Align, Axis, BuildPart, Box, chamfer, fillet

# --- Parameters (mm, Z up) ---
WIDTH = 84  # X and Y (square)
THICKNESS = 12  # Z
CORNER_R = 8  # vertical edge fillet radius
TOP_CHAMFER = 2  # chamfer on the top edges (touch the bed when printed)
BOTTOM_R = 3  # fillet on the underside edges


def build(width=WIDTH, thickness=THICKNESS, corner_r=CORNER_R, top_chamfer=TOP_CHAMFER, bottom_r=BOTTOM_R):
    with BuildPart() as part:
        Box(width, width, thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(part.edges().filter_by(Axis.Z), corner_r)
        fillet((part.faces() << Axis.Z).edges(), bottom_r)
        chamfer((part.faces() >> Axis.Z).edges(), top_chamfer)
    return part.part


result = build()
