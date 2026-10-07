# Plaque: flat plate with a stepped brightness relief of a photo (left) and raised text (right). Origin: bottom center.
# Function: decorative plaque. Process: FDM, bottom face on the bed, no supports.
# Expect: bodies=1, bbox 150 x 80 x 6
from pathlib import Path

import contourpy
import numpy as np
from build123d import Align, Axis, Box, BuildPart, BuildSketch, FontStyle, Locations, Mode, Plane, Polygon, Text, chamfer, extrude, fillet
from PIL import Image, ImageDraw, ImageFilter

from models.common import BED_CHAMFER, MIN_WALL

# --- Parameters (mm, Z up) ---
LENGTH = 150  # X
WIDTH = 80  # Y
THICKNESS = 4  # Z, plate
CORNER_R = 3  # vertical edge fillet radius
RELIEF_H = 2  # height of photo relief (brightest level) and text above the plate
LEVELS = 5  # height steps of the photo: level 1 = whole figure, level LEVELS = brightest areas
MARGIN = 5  # free space between relief and plate edge
PHOTO = Path(__file__).resolve().parent.parent / "assets" / "photo.webp"
PHOTO_H = WIDTH - 2 * MARGIN  # photo height, width follows the aspect ratio
TEXT = "v4.0.0\nsuccess"
TEXT_SIZE = 21
TEXT_GAP = 5  # free space between photo and text block
BG_MIN = 248  # gray level from which a border-connected pixel counts as background
MASK_PX = 500  # mask height in pixels
BLUR_PX = 2  # blur radius that removes the jeans fringe before re-thresholding
TONE_BLUR_PX = 3  # blur radius of the brightness field, removes pixel noise and fabric texture
SIMPLIFY = 0.08  # outline simplification tolerance
MIN_FEATURE = MIN_WALL  # islands and holes with a smaller bbox side are dropped
STEP = RELIEF_H / LEVELS  # height of one level


def rdp(pts, eps):  # Ramer-Douglas-Peucker on a closed ring, pts: (n, 2)
    def run(p):
        if len(p) < 3:
            return p
        a, b = p[0], p[-1]
        d = b - a
        n = np.hypot(*d)
        dist = np.abs(d[0] * (p[:, 1] - a[1]) - d[1] * (p[:, 0] - a[0])) / n if n else np.hypot(*(p - a).T)
        i = int(dist.argmax())
        if dist[i] <= eps:
            return np.array([a, b])
        return np.vstack([run(p[: i + 1])[:-1], run(p[i:])])

    ring = pts[:-1] if (pts[0] == pts[-1]).all() else pts
    h = len(ring) // 2  # split in two halves so the closing segment is never degenerate
    return np.vstack([run(ring[: h + 1])[:-1], run(np.vstack([ring[h:], ring[:1]]))[:-1]])


def blur(a, r):  # float or bool array in 0..1 -> blurred float array in 0..1
    return np.array(Image.fromarray((np.asarray(a, float) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(r))) / 255


def trace(mask, k):  # bool mask -> [(outer, [holes])] in mm, Y up, origin at the bottom left of the mask
    field = blur(np.pad(mask, 1), BLUR_PX)  # zero border closes every contour
    gen = contourpy.contour_generator(z=field, fill_type=contourpy.FillType.OuterCode)
    polys = []
    for pts, codes in zip(*gen.filled(0.5, 2.0)):
        rings = np.split(pts, np.where(codes == 1)[0][1:])
        rings = [rdp(np.c_[r[:, 0] * k, (field.shape[0] - r[:, 1]) * k], SIMPLIFY) for r in rings]  # flip Y: image Y points down
        keep = lambda r: np.ptp(r, axis=0).min() >= MIN_FEATURE
        if keep(rings[0]):
            polys.append((rings[0], [r for r in rings[1:] if keep(r)]))
    return polys


def relief(path=PHOTO, height=PHOTO_H, levels=LEVELS):  # -> (width mm, [polys per level]); level i = figure area brighter than quantile i/levels
    img = Image.open(path).convert("L")
    img = img.resize((round(img.width * MASK_PX / img.height), MASK_PX), Image.LANCZOS)
    bg = img.point(lambda v: 255 if v >= BG_MIN else 0)
    for seed in ((0, 0), (bg.width - 1, 0), (0, bg.height - 1), (bg.width - 1, bg.height - 1)):
        ImageDraw.floodfill(bg, seed, 128, thresh=0)  # only border-connected background becomes 128
    fg = blur(np.array(bg) != 128, BLUR_PX) > 0.5  # figure mask without the fringe
    rows, cols = np.where(fg)
    crop = (slice(rows.min(), rows.max() + 1), slice(cols.min(), cols.max() + 1))
    tone = np.array(img.filter(ImageFilter.GaussianBlur(TONE_BLUR_PX)), float)[crop]
    masks = [fg[crop]]
    for q in np.quantile(tone[masks[0]], np.arange(1, levels) / levels):  # equal-area bands use the full height range
        masks.append(blur(masks[-1] & (tone >= q), BLUR_PX) > 0.5)  # nested: each level lies inside the previous one
    k = height / (masks[0].shape[0] + 2)  # +2 = padding added in trace()
    return (masks[0].shape[1] + 2) * k, [trace(m, k) for m in masks]


def build(length=LENGTH, width=WIDTH, thickness=THICKNESS, corner_r=CORNER_R, relief_h=RELIEF_H, margin=MARGIN, bed_chamfer=BED_CHAMFER):
    photo_w, levels = relief(height=width - 2 * margin)
    step = relief_h / len(levels)
    x0 = -length / 2 + margin  # left edge of the photo
    text_x0 = x0 + photo_w + TEXT_GAP  # left edge of the text area
    text_w = length / 2 - margin - text_x0
    with BuildPart() as part:
        Box(length, width, thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        if corner_r:
            fillet(part.edges().filter_by(Axis.Z), corner_r)
        for i, polys in enumerate(levels):  # each level adds one step on top of the previous one
            if not polys:
                continue
            with BuildSketch(Plane.XY.offset(thickness + i * step)):
                for outer, holes in polys:
                    Polygon(*(outer + (x0, -width / 2 + margin)), align=None)
                    for h in holes:
                        Polygon(*(h + (x0, -width / 2 + margin)), align=None, mode=Mode.SUBTRACT)
            extrude(amount=step)
        with BuildSketch(Plane.XY.offset(thickness)) as txt:
            with Locations((text_x0 + text_w / 2, 0)):
                Text(TEXT, TEXT_SIZE, font_style=FontStyle.BOLD)
        bb = txt.sketch.bounding_box()
        assert bb.min.X >= text_x0 and bb.max.X <= length / 2 - margin, f"text {bb.size.X:.1f} wide does not fit {text_w:.1f}"
        extrude(amount=relief_h)
        if bed_chamfer:
            chamfer((part.faces() << Axis.Z).edges(), bed_chamfer)
    return part.part


result = build()
