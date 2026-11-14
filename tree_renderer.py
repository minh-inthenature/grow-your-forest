"""
Tree rendering module for Grow Your Forest.
High-quality organic procedural botanical trees:
- Classic Oak (oak)
- Cherry Blossom (cherry_blossom)
- Pine (pine)
- Angel Oak (angel_oak)

Renders with organic Bezier curves, multi-tiered volumetric lighting,
sculpted dimensional trunks, and soft perspective grounding.
"""

import math
import random

# Color palettes by species & lighting layers
COLORS = {
    # Ground & Common Shadows
    "shadow_deep": "#102313",
    "shadow_soft": "#1D3820",
    "shadow_ambient": "#2E4F32",
    "soil_dark": "#4E342E",
    "soil_rich": "#6D4C41",
    "soil_light": "#8D6E63",
    "grass_deep": "#2E7D32",
    "grass_lush": "#43A047",
    "grass_bright": "#66BB6A",
    "grass_sun": "#81C784",
    "ground_green": "#A5D6A7",
    "ground_grass": "#C8E6C9",

    # Classic Oak
    "oak_bark_shadow": "#2D1D16",
    "oak_bark_dark": "#432C23",
    "oak_bark_mid": "#5D3E32",
    "oak_bark_light": "#7D5847",
    "oak_bark_sun": "#9C735E",
    "oak_foliage_shadow": "#0F3818",
    "oak_foliage_deep": "#195024",
    "oak_foliage_dark": "#236B32",
    "oak_foliage_mid": "#2E853E",
    "oak_foliage_light": "#43A854",
    "oak_foliage_bright": "#68C477",
    "oak_foliage_sun": "#9DE0A8",
    "oak_acorn_cap": "#4E342E",
    "oak_acorn_nut": "#8D6E63",

    # Cherry Blossom (Sakura)
    "cherry_bark_shadow": "#211517",
    "cherry_bark_dark": "#362125",
    "cherry_bark_mid": "#4E3237",
    "cherry_bark_light": "#6B484F",
    "cherry_bark_sun": "#8A6169",
    "cherry_petal_shadow": "#880E4F",
    "cherry_petal_deep": "#AD1457",
    "cherry_petal_rose": "#C2185B",
    "cherry_petal_vibrant": "#E91E63",
    "cherry_petal_pink": "#F06292",
    "cherry_petal_soft": "#F48FB1",
    "cherry_petal_light": "#F8BBD0",
    "cherry_petal_white": "#FFF0F5",

    # Pine / Evergreen
    "pine_bark_shadow": "#1A1412",
    "pine_bark_dark": "#2E201B",
    "pine_bark_mid": "#45322B",
    "pine_bark_light": "#61473E",
    "pine_needle_shadow": "#0A241A",
    "pine_needle_deep": "#103828",
    "pine_needle_dark": "#164E38",
    "pine_needle_mid": "#1E684C",
    "pine_needle_light": "#2D8562",
    "pine_needle_bright": "#43A67D",
    "pine_needle_sun": "#72C7A1",
    "pine_cone_dark": "#3E2723",
    "pine_cone_mid": "#5D4037",

    # Angel Oak (Ancient Live Oak with Spanish Moss)
    "angel_bark_shadow": "#16120F",
    "angel_bark_dark": "#29211C",
    "angel_bark_mid": "#3E332C",
    "angel_bark_light": "#58493F",
    "angel_bark_mossy": "#404C38",
    "angel_foliage_shadow": "#0E2413",
    "angel_foliage_deep": "#18361E",
    "angel_foliage_mid": "#254B2D",
    "angel_foliage_light": "#36663E",
    "angel_moss_shadow": "#45533F",
    "angel_moss_deep": "#63745C",
    "angel_moss_sage": "#85977D",
    "angel_moss_light": "#ADC0A4",
    "angel_moss_sun": "#D3E2CC",
}

SPECIES_METADATA = {
    "oak": {
        "id": "oak",
        "name": "Classic Oak",
        "icon": "🌳",
        "tagline": "Sturdy, balanced & enduring",
        "theme_color": "#2E7D32",
        "particles": ["🍃", "🌱", "💧"],
    },
    "cherry_blossom": {
        "id": "cherry_blossom",
        "name": "Cherry Blossom",
        "icon": "🌸",
        "tagline": "Graceful pink sakura blooms",
        "theme_color": "#D81B60",
        "particles": ["🌸", "💮", "✨"],
    },
    "pine": {
        "id": "pine",
        "name": "Pine",
        "icon": "🌲",
        "tagline": "Resilient alpine evergreen",
        "theme_color": "#1E684C",
        "particles": ["🌲", "❄️", "✨"],
    },
    "angel_oak": {
        "id": "angel_oak",
        "name": "Angel Oak",
        "icon": "🌿",
        "tagline": "Ancient mystical canopy",
        "theme_color": "#3E332C",
        "particles": ["🌿", "✨", "🌟"],
    },
}

STAGE_LABELS = {
    "seed": "🌱 Seed",
    "sprout": "🌿 Sprout",
    "seedling": "🪴 Small Sapling",
    "young": "🌲 Young Tree",
    "mature": "🌳 Mature Tree",
    "flourishing": "✨ Flourishing Tree",
}

_IN_MINI_TREE = False


# ── Organic geometry helpers ──────────────────────────────────────

def _make_organic_points(cx, cy, rx, ry, num_pts=16, roughness=0.18, seed=None):
    """Generate a smooth multi-lobed organic polygon perimeter."""
    if seed is not None:
        random.seed(seed)
    pts = []
    for i in range(num_pts):
        ang = (2 * math.pi * i) / num_pts
        r_jitter = 1.0 + random.uniform(-roughness, roughness)
        x = cx + rx * r_jitter * math.cos(ang)
        y = cy + ry * r_jitter * math.sin(ang)
        pts.extend([int(x), int(y)])
    return pts


def _draw_organic_lobe(canvas, cx, cy, rx, ry, fill, outline="", num_pts=16, roughness=0.18, seed=None):
    """Draw a hand-painted cloud-like foliage mass with smooth Bezier curves."""
    pts = _make_organic_points(cx, cy, rx, ry, num_pts=num_pts, roughness=roughness, seed=seed)
    return canvas.create_polygon(pts, fill=fill, outline=outline, width=1 if outline else 0, smooth=True)


