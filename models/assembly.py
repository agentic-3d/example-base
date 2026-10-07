# Exploded view of two independent parts (not screwed together, so their hole patterns differ on purpose).
# Expect: bodies=2 (check with `--bodies 2`), bbox 60 x 40 x 44. For printing, export the parts individually.
from build123d import Compound, Pos

from models import bracket, plate

# --- Parameters (mm, Z up) ---
EXPLODE_GAP = 5  # vertical gap between plate top and bracket bottom (exploded view)

# both parts have their origin at the bottom center
result = Compound([plate.result, Pos(0, 0, plate.THICKNESS + EXPLODE_GAP) * bracket.result])
