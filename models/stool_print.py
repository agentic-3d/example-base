# Stool in print orientation: seat top face on the bed, legs rise from it, feet at the top.
# Expect: bodies=1, same bbox as stool
from build123d import Pos, Rot

from models import stool

result = Pos(0, 0, stool.HEIGHT) * Rot(180, 0, 0) * stool.result