def _draw_shadow_and_soil(canvas, cx, cy, rx, ry, grass_color="#43A047"):
    """Draw a perspective shadow; mini forest trees get subtle turf & shadow,
    while full study trees get a contoured sanctuary earth mound with pebbles."""
    if _IN_MINI_TREE or rx < 50:
        # Lightweight meadow integration: soft contact shadow + 2 small grass tufts
        srx = max(8, int(rx * 0.75))
        sry = max(3, int(ry * 0.65))
        canvas.create_oval(
            cx - srx, cy - sry,
            cx + srx, cy + sry,
            fill="#1D3820", outline="", width=0
        )
        for dx, h_dir in ((-int(rx * 0.45), -1), (int(rx * 0.42), 1)):
            tx = cx + dx
            canvas.create_line(tx, cy, tx + h_dir * 3, cy - max(4, int(ry * 0.9)),
                               fill=grass_color, width=1)
            canvas.create_line(tx, cy, tx + h_dir * 6, cy - max(3, int(ry * 0.65)),
                               fill=COLORS["grass_sun"], width=1)
        return

    # Full study sanctuary earth mound
    # Outer diffuse shadow
    canvas.create_oval(
        cx - int(rx * 1.25), cy - int(ry * 0.55),
        cx + int(rx * 1.25), cy + int(ry * 1.15),
        fill="#142617", outline="", width=0
    )
    # Core contact shadow
    canvas.create_oval(
        cx - int(rx * 0.95), cy - int(ry * 0.35),
        cx + int(rx * 0.95), cy + int(ry * 0.85),
        fill="#0B170D", outline="", width=0
    )
    # Earth mound base
    canvas.create_oval(
        cx - rx, cy - ry,
        cx + rx, cy + ry,
        fill=COLORS["soil_rich"], outline=COLORS["soil_dark"], width=1
    )
    # Lush grassy crest
    canvas.create_oval(
        cx - rx + 3, cy - ry - 2,
        cx + rx - 3, cy + int(ry * 0.4),
        fill=grass_color, outline="", width=0
    )
    # Highlight rim on sunlit top of mound
    canvas.create_arc(
        cx - rx + 6, cy - ry - 3,
        cx + rx - 6, cy + int(ry * 0.3),
        start=30, extent=120,
        outline=COLORS["grass_sun"], width=2, style="arc"
    )
    # 3 small decorative pebbles along the front slope of the mound
    pebbles = [
        (-int(rx * 0.52), int(ry * 0.35), max(3, int(rx * 0.08)), max(2, int(ry * 0.16))),
        (int(rx * 0.38), int(ry * 0.42), max(4, int(rx * 0.10)), max(2, int(ry * 0.20))),
        (int(rx * 0.58), int(ry * 0.25), max(2, int(rx * 0.06)), max(2, int(ry * 0.14))),
    ]
    for px, py, prx, pry in pebbles:
        canvas.create_oval(
            cx + px - prx, cy + py - pry,
            cx + px + prx, cy + py + pry,
            fill="#BCAAA4", outline="#8D6E63", width=1
        )


# ══════════════════════════════════════════════════════════════════
# 1. CLASSIC OAK (Lush, volumetric, regal woodland oak)
# ══════════════════════════════════════════════════════════════════

def draw_oak_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    # Cozy nest of clover & moss leaflets around the base
    for ox, oy, col in ((-11, 15, COLORS["oak_foliage_dark"]), (11, 16, COLORS["oak_foliage_mid"]),
                        (-6, 18, COLORS["oak_foliage_light"]), (6, 18, COLORS["oak_foliage_light"])):
        _draw_organic_lobe(canvas, cx + int(ox * size), cy + oy, int(7 * size), int(4 * size),
                           fill=col, num_pts=8, roughness=0.14, seed=200 + ox)
    # Prominent Acorn body (1.3x)
    nut_h = int(24 * size)
    nut_w = int(18 * size)
    acorn_y = cy + 12 - int(nut_h * 0.6)
    # Acorn nut
    canvas.create_oval(
        cx - nut_w // 2, acorn_y,
        cx + nut_w // 2, acorn_y + nut_h,
        fill=COLORS["oak_acorn_nut"], outline=COLORS["oak_bark_dark"], width=1
    )
    # Acorn cap
    cap_h = int(10 * size)
    cap_w = int(21 * size)
    canvas.create_oval(
        cx - cap_w // 2, acorn_y - cap_h // 2,
        cx + cap_w // 2, acorn_y + cap_h // 2 + 1,
        fill=COLORS["oak_acorn_cap"], outline=COLORS["oak_bark_shadow"], width=1
    )
    # Cap stem
    canvas.create_line(
        cx, acorn_y - cap_h // 2, cx - 2, acorn_y - cap_h // 2 - int(8 * size),
        fill=COLORS["oak_bark_dark"], width=max(1, int(2.5 * size))
    )
    # Warm sun highlight glint
    canvas.create_oval(
        cx - int(4 * size), acorn_y + int(4 * size),
        cx, acorn_y + int(8 * size),
        fill="#EFE6DF", outline=""
    )


def draw_oak_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(11 * size))
    # Tender curved shoot & tiny root flare at base
    shoot_h = int(42 * size)
    canvas.create_polygon(
        cx - int(4 * size), cy + 23,
        cx + int(4 * size), cy + 23,
        cx + int(2 * size), cy + 16,
        cx - int(2 * size), cy + 16,
        fill=COLORS["oak_bark_mid"], outline=""
    )
    stem_pts = [
        cx, cy + 21,
        cx - int(5 * size), cy + 21 - shoot_h // 2,
        cx, cy + 21 - shoot_h
    ]
    canvas.create_line(stem_pts, fill=COLORS["oak_foliage_dark"], width=max(2, int(3.5 * size)), smooth=True)
    canvas.create_line(stem_pts, fill=COLORS["oak_foliage_light"], width=max(1, int(1.6 * size)), smooth=True)

    # Lower secondary pair of small stipule leaves
    low_y = cy + 21 - int(shoot_h * 0.45)
    _draw_organic_lobe(canvas, cx - int(9 * size), low_y, int(7 * size), int(4 * size),
                       fill=COLORS["oak_foliage_dark"], num_pts=8, roughness=0.12, seed=5)
    _draw_organic_lobe(canvas, cx + int(7 * size), low_y - int(2 * size), int(7 * size), int(4 * size),
                       fill=COLORS["oak_foliage_mid"], num_pts=8, roughness=0.12, seed=6)

    top_y = cy + 21 - shoot_h
    # Left cotyledon leaf
    _draw_organic_lobe(canvas, cx - int(13 * size), top_y - int(3 * size), int(13 * size), int(7 * size),
                       fill=COLORS["oak_foliage_mid"], num_pts=10, roughness=0.12, seed=1)
    _draw_organic_lobe(canvas, cx - int(12 * size), top_y - int(5 * size), int(10 * size), int(5 * size),
                       fill=COLORS["oak_foliage_light"], num_pts=8, roughness=0.1, seed=2)
    # Right cotyledon leaf
    _draw_organic_lobe(canvas, cx + int(13 * size), top_y - int(2 * size), int(13 * size), int(7 * size),
                       fill=COLORS["oak_foliage_light"], num_pts=10, roughness=0.12, seed=3)
    _draw_organic_lobe(canvas, cx + int(12 * size), top_y - int(4 * size), int(10 * size), int(5 * size),
                       fill=COLORS["oak_foliage_bright"], num_pts=8, roughness=0.1, seed=4)

    # Glistening morning dewdrop
    canvas.create_oval(
        cx + int(5 * size), top_y - int(6 * size),
        cx + int(9 * size), top_y - int(2 * size),
        fill="#E0F7FA", outline="#80DEEA", width=1
    )


def draw_oak_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(70 * size), int(12 * size))
    trunk_h = int(65 * size)
    # Tapered woody stem
    trunk_pts = [
        cx - int(4 * size), cy + 28,
        cx + int(4 * size), cy + 28,
        cx + int(2 * size), cy + 28 - trunk_h,
        cx - int(2 * size), cy + 28 - trunk_h,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["oak_bark_mid"], outline=COLORS["oak_bark_dark"], width=1)

    # Multi-lobed young crown
    top_y = cy + 28 - trunk_h
    r = int(28 * size)

    # Ambient under-shadow
    _draw_organic_lobe(canvas, cx, top_y + int(6 * size), r, int(r * 0.75), fill=COLORS["oak_foliage_shadow"], seed=10)
    # Main midtone body
    _draw_organic_lobe(canvas, cx - int(4 * size), top_y, int(r * 0.95), int(r * 0.85), fill=COLORS["oak_foliage_dark"], seed=11)
    _draw_organic_lobe(canvas, cx + int(4 * size), top_y - int(2 * size), int(r * 0.9), int(r * 0.8), fill=COLORS["oak_foliage_mid"], seed=12)
    # Sunlit crest
    _draw_organic_lobe(canvas, cx - int(5 * size), top_y - int(8 * size), int(r * 0.75), int(r * 0.65), fill=COLORS["oak_foliage_light"], seed=13)
    _draw_organic_lobe(canvas, cx - int(7 * size), top_y - int(12 * size), int(r * 0.5), int(r * 0.45), fill=COLORS["oak_foliage_bright"], seed=14)


