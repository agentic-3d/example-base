# Stool stretcher: round rod along X. Origin: center.
# Expect: bodies=1, bbox 58 x 9 x 9
from build123d import Cylinder

# --- Parameters (mm) ---
LENGTH = 58  # X
DIAMETER = 9


def build(length=LENGTH, d=DIAMETER):
    return Cylinder(d / 2, length, rotation=(0, 90, 0))


result = build()
