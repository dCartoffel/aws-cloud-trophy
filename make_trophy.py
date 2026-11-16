"""Generate the Cloud Innovation Challenge trophy as printable STLs.

usage: python make_trophy.py <out_dir> [label] [--design cloud|scale|zones|shield]

The label is split into lines at "|", e.g. "CLOUD INNOVATION CHALLENGE|TUM 2026".

Every design is a flat symbol (prints flat, no supports) whose tabs slot into the same
two-step plinth with an engraved label. The designs follow the case:
  cloud  - a cloud with a traffic spike cut through it (15x traffic, and a cloud that takes it)
  scale  - a bar chart that scales up to 15x, the last bar ending in an arrow
  zones  - three linked rings, the three Availability Zones that keep the shop up
  shield - a shield with the ring of EU stars and a keyhole (data stays in the EU, under your key)

Outputs (prefixed with the design name):
  <design>_trophy_symbol.stl      - the symbol, print flat (no supports)
  <design>_trophy_base.stl        - two-step plinth with its slots, print flat (no supports)
  <design>_trophy_label_inlay.stl - optional label fill for 2-colour prints (sits in the engraving)
  <design>_trophy_base_2colour.3mf - base + label as two objects, ready for an AMS/MMU
  <design>_trophy_onepiece.stl    - everything fused, print upright (cut-outs bridge)
"""
import sys, os, argparse
import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

ap = argparse.ArgumentParser()
ap.add_argument("out_dir")
ap.add_argument("label", nargs="?", default="CLOUD INNOVATION CHALLENGE|TUM · 2026")
ap.add_argument("--design", default="cloud", choices=["cloud", "scale", "zones", "shield"])
args = ap.parse_args()
OUT, LABEL, DESIGN = args.out_dir, args.label, args.design

# ---------------- parameters (mm) ----------------
SYM_T = 8.0            # symbol thickness
INSERT = 4.0           # how deep each tab sits in the plinth
CLEAR = 0.15           # clearance per side for the slots (PLA/PETG on a 0.4 nozzle)
SEAT = 0.4             # extra slot depth so the symbol seats on its bottom, not on the tab tips
PLINTH = (112, 34, 10, 8)   # upper step: w, d, h, corner radius
STEP = (126, 46, 6, 11)     # lower step: w, d, h, corner radius
SYM_Y = 5.0            # symbol sits this far behind centre -> room for the label in front
TOP_CH = 1.5           # chamfer on the plinth's top edge
FOOT_CH = 0.5          # 45 deg chamfer on the bed edge (beats elephant foot)
ENGRAVE = 0.6          # label depth, engraved into the top face
TEXT_H = 6.0           # max cap height of the label
LINE_GAP = 0.55        # gap between label lines, as a fraction of the cap height
INLAY_CLEAR = 0.1

# ---------------- the symbols, in (x, z) with their flat bottom on z = 0 ----------------
FLOOR = box(-200, 0, 200, 300)

def rrect_xy(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 48)

def arrowhead(p, q, length, back, half_w):
    u = np.array([q[0] - p[0], q[1] - p[1]], float); u /= np.linalg.norm(u)
    n = np.array([-u[1], u[0]]); q = np.array(q, float)
    return Polygon([q + length * u, q - back * u + half_w * n, q - back * u - half_w * n])

def star(cx, cy, r_out, r_in, k=5, rot=90):
    a = np.radians(rot) + np.arange(2 * k) * np.pi / k
    r = np.where(np.arange(2 * k) % 2 == 0, r_out, r_in)
    return Polygon(np.c_[cx + r * np.cos(a), cy + r * np.sin(a)])

def design_cloud():
    cloud = unary_union([
        rrect_xy(-46, 0, 46, 24, 9),          # flat-bottomed body
        Point(-26, 23).buffer(17, 96),        # left puff
        Point(3, 33).buffer(24, 128),         # big middle puff
        Point(30, 24).buffer(15, 96),         # right puff
    ]).buffer(4, 64).buffer(-4, 64)           # fillet the dips between the puffs
    # traffic spike: quiet, quiet, then up through the roof, with an arrowhead
    pts = [(-33, 10), (-20, 15), (-10, 11), (14, 37)]
    spike = unary_union([LineString(pts).buffer(2.2, cap_style=2, join_style=2, mitre_limit=3),
                         arrowhead(pts[-2], pts[-1], 5.5, 4.0, 6.0)])
    return cloud.difference(spike), (-24, 24), 14.0

def design_scale():
    # five bars on a common foot: 1x, 2x, 4x, 8x, then the 15x bar shoots up as an arrow
    w, gap, foot = 13.0, 4.0, 7.0
    x0 = -(5 * w + 4 * gap) / 2
    xs = [x0 + i * (w + gap) for i in range(5)]
    bars = [rrect_xy(x, 0, x + w, foot + 3.2 * f, 2.5) for x, f in zip(xs, (1, 2, 4, 8))]
    xl = xs[4]
    shaft = box(xl, 0, xl + w, 55)
    head = Polygon([(xl - 6, 53), (xl + w + 6, 53), (xl + w / 2, 70)])
    base = box(x0, 0, x0 + 5 * w + 4 * gap, foot)
    shape = unary_union(bars + [shaft, head, base])
    shape = shape.buffer(1.0, 32).buffer(-2.0, 32).buffer(1.0, 32)   # soften every corner
    return shape.intersection(FLOOR), (xs[1] + w / 2, xs[3] + w / 2), 12.0