def draw_oak_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(95 * size), int(15 * size))
    trunk_h = int(95 * size)
    # Sculpted trunk with root flare
    trunk_pts = [
        cx - int(9 * size), cy + 33,
        cx - int(4 * size), cy + 25,
        cx - int(3 * size), cy + 35 - trunk_h,
        cx + int(3 * size), cy + 35 - trunk_h,
        cx + int(4 * size), cy + 25,
        cx + int(9 * size), cy + 33,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["oak_bark_mid"], outline=COLORS["oak_bark_dark"], width=1, smooth=True)

    # Boughs
    top_y = cy + 35 - trunk_h
    boughs = [(-int(28 * size), -int(18 * size), 0.4), (int(26 * size), -int(20 * size), 0.45),
              (-int(18 * size), -int(30 * size), 0.7), (int(20 * size), -int(28 * size), 0.75)]
    for dx, dy, frac in boughs:
        by = cy + 35 - int(trunk_h * frac)
        canvas.create_line(cx, by, cx + dx, by + dy, fill=COLORS["oak_bark_mid"], width=max(2, int(3 * size)), smooth=True)

    # Volumetric cloud canopy
    r = int(45 * size)
    clusters = [
        # Under-canopy shadow base
        (0, int(r * 0.25), int(r * 0.75), int(r * 0.55), COLORS["oak_foliage_shadow"], 20),
        (-int(r * 0.5), int(r * 0.15), int(r * 0.65), int(r * 0.5), COLORS["oak_foliage_deep"], 21),
        (int(r * 0.5), int(r * 0.15), int(r * 0.65), int(r * 0.5), COLORS["oak_foliage_deep"], 22),
        # Midtones
        (-int(r * 0.35), -int(r * 0.15), int(r * 0.7), int(r * 0.55), COLORS["oak_foliage_dark"], 23),
        (int(r * 0.35), -int(r * 0.15), int(r * 0.7), int(r * 0.55), COLORS["oak_foliage_mid"], 24),
        (0, -int(r * 0.1), int(r * 0.8), int(r * 0.6), COLORS["oak_foliage_mid"], 25),
        # Sunlit highlights (top & left)
        (-int(r * 0.25), -int(r * 0.45), int(r * 0.65), int(r * 0.5), COLORS["oak_foliage_light"], 26),
        (int(r * 0.15), -int(r * 0.45), int(r * 0.6), int(r * 0.45), COLORS["oak_foliage_light"], 27),
        (-int(r * 0.2), -int(r * 0.6), int(r * 0.45), int(r * 0.35), COLORS["oak_foliage_bright"], 28),
    ]
    for ox, oy, rx, ry, col, s in clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)


def draw_oak_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(135 * size), int(18 * size))
    trunk_h = int(120 * size)
    top_y = cy + 40 - trunk_h

    # Robust sculpted trunk with strong root buttresses
    trunk_pts = [
        cx - int(24 * size), cy + 42,
        cx - int(14 * size), cy + 32,
        cx - int(8 * size), cy + 40 - int(trunk_h * 0.5),
        cx - int(7 * size), top_y,
        cx + int(7 * size), top_y,
        cx + int(8 * size), cy + 40 - int(trunk_h * 0.5),
        cx + int(14 * size), cy + 32,
        cx + int(24 * size), cy + 42,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["oak_bark_mid"], outline=COLORS["oak_bark_dark"], width=2, smooth=True)

    # Bark striations and light side
    canvas.create_line(
        cx - int(4 * size), top_y + int(15 * size),
        cx - int(6 * size), cy + 35,
        fill=COLORS["oak_bark_sun"], width=max(1, int(2.5 * size)), smooth=True
    )
    canvas.create_line(
        cx + int(3 * size), top_y + int(20 * size),
        cx + int(5 * size), cy + 35,
        fill=COLORS["oak_bark_shadow"], width=max(1, int(2 * size)), smooth=True
    )

    # Spreading crown limbs reaching into canopy
    limbs = [
        (-int(45 * size), -int(28 * size), 0.35, 5),
        (int(42 * size), -int(25 * size), 0.40, 5),
        (-int(30 * size), -int(48 * size), 0.65, 4),
        (int(32 * size), -int(45 * size), 0.70, 4),
    ]
    for dx, dy, frac, lw in limbs:
        by = cy + 40 - int(trunk_h * frac)
        canvas.create_line(cx, by, cx + dx, by + dy, fill=COLORS["oak_bark_mid"],
                           width=max(2, int(lw * size)), smooth=True)

    # Grand volumetric layered canopy
    r = int(68 * size)
    canopy_clusters = [
        # Deep under-shadow base
        (0, int(r * 0.35), int(r * 0.85), int(r * 0.55), COLORS["oak_foliage_shadow"], 30),
        (-int(r * 0.65), int(r * 0.25), int(r * 0.75), int(r * 0.5), COLORS["oak_foliage_shadow"], 31),
        (int(r * 0.65), int(r * 0.25), int(r * 0.75), int(r * 0.5), COLORS["oak_foliage_shadow"], 32),
        # Dark body
        (-int(r * 0.45), int(r * 0.05), int(r * 0.8), int(r * 0.6), COLORS["oak_foliage_deep"], 33),
        (int(r * 0.45), int(r * 0.05), int(r * 0.8), int(r * 0.6), COLORS["oak_foliage_deep"], 34),
        (0, int(r * 0.05), int(r * 0.9), int(r * 0.65), COLORS["oak_foliage_dark"], 35),
        # Midtone volume
        (-int(r * 0.35), -int(r * 0.25), int(r * 0.8), int(r * 0.6), COLORS["oak_foliage_mid"], 36),
        (int(r * 0.35), -int(r * 0.25), int(r * 0.75), int(r * 0.55), COLORS["oak_foliage_mid"], 37),
        (0, -int(r * 0.2), int(r * 0.85), int(r * 0.65), COLORS["oak_foliage_mid"], 38),
        # Sunlit foliage tiers (top-left emphasis)
        (-int(r * 0.4), -int(r * 0.5), int(r * 0.65), int(r * 0.48), COLORS["oak_foliage_light"], 39),
        (int(r * 0.2), -int(r * 0.5), int(r * 0.6), int(r * 0.45), COLORS["oak_foliage_light"], 40),
        (-int(r * 0.15), -int(r * 0.7), int(r * 0.55), int(r * 0.4), COLORS["oak_foliage_bright"], 41),
        (-int(r * 0.3), -int(r * 0.75), int(r * 0.38), int(r * 0.28), COLORS["oak_foliage_sun"], 42),
    ]
    for ox, oy, rx, ry, col, s in canopy_clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)


def draw_oak_flourishing(canvas, cx, cy, size=1.0):
    draw_oak_mature(canvas, cx, cy, size * 1.08)
    top_y = cy + 40 - int(120 * size * 1.08)
    r = int(68 * size * 1.08)

    # Sunbeams & glowing leaf sparkles
    sparkle_pts = [
        (-int(r * 0.8), -int(r * 0.5)),
        (int(r * 0.85), -int(r * 0.4)),
        (-int(r * 0.4), -int(r * 0.9)),
        (int(r * 0.3), -int(r * 0.85)),
        (0, -int(r * 0.95)),
        (-int(r * 0.9), int(r * 0.1)),
        (int(r * 0.9), int(r * 0.2)),
    ]
    for ox, oy in sparkle_pts:
        sx, sy = cx + ox, top_y + oy
        # Little 4-point golden star
        sl = int(5 * size)
        canvas.create_line(sx - sl, sy, sx + sl, sy, fill="#FFF9C4", width=2)
        canvas.create_line(sx, sy - sl, sx, sy + sl, fill="#FFF9C4", width=2)
        canvas.create_oval(sx - 2, sy - 2, sx + 2, sy + 2, fill="#FFFFFF", outline="")

    # Scattered golden acorns & blooming woodland clover at the base
    ground_y = cy + 42
    for fx in [-int(55 * size), -int(25 * size), int(30 * size), int(60 * size)]:
        canvas.create_oval(cx + fx - 4, ground_y - 2, cx + fx + 4, ground_y + 2, fill="#C8E6C9", outline="")
        canvas.create_oval(cx + fx - 2, ground_y - 4, cx + fx + 2, ground_y, fill="#FFFFFF", outline="")


# ══════════════════════════════════════════════════════════════════
# 2. CHERRY BLOSSOM (SAKURA) (Ethereal pink clouds & dark bonsai trunk)
# ══════════════════════════════════════════════════════════════════

def draw_cherry_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size), grass_color="#66BB6A")
    # Cozy moss nest & clover leaves
    for ox, oy, col in ((-10, 15, COLORS["grass_deep"]), (10, 15, COLORS["grass_lush"]),
                        (-5, 18, COLORS["grass_bright"]), (5, 18, COLORS["grass_bright"])):
        _draw_organic_lobe(canvas, cx + int(ox * size), cy + oy, int(7 * size), int(4 * size),
                           fill=col, num_pts=8, roughness=0.14, seed=210 + ox)
    # Prominent Sakura pit seed (1.3x)
    seed_r = int(9.5 * size)
    seed_cy = cy + 9
    canvas.create_oval(
        cx - seed_r, seed_cy - seed_r,
        cx + seed_r, seed_cy + seed_r,
        fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_shadow"], width=1
    )
    # Warm sun glint on sakura pit
    canvas.create_oval(
        cx - int(4 * size), seed_cy - int(4 * size),
        cx - int(1 * size), seed_cy - int(1 * size),
        fill=COLORS["cherry_bark_sun"], outline=""
    )
    # Fallen pink blossom petals resting beside it
    canvas.create_oval(
        cx + int(10 * size), cy + 12,
        cx + int(19 * size), cy + 17,
        fill=COLORS["cherry_petal_soft"], outline=COLORS["cherry_petal_rose"], width=1
    )
    canvas.create_oval(
        cx - int(18 * size), cy + 13,
        cx - int(11 * size), cy + 17,
        fill=COLORS["cherry_petal_light"], outline=COLORS["cherry_petal_pink"], width=1
    )


def draw_cherry_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(11 * size))
    # Rooted collar base
    canvas.create_polygon(
        cx - int(4 * size), cy + 23,
        cx + int(4 * size), cy + 23,
        cx + int(2 * size), cy + 16,
        cx - int(2 * size), cy + 16,
        fill=COLORS["cherry_bark_dark"], outline=""
    )
    # Elegant curved mahogany stem
    shoot_h = int(42 * size)
    stem_pts = [
        cx, cy + 21,
        cx + int(5 * size), cy + 21 - shoot_h // 2,
        cx, cy + 21 - shoot_h
    ]
    canvas.create_line(stem_pts, fill=COLORS["cherry_bark_mid"], width=max(2, int(3.2 * size)), smooth=True)

    # Lower secondary green leaflet pair
    low_y = cy + 21 - int(shoot_h * 0.44)
    _draw_organic_lobe(canvas, cx - int(6 * size), low_y, int(7 * size), int(4 * size),
                       fill=COLORS["grass_lush"], num_pts=8, roughness=0.12, seed=54)
    _draw_organic_lobe(canvas, cx + int(9 * size), low_y - int(2 * size), int(7 * size), int(4 * size),
                       fill=COLORS["grass_bright"], num_pts=8, roughness=0.12, seed=55)

    top_y = cy + 21 - shoot_h
    # Two delicate blush pink flower budlets
    _draw_organic_lobe(canvas, cx - int(11 * size), top_y - int(3 * size), int(11 * size), int(7 * size),
                       fill=COLORS["cherry_petal_pink"], seed=50)
    _draw_organic_lobe(canvas, cx - int(10 * size), top_y - int(5 * size), int(8 * size), int(5 * size),
                       fill=COLORS["cherry_petal_soft"], seed=51)

    _draw_organic_lobe(canvas, cx + int(11 * size), top_y - int(2 * size), int(11 * size), int(7 * size),
                       fill=COLORS["cherry_petal_soft"], seed=52)
    _draw_organic_lobe(canvas, cx + int(10 * size), top_y - int(4 * size), int(8 * size), int(5 * size),
                       fill=COLORS["cherry_petal_white"], seed=53)


def draw_cherry_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(70 * size), int(12 * size))
    trunk_h = int(65 * size)
    top_y = cy + 28 - trunk_h

    # Slender curved mahogany trunk
    trunk_pts = [
        cx - int(4 * size), cy + 28,
        cx + int(3 * size), cy + 28,
        cx + int(5 * size), cy + 28 - trunk_h // 2,
        cx + int(2 * size), top_y,
        cx - int(1 * size), top_y,
        cx + int(1 * size), cy + 28 - trunk_h // 2,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_dark"], width=1, smooth=True)

    r = int(30 * size)
    # Sakura blossom puffs
    _draw_organic_lobe(canvas, cx, top_y + int(4 * size), r, int(r * 0.75), fill=COLORS["cherry_petal_shadow"], seed=60)
    _draw_organic_lobe(canvas, cx - int(6 * size), top_y - int(2 * size), int(r * 0.9), int(r * 0.8), fill=COLORS["cherry_petal_deep"], seed=61)
    _draw_organic_lobe(canvas, cx + int(5 * size), top_y - int(4 * size), int(r * 0.85), int(r * 0.75), fill=COLORS["cherry_petal_rose"], seed=62)
    _draw_organic_lobe(canvas, cx - int(4 * size), top_y - int(10 * size), int(r * 0.75), int(r * 0.65), fill=COLORS["cherry_petal_pink"], seed=63)
    _draw_organic_lobe(canvas, cx - int(6 * size), top_y - int(14 * size), int(r * 0.5), int(r * 0.45), fill=COLORS["cherry_petal_soft"], seed=64)


def draw_cherry_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(95 * size), int(15 * size))
    trunk_h = int(95 * size)
    top_y = cy + 35 - trunk_h

    # Graceful curved bonsai trunk
    trunk_pts = [
        cx - int(8 * size), cy + 33,
        cx - int(2 * size), cy + 30,
        cx + int(8 * size), cy + 35 - int(trunk_h * 0.5),
        cx + int(3 * size), top_y,
        cx - int(3 * size), top_y,
        cx + int(3 * size), cy + 35 - int(trunk_h * 0.5),
        cx - int(6 * size), cy + 30,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_dark"], width=1, smooth=True)

    # Branch forks
    boughs = [(-int(32 * size), -int(18 * size), 0.45), (int(30 * size), -int(24 * size), 0.5),
              (-int(20 * size), -int(35 * size), 0.75), (int(22 * size), -int(32 * size), 0.8)]
    for dx, dy, frac in boughs:
        by = cy + 35 - int(trunk_h * frac)
        canvas.create_line(cx + int(4 * size), by, cx + dx, by + dy, fill=COLORS["cherry_bark_mid"],
                           width=max(2, int(3 * size)), smooth=True)

    r = int(48 * size)
    clusters = [
        # Under-canopy shadow
        (0, int(r * 0.25), int(r * 0.78), int(r * 0.55), COLORS["cherry_petal_shadow"], 70),
        (-int(r * 0.5), int(r * 0.15), int(r * 0.68), int(r * 0.5), COLORS["cherry_petal_deep"], 71),
        (int(r * 0.5), int(r * 0.15), int(r * 0.68), int(r * 0.5), COLORS["cherry_petal_deep"], 72),
        # Mid-tone clouds
        (-int(r * 0.35), -int(r * 0.15), int(r * 0.75), int(r * 0.58), COLORS["cherry_petal_rose"], 73),
        (int(r * 0.35), -int(r * 0.15), int(r * 0.72), int(r * 0.55), COLORS["cherry_petal_vibrant"], 74),
        (0, -int(r * 0.1), int(r * 0.82), int(r * 0.62), COLORS["cherry_petal_pink"], 75),
        # Soft highlights
        (-int(r * 0.3), -int(r * 0.45), int(r * 0.68), int(r * 0.5), COLORS["cherry_petal_soft"], 76),
        (int(r * 0.2), -int(r * 0.45), int(r * 0.62), int(r * 0.46), COLORS["cherry_petal_soft"], 77),
        (-int(r * 0.2), -int(r * 0.65), int(r * 0.48), int(r * 0.38), COLORS["cherry_petal_white"], 78),
    ]
    for ox, oy, rx, ry, col, s in clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)