def design_zones():
    # three linked rings in a triangle: three Availability Zones, one region
    R, ring_w, c, cy = 20.0, 6.0, 34.0, 18.0                # rings dip 2 mm below z = 0 -> flat feet
    centres = [(-c / 2, cy), (c / 2, cy), (0, cy + c * np.sqrt(3) / 2)]
    rings = unary_union([Point(x, y).buffer(R, 128).difference(Point(x, y).buffer(R - ring_w, 128)) for x, y in centres])
    return rings.intersection(FLOOR), (-c / 2, c / 2), 12.0

def design_shield():
    # shield on a flat 20 mm foot, ring of 12 EU stars, keyhole in the middle
    top, half, side = 74.0, 31.0, 44.0
    p0, p1, p2 = np.array([half, side]), np.array([half, 14.0]), np.array([10.0, 0.0])
    curve = [tuple((1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s ** 2 * p2) for s in np.linspace(0, 1, 40)]
    right = [(half, top - 4)] + curve
    outline = right + [(-x, y) for x, y in reversed(right)] + [(0, top + 2)]
    shield = Polygon(outline).buffer(2, 32).buffer(-2, 32).intersection(FLOOR)
    cx, cy, rr = 0.0, 44.0, 19.0
    stars = unary_union([star(cx + rr * np.cos(a), cy + rr * np.sin(a), 3.6, 1.5)
                         for a in np.radians(np.arange(0, 360, 30))])
    key = unary_union([Point(cx, cy + 3).buffer(4.2, 48),
                       Polygon([(cx - 2, cy + 1), (cx + 2, cy + 1), (cx + 3.4, cy - 9), (cx - 3.4, cy - 9)])])
    return shield.difference(unary_union([stars, key])), (0.0,), 18.0

symbol, TAB_XS, TAB_W = {"cloud": design_cloud, "scale": design_scale,
                         "zones": design_zones, "shield": design_shield}[DESIGN]()
TAB_XS = tuple(float(x) for x in TAB_XS)
tabs = unary_union([box(x - TAB_W / 2, -INSERT, x + TAB_W / 2, 0.01) for x in TAB_XS])
symbol_tabs = unary_union([symbol, tabs])
# thinnest neck: the smallest erosion that splits the shape or makes it vanish
thin = next((w for w in np.arange(0.5, 12, 0.25)
             if symbol.buffer(-w / 2).is_empty or symbol.buffer(-w / 2).geom_type == "MultiPolygon"), None)
print(DESIGN, "symbol size mm:", np.round(np.subtract(symbol.bounds[2:], symbol.bounds[:2]), 1),
      "one piece:", symbol.geom_type == "Polygon", "thinnest neck mm: ~", thin)

# ---------------- helpers ----------------
def rrect(w, d, r):
    r = max(min(r, w / 2 - 0.01, d / 2 - 0.01), 0.01)
    return box(-w / 2 + r, -d / 2 + r, w / 2 - r, d / 2 - r).buffer(r, 32)

def section(w, d, r, z):
    p = np.array(rrect(w, d, r).exterior.coords)
    return np.c_[p, np.full(len(p), z)]

def loft(*secs):
    """Convex hull of rounded-rect sections, segment by segment -> a chamfered/tapered solid."""
    parts = [trimesh.convex.convex_hull(np.vstack([section(*a), section(*b)])) for a, b in zip(secs, secs[1:])]
    return U(parts) if len(parts) > 1 else parts[0]

def tier(w, d, r, h, z0, bottom=0.0, top=0.0):
    secs = []
    if bottom: secs.append((w - 2 * bottom, d - 2 * bottom, r - bottom, z0))
    secs.append((w, d, r, z0 + bottom))
    secs.append((w, d, r, z0 + h - top))
    if top: secs.append((w - 2 * top, d - 2 * top, r - top, z0 + h))
    return loft(*secs)

def extrude_xz(poly2d, thickness, y_center=0.0):
    """Extrude a 2D (x, z) shape along Y, centred on y_center."""
    if poly2d.geom_type == "MultiPolygon":
        return U([extrude_xz(g, thickness, y_center) for g in poly2d.geoms])
    m = trimesh.creation.extrude_polygon(poly2d, thickness)
    T = np.array([[1, 0, 0, 0], [0, 0, 1, -thickness / 2 + y_center], [0, 1, 0, 0], [0, 0, 0, 1]], float)
    m.apply_transform(T)
    if m.volume < 0:
        m.invert()
    return m

U = lambda ms: trimesh.boolean.union(ms, engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")

def ext_z(poly, h, z0):
    gs = poly.geoms if poly.geom_type == "MultiPolygon" else [poly]
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(g, h) for g in gs])
    m.apply_translation([0, 0, z0]); return m