def draw_cherry_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(135 * size), int(18 * size))
    trunk_h = int(120 * size)
    top_y = cy + 40 - trunk_h

    # Elegant dark cherry wood trunk with artistic curves
    trunk_pts = [
        cx - int(20 * size), cy + 42,
        cx - int(10 * size), cy + 32,
        cx - int(3 * size), cy + 40 - int(trunk_h * 0.35),
        cx + int(8 * size), cy + 40 - int(trunk_h * 0.65),
        cx + int(5 * size), top_y,
        cx - int(5 * size), top_y,
        cx - int(1 * size), cy + 40 - int(trunk_h * 0.65),
        cx - int(9 * size), cy + 40 - int(trunk_h * 0.35),
        cx - int(15 * size), cy + 32,
        cx - int(24 * size), cy + 42,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["cherry_bark_dark"], outline=COLORS["cherry_bark_shadow"], width=2, smooth=True)

    # Highlight vein along curve
    canvas.create_line(
        cx - int(8 * size), cy + 35,
        cx + int(6 * size), cy + 40 - int(trunk_h * 0.6),
        cx + int(2 * size), top_y + int(10 * size),
        fill=COLORS["cherry_bark_light"], width=max(1, int(2 * size)), smooth=True
    )

    # Reaching cherry boughs
    limbs = [
        (-int(52 * size), -int(24 * size), 0.40, 4),
        (int(48 * size), -int(28 * size), 0.45, 4),
        (-int(36 * size), -int(52 * size), 0.70, 3),
        (int(38 * size), -int(48 * size), 0.75, 3),
    ]
    for dx, dy, frac, lw in limbs:
        by = cy + 40 - int(trunk_h * frac)
        canvas.create_line(cx + int(2 * size), by, cx + dx, by + dy, fill=COLORS["cherry_bark_mid"],
                           width=max(2, int(lw * size)), smooth=True)

    # Lush layered sakura blossom clouds
    r = int(72 * size)
    canopy_clusters = [
        # Under-blossom shadow
        (0, int(r * 0.35), int(r * 0.88), int(r * 0.58), COLORS["cherry_petal_shadow"], 80),
        (-int(r * 0.65), int(r * 0.25), int(r * 0.75), int(r * 0.52), COLORS["cherry_petal_deep"], 81),
        (int(r * 0.65), int(r * 0.25), int(r * 0.75), int(r * 0.52), COLORS["cherry_petal_deep"], 82),
        # Rose midtone
        (-int(r * 0.45), int(r * 0.05), int(r * 0.82), int(r * 0.6), COLORS["cherry_petal_rose"], 83),
        (int(r * 0.45), int(r * 0.05), int(r * 0.82), int(r * 0.6), COLORS["cherry_petal_vibrant"], 84),
        (0, int(r * 0.05), int(r * 0.92), int(r * 0.68), COLORS["cherry_petal_vibrant"], 85),
        # Pink blossom body
        (-int(r * 0.35), -int(r * 0.25), int(r * 0.82), int(r * 0.62), COLORS["cherry_petal_pink"], 86),
        (int(r * 0.35), -int(r * 0.25), int(r * 0.78), int(r * 0.58), COLORS["cherry_petal_pink"], 87),
        (0, -int(r * 0.2), int(r * 0.88), int(r * 0.66), COLORS["cherry_petal_soft"], 88),
        # Sunlit blossom crests (top-left)
        (-int(r * 0.4), -int(r * 0.5), int(r * 0.68), int(r * 0.5), COLORS["cherry_petal_soft"], 89),
        (int(r * 0.2), -int(r * 0.5), int(r * 0.62), int(r * 0.48), COLORS["cherry_petal_soft"], 90),
        (-int(r * 0.15), -int(r * 0.72), int(r * 0.58), int(r * 0.42), COLORS["cherry_petal_light"], 91),
        (-int(r * 0.3), -int(r * 0.78), int(r * 0.4), int(r * 0.3), COLORS["cherry_petal_white"], 92),
    ]
    for ox, oy, rx, ry, col, s in canopy_clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)

    # Falling petals fluttering down
    petal_offsets = [
        (-int(55 * size), -int(15 * size)), (-int(40 * size), int(10 * size)),
        (-int(20 * size), int(30 * size)), (int(35 * size), int(5 * size)),
        (int(50 * size), int(25 * size)), (int(15 * size), int(35 * size))
    ]
    for px, py in petal_offsets:
        canvas.create_oval(
            cx + px - 3, top_y + py - 2,
            cx + px + 3, top_y + py + 2,
            fill=COLORS["cherry_petal_soft"], outline=COLORS["cherry_petal_rose"], width=1
        )

    # Ground petal carpet
    ground_y = cy + 42
    for px in [-int(60 * size), -int(35 * size), -int(10 * size), int(15 * size), int(45 * size), int(65 * size)]:
        canvas.create_oval(
            cx + px - 4, ground_y - 2,
            cx + px + 4, ground_y + 2,
            fill=COLORS["cherry_petal_pink"], outline=COLORS["cherry_petal_rose"], width=1
        )


def draw_cherry_flourishing(canvas, cx, cy, size=1.0):
    draw_cherry_mature(canvas, cx, cy, size * 1.08)
    top_y = cy + 40 - int(120 * size * 1.08)
    r = int(72 * size * 1.08)

    # Glowing celestial sparkles in the sakura tree
    sparkles = [
        (-int(r * 0.75), -int(r * 0.45)), (int(r * 0.8), -int(r * 0.35)),
        (-int(r * 0.3), -int(r * 0.85)), (int(r * 0.3), -int(r * 0.8)),
        (0, -int(r * 0.95)), (-int(r * 0.85), int(r * 0.15)),
        (int(r * 0.85), int(r * 0.2))
    ]
    for ox, oy in sparkles:
        sx, sy = cx + ox, top_y + oy
        sl = int(5 * size)
        canvas.create_line(sx - sl, sy, sx + sl, sy, fill="#FFF0F5", width=2)
        canvas.create_line(sx, sy - sl, sx, sy + sl, fill="#FFF0F5", width=2)
        canvas.create_oval(sx - 2, sy - 2, sx + 2, sy + 2, fill="#FFFFFF", outline="")


# ══════════════════════════════════════════════════════════════════
# 3. PINE (CONIFER) (Majestic tiered alpine evergreen)
# ══════════════════════════════════════════════════════════════════

def draw_pine_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    # Pine moss & forest floor needles nest
    for ox, oy, col in ((-10, 15, COLORS["pine_needle_deep"]), (10, 15, COLORS["pine_needle_mid"]),
                        (-5, 18, COLORS["pine_needle_light"]), (5, 18, COLORS["pine_needle_bright"])):
        _draw_organic_lobe(canvas, cx + int(ox * size), cy + oy, int(7 * size), int(4 * size),
                           fill=col, num_pts=8, roughness=0.14, seed=220 + ox)
    # Prominent Pinecone seed (1.3x)
    cone_h = int(24 * size)
    cone_w = int(16 * size)
    py = cy + 12 - int(cone_h * 0.6)
    canvas.create_oval(
        cx - cone_w // 2, py,
        cx + cone_w // 2, py + cone_h,
        fill=COLORS["pine_cone_mid"], outline=COLORS["pine_cone_dark"], width=1
    )
    # Cone scale lines + warm glint
    for i in range(3):
        sy = py + int(cone_h * (0.25 + i * 0.25))
        canvas.create_line(cx - cone_w // 3, sy, cx + cone_w // 3, sy, fill=COLORS["pine_cone_dark"], width=1)
    canvas.create_oval(
        cx - int(3 * size), py + int(4 * size),
        cx, py + int(8 * size),
        fill="#D7CCC8", outline=""
    )


def draw_pine_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(11 * size))
    shoot_h = int(42 * size)
    # Root collar at base
    canvas.create_polygon(
        cx - int(4 * size), cy + 23,
        cx + int(4 * size), cy + 23,
        cx + int(2 * size), cy + 16,
        cx - int(2 * size), cy + 16,
        fill=COLORS["pine_bark_dark"], outline=""
    )
    # Slender conifer stem
    canvas.create_line(cx, cy + 21, cx, cy + 21 - shoot_h, fill=COLORS["pine_bark_mid"], width=max(2, int(3.2 * size)))
    # Lower secondary needle tufts
    low_y = cy + 21 - int(shoot_h * 0.45)
    for lx, ly in ((-9, -4), (-7, -8), (9, -4), (7, -8)):
        canvas.create_line(cx, low_y, cx + int(lx * size), low_y + int(ly * size),
                           fill=COLORS["pine_needle_dark"], width=max(1, int(2 * size)))

    top_y = cy + 21 - shoot_h
    # Radiating conifer needle whorl
    needle_angles = [-65, -42, -20, 0, 20, 42, 65]
    n_len = int(17 * size)
    for ang in needle_angles:
        rad = math.radians(ang - 90)
        nx = cx + n_len * math.cos(rad)
        ny = top_y + n_len * math.sin(rad)
        canvas.create_line(cx, top_y, int(nx), int(ny), fill=COLORS["pine_needle_mid"],
                           width=max(1, int(2.2 * size)))
    # Sunlit central leader needle
    canvas.create_line(cx, top_y, cx, top_y - int(n_len * 0.9), fill=COLORS["pine_needle_bright"],
                       width=max(1, int(2 * size)))


def draw_pine_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(70 * size), int(12 * size))
    trunk_h = int(65 * size)
    top_y = cy + 28 - trunk_h
    # Trunk
    canvas.create_polygon(
        cx - int(3 * size), cy + 28,
        cx + int(3 * size), cy + 28,
        cx + int(2 * size), top_y,
        cx - int(2 * size), top_y,
        fill=COLORS["pine_bark_mid"], outline=COLORS["pine_bark_dark"], width=1
    )
    # 2 needle skirt tiers
    _draw_pine_tier(canvas, cx, top_y + int(22 * size), int(26 * size), int(18 * size))
    _draw_pine_tier(canvas, cx, top_y + int(8 * size), int(18 * size), int(15 * size))


def _draw_pine_tier(canvas, cx, cy, width, height, serrations=5):
    """Draw a tiered evergreen needle skirt with organic serrated fringe."""
    half_w = width // 2
    pts = [cx, cy - height]
    # Right slope with needle serrations
    for i in range(1, serrations + 1):
        frac = i / serrations
        tx = cx + int(half_w * frac)
        ty = cy - height + int(height * frac)
        pts.extend([tx, ty])
        if i < serrations:
            pts.extend([tx - 3, ty + 2])
    # Bottom scallops
    pts.extend([cx, cy - int(height * 0.15)])
    # Left slope
    for i in range(serrations, 0, -1):
        frac = i / serrations
        tx = cx - int(half_w * frac)
        ty = cy - height + int(height * frac)
        if i < serrations:
            pts.extend([tx + 3, ty + 2])
        pts.extend([tx, ty])

    # Deep under-shadow tier
    canvas.create_polygon(pts, fill=COLORS["pine_needle_deep"], outline=COLORS["pine_needle_shadow"], width=1, smooth=True)
    # Sunlit left crest
    half_pts = [cx, cy - height]
    for i in range(1, serrations + 1):
        frac = i / serrations
        tx = cx - int(half_w * frac * 0.7)
        ty = cy - height + int(height * frac * 0.8)
        half_pts.extend([tx, ty])
    half_pts.extend([cx, cy - int(height * 0.3)])
    canvas.create_polygon(half_pts, fill=COLORS["pine_needle_light"], outline="", smooth=True)


def draw_pine_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(95 * size), int(15 * size))
    trunk_h = int(95 * size)
    top_y = cy + 35 - trunk_h

    # Trunk
    canvas.create_polygon(
        cx - int(6 * size), cy + 33,
        cx + int(6 * size), cy + 33,
        cx + int(3 * size), top_y,
        cx - int(3 * size), top_y,
        fill=COLORS["pine_bark_mid"], outline=COLORS["pine_bark_dark"], width=1
    )

    # 4 tiered conifer skirts
    tiers = [
        (int(36 * size), int(52 * size), int(26 * size)),
        (int(20 * size), int(42 * size), int(24 * size)),
        (int(6 * size), int(32 * size), int(20 * size)),
        (-int(6 * size), int(20 * size), int(16 * size)),
    ]
    for dy, tw, th in tiers:
        _draw_pine_tier(canvas, cx, top_y + dy, tw, th)


def draw_pine_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(135 * size), int(18 * size))
    trunk_h = int(125 * size)
    top_y = cy + 40 - trunk_h

    # Robust alpine conifer trunk
    trunk_pts = [
        cx - int(14 * size), cy + 42,
        cx - int(7 * size), cy + 30,
        cx - int(4 * size), top_y,
        cx + int(4 * size), top_y,
        cx + int(7 * size), cy + 30,
        cx + int(14 * size), cy + 42,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["pine_bark_mid"], outline=COLORS["pine_bark_shadow"], width=2, smooth=True)

    # Conifer bark plates
    for i in range(4):
        by = cy + 36 - int(trunk_h * (0.2 + i * 0.2))
        canvas.create_line(cx - int(4 * size), by, cx + int(4 * size), by - int(4 * size),
                           fill=COLORS["pine_bark_light"], width=max(1, int(2 * size)))

    # 5 majestic evergreen needle tiers
    tiers = [
        (int(46 * size), int(78 * size), int(34 * size)),
        (int(26 * size), int(64 * size), int(30 * size)),
        (int(8 * size), int(50 * size), int(26 * size)),
        (-int(8 * size), int(36 * size), int(22 * size)),
        (-int(22 * size), int(22 * size), int(18 * size)),
    ]
    for dy, tw, th in tiers:
        _draw_pine_tier(canvas, cx, top_y + dy, tw, th, serrations=6)

    # Hanging pinecones
    cones = [
        (-int(28 * size), top_y + int(46 * size)),
        (int(26 * size), top_y + int(48 * size)),
        (-int(18 * size), top_y + int(28 * size)),
        (int(20 * size), top_y + int(30 * size)),
    ]
    for px, py in cones:
        canvas.create_oval(px - 3, py, px + 3, py + int(8 * size),
                           fill=COLORS["pine_cone_mid"], outline=COLORS["pine_cone_dark"], width=1)