# ---------------- plinth ----------------
W, Dp, H1, R = PLINTH
SW, SD, SH, SR = STEP
H = SH + H1                                   # top of the upper step
plinth = U([tier(SW, SD, SR, SH, 0.0, bottom=FOOT_CH, top=1.0),
            tier(W, Dp, R, H1 + 0.01, SH - 0.01, top=TOP_CH)])

fp = FontProperties(family="DejaVu Sans", weight="bold")
CAP = TextPath((0, 0), "H", size=10, prop=fp).get_extents().height

def text_line(s):
    t = Polygon()
    for p in sorted([Polygon(p) for p in TextPath((0, 0), s, size=10, prop=fp).to_polygons() if len(p) >= 3],
                    key=lambda p: -p.area):
        t = t.symmetric_difference(p.buffer(0))
    x0, _, x1, _ = t.bounds
    return affinity.translate(t, -(x0 + x1) / 2, 0)      # centre each line, baseline at 0

lines = [l.strip() for l in LABEL.split("|") if l.strip()]
pitch = CAP * (1 + LINE_GAP)
txt = unary_union([affinity.translate(text_line(l), 0, -i * pitch) for i, l in enumerate(lines)])
front_edge, sym_front = -Dp / 2 + TOP_CH, SYM_Y - SYM_T / 2
strip = sym_front - front_edge
x0, y0, x1, y1 = txt.bounds
k = min(TEXT_H / CAP, (W - 2 * R) / (x1 - x0), (strip - 3.0) / (y1 - y0))
txt = affinity.scale(txt, k, k, origin=(0, 0))
x0, y0, x1, y1 = txt.bounds
txt = affinity.translate(txt, -(x0 + x1) / 2, (front_edge + sym_front) / 2 - (y0 + y1) / 2)
print("label lines:", lines, "cap height mm:", round(k * CAP, 2))
cut = ext_z(txt, 2 * ENGRAVE, H - ENGRAVE)
plinth = D(plinth, cut)
inlay = ext_z(txt.buffer(-INLAY_CLEAR, join_style=2), ENGRAVE, H - ENGRAVE)

# ---------------- symbol: bottom on the plinth top, tabs down into the slots ----------------
sym_z = affinity.translate(symbol_tabs, 0, H)
sym_m = extrude_xz(sym_z, SYM_T, y_center=SYM_Y)

# one straight slot per tab, with a 0.6 mm lead-in
sw, sd = TAB_W + 2 * CLEAR, SYM_T + 2 * CLEAR
def slot(x):
    m = loft((sw, sd, 0.3, H - INSERT - SEAT), (sw, sd, 0.3, H - 0.6), (sw + 1.2, sd + 1.2, 0.6, H + 0.01), (sw + 1.2, sd + 1.2, 0.6, H + 2))
    m.apply_translation([x, SYM_Y, 0]); return m
slots = U([slot(x) for x in TAB_XS])

def flat_symbol():
    """Same shape, but the face that goes on the bed is inset 0.4 mm (no elephant foot)."""
    back = extrude_xz(sym_z.buffer(-0.4, join_style=2), 0.4, y_center=SYM_Y + SYM_T / 2 - 0.2)
    rest = extrude_xz(sym_z, SYM_T - 0.4, y_center=SYM_Y - 0.2)
    return U([back, rest])

os.makedirs(OUT, exist_ok=True)
one = U([plinth, sym_m])
one.export(os.path.join(OUT, f"{DESIGN}_trophy_onepiece.stl"))
sym = flat_symbol()
sym.export(os.path.join(OUT, f"_{DESIGN}_symbol_assembled.stl"))
lp = sym.copy()
lp.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))   # back face down
lp.apply_translation(-lp.bounds[0])
lp.export(os.path.join(OUT, f"{DESIGN}_trophy_symbol.stl"))
base_part = D(plinth, slots)
base_part.export(os.path.join(OUT, f"{DESIGN}_trophy_base.stl"))
inlay.export(os.path.join(OUT, f"{DESIGN}_trophy_label_inlay.stl"))
sc = trimesh.Scene()
sc.add_geometry(base_part, node_name="base", geom_name="base")
sc.add_geometry(inlay, node_name="label", geom_name="label")
sc.export(os.path.join(OUT, f"{DESIGN}_trophy_base_2colour.3mf"))

for nm, m in [("onepiece", one), ("symbol", lp), ("base", base_part), ("inlay", inlay)]:
    print(nm, "watertight:", m.is_watertight, "size mm:", np.round(m.extents, 1), "vol cm3:", round(m.volume / 1000, 2))
hit = trimesh.boolean.intersection([base_part, sym], engine="manifold")
print("symbol/base overlap mm3:", round(hit.volume, 3) if not hit.is_empty else 0)