def draw_pine_flourishing(canvas, cx, cy, size=1.0):
    draw_pine_mature(canvas, cx, cy, size * 1.08)
    top_y = cy + 40 - int(125 * size * 1.08)

    # Alpine stars / frosty dawn glints
    glints = [
        (-int(38 * size), top_y + int(25 * size)), (int(36 * size), top_y + int(20 * size)),
        (0, top_y - int(30 * size)), (-int(22 * size), top_y + int(2 * size)),
        (int(24 * size), top_y + int(5 * size)), (-int(42 * size), top_y + int(50 * size)),
        (int(40 * size), top_y + int(52 * size))
    ]
    for sx, sy in glints:
        sl = int(5 * size)
        canvas.create_line(sx - sl, sy, sx + sl, sy, fill="#E0F2F1", width=2)
        canvas.create_line(sx, sy - sl, sx, sy + sl, fill="#E0F2F1", width=2)
        canvas.create_oval(sx - 2, sy - 2, sx + 2, sy + 2, fill="#FFFFFF", outline="")


# ══════════════════════════════════════════════════════════════════
# 4. ANGEL OAK (Ancient Live Oak with weeping Spanish Moss)
# ══════════════════════════════════════════════════════════════════

def draw_angel_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    # Cozy bed of sage moss & fern tufts
    for ox, oy, col in ((-11, 15, COLORS["angel_moss_deep"]), (11, 15, COLORS["angel_moss_sage"]),
                        (-6, 18, COLORS["angel_moss_light"]), (6, 18, COLORS["angel_foliage_mid"])):
        _draw_organic_lobe(canvas, cx + int(ox * size), cy + oy, int(7 * size), int(4 * size),
                           fill=col, num_pts=8, roughness=0.14, seed=230 + ox)
    # Prominent ancient mossy seed (1.3x)
    nut_h = int(21 * size)
    nut_w = int(18 * size)
    seed_cy = cy + 9
    canvas.create_oval(
        cx - nut_w // 2, seed_cy - nut_h // 2,
        cx + nut_w // 2, seed_cy + nut_h // 2,
        fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"], width=1
    )
    # Warm highlight glint
    canvas.create_oval(
        cx - int(4 * size), seed_cy - int(4 * size),
        cx - int(1 * size), seed_cy - int(1 * size),
        fill="#D7CCC8", outline=""
    )
    # Delicate draping strands of sage moss
    canvas.create_line(
        cx - 2, seed_cy, cx + int(10 * size), cy + 17,
        fill=COLORS["angel_moss_sage"], width=2, smooth=True
    )
    canvas.create_line(
        cx + 1, seed_cy + 2, cx + int(7 * size), cy + 19,
        fill=COLORS["angel_moss_light"], width=1, smooth=True
    )


def draw_angel_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(11 * size))
    shoot_h = int(40 * size)
    # Root collar flare
    canvas.create_polygon(
        cx - int(5 * size), cy + 23,
        cx + int(5 * size), cy + 23,
        cx + int(2 * size), cy + 16,
        cx - int(2 * size), cy + 16,
        fill=COLORS["angel_bark_mid"], outline=""
    )
    stem_pts = [
        cx, cy + 21,
        cx - int(5 * size), cy + 21 - shoot_h // 2,
        cx, cy + 21 - shoot_h
    ]
    canvas.create_line(stem_pts, fill=COLORS["angel_bark_dark"], width=max(2, int(3.4 * size)), smooth=True)

    # Lower secondary mossy leaflets
    low_y = cy + 21 - int(shoot_h * 0.45)
    _draw_organic_lobe(canvas, cx - int(9 * size), low_y, int(7 * size), int(4 * size),
                       fill=COLORS["angel_foliage_deep"], seed=102)
    _draw_organic_lobe(canvas, cx + int(7 * size), low_y - int(2 * size), int(7 * size), int(4 * size),
                       fill=COLORS["angel_foliage_mid"], seed=103)

    top_y = cy + 21 - shoot_h
    # Ancient mossy leaves
    _draw_organic_lobe(canvas, cx - int(12 * size), top_y - int(3 * size), int(12 * size), int(7 * size),
                       fill=COLORS["angel_foliage_mid"], seed=100)
    _draw_organic_lobe(canvas, cx + int(12 * size), top_y - int(2 * size), int(12 * size), int(7 * size),
                       fill=COLORS["angel_foliage_light"], seed=101)
    # First tiny drape of Spanish moss
    canvas.create_line(cx - int(8 * size), top_y + 1, cx - int(8 * size), top_y + int(10 * size),
                       fill=COLORS["angel_moss_sage"], width=1, dash=(2, 2))


def draw_angel_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(70 * size), int(12 * size))
    trunk_h = int(60 * size)
    top_y = cy + 28 - trunk_h

    # Slender ancient trunk
    canvas.create_polygon(
        cx - int(5 * size), cy + 28,
        cx + int(5 * size), cy + 28,
        cx + int(3 * size), top_y,
        cx - int(3 * size), top_y,
        fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"], width=1
    )
    r = int(32 * size)
    _draw_organic_lobe(canvas, cx, top_y + int(4 * size), r, int(r * 0.7), fill=COLORS["angel_foliage_shadow"], seed=110)
    _draw_organic_lobe(canvas, cx - int(6 * size), top_y - int(2 * size), int(r * 0.9), int(r * 0.75), fill=COLORS["angel_foliage_deep"], seed=111)
    _draw_organic_lobe(canvas, cx + int(5 * size), top_y - int(4 * size), int(r * 0.85), int(r * 0.7), fill=COLORS["angel_foliage_mid"], seed=112)
    _draw_organic_lobe(canvas, cx - int(4 * size), top_y - int(8 * size), int(r * 0.7), int(r * 0.6), fill=COLORS["angel_foliage_light"], seed=113)

    # First strand of Spanish Moss
    canvas.create_line(
        cx - int(15 * size), top_y + int(10 * size),
        cx - int(14 * size), top_y + int(24 * size),
        fill=COLORS["angel_moss_sage"], width=2, dash=(3, 2)
    )


def draw_angel_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(95 * size), int(15 * size))
    trunk_h = int(85 * size)
    top_y = cy + 35 - trunk_h

    # Low-slung, twisting gnarled trunk
    trunk_pts = [
        cx - int(14 * size), cy + 33,
        cx - int(6 * size), cy + 26,
        cx - int(5 * size), cy + 35 - int(trunk_h * 0.5),
        cx - int(4 * size), top_y,
        cx + int(4 * size), top_y,
        cx + int(5 * size), cy + 35 - int(trunk_h * 0.5),
        cx + int(8 * size), cy + 26,
        cx + int(16 * size), cy + 33,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"], width=2, smooth=True)

    # Sweeping horizontal boughs
    boughs = [(-int(38 * size), -int(12 * size), 0.35), (int(36 * size), -int(14 * size), 0.4),
              (-int(28 * size), -int(28 * size), 0.7), (int(26 * size), -int(26 * size), 0.75)]
    for dx, dy, frac in boughs:
        by = cy + 35 - int(trunk_h * frac)
        canvas.create_line(cx, by, cx + dx, by + dy, fill=COLORS["angel_bark_mid"],
                           width=max(2, int(4 * size)), smooth=True)

    r = int(52 * size)
    clusters = [
        (0, int(r * 0.2), int(r * 0.85), int(r * 0.5), COLORS["angel_foliage_shadow"], 120),
        (-int(r * 0.55), int(r * 0.1), int(r * 0.75), int(r * 0.45), COLORS["angel_foliage_deep"], 121),
        (int(r * 0.55), int(r * 0.1), int(r * 0.75), int(r * 0.45), COLORS["angel_foliage_deep"], 122),
        (-int(r * 0.3), -int(r * 0.15), int(r * 0.8), int(r * 0.5), COLORS["angel_foliage_mid"], 123),
        (int(r * 0.3), -int(r * 0.15), int(r * 0.75), int(r * 0.48), COLORS["angel_foliage_mid"], 124),
        (0, -int(r * 0.1), int(r * 0.85), int(r * 0.52), COLORS["angel_foliage_light"], 125),
    ]
    for ox, oy, rx, ry, col, s in clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)

    # Cascading Spanish Moss veils
    for mx in [-35, -20, -5, 10, 25, 38]:
        bx = cx + int(mx * size)
        by = top_y + int(12 * size)
        ml = int(22 * size)
        canvas.create_line(bx, by, bx, by + ml, fill=COLORS["angel_moss_sage"], width=2, dash=(3, 2))


def draw_angel_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(150 * size), int(20 * size))
    trunk_h = int(105 * size)
    top_y = cy + 40 - trunk_h

    # Immense ancient live oak trunk with massive spreading root flares
    trunk_pts = [
        cx - int(32 * size), cy + 42,
        cx - int(20 * size), cy + 30,
        cx - int(12 * size), cy + 40 - int(trunk_h * 0.4),
        cx - int(9 * size), top_y,
        cx + int(9 * size), top_y,
        cx + int(12 * size), cy + 40 - int(trunk_h * 0.4),
        cx + int(20 * size), cy + 30,
        cx + int(32 * size), cy + 42,
    ]
    canvas.create_polygon(trunk_pts, fill=COLORS["angel_bark_dark"], outline=COLORS["angel_bark_shadow"], width=2, smooth=True)

    # Ancient hollow & bark texture
    canvas.create_oval(
        cx - int(5 * size), cy + 22,
        cx + int(4 * size), cy + 34,
        fill=COLORS["angel_bark_shadow"], outline=""
    )

    # Heavy, massive wandering boughs that dip low to the earth
    limbs = [
        (-int(75 * size), -int(10 * size), 0.35, 6),
        (int(70 * size), -int(12 * size), 0.38, 6),
        (-int(55 * size), -int(35 * size), 0.60, 5),
        (int(52 * size), -int(32 * size), 0.65, 5),
        (-int(28 * size), -int(52 * size), 0.85, 4),
        (int(26 * size), -int(50 * size), 0.88, 4),
    ]
    for dx, dy, frac, lw in limbs:
        by = cy + 40 - int(trunk_h * frac)
        canvas.create_line(cx, by, cx + dx, by + dy, fill=COLORS["angel_bark_mid"],
                           width=max(2, int(lw * size)), smooth=True)

    # Expansive, sprawling ancient umbrella canopy
    r = int(82 * size)
    canopy_clusters = [
        # Under-canopy shadow
        (0, int(r * 0.28), int(r * 0.95), int(r * 0.45), COLORS["angel_foliage_shadow"], 130),
        (-int(r * 0.7), int(r * 0.18), int(r * 0.8), int(r * 0.42), COLORS["angel_foliage_shadow"], 131),
        (int(r * 0.7), int(r * 0.18), int(r * 0.8), int(r * 0.42), COLORS["angel_foliage_shadow"], 132),
        # Deep forest body
        (-int(r * 0.48), int(r * 0.05), int(r * 0.88), int(r * 0.48), COLORS["angel_foliage_deep"], 133),
        (int(r * 0.48), int(r * 0.05), int(r * 0.88), int(r * 0.48), COLORS["angel_foliage_deep"], 134),
        (0, int(r * 0.02), int(r * 1.0), int(r * 0.52), COLORS["angel_foliage_mid"], 135),
        # Midtone & sunlit tiers
        (-int(r * 0.38), -int(r * 0.18), int(r * 0.85), int(r * 0.48), COLORS["angel_foliage_mid"], 136),
        (int(r * 0.38), -int(r * 0.18), int(r * 0.82), int(r * 0.45), COLORS["angel_foliage_mid"], 137),
        (0, -int(r * 0.15), int(r * 0.92), int(r * 0.5), COLORS["angel_foliage_light"], 138),
        (-int(r * 0.25), -int(r * 0.35), int(r * 0.7), int(r * 0.38), COLORS["angel_foliage_light"], 139),
    ]
    for ox, oy, rx, ry, col, s in canopy_clusters:
        _draw_organic_lobe(canvas, cx + ox, top_y + oy, rx, ry, fill=col, seed=s)

    # Graceful hanging Spanish Moss curtains
    moss_strands = [-72, -58, -44, -30, -16, 2, 18, 32, 46, 60, 74]
    for mx in moss_strands:
        bx = cx + int(mx * size)
        by = top_y + int(10 * size) + random.randint(-4, 12)
        ml = random.randint(int(24 * size), int(48 * size))
        canvas.create_line(
            bx, by,
            bx + random.randint(-2, 2), by + ml // 2,
            bx + random.randint(-2, 2), by + ml,
            fill=COLORS["angel_moss_sage"], width=max(1, int(2 * size)),
            dash=(3, 2), smooth=True
        )


def draw_angel_flourishing(canvas, cx, cy, size=1.0):
    draw_angel_mature(canvas, cx, cy, size * 1.08)
    top_y = cy + 40 - int(105 * size * 1.08)
    r = int(82 * size * 1.08)

    # Enchanted forest fireflies / ethereal sun motes
    motes = [
        (-int(r * 0.85), int(r * 0.1)), (int(r * 0.88), int(r * 0.15)),
        (-int(r * 0.45), -int(r * 0.4)), (int(r * 0.4), -int(r * 0.35)),
        (0, -int(r * 0.45)), (-int(r * 0.6), int(r * 0.3)),
        (int(r * 0.65), int(r * 0.35)), (-int(15 * size), int(r * 0.2))
    ]
    for ox, oy in motes:
        sx, sy = cx + ox, top_y + oy
        # Soft glowing halo
        canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill="#F0FDF4", outline="")
        canvas.create_oval(sx - 2, sy - 2, sx + 2, sy + 2, fill="#BBF7D0", outline="")


# ══════════════════════════════════════════════════════════════════
# DISPATCH TABLE
# ══════════════════════════════════════════════════════════════════

SPECIES_DRAWERS = {
    "oak": {
        "seed": draw_oak_seed,
        "sprout": draw_oak_sprout,
        "seedling": draw_oak_seedling,
        "young": draw_oak_young,
        "mature": draw_oak_mature,
        "flourishing": draw_oak_flourishing,
    },
    "cherry_blossom": {
        "seed": draw_cherry_seed,
        "sprout": draw_cherry_sprout,
        "seedling": draw_cherry_seedling,
        "young": draw_cherry_young,
        "mature": draw_cherry_mature,
        "flourishing": draw_cherry_flourishing,
    },
    "pine": {
        "seed": draw_pine_seed,
        "sprout": draw_pine_sprout,
        "seedling": draw_pine_seedling,
        "young": draw_pine_young,
        "mature": draw_pine_mature,
        "flourishing": draw_pine_flourishing,
    },
    "angel_oak": {
        "seed": draw_angel_seed,
        "sprout": draw_angel_sprout,
        "seedling": draw_angel_seedling,
        "young": draw_angel_young,
        "mature": draw_angel_mature,
        "flourishing": draw_angel_flourishing,
    },
}


def draw_tree(canvas, stage, cx=None, cy=None, size=1.0, species="oak"):
    """Draw a tree of the given species and stage on the canvas."""
    if cx is None:
        cx = int(canvas.winfo_width() / 2)
    if cy is None:
        cy = int(canvas.winfo_height() / 2 + 20)

    spec_table = SPECIES_DRAWERS.get(species, SPECIES_DRAWERS["oak"])
    drawer = spec_table.get(stage, spec_table["seed"])
    drawer(canvas, cx, cy, size)


def draw_mini_tree(canvas, stage, cx, cy, size=0.4, species="oak"):
    """Draw a small tree of the given species and stage for the forest view."""
    global _IN_MINI_TREE
    spec_table = SPECIES_DRAWERS.get(species, SPECIES_DRAWERS["oak"])
    drawer = spec_table.get(stage, spec_table["seed"])
    prev = _IN_MINI_TREE
    _IN_MINI_TREE = True
    try:
        drawer(canvas, cx, cy, size)
    finally:
        _IN_MINI_TREE = prev
