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
    "cherry_petal_shadow": "#9E2A5B",
    "cherry_petal_deep": "#C24678",
    "cherry_petal_rose": "#D86390",
    "cherry_petal_vibrant": "#E876A0",
    "cherry_petal_pink": "#F48FB1",
    "cherry_petal_soft": "#F8BBD0",
    "cherry_petal_light": "#FCE4EC",
    "cherry_petal_white": "#FFF8FA",

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
    "angel_bark_mossy": "#42523A",
    "angel_foliage_shadow": "#1B3B2B",
    "angel_foliage_deep": "#224834",
    "angel_foliage_mid": "#2D5A3C",
    "angel_foliage_light": "#4A7C59",
    "angel_foliage_sun": "#5E926C",
    "angel_moss_shadow": "#7C9488",
    "angel_moss_deep": "#7C9488",
    "angel_moss_sage": "#9DB2A6",
    "angel_moss_light": "#B7C9BF",
    "angel_moss_sun": "#D3E2CC",
    "angel_firefly_halo": "#FEF08A",
    "angel_firefly_core": "#FDE047",

    # Weeping Willow
    "willow_bark_shadow": "#2B1F19",
    "willow_bark_dark": "#3E2E26",
    "willow_bark_mid": "#4E3B31",
    "willow_bark_light": "#6B5347",
    "willow_leaf_shadow": "#244A33",
    "willow_leaf_deep": "#3A6B4C",
    "willow_leaf_mid": "#5E9C71",
    "willow_leaf_light": "#8BC499",

    # Japanese Maple
    "maple_bark_shadow": "#221615",
    "maple_bark_dark": "#3B2826",
    "maple_bark_mid": "#523835",
    "maple_bark_light": "#73524D",
    "maple_leaf_shadow": "#6A1822",
    "maple_leaf_crimson": "#8E2430",
    "maple_leaf_scarlet": "#C93B3B",
    "maple_leaf_amber": "#E87A3E",
    "maple_leaf_peach": "#F4A261",

    # Moonlit Blossom
    "moon_bark_shadow": "#141221",
    "moon_bark_dark": "#252338",
    "moon_bark_mid": "#353250",
    "moon_bark_light": "#4F4B73",
    "moon_petal_shadow": "#2B264A",
    "moon_petal_deep": "#3B3561",
    "moon_petal_mid": "#6C63A6",
    "moon_petal_cyan": "#7CE8FF",
    "moon_petal_glow": "#D8F8FF",
}

SPECIES_METADATA = {
    "oak": {
        "id": "oak",
        "name": "Classic Oak",
        "icon": "🌳",
        "rarity": "Common",
        "tagline": "Sturdy, balanced & enduring",
        "theme_color": "#2E7D32",
        "particles": ["🍃", "🌱", "💧"],
    },
    "cherry_blossom": {
        "id": "cherry_blossom",
        "name": "Cherry Blossom",
        "icon": "🌸",
        "rarity": "Common",
        "tagline": "Graceful pink sakura blooms",
        "theme_color": "#D81B60",
        "particles": ["🌸", "💮", "✨"],
    },
    "pine": {
        "id": "pine",
        "name": "Pine",
        "icon": "🌲",
        "rarity": "Common",
        "tagline": "Resilient alpine evergreen",
        "theme_color": "#1E684C",
        "particles": ["🌲", "❄️", "✨"],
    },
    "angel_oak": {
        "id": "angel_oak",
        "name": "Angel Oak",
        "icon": "🌿",
        "rarity": "Common",
        "tagline": "Ancient mystical canopy",
        "theme_color": "#3E332C",
        "particles": ["🌿", "✨", "🌟"],
    },
    "willow": {
        "id": "willow",
        "name": "Weeping Willow",
        "icon": "🪴",
        "rarity": "Rare",
        "tagline": "Graceful cascading emerald vines",
        "theme_color": "#3A6B4C",
        "particles": ["🌿", "🍃", "💧"],
    },
    "maple": {
        "id": "maple",
        "name": "Japanese Maple",
        "icon": "🍁",
        "rarity": "Epic",
        "tagline": "Vibrant autumn crimson canopy",
        "theme_color": "#C93B3B",
        "particles": ["🍁", "🍂", "✨"],
    },
    "moonlit_blossom": {
        "id": "moonlit_blossom",
        "name": "Moonlit Blossom",
        "icon": "💠",
        "rarity": "Mythic",
        "tagline": "Rare luminous nocturnal flora",
        "theme_color": "#6C63A6",
        "particles": ["✨", "💠", "🌙"],
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


def _draw_tapered_branch(canvas, pts, w_start, w_end, fill, outline=""):
    """Draw a naturally curving branch polygon that tapers from w_start to w_end."""
    if len(pts) < 2:
        return
    left_side = []
    right_side = []
    n = len(pts)
    for i, (px, py) in enumerate(pts):
        t = i / (n - 1)
        half_w = max(0.7, (w_start * (1.0 - t) + w_end * t) * 0.5)
        if i == 0:
            tx, ty = pts[1][0] - px, pts[1][1] - py
        elif i == n - 1:
            tx, ty = px - pts[i - 1][0], py - pts[i - 1][1]
        else:
            tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        length = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / length, tx / length
        left_side.append((px + nx * half_w, py + ny * half_w))
        right_side.append((px - nx * half_w, py - ny * half_w))
    poly = left_side + list(reversed(right_side))
    flat = [coord for pt in poly for coord in pt]
    canvas.create_polygon(
        flat, fill=fill, outline=outline, width=1 if outline else 0, smooth=True
    )


def _draw_organic_root_trunk(
    canvas, cx, base_y, top_y, base_w, top_w, curve_dx, root_spread,
    fill, outline, bark_hi, bark_dark, size=1.0, seed=1, gnarled=False
):
    """Draw a curved organic trunk with splayed root flare and textured bark details."""
    h = max(12, base_y - top_y)
    mid1_y = base_y - h * 0.34
    mid2_y = base_y - h * 0.70
    mid1_x = cx + curve_dx * 0.35
    mid2_x = cx + curve_dx * 0.88
    top_x = cx + curve_dx * 0.72

    pts = [
        cx - root_spread, base_y + 2 * size,
        cx - root_spread * 0.65, base_y - 4 * size,
        cx - base_w * 0.52, base_y - 11 * size,
        mid1_x - base_w * 0.40, mid1_y,
        mid2_x - top_w * 0.58, mid2_y,
        top_x - top_w * 0.48, top_y,
        top_x + top_w * 0.48, top_y,
        mid2_x + top_w * 0.58, mid2_y,
        mid1_x + base_w * 0.40, mid1_y,
        cx + base_w * 0.55, base_y - 11 * size,
        cx + root_spread * 0.68, base_y - 4 * size,
        cx + root_spread, base_y + 2 * size,
        cx + root_spread * 0.35, base_y + 3 * size,
        cx, base_y + 1 * size,
        cx - root_spread * 0.35, base_y + 3 * size,
    ]
    canvas.create_polygon(pts, fill=fill, outline=outline, width=max(1, int(1.5 * size)), smooth=True)

    if root_spread >= 10 * size:
        for side in (-1, 1):
            rx0 = cx + side * base_w * 0.22
            rx1 = cx + side * root_spread * 0.88
            _draw_tapered_branch(
                canvas,
                [(rx0, base_y - 10 * size), (cx + side * root_spread * 0.55, base_y - 2 * size), (rx1, base_y + 3 * size)],
                max(2.0, base_w * 0.24), max(1.0, 1.5 * size),
                fill=fill, outline=outline
            )

    canvas.create_line(
        cx - base_w * 0.18, base_y - 9 * size,
        mid1_x - base_w * 0.14, mid1_y,
        mid2_x - top_w * 0.18, mid2_y,
        top_x - top_w * 0.12, top_y + 6 * size,
        fill=bark_hi, width=max(1, int(1.8 * size)), smooth=True
    )

    rng = random.Random(seed)
    if gnarled:
        for frac, ox_frac in ((0.18, 0.12), (0.38, -0.10), (0.56, 0.16), (0.74, -0.08)):
            by0 = base_y - h * frac
            by1 = by0 - h * 0.18
            bx0 = cx + curve_dx * frac + base_w * ox_frac
            canvas.create_line(
                bx0, by0,
                bx0 + rng.uniform(-3, 3) * size, (by0 + by1) * 0.5,
                bx0 + rng.uniform(-2, 2) * size, by1,
                fill=bark_dark, width=max(1, int(1.6 * size)), smooth=True
            )
    else:
        for frac in (0.24, 0.42, 0.60, 0.78):
            ly = base_y - h * frac
            lx = cx + curve_dx * frac * 0.8 + rng.uniform(-2, 2) * size
            lw = max(3, int(base_w * 0.26 * (1.0 - frac * 0.35)))
            canvas.create_line(
                lx - lw, ly, lx + lw, ly,
                fill=bark_dark, width=max(1, int(1.3 * size))
            )


def _draw_scalloped_cluster(canvas, cx, cy, rx, ry, fill, outline="", puffs=7, seed=1):
    """Draw an airy, scalloped foliage/blossom cluster with overlapping pixel-art sub-lobes."""
    rng = random.Random(seed)
    _draw_organic_lobe(canvas, cx, cy, rx * 0.78, ry * 0.74, fill=fill, outline=outline, num_pts=14, roughness=0.22, seed=seed)
    for i in range(puffs):
        ang = (2.0 * math.pi * i) / puffs + rng.uniform(-0.22, 0.22)
        dist = rng.uniform(0.42, 0.66)
        px = cx + math.cos(ang) * rx * dist
        py = cy + math.sin(ang) * ry * dist
        prx = max(2.5, rx * rng.uniform(0.36, 0.52))
        pry = max(2.5, ry * rng.uniform(0.36, 0.52))
        _draw_organic_lobe(canvas, px, py, prx, pry, fill=fill, outline=outline, num_pts=10, roughness=0.18, seed=seed + i + 11)


def _draw_dither_pixels(canvas, cx, cy, rx, ry, color, count=10, px_size=3, seed=1):
    """Scatter small crisp pixel-art highlight clusters inside upper canopy crests."""
    rng = random.Random(seed)
    ps = max(1.5, px_size)
    for _ in range(count):
        ang = rng.uniform(0, 2.0 * math.pi)
        rad = math.sqrt(rng.uniform(0.05, 0.85))
        px = cx + math.cos(ang) * rx * rad
        py = cy + math.sin(ang) * ry * rad
        canvas.create_rectangle(
            px - ps * 0.5, py - ps * 0.5,
            px + ps * 0.5, py + ps * 0.5,
            fill=color, outline=""
        )


def _draw_spanish_moss_strand(canvas, x, y, units, size, color_main, color_deep, seed=1):
    """Draw an organic tapered hanging strand of Spanish moss (2 to 6 pixel units tall)."""
    rng = random.Random(seed)
    unit_px = max(2.0, 4.0 * size)
    length = units * unit_px
    sway = rng.uniform(-1.8, 1.8) * size
    w_top = max(1.4, 2.8 * size)
    _draw_tapered_branch(
        canvas,
        [(x, y), (x + sway * 0.5, y + length * 0.55), (x + sway, y + length)],
        w_top, max(0.7, 0.8 * size),
        fill=color_main
    )
    if units >= 3:
        ox = rng.choice((-1.5, 1.5)) * size
        _draw_tapered_branch(
            canvas,
            [(x + ox, y + unit_px * 0.4), (x + ox + sway * 0.4, y + length * 0.72)],
            max(1.0, 1.8 * size), max(0.6, 0.7 * size),
            fill=color_deep
        )


def _draw_tiny_soil_mound(canvas, cx, cy, size=1.0):
    """Draw a tiny, organic textured dark-loam mound with speckles for nestled seeds."""
    mw = max(6, int(13 * size))
    mh = max(3, int(5.5 * size))
    # Soft earthy contact shadow
    canvas.create_oval(
        cx - mw * 1.08, cy - mh * 0.35,
        cx + mw * 1.08, cy + mh * 0.90,
        fill="#26331F", outline=""
    )
    # Raised dark-loam mound with warm earthy outline
    mound_pts = [
        cx - mw * 0.92, cy + mh * 0.4,
        cx - mw * 0.62, cy - mh * 0.5,
        cx - mw * 0.10, cy - mh * 0.92,
        cx + mw * 0.42, cy - mh * 0.72,
        cx + mw * 0.88, cy + mh * 0.3,
        cx + mw * 0.50, cy + mh * 0.72,
        cx - mw * 0.42, cy + mh * 0.76,
    ]
    canvas.create_polygon(mound_pts, fill="#4A3525", outline="#2E261F", width=1, smooth=True)
    # Soft highlight around the nestled seed
    canvas.create_oval(
        cx - mw * 0.45, cy - mh * 0.52,
        cx + mw * 0.42, cy + mh * 0.18,
        fill="#5E4634", outline=""
    )
    # Tiny organic loam speckles
    for ox, oy, col in (
        (-int(6 * size), int(2 * size), "#2E261F"),
        (int(7 * size), int(1 * size), "#3B332A"),
        (int(2 * size), int(3 * size), "#6B513D"),
        (-int(3 * size), -int(1 * size), "#6B513D"),
    ):
        canvas.create_oval(cx + ox - 1, cy + oy - 1, cx + ox + 1, cy + oy + 1, fill=col, outline="")


def _draw_shadow_and_soil(canvas, cx, cy, rx, ry, grass_color="#43A047"):
    """Draw a grounded stone-ringed garden clearing with soft ambient grass shadow,
    textured dark-loam mound, concentric watering rings, and overlapping grass/wildflowers."""
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

    s_rx = rx
    s_ry = max(int(ry * 1.2), int(rx * 0.27))

    # 0. Soft ambient shadow beneath stones & outer rim so the ring sits IN the grass
    canvas.create_oval(
        cx - int(s_rx * 1.12), cy - int(s_ry * 1.02),
        cx + int(s_rx * 1.12), cy + int(s_ry * 1.16),
        fill="#24341E", outline=""
    )
    canvas.create_oval(
        cx - int(s_rx * 1.02), cy - int(s_ry * 0.92),
        cx + int(s_rx * 1.02), cy + int(s_ry * 1.05),
        fill="#2B3D24", outline=""
    )

    # Organically spaced 5 accent stones (3 clustered on left, 2 on right), leaving open grass/wildflower gaps
    accent_stone_specs = [
        # Left cluster (3 stones of varied sizes)
        (2.58, 0.96, 0.17, 0.42),
        (2.96, 0.93, 0.21, 0.50),
        (3.40, 0.97, 0.14, 0.36),
        # Right cluster (2 stones of varied sizes)
        (0.18, 0.95, 0.19, 0.46),
        (5.86, 0.94, 0.15, 0.38),
    ]
    cobblestones = []
    for i, (ang, r_mul, wf, hf) in enumerate(accent_stone_specs):
        kx = cx + s_rx * r_mul * math.cos(ang)
        ky = cy + s_ry * r_mul * math.sin(ang)
        sw = max(5, int(s_rx * wf))
        sh = max(3, int(s_ry * hf))
        cobblestones.append((i, kx, ky, sw, sh, ang))

    def _draw_cobblestone(idx, kx, ky, sw, sh):
        stone_pts = [
            kx - sw, ky,
            kx - sw * 0.7, ky - sh * 0.85,
            kx + sw * 0.55, ky - sh * 0.9,
            kx + sw, ky - sh * 0.15,
            kx + sw * 0.75, ky + sh * 0.8,
            kx - sw * 0.55, ky + sh * 0.85,
        ]
        # Warm earthy stone outline (#2E261F / #3B332A) instead of harsh black
        s_fill = "#7E7A70" if idx % 2 == 0 else "#747066"
        s_out = "#2E261F" if idx % 2 == 0 else "#3B332A"
        canvas.create_polygon(stone_pts, fill=s_fill, outline=s_out, width=1, smooth=True)
        # Soft sunlit top highlight
        canvas.create_line(
            kx - sw * 0.6, ky - sh * 0.45,
            kx, ky - sh * 0.7,
            kx + sw * 0.5, ky - sh * 0.5,
            fill="#ADA99D", width=1.4, smooth=True
        )
        # Subtle moss patch on select cobblestones
        if idx % 3 != 1:
            mox = kx - sw * 0.25 if idx % 2 == 0 else kx + sw * 0.2
            moy = ky + sh * 0.15 if idx % 2 == 0 else ky - sh * 0.2
            mr = max(1.5, sw * 0.28)
            canvas.create_oval(
                mox - mr, moy - mr * 0.6,
                mox + mr, moy + mr * 0.6,
                fill="#596F4B" if idx % 2 == 0 else "#4B613E", outline=""
            )

    # 1. Back cobblestones (upper rim, ky < cy) drawn behind the soil mound
    back_stones = [s for s in cobblestones if s[2] < cy]
    for idx, kx, ky, sw, sh, _ in back_stones:
        _draw_cobblestone(idx, kx, ky, sw, sh)

    # 2. Raised, textured dark-loam mound with warm earthy rim & concentric watering rings
    canvas.create_oval(
        cx - int(s_rx * 0.86), cy - int(s_ry * 0.78),
        cx + int(s_rx * 0.86), cy + int(s_ry * 0.86),
        fill="#2E261F", outline=""
    )
    soil_pts = []
    n_soil_pts = 16
    for i in range(n_soil_pts):
        ang = (i / n_soil_pts) * 6.2831853
        wob = 1.0 + 0.032 * math.sin(i * 3.1) - 0.018 * math.cos(i * 4.7)
        px = cx + s_rx * 0.82 * wob * math.cos(ang)
        py = cy + s_ry * 0.78 * wob * math.sin(ang)
        soil_pts.extend((px, py))
    canvas.create_polygon(soil_pts, fill="#3D2B1F", outline="#2E261F", width=1, smooth=True)

    # Slightly raised inner loam dome
    canvas.create_oval(
        cx - int(s_rx * 0.68), cy - int(s_ry * 0.62),
        cx + int(s_rx * 0.68), cy + int(s_ry * 0.56),
        fill="#4E3828", outline=""
    )
    # Soft highlight around the planted seed / sprout center
    canvas.create_oval(
        cx - int(s_rx * 0.36), cy - int(s_ry * 0.34),
        cx + int(s_rx * 0.36), cy + int(s_ry * 0.24),
        fill="#5E4634", outline=""
    )

    # Concentric watering rings
    for ring_f, ring_col in ((0.64, "#36251A"), (0.44, "#664D3A"), (0.26, "#3B291E")):
        canvas.create_oval(
            cx - int(s_rx * ring_f), cy - int(s_ry * ring_f * 0.82),
            cx + int(s_rx * ring_f), cy + int(s_ry * ring_f * 0.78),
            fill="", outline=ring_col, width=1
        )

    # Organic soil crumb speckles
    rng_soil = random.Random(42)
    for k in range(18):
        ang = rng_soil.uniform(0, 6.2831853)
        rad = math.sqrt(rng_soil.uniform(0.08, 0.82))
        sx = cx + s_rx * 0.70 * rad * math.cos(ang)
        sy = cy + s_ry * 0.65 * rad * math.sin(ang)
        sr = 1.4 if k % 3 != 0 else 1.8
        scol = ("#2E261F", "#6E5440", "#7A5E48")[k % 3]
        canvas.create_oval(sx - sr, sy - sr * 0.7, sx + sr, sy + sr * 0.7, fill=scol, outline="")

    # 3. Front cobblestones (lower rim, ky >= cy) with soft earthy ambient contact shadow
    front_stones = [s for s in cobblestones if s[2] >= cy]
    for _, kx, ky, sw, sh, _ in front_stones:
        canvas.create_oval(
            kx - sw * 0.92, ky + sh * 0.22,
            kx + sw * 0.92, ky + sh * 1.05,
            fill="#25341F", outline=""
        )
    for idx, kx, ky, sw, sh, _ in front_stones:
        _draw_cobblestone(idx, kx, ky, sw, sh)

    # 4. Foreground grass blades, clover tufts & tiny wildflowers overlapping bottom stones & soil rim
    tuft_angles = [0.05, 0.35, 0.65, 0.95, 1.25, 1.55, 1.85, 2.15, 2.45, 2.75, 3.05, 3.65, 4.55, 5.55]
    flower_cols = ("#FFF3B0", "#FFE082", "#F8BBD0", "#E8F5E9")
    for i, tang in enumerate(tuft_angles):
        is_front = (0.05 <= tang <= 3.10)
        dist_r = s_rx * ((0.96 if is_front else 0.86) + 0.08 * math.sin(i * 2.3))
        dist_ry = s_ry * ((0.98 if is_front else 0.84) + 0.08 * math.cos(i * 1.9))
        gx = cx + dist_r * math.cos(tang)
        gy = cy + dist_ry * math.sin(tang)
        b_len = max(5, int(s_ry * (0.55 if is_front else 0.42)))
        canvas.create_line(gx, gy + 1, gx - 2.5, gy - b_len, fill="#4E753F", width=1.2)
        canvas.create_line(gx, gy + 1, gx + 2.5, gy - int(b_len * 0.88), fill="#699254", width=1.1)
        canvas.create_line(gx, gy + 1, gx, gy - int(b_len * 1.15), fill="#7DA764", width=1.1)

        # Clover tufts & tiny wildflowers in front of the bottom stone rim
        if is_front and i % 3 == 1:
            for lx, ly in ((-2.2, -1.5), (2.2, -1.2), (0, -3.0)):
                canvas.create_oval(
                    gx + lx - 1.8, gy + ly - 1.3,
                    gx + lx + 1.8, gy + ly + 1.3,
                    fill="#5D8A4B", outline=""
                )
        if is_front and i % 4 == 2:
            fcol = flower_cols[i % len(flower_cols)]
            fy = gy - int(b_len * 0.72)
            canvas.create_oval(gx - 2, fy - 2, gx + 2, fy + 2, fill=fcol, outline="")
            canvas.create_oval(gx - 0.8, fy - 0.8, gx + 0.8, fy + 0.8, fill="#F59E0B", outline="")


# ══════════════════════════════════════════════════════════════════
# 1. CLASSIC OAK (Lush, volumetric, regal woodland oak)
# ══════════════════════════════════════════════════════════════════

def draw_oak_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 18, size)

    # Delicate organic acorn nestled into the soil mound (40% size)
    nut_h = max(4, int(10 * size))
    nut_w = max(3, int(7 * size))
    sy = cy + 17 - int(nut_h * 0.45)

    # Pointed acorn nut body tapering into the soil
    nut_pts = [
        cx - nut_w // 2, sy,
        cx - nut_w // 2 + 1, sy + int(nut_h * 0.55),
        cx, sy + nut_h,
        cx + nut_w // 2 - 1, sy + int(nut_h * 0.55),
        cx + nut_w // 2, sy,
    ]
    canvas.create_polygon(nut_pts, fill="#8D6E63", outline="#4E342E", width=1, smooth=True)
    # Sun highlight glint on acorn
    canvas.create_oval(
        cx - max(1, int(2 * size)), sy + max(1, int(2 * size)),
        cx, sy + max(2, int(4 * size)),
        fill="#EFE6DF", outline=""
    )

    # Classic Acorn Cap
    cap_w = max(4, int(8.5 * size))
    cap_h = max(2, int(4 * size))
    canvas.create_oval(
        cx - cap_w // 2, sy - cap_h // 2,
        cx + cap_w // 2, sy + cap_h // 2,
        fill="#5D4037", outline="#3E2723", width=1
    )
    # Cap texture cross-line
    canvas.create_line(cx - cap_w // 3, sy, cx + cap_w // 3, sy, fill="#3E2723", width=1)
    # Tiny curved stem
    stem_top_y = sy - cap_h // 2 - max(2, int(3 * size))
    canvas.create_line(
        cx, sy - cap_h // 2,
        cx - max(1, int(1.5 * size)), stem_top_y,
        fill="#3E2723", width=1
    )

    # Tiny emerging pale-green shoot (1-2 tiny curved leaves)
    shoot_h = max(3, int(7 * size))
    shoot_tip_x = cx + max(1, int(2 * size))
    shoot_tip_y = stem_top_y - shoot_h + max(1, int(1.5 * size))
    canvas.create_line(
        cx, sy - cap_h // 2,
        cx + max(1, int(1.5 * size)), sy - cap_h // 2 - int(shoot_h * 0.5),
        shoot_tip_x, shoot_tip_y,
        fill="#81C784", width=max(1, int(1.4 * size)), smooth=True
    )
    # 2 tiny curved sprout leaves at tip
    leaf_w = max(2, int(3.5 * size))
    leaf_h = max(2, int(2.5 * size))
    canvas.create_oval(
        shoot_tip_x - leaf_w, shoot_tip_y - leaf_h,
        shoot_tip_x, shoot_tip_y + leaf_h // 2,
        fill="#66BB6A", outline="#43A047", width=1
    )
    canvas.create_oval(
        shoot_tip_x - 1, shoot_tip_y - int(leaf_h * 0.8),
        shoot_tip_x + leaf_w - 1, shoot_tip_y + int(leaf_h * 0.3),
        fill="#81C784", outline="", width=0
    )

    # Cozy moss / clover leaflets nestled in the soil
    for ox, oy, col in ((-int(7 * size), int(16 * size), "#4E7037"), (int(8 * size), int(17 * size), "#689F38")):
        _draw_organic_lobe(canvas, cx + ox, cy + oy, max(2, int(3.5 * size)), max(2, int(2.2 * size)),
                           fill=col, num_pts=6, roughness=0.12, seed=200 + ox)


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
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 18, size)

    # Delicate pointed sakura pit nestled into soil (40% size)
    pit_h = max(4, int(9.5 * size))
    pit_w = max(3, int(6.5 * size))
    sy = cy + 17 - int(pit_h * 0.45)

    pit_pts = [
        cx, sy - max(1, int(1.5 * size)),
        cx - pit_w // 2, sy + int(pit_h * 0.35),
        cx - max(1, int(1.5 * size)), sy + pit_h,
        cx + max(1, int(1.5 * size)), sy + pit_h,
        cx + pit_w // 2, sy + int(pit_h * 0.35),
    ]
    canvas.create_polygon(pit_pts, fill="#6D4C41", outline="#4A3528", width=1, smooth=True)
    # Center pit ridge & glint
    canvas.create_line(cx, sy, cx, sy + int(pit_h * 0.7), fill="#4E342E", width=1)
    canvas.create_oval(
        cx - max(1, int(2 * size)), sy + max(1, int(2 * size)),
        cx - 1, sy + max(2, int(3.5 * size)),
        fill="#D7CCC8", outline=""
    )

    # Tiny emerging pale-green shoot with sprout leaf
    shoot_h = max(3, int(6.5 * size))
    shoot_tip_x = cx + max(1, int(2 * size))
    shoot_tip_y = sy - shoot_h
    canvas.create_line(
        cx, sy,
        cx + 1, sy - int(shoot_h * 0.5),
        shoot_tip_x, shoot_tip_y,
        fill="#81C784", width=max(1, int(1.3 * size)), smooth=True
    )
    lw = max(2, int(3 * size))
    lh = max(2, int(2 * size))
    canvas.create_oval(
        shoot_tip_x, shoot_tip_y - lh,
        shoot_tip_x + lw, shoot_tip_y + lh // 2,
        fill="#66BB6A", outline="#388E3C", width=1
    )

    # Species-tinted detail: Tiny emerging pink blossom bud beside shoot
    bud_x = cx - max(1, int(2.5 * size))
    bud_y = sy - max(1, int(3 * size))
    bw = max(2, int(3.2 * size))
    bh = max(2, int(2.8 * size))
    canvas.create_oval(
        bud_x - bw // 2, bud_y - bh // 2,
        bud_x + bw // 2, bud_y + bh // 2,
        fill="#FFB7C5", outline="#F48FB1", width=1
    )
    canvas.create_oval(
        bud_x - max(1, int(1 * size)), bud_y - max(1, int(1.5 * size)),
        bud_x + max(1, int(1 * size)), bud_y,
        fill="#FFF0F5", outline=""
    )

    # Tiny fallen pink petal resting beside it on the rich soil
    canvas.create_oval(
        cx + int(8 * size), cy + 18,
        cx + int(14 * size), cy + int(21.5 * size),
        fill="#FFB7C5", outline="#F06292", width=1
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
    base_y = cy + 28
    trunk_h = int(65 * size)
    top_y = base_y - trunk_h

    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y,
        base_w=8 * size, top_w=3 * size, curve_dx=6 * size, root_spread=10 * size,
        fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_shadow"],
        bark_hi=COLORS["cherry_bark_light"], bark_dark=COLORS["cherry_bark_shadow"],
        size=size, seed=60, gnarled=False
    )
    # Small Y-split forks at crown
    _draw_tapered_branch(
        canvas,
        [(cx + 3 * size, top_y + 12 * size), (cx - 10 * size, top_y + 2 * size), (cx - 18 * size, top_y - 4 * size)],
        3 * size, 1 * size, fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_shadow"]
    )
    _draw_tapered_branch(
        canvas,
        [(cx + 4 * size, top_y + 10 * size), (cx + 12 * size, top_y), (cx + 19 * size, top_y - 5 * size)],
        2.8 * size, 1 * size, fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_shadow"]
    )

    r = int(28 * size)
    _draw_scalloped_cluster(canvas, cx - 10 * size, top_y + 2 * size, r * 0.85, r * 0.6, fill=COLORS["cherry_petal_shadow"], puffs=5, seed=61)
    _draw_scalloped_cluster(canvas, cx + 10 * size, top_y, r * 0.8, r * 0.56, fill=COLORS["cherry_petal_deep"], puffs=5, seed=62)
    _draw_scalloped_cluster(canvas, cx - 5 * size, top_y - 6 * size, r * 0.9, r * 0.65, fill=COLORS["cherry_petal_pink"], puffs=6, seed=63)
    _draw_scalloped_cluster(canvas, cx + 8 * size, top_y - 8 * size, r * 0.72, r * 0.52, fill=COLORS["cherry_petal_light"], puffs=5, seed=64)
    _draw_dither_pixels(canvas, cx, top_y - 9 * size, r * 0.7, r * 0.4, COLORS["cherry_petal_white"], count=6, px_size=max(1.5, 2.2 * size), seed=65)


def draw_cherry_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(98 * size), int(15 * size))
    base_y = cy + 33
    trunk_h = int(92 * size)
    top_y = base_y - trunk_h

    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 16 * size,
        base_w=13 * size, top_w=5 * size, curve_dx=8 * size, root_spread=16 * size,
        fill=COLORS["cherry_bark_mid"], outline=COLORS["cherry_bark_shadow"],
        bark_hi=COLORS["cherry_bark_light"], bark_dark=COLORS["cherry_bark_shadow"],
        size=size, seed=70, gnarled=False
    )

    r = int(50 * size)
    # Lower shadow pockets behind branches
    _draw_scalloped_cluster(canvas, cx - 28 * size, top_y + 10 * size, r * 0.68, r * 0.46, fill=COLORS["cherry_petal_shadow"], puffs=6, seed=71)
    _draw_scalloped_cluster(canvas, cx + 26 * size, top_y + 14 * size, r * 0.62, r * 0.44, fill=COLORS["cherry_petal_shadow"], puffs=6, seed=72)

    # Multi-tiered curved Y-split branches tapering into the umbrella canopy
    branch_paths = [
        ([(cx + 3 * size, base_y - trunk_h * 0.48), (cx - 16 * size, top_y + 24 * size), (cx - 38 * size, top_y + 10 * size)], 5.0, 1.4),
        ([(cx - 16 * size, top_y + 24 * size), (cx - 24 * size, top_y + 8 * size), (cx - 28 * size, top_y - 8 * size)], 2.8, 1.0),
        ([(cx + 5 * size, base_y - trunk_h * 0.56), (cx + 20 * size, top_y + 22 * size), (cx + 40 * size, top_y + 8 * size)], 4.6, 1.3),
        ([(cx + 20 * size, top_y + 22 * size), (cx + 22 * size, top_y + 4 * size), (cx + 24 * size, top_y - 12 * size)], 2.6, 1.0),
        ([(cx + 5 * size, top_y + 18 * size), (cx - 4 * size, top_y - 2 * size), (cx - 8 * size, top_y - 18 * size)], 3.8, 1.1),
    ]
    for pts, ws, we in branch_paths:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["cherry_bark_dark"], outline=COLORS["cherry_bark_shadow"])

    # Asymmetric airy umbrella clusters leaving gaps so sub-branches peek through
    _draw_scalloped_cluster(canvas, cx - 32 * size, top_y + 2 * size, r * 0.72, r * 0.48, fill=COLORS["cherry_petal_pink"], puffs=7, seed=73)
    _draw_scalloped_cluster(canvas, cx + 32 * size, top_y + 6 * size, r * 0.68, r * 0.46, fill=COLORS["cherry_petal_pink"], puffs=7, seed=74)
    _draw_scalloped_cluster(canvas, cx - 8 * size, top_y - 14 * size, r * 0.78, r * 0.52, fill=COLORS["cherry_petal_pink"], puffs=7, seed=75)
    _draw_scalloped_cluster(canvas, cx - 18 * size, top_y - 22 * size, r * 0.62, r * 0.42, fill=COLORS["cherry_petal_light"], puffs=6, seed=76)
    _draw_scalloped_cluster(canvas, cx + 14 * size, top_y - 18 * size, r * 0.58, r * 0.40, fill=COLORS["cherry_petal_light"], puffs=6, seed=77)
    _draw_dither_pixels(canvas, cx - 6 * size, top_y - 22 * size, r * 0.75, r * 0.36, COLORS["cherry_petal_white"], count=10, px_size=max(2, 2.6 * size), seed=78)

    # Tiny fallen petals around base
    for px, py, col in [(-24, 2, "cherry_petal_pink"), (-8, 5, "cherry_petal_light"), (14, 3, "cherry_petal_pink"), (26, 1, "cherry_petal_light")]:
        pw = max(1.5, 2.6 * size)
        ph = max(1.0, 1.5 * size)
        canvas.create_oval(cx + px * size - pw, base_y + py * size - ph, cx + px * size + pw, base_y + py * size + ph, fill=COLORS[col], outline="")


def draw_cherry_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(142 * size), int(18 * size))
    base_y = cy + 40
    trunk_h = int(112 * size)
    top_y = base_y - trunk_h

    # Curved dark sakura trunk with splayed root flare & lenticel marks
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 24 * size,
        base_w=22 * size, top_w=8 * size, curve_dx=10 * size, root_spread=26 * size,
        fill=COLORS["cherry_bark_dark"], outline=COLORS["cherry_bark_shadow"],
        bark_hi=COLORS["cherry_bark_light"], bark_dark=COLORS["cherry_bark_shadow"],
        size=size, seed=80, gnarled=False
    )

    r = int(76 * size)
    # 1. Deep rose-magenta lower shadow pockets (#9E2A5B / #C24678)
    shadow_puffs = [
        (-56, 22, 0.56, 0.38, COLORS["cherry_petal_shadow"], 81),
        (52, 26, 0.52, 0.36, COLORS["cherry_petal_shadow"], 82),
        (-18, 12, 0.64, 0.42, COLORS["cherry_petal_deep"], 83),
        (22, 16, 0.58, 0.38, COLORS["cherry_petal_deep"], 84),
    ]
    for ox, oy, rx_f, ry_f, col, s in shadow_puffs:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rx_f, r * ry_f, fill=col, puffs=6, seed=s)

    # 2. Multi-tiered Y-split boughs & sub-branches peeking through foliage gaps
    boughs = [
        # Left sweeping lower bough + Y-fork
        ([(cx + 3 * size, base_y - trunk_h * 0.42), (cx - 24 * size, top_y + 42 * size), (cx - 56 * size, top_y + 22 * size), (cx - 78 * size, top_y + 10 * size)], 7.5, 1.8),
        ([(cx - 38 * size, top_y + 32 * size), (cx - 52 * size, top_y + 8 * size), (cx - 64 * size, top_y - 12 * size)], 3.8, 1.1),
        # Right sweeping bough + Y-fork
        ([(cx + 8 * size, base_y - trunk_h * 0.48), (cx + 32 * size, top_y + 36 * size), (cx + 62 * size, top_y + 18 * size), (cx + 80 * size, top_y + 8 * size)], 7.0, 1.7),
        ([(cx + 40 * size, top_y + 28 * size), (cx + 46 * size, top_y + 4 * size), (cx + 52 * size, top_y - 16 * size)], 3.6, 1.1),
        # Upper crown Y-splits
        ([(cx + 7 * size, top_y + 28 * size), (cx - 12 * size, top_y + 2 * size), (cx - 26 * size, top_y - 24 * size)], 5.5, 1.4),
        ([(cx + 7 * size, top_y + 26 * size), (cx + 18 * size, top_y), (cx + 26 * size, top_y - 22 * size)], 5.0, 1.3),
    ]
    for pts, ws, we in boughs:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["cherry_bark_dark"], outline=COLORS["cherry_bark_shadow"])

    # 3. Asymmetric wide-spreading umbrella canopy: warm sakura pink mid-tones (#F48FB1)
    mid_clusters = [
        (-66, 4, 0.56, 0.38, COLORS["cherry_petal_pink"], 85),
        (64, 10, 0.54, 0.36, COLORS["cherry_petal_pink"], 86),
        (-34, -14, 0.62, 0.42, COLORS["cherry_petal_pink"], 87),
        (28, -8, 0.58, 0.40, COLORS["cherry_petal_pink"], 88),
        (-4, -22, 0.64, 0.44, COLORS["cherry_petal_soft"], 89),
    ]
    for ox, oy, rx_f, ry_f, col, s in mid_clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rx_f, r * ry_f, fill=col, puffs=7, seed=s)

    # Small visible upper twig tips peeking through gaps between clusters
    for pts in (
        [(cx - 28 * size, top_y + 6 * size), (cx - 38 * size, top_y - 10 * size)],
        [(cx + 24 * size, top_y + 4 * size), (cx + 34 * size, top_y - 12 * size)],
    ):
        _draw_tapered_branch(canvas, pts, 2.4 * size, 0.9 * size, fill=COLORS["cherry_bark_shadow"])

    # 4. Soft blush upper clusters (#FCE4EC) + scattered pixel highlights (#FFF8FA)
    upper_clusters = [
        (-46, -24, 0.46, 0.32, COLORS["cherry_petal_light"], 90),
        (36, -20, 0.44, 0.30, COLORS["cherry_petal_light"], 91),
        (-12, -38, 0.52, 0.34, COLORS["cherry_petal_light"], 92),
    ]
    for ox, oy, rx_f, ry_f, col, s in upper_clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rx_f, r * ry_f, fill=col, puffs=6, seed=s)

    _draw_dither_pixels(canvas, cx - 10 * size, top_y - 36 * size, r * 0.56, r * 0.28, COLORS["cherry_petal_white"], count=12, px_size=max(2, 2.8 * size), seed=93)
    _draw_dither_pixels(canvas, cx - 50 * size, top_y - 16 * size, r * 0.36, r * 0.24, COLORS["cherry_petal_white"], count=7, px_size=max(2, 2.6 * size), seed=94)
    _draw_dither_pixels(canvas, cx + 40 * size, top_y - 14 * size, r * 0.34, r * 0.22, COLORS["cherry_petal_white"], count=7, px_size=max(2, 2.6 * size), seed=95)

    # 5. Subtle falling petals + 5 tiny pink petals resting on dirt/grass around base
    for px, py in [(-56, 28), (-26, 42), (38, 34), (62, 46)]:
        pw = max(1.5, 2.6 * size)
        ph = max(1.0, 1.6 * size)
        canvas.create_oval(
            cx + px * size - pw, top_y + py * size - ph,
            cx + px * size + pw, top_y + py * size + ph,
            fill=COLORS["cherry_petal_light"], outline=COLORS["cherry_petal_rose"], width=1
        )

    for px, py, col in [
        (-48, 3, "cherry_petal_pink"),
        (-22, 6, "cherry_petal_light"),
        (6, 5, "cherry_petal_pink"),
        (32, 4, "cherry_petal_light"),
        (54, 2, "cherry_petal_pink"),
    ]:
        pw = max(1.8, 3.0 * size)
        ph = max(1.1, 1.7 * size)
        canvas.create_oval(
            cx + px * size - pw, base_y + py * size - ph,
            cx + px * size + pw, base_y + py * size + ph,
            fill=COLORS[col], outline=""
        )


def draw_cherry_flourishing(canvas, cx, cy, size=1.0):
    draw_cherry_mature(canvas, cx, cy, size * 1.08)
    top_y = cy + 40 - int(112 * size * 1.08)
    r = int(76 * size * 1.08)

    # Subtle celestial sparkles in the sakura canopy
    sparkles = [
        (-int(r * 0.78), -int(r * 0.22)), (int(r * 0.76), -int(r * 0.16)),
        (-int(r * 0.30), -int(r * 0.62)), (int(r * 0.28), -int(r * 0.56)),
        (0, -int(r * 0.72)), (-int(r * 0.86), int(r * 0.24)),
    ]
    for ox, oy in sparkles:
        sx, sy = cx + ox, top_y + oy
        sl = max(2, int(4.5 * size))
        canvas.create_line(sx - sl, sy, sx + sl, sy, fill=COLORS["cherry_petal_white"], width=max(1, int(1.8 * size)))
        canvas.create_line(sx, sy - sl, sx, sy + sl, fill=COLORS["cherry_petal_white"], width=max(1, int(1.8 * size)))
        canvas.create_oval(sx - 1.8, sy - 1.8, sx + 1.8, sy + 1.8, fill="#FFFFFF", outline="")


# ══════════════════════════════════════════════════════════════════
# 3. PINE (CONIFER) (Majestic tiered alpine evergreen)
# ══════════════════════════════════════════════════════════════════

def draw_pine_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 18, size)

    # Delicate pointed pine nut seed with winged scale (40% size)
    nut_h = max(4, int(10 * size))
    nut_w = max(3, int(6 * size))
    sy = cy + 17 - int(nut_h * 0.45)

    # Teardrop pine nut nestled into soil
    nut_pts = [
        cx, sy,
        cx - nut_w // 2, sy + int(nut_h * 0.4),
        cx - 1, sy + nut_h,
        cx + 1, sy + nut_h,
        cx + nut_w // 2, sy + int(nut_h * 0.4),
    ]
    canvas.create_polygon(nut_pts, fill="#5D4037", outline="#3E2723", width=1, smooth=True)
    # Winged seed scale detail along one flank
    canvas.create_polygon(
        cx + nut_w // 2 - 1, sy + int(nut_h * 0.2),
        cx + nut_w // 2 + max(1, int(2.5 * size)), sy + int(nut_h * 0.5),
        cx + nut_w // 2, sy + int(nut_h * 0.8),
        fill="#8D6E63", outline="", smooth=True
    )
    # Sun glint
    canvas.create_oval(
        cx - max(1, int(1.5 * size)), sy + max(1, int(2 * size)),
        cx, sy + max(2, int(4 * size)),
        fill="#D7CCC8", outline=""
    )

    # Species-tinted detail: Emerging pine needle tip (2 tiny needle-like sprout leaves)
    needle_h = max(3, int(6.5 * size))
    # Left needle
    canvas.create_line(
        cx, sy,
        cx - max(1, int(2 * size)), sy - needle_h,
        fill="#4CAF50", width=max(1, int(1.2 * size))
    )
    # Right needle
    canvas.create_line(
        cx, sy,
        cx + max(1, int(2.2 * size)), sy - int(needle_h * 0.9),
        fill="#81C784", width=max(1, int(1.2 * size))
    )
    # Tiny sunlit tip
    canvas.create_oval(
        cx - max(1, int(2.5 * size)), sy - needle_h - 1,
        cx - max(1, int(1.5 * size)), sy - needle_h + 1,
        fill="#C8E6C9", outline=""
    )

    # 2 tiny dropped needles on the dark soil
    canvas.create_line(
        cx - int(9 * size), cy + 18,
        cx - int(4 * size), cy + int(19.5 * size),
        fill="#4E342E", width=1
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
    _draw_tiny_soil_mound(canvas, cx, cy + 18, size)

    # Ancient mystical teardrop seed nestled into soil (40% size)
    nut_h = max(4, int(10 * size))
    nut_w = max(3, int(7 * size))
    sy = cy + 17 - int(nut_h * 0.45)

    nut_pts = [
        cx, sy,
        cx - nut_w // 2, sy + int(nut_h * 0.4),
        cx - 1, sy + nut_h,
        cx + 1, sy + nut_h,
        cx + nut_w // 2, sy + int(nut_h * 0.4),
    ]
    canvas.create_polygon(nut_pts, fill="#543D2B", outline="#36281D", width=1, smooth=True)
    # Sage moss striations
    canvas.create_line(cx - 1, sy + 2, cx - 1, sy + int(nut_h * 0.7), fill="#81977A", width=1)
    # Sun glint
    canvas.create_oval(
        cx - max(1, int(2 * size)), sy + max(1, int(2 * size)),
        cx, sy + max(2, int(4 * size)),
        fill="#D7CCC8", outline=""
    )

    # Tiny ethereal emerging shoot with 2 delicate curved leaves
    shoot_h = max(3, int(6.5 * size))
    shoot_tip_x = cx + max(1, int(1.5 * size))
    shoot_tip_y = sy - shoot_h
    canvas.create_line(
        cx, sy,
        cx + 1, sy - int(shoot_h * 0.5),
        shoot_tip_x, shoot_tip_y,
        fill="#9CCC65", width=max(1, int(1.3 * size)), smooth=True
    )
    # Delicate sage-green sprout leaves
    canvas.create_oval(
        shoot_tip_x - max(2, int(3 * size)), shoot_tip_y - max(1, int(1.8 * size)),
        shoot_tip_x, shoot_tip_y + max(1, int(1 * size)),
        fill="#AED581", outline="#7CB342", width=1
    )
    canvas.create_oval(
        shoot_tip_x, shoot_tip_y - max(1, int(2 * size)),
        shoot_tip_x + max(2, int(2.5 * size)), shoot_tip_y + max(1, int(0.8 * size)),
        fill="#C5E1A5", outline="", width=0
    )

    # Delicate draping strands of sage moss around seed
    canvas.create_line(
        cx - 2, sy + int(nut_h * 0.5),
        cx + int(6 * size), cy + 18,
        fill=COLORS["angel_moss_sage"], width=1.5, smooth=True
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
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(74 * size), int(12 * size))
    base_y = cy + 28
    trunk_h = int(58 * size)
    top_y = base_y - trunk_h

    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y,
        base_w=10 * size, top_w=4 * size, curve_dx=-4 * size, root_spread=13 * size,
        fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"],
        bark_hi=COLORS["angel_bark_light"], bark_dark=COLORS["angel_bark_shadow"],
        size=size, seed=110, gnarled=True
    )
    _draw_tapered_branch(
        canvas,
        [(cx - 2 * size, top_y + 14 * size), (cx - 14 * size, top_y + 8 * size), (cx - 22 * size, top_y + 2 * size)],
        3.5 * size, 1.1 * size, fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"]
    )
    _draw_tapered_branch(
        canvas,
        [(cx, top_y + 12 * size), (cx + 12 * size, top_y + 6 * size), (cx + 21 * size, top_y)],
        3.4 * size, 1.1 * size, fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"]
    )

    r = int(32 * size)
    _draw_scalloped_cluster(canvas, cx - 10 * size, top_y + 4 * size, r * 0.85, r * 0.56, fill=COLORS["angel_foliage_shadow"], puffs=5, seed=111)
    _draw_scalloped_cluster(canvas, cx + 10 * size, top_y + 2 * size, r * 0.82, r * 0.54, fill=COLORS["angel_foliage_deep"], puffs=5, seed=112)
    _draw_scalloped_cluster(canvas, cx, top_y - 4 * size, r * 0.92, r * 0.6, fill=COLORS["angel_foliage_mid"], puffs=6, seed=113)
    _draw_scalloped_cluster(canvas, cx - 6 * size, top_y - 9 * size, r * 0.7, r * 0.45, fill=COLORS["angel_foliage_light"], puffs=5, seed=114)

    _draw_spanish_moss_strand(canvas, cx - 16 * size, top_y + 8 * size, 3, size, COLORS["angel_moss_sage"], COLORS["angel_moss_deep"], seed=115)
    _draw_spanish_moss_strand(canvas, cx + 13 * size, top_y + 7 * size, 2, size, COLORS["angel_moss_sage"], COLORS["angel_moss_deep"], seed=116)


def draw_angel_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(112 * size), int(16 * size))
    base_y = cy + 33
    trunk_h = int(80 * size)
    top_y = base_y - trunk_h

    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 16 * size,
        base_w=20 * size, top_w=8 * size, curve_dx=-5 * size, root_spread=24 * size,
        fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"],
        bark_hi=COLORS["angel_bark_light"], bark_dark=COLORS["angel_bark_shadow"],
        size=size, seed=120, gnarled=True
    )

    r = int(58 * size)
    # Lower canopy shadow clusters
    _draw_scalloped_cluster(canvas, cx - 34 * size, top_y + 12 * size, r * 0.72, r * 0.42, fill=COLORS["angel_foliage_shadow"], puffs=6, seed=121)
    _draw_scalloped_cluster(canvas, cx + 34 * size, top_y + 12 * size, r * 0.72, r * 0.42, fill=COLORS["angel_foliage_shadow"], puffs=6, seed=122)

    # Low-splitting sweeping boughs dipping slightly before curving upward
    boughs = [
        ([(cx - 4 * size, base_y - trunk_h * 0.34), (cx - 26 * size, base_y - trunk_h * 0.28), (cx - 46 * size, base_y - trunk_h * 0.34), (cx - 56 * size, top_y + 18 * size)], 6.5, 1.8),
        ([(cx + 4 * size, base_y - trunk_h * 0.38), (cx + 26 * size, base_y - trunk_h * 0.31), (cx + 46 * size, base_y - trunk_h * 0.36), (cx + 56 * size, top_y + 16 * size)], 6.2, 1.7),
        ([(cx - 4 * size, top_y + 24 * size), (cx - 22 * size, top_y + 6 * size), (cx - 32 * size, top_y - 10 * size)], 4.5, 1.4),
        ([(cx + 2 * size, top_y + 22 * size), (cx + 20 * size, top_y + 4 * size), (cx + 30 * size, top_y - 12 * size)], 4.2, 1.3),
    ]
    for pts, ws, we in boughs:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"])

    # Layered mossy canopy clusters
    _draw_scalloped_cluster(canvas, cx - 40 * size, top_y + 4 * size, r * 0.70, r * 0.42, fill=COLORS["angel_foliage_mid"], puffs=6, seed=123)
    _draw_scalloped_cluster(canvas, cx + 38 * size, top_y + 4 * size, r * 0.70, r * 0.42, fill=COLORS["angel_foliage_mid"], puffs=6, seed=124)
    _draw_scalloped_cluster(canvas, cx, top_y - 6 * size, r * 0.86, r * 0.48, fill=COLORS["angel_foliage_mid"], puffs=7, seed=125)
    _draw_scalloped_cluster(canvas, cx - 18 * size, top_y - 16 * size, r * 0.65, r * 0.38, fill=COLORS["angel_foliage_light"], puffs=6, seed=126)
    _draw_scalloped_cluster(canvas, cx + 18 * size, top_y - 14 * size, r * 0.60, r * 0.36, fill=COLORS["angel_foliage_light"], puffs=6, seed=127)
    _draw_dither_pixels(canvas, cx, top_y - 16 * size, r * 0.70, r * 0.28, COLORS["angel_foliage_sun"], count=8, px_size=max(2, 2.4 * size), seed=128)

    # Organic irregularly spaced tapered Spanish moss strands (2 to 5 units)
    for mx, my, units, ms in [(-46, 16, 4, 129), (-34, 10, 2, 130), (-19, 14, 5, 131), (17, 13, 3, 132), (35, 11, 4, 133), (48, 17, 2, 134)]:
        _draw_spanish_moss_strand(canvas, cx + mx * size, top_y + my * size, units, size, COLORS["angel_moss_sage"], COLORS["angel_moss_deep"], seed=ms)


def draw_angel_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(175 * size), int(22 * size))
    base_y = cy + 40
    trunk_h = int(104 * size)
    top_y = base_y - trunk_h

    # Thick gnarled trunk with deep bark lines & root ridges gripping the grass shadow
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 28 * size,
        base_w=36 * size, top_w=16 * size, curve_dx=-6 * size, root_spread=40 * size,
        fill=COLORS["angel_bark_dark"], outline=COLORS["angel_bark_shadow"],
        bark_hi=COLORS["angel_bark_light"], bark_dark=COLORS["angel_bark_shadow"],
        size=size, seed=130, gnarled=True
    )

    # Subtle gnarled hollow & root-base grass tufts
    canvas.create_oval(
        cx - int(5 * size), cy + 20,
        cx + int(4 * size), cy + 31,
        fill=COLORS["angel_bark_shadow"], outline=""
    )

    r = int(94 * size)
    # 1. Deep forest shadow underside (#1B3B2B)
    shadow_clusters = [
        (-74, 18, 0.56, 0.34, COLORS["angel_foliage_shadow"], 131),
        (74, 18, 0.56, 0.34, COLORS["angel_foliage_shadow"], 132),
        (0, 12, 0.80, 0.38, COLORS["angel_foliage_shadow"], 133),
    ]
    for ox, oy, rxf, ryf, col, s in shadow_clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rxf, r * ryf, fill=col, puffs=7, seed=s)

    # 2. Low-splitting, heavy sweeping horizontal limbs that dip low toward the ground then curve back up
    sweeping_limbs = [
        # Left lowest sweeping bough (dips down toward base_y - 12 then curls up)
        ([(cx - 8 * size, base_y - trunk_h * 0.30), (cx - 38 * size, base_y - trunk_h * 0.14), (cx - 72 * size, base_y - trunk_h * 0.10), (cx - 98 * size, base_y - trunk_h * 0.24), (cx - 104 * size, base_y - trunk_h * 0.40)], 11.5, 2.2),
        # Right lowest sweeping bough (dips low then curls up)
        ([(cx + 6 * size, base_y - trunk_h * 0.32), (cx + 38 * size, base_y - trunk_h * 0.16), (cx + 72 * size, base_y - trunk_h * 0.12), (cx + 96 * size, base_y - trunk_h * 0.26), (cx + 102 * size, base_y - trunk_h * 0.42)], 11.0, 2.2),
        # Mid-tier spreading boughs + Y-splits
        ([(cx - 6 * size, base_y - trunk_h * 0.54), (cx - 38 * size, top_y + 38 * size), (cx - 68 * size, top_y + 22 * size), (cx - 84 * size, top_y + 6 * size)], 8.5, 1.8),
        ([(cx - 46 * size, top_y + 34 * size), (cx - 56 * size, top_y + 12 * size), (cx - 62 * size, top_y - 10 * size)], 4.5, 1.3),
        ([(cx + 4 * size, base_y - trunk_h * 0.56), (cx + 36 * size, top_y + 36 * size), (cx + 66 * size, top_y + 20 * size), (cx + 82 * size, top_y + 6 * size)], 8.2, 1.8),
        ([(cx + 44 * size, top_y + 32 * size), (cx + 54 * size, top_y + 10 * size), (cx + 60 * size, top_y - 12 * size)], 4.4, 1.3),
        # Upper dome Y-splits
        ([(cx - 4 * size, top_y + 34 * size), (cx - 18 * size, top_y + 6 * size), (cx - 30 * size, top_y - 18 * size)], 6.5, 1.5),
        ([(cx - 2 * size, top_y + 32 * size), (cx + 16 * size, top_y + 6 * size), (cx + 28 * size, top_y - 16 * size)], 6.2, 1.5),
    ]
    for pts, ws, we in sweeping_limbs:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["angel_bark_mid"], outline=COLORS["angel_bark_shadow"])

    # Subtle mossy patches along upper backs of sweeping limbs
    for mx, my, mw in [(-42, 46, 12), (38, 44, 12), (-24, 24, 9)]:
        canvas.create_oval(
            cx + (mx - mw) * size, top_y + my * size - 2 * size,
            cx + (mx + mw) * size, top_y + my * size + 2.5 * size,
            fill=COLORS["angel_bark_mossy"], outline=""
        )

    # 3. Broad wide-domed canopy: rich mossy & deep forest greens (#224834, #2D5A3C, #4A7C59)
    mid_clusters = [
        (-92, 16, 0.42, 0.28, COLORS["angel_foliage_deep"], 134),
        (90, 16, 0.42, 0.28, COLORS["angel_foliage_deep"], 135),
        (-60, -4, 0.56, 0.34, COLORS["angel_foliage_mid"], 136),
        (58, -4, 0.56, 0.34, COLORS["angel_foliage_mid"], 137),
        (0, -10, 0.74, 0.40, COLORS["angel_foliage_mid"], 138),
    ]
    for ox, oy, rxf, ryf, col, s in mid_clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rxf, r * ryf, fill=col, puffs=7, seed=s)

    # Upper sunlit mossy foliage clusters (#4A7C59) + pixel texture highlights
    top_clusters = [
        (-48, -22, 0.46, 0.28, COLORS["angel_foliage_light"], 139),
        (44, -20, 0.44, 0.26, COLORS["angel_foliage_light"], 140),
        (-14, -30, 0.54, 0.32, COLORS["angel_foliage_light"], 141),
        (16, -28, 0.48, 0.28, COLORS["angel_foliage_light"], 142),
    ]
    for ox, oy, rxf, ryf, col, s in top_clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rxf, r * ryf, fill=col, puffs=6, seed=s)

    _draw_dither_pixels(canvas, cx - 10 * size, top_y - 26 * size, r * 0.68, r * 0.24, COLORS["angel_foliage_sun"], count=14, px_size=max(2, 2.8 * size), seed=143)

    # 4. Organic irregularly spaced, tapered hanging Spanish Moss strands (2 to 6 units tall)
    moss_specs = [
        (-95, 30, 4, 150), (-82, 24, 6, 151), (-71, 48, 3, 152), (-58, 18, 5, 153),
        (-44, 54, 4, 154), (-31, 20, 2, 155), (-18, 15, 5, 156), (16, 16, 4, 157),
        (29, 22, 6, 158), (43, 52, 3, 159), (56, 18, 5, 160), (70, 46, 4, 161),
        (83, 25, 6, 162), (96, 31, 3, 163),
    ]
    for mx, my, units, ms in moss_specs:
        _draw_spanish_moss_strand(
            canvas, cx + mx * size, top_y + my * size, units, size,
            COLORS["angel_moss_sage"], COLORS["angel_moss_deep"], seed=ms
        )

    # 5. Subtle golden firefly/sparkle accents near the base
    base_motes = [
        (-54, -4), (-32, -12), (34, -10), (58, -3), (-16, -6), (20, -15),
    ]
    for ox, oy in base_motes:
        fx, fy = cx + ox * size, base_y + oy * size
        hr = max(2.2, 3.6 * size)
        cr = max(1.1, 1.7 * size)
        canvas.create_oval(fx - hr, fy - hr, fx + hr, fy + hr, fill=COLORS["angel_firefly_halo"], outline="")
        canvas.create_oval(fx - cr, fy - cr, fx + cr, fy + cr, fill=COLORS["angel_firefly_core"], outline="")


def draw_angel_flourishing(canvas, cx, cy, size=1.0):
    draw_angel_mature(canvas, cx, cy, size * 1.08)
    s = size * 1.08
    top_y = cy + 40 - int(104 * s)
    r = int(94 * s)

    # Extra enchanted golden fireflies & soft canopy motes
    motes = [
        (-int(r * 0.88), int(r * 0.14)), (int(r * 0.88), int(r * 0.16)),
        (-int(r * 0.45), -int(r * 0.28)), (int(r * 0.44), -int(r * 0.26)),
        (0, -int(r * 0.40)), (-int(r * 0.64), int(r * 0.34)),
        (int(r * 0.66), int(r * 0.36)),
    ]
    for ox, oy in motes:
        sx, sy = cx + ox, top_y + oy
        hr = max(2.8, 4.5 * size)
        cr = max(1.3, 2.0 * size)
        canvas.create_oval(sx - hr, sy - hr, sx + hr, sy + hr, fill=COLORS["angel_firefly_halo"], outline="")
        canvas.create_oval(sx - cr, sy - cr, sx + cr, sy + cr, fill=COLORS["angel_firefly_core"], outline="")


# ══════════════════════════════════════════════════════════════════
# 5. WEEPING WILLOW (Graceful cascading emerald vines)
# ══════════════════════════════════════════════════════════════════

def _draw_willow_vine(canvas, x, y, length, w_top, size, col_main, col_hi, seed=1):
    """Draw a vertical cascading willow vine curtain with tapered scalloped tip."""
    rng = random.Random(seed)
    sway = rng.uniform(-2.2, 2.2) * size
    _draw_tapered_branch(
        canvas,
        [(x, y), (x + sway * 0.4, y + length * 0.5), (x + sway, y + length)],
        w_top * size, max(1.0, 1.3 * size),
        fill=col_main
    )
    # Scalloped droplet tip + gentle mid highlight
    tip_r = max(1.4, 2.2 * size)
    canvas.create_oval(
        x + sway - tip_r, y + length - tip_r * 0.8,
        x + sway + tip_r, y + length + tip_r * 1.1,
        fill=col_hi, outline=""
    )


def draw_willow_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 16, size)
    sw = max(4, int(7 * size))
    sh = max(5, int(9 * size))
    canvas.create_oval(cx - sw, cy + 16 - sh, cx + sw, cy + 16 + 2, fill=COLORS["willow_leaf_deep"], outline=COLORS["willow_bark_shadow"], width=1)
    canvas.create_oval(cx - sw * 0.4, cy + 16 - sh * 0.7, cx + sw * 0.2, cy + 16 - 2, fill=COLORS["willow_leaf_light"], outline="")


def draw_willow_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(12 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 22, size * 0.9)
    top_y = cy + 22 - int(28 * size)
    _draw_tapered_branch(
        canvas,
        [(cx, cy + 22), (cx + 2 * size, cy + 22 - 14 * size), (cx + 1 * size, top_y)],
        4 * size, 1.8 * size, fill=COLORS["willow_bark_mid"], outline=COLORS["willow_bark_shadow"]
    )
    for side in (-1, 1):
        _draw_willow_vine(canvas, cx + side * 6 * size, top_y + 2 * size, 16 * size, 3.0, size, COLORS["willow_leaf_mid"], COLORS["willow_leaf_light"], seed=200 + side)


def draw_willow_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(72 * size), int(12 * size))
    base_y = cy + 28
    top_y = base_y - int(62 * size)
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 12 * size,
        base_w=10 * size, top_w=4 * size, curve_dx=5 * size, root_spread=12 * size,
        fill=COLORS["willow_bark_mid"], outline=COLORS["willow_bark_shadow"],
        bark_hi=COLORS["willow_bark_light"], bark_dark=COLORS["willow_bark_shadow"],
        size=size, seed=210, gnarled=False
    )
    r = int(32 * size)
    _draw_scalloped_cluster(canvas, cx, top_y + 4 * size, r * 0.95, r * 0.58, fill=COLORS["willow_leaf_deep"], puffs=6, seed=211)
    _draw_scalloped_cluster(canvas, cx, top_y - 2 * size, r * 0.80, r * 0.48, fill=COLORS["willow_leaf_mid"], puffs=6, seed=212)
    for idx, vx in enumerate((-22, -12, -2, 8, 18)):
        _draw_willow_vine(canvas, cx + vx * size, top_y + 6 * size, (22 + (idx % 3) * 6) * size, 3.2, size, COLORS["willow_leaf_mid"], COLORS["willow_leaf_light"], seed=213 + idx)


def draw_willow_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(98 * size), int(15 * size))
    base_y = cy + 33
    trunk_h = int(92 * size)
    top_y = base_y - trunk_h
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 18 * size,
        base_w=16 * size, top_w=7 * size, curve_dx=6 * size, root_spread=19 * size,
        fill=COLORS["willow_bark_mid"], outline=COLORS["willow_bark_shadow"],
        bark_hi=COLORS["willow_bark_light"], bark_dark=COLORS["willow_bark_shadow"],
        size=size, seed=220, gnarled=False
    )
    for pts in (
        [(cx + 3 * size, top_y + 34 * size), (cx - 22 * size, top_y + 16 * size), (cx - 38 * size, top_y + 14 * size)],
        [(cx + 4 * size, top_y + 30 * size), (cx + 24 * size, top_y + 14 * size), (cx + 38 * size, top_y + 12 * size)],
    ):
        _draw_tapered_branch(canvas, pts, 5.5 * size, 1.6 * size, fill=COLORS["willow_bark_dark"], outline=COLORS["willow_bark_shadow"])

    r = int(52 * size)
    _draw_scalloped_cluster(canvas, cx, top_y + 6 * size, r * 1.02, r * 0.60, fill=COLORS["willow_leaf_deep"], puffs=7, seed=221)
    _draw_scalloped_cluster(canvas, cx - 14 * size, top_y - 4 * size, r * 0.78, r * 0.48, fill=COLORS["willow_leaf_mid"], puffs=6, seed=222)
    _draw_scalloped_cluster(canvas, cx + 16 * size, top_y - 2 * size, r * 0.74, r * 0.46, fill=COLORS["willow_leaf_mid"], puffs=6, seed=223)
    _draw_scalloped_cluster(canvas, cx, top_y - 14 * size, r * 0.65, r * 0.38, fill=COLORS["willow_leaf_light"], puffs=5, seed=224)

    for idx, (vx, vy, vl) in enumerate([
        (-42, 10, 40), (-32, 6, 48), (-22, 12, 44), (-11, 8, 52),
        (2, 10, 46), (14, 7, 50), (26, 11, 45), (37, 9, 38)
    ]):
        col = COLORS["willow_leaf_deep"] if idx % 3 == 0 else COLORS["willow_leaf_mid"]
        _draw_willow_vine(canvas, cx + vx * size, top_y + vy * size, vl * size, 3.6, size, col, COLORS["willow_leaf_light"], seed=225 + idx)


def draw_willow_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(146 * size), int(19 * size))
    base_y = cy + 40
    trunk_h = int(116 * size)
    top_y = base_y - trunk_h

    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 28 * size,
        base_w=26 * size, top_w=11 * size, curve_dx=8 * size, root_spread=30 * size,
        fill=COLORS["willow_bark_mid"], outline=COLORS["willow_bark_shadow"],
        bark_hi=COLORS["willow_bark_light"], bark_dark=COLORS["willow_bark_shadow"],
        size=size, seed=230, gnarled=True
    )

    r = int(80 * size)
    # Deep shadow dome
    _draw_scalloped_cluster(canvas, cx, top_y + 12 * size, r * 1.05, r * 0.56, fill=COLORS["willow_leaf_shadow"], puffs=8, seed=231)

    # High-domed crown boughs
    for pts in (
        [(cx + 3 * size, top_y + 44 * size), (cx - 32 * size, top_y + 18 * size), (cx - 64 * size, top_y + 12 * size)],
        [(cx + 6 * size, top_y + 40 * size), (cx + 36 * size, top_y + 16 * size), (cx + 66 * size, top_y + 10 * size)],
        [(cx + 5 * size, top_y + 34 * size), (cx - 14 * size, top_y + 4 * size), (cx - 24 * size, top_y - 16 * size)],
        [(cx + 5 * size, top_y + 32 * size), (cx + 18 * size, top_y + 2 * size), (cx + 28 * size, top_y - 16 * size)],
    ):
        _draw_tapered_branch(canvas, pts, 8.0 * size, 1.8 * size, fill=COLORS["willow_bark_dark"], outline=COLORS["willow_bark_shadow"])

    # Back vine curtain behind trunk/front dome
    for idx, vx in enumerate((-68, -56, -42, 42, 56, 68)):
        _draw_willow_vine(canvas, cx + vx * size, top_y + 16 * size, (66 + (idx % 3) * 10) * size, 4.0, size, COLORS["willow_leaf_shadow"], COLORS["willow_leaf_deep"], seed=232 + idx)

    # Wide high-domed crown clusters
    _draw_scalloped_cluster(canvas, cx - 44 * size, top_y + 2 * size, r * 0.62, r * 0.42, fill=COLORS["willow_leaf_deep"], puffs=7, seed=240)
    _draw_scalloped_cluster(canvas, cx + 44 * size, top_y + 2 * size, r * 0.62, r * 0.42, fill=COLORS["willow_leaf_deep"], puffs=7, seed=241)
    _draw_scalloped_cluster(canvas, cx, top_y - 12 * size, r * 0.84, r * 0.50, fill=COLORS["willow_leaf_mid"], puffs=8, seed=242)
    _draw_scalloped_cluster(canvas, cx - 22 * size, top_y - 24 * size, r * 0.56, r * 0.36, fill=COLORS["willow_leaf_light"], puffs=6, seed=243)
    _draw_scalloped_cluster(canvas, cx + 22 * size, top_y - 22 * size, r * 0.54, r * 0.34, fill=COLORS["willow_leaf_light"], puffs=6, seed=244)
    _draw_dither_pixels(canvas, cx, top_y - 26 * size, r * 0.65, r * 0.25, COLORS["willow_leaf_light"], count=12, px_size=max(2, 2.8 * size), seed=245)

    # Foreground cascading emerald vine curtains
    front_vines = [
        (-62, 12, 68), (-50, 18, 76), (-38, 10, 82), (-26, 16, 70), (-15, 14, 78),
        (14, 15, 76), (26, 10, 82), (38, 17, 74), (50, 12, 70), (62, 16, 64),
    ]
    for idx, (vx, vy, vl) in enumerate(front_vines):
        col = COLORS["willow_leaf_mid"] if idx % 2 == 0 else COLORS["willow_leaf_deep"]
        _draw_willow_vine(canvas, cx + vx * size, top_y + vy * size, vl * size, 4.2, size, col, COLORS["willow_leaf_light"], seed=250 + idx)

    # Tiny fallen willow leaves on grass around base
    for px, py in ((-46, 3), (-18, 5), (22, 4), (48, 2)):
        pw = max(1.8, 3.2 * size)
        ph = max(1.0, 1.5 * size)
        canvas.create_oval(cx + px * size - pw, base_y + py * size - ph, cx + px * size + pw, base_y + py * size + ph, fill=COLORS["willow_leaf_mid"], outline="")


def draw_willow_flourishing(canvas, cx, cy, size=1.0):
    draw_willow_mature(canvas, cx, cy, size * 1.08)
    s = size * 1.08
    top_y = cy + 40 - int(116 * s)
    r = int(80 * s)
    for ox, oy in ((-r * 0.7, -r * 0.1), (r * 0.72, -r * 0.08), (-r * 0.28, -r * 0.42), (r * 0.30, -r * 0.40)):
        sx, sy = cx + ox, top_y + oy
        canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill="#D8F3DC", outline="")


# ══════════════════════════════════════════════════════════════════
# 6. JAPANESE MAPLE (Vibrant autumn crimson canopy)
# ══════════════════════════════════════════════════════════════════

def draw_maple_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 16, size)
    sw = max(4, int(7 * size))
    sh = max(5, int(9 * size))
    canvas.create_oval(cx - sw, cy + 16 - sh, cx + sw, cy + 16 + 2, fill=COLORS["maple_leaf_crimson"], outline=COLORS["maple_bark_shadow"], width=1)
    canvas.create_oval(cx - sw * 0.4, cy + 16 - sh * 0.7, cx + sw * 0.2, cy + 16 - 2, fill=COLORS["maple_leaf_amber"], outline="")


def draw_maple_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(12 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 22, size * 0.9)
    top_y = cy + 22 - int(28 * size)
    _draw_tapered_branch(
        canvas,
        [(cx, cy + 22), (cx - 2 * size, cy + 22 - 14 * size), (cx + 1 * size, top_y)],
        3.5 * size, 1.5 * size, fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"]
    )
    _draw_scalloped_cluster(canvas, cx - 6 * size, top_y, 9 * size, 5.5 * size, fill=COLORS["maple_leaf_scarlet"], puffs=4, seed=300)
    _draw_scalloped_cluster(canvas, cx + 6 * size, top_y - 2 * size, 8 * size, 5 * size, fill=COLORS["maple_leaf_amber"], puffs=4, seed=301)


def draw_maple_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(72 * size), int(12 * size))
    base_y = cy + 28
    top_y = base_y - int(64 * size)
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 10 * size,
        base_w=8 * size, top_w=3 * size, curve_dx=-6 * size, root_spread=11 * size,
        fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"],
        bark_hi=COLORS["maple_bark_light"], bark_dark=COLORS["maple_bark_shadow"],
        size=size, seed=310, gnarled=False
    )
    r = int(28 * size)
    _draw_scalloped_cluster(canvas, cx - 10 * size, top_y + 3 * size, r * 0.9, r * 0.45, fill=COLORS["maple_leaf_crimson"], puffs=5, seed=311)
    _draw_scalloped_cluster(canvas, cx + 10 * size, top_y, r * 0.85, r * 0.42, fill=COLORS["maple_leaf_scarlet"], puffs=5, seed=312)
    _draw_scalloped_cluster(canvas, cx - 3 * size, top_y - 7 * size, r * 0.75, r * 0.38, fill=COLORS["maple_leaf_amber"], puffs=5, seed=313)


def draw_maple_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(98 * size), int(15 * size))
    base_y = cy + 33
    trunk_h = int(94 * size)
    top_y = base_y - trunk_h
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 16 * size,
        base_w=12 * size, top_w=5 * size, curve_dx=-7 * size, root_spread=16 * size,
        fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"],
        bark_hi=COLORS["maple_bark_light"], bark_dark=COLORS["maple_bark_shadow"],
        size=size, seed=320, gnarled=False
    )
    for pts in (
        [(cx - 3 * size, base_y - trunk_h * 0.48), (cx - 22 * size, top_y + 24 * size), (cx - 38 * size, top_y + 12 * size)],
        [(cx - 2 * size, base_y - trunk_h * 0.58), (cx + 20 * size, top_y + 20 * size), (cx + 36 * size, top_y + 10 * size)],
        [(cx - 5 * size, top_y + 20 * size), (cx - 10 * size, top_y), (cx - 14 * size, top_y - 16 * size)],
    ):
        _draw_tapered_branch(canvas, pts, 4.5 * size, 1.2 * size, fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"])

    r = int(50 * size)
    # Layered horizontal cloud-like autumn pads
    _draw_scalloped_cluster(canvas, cx - 30 * size, top_y + 10 * size, r * 0.72, r * 0.36, fill=COLORS["maple_leaf_crimson"], puffs=6, seed=321)
    _draw_scalloped_cluster(canvas, cx + 28 * size, top_y + 8 * size, r * 0.68, r * 0.34, fill=COLORS["maple_leaf_crimson"], puffs=6, seed=322)
    _draw_scalloped_cluster(canvas, cx - 12 * size, top_y - 4 * size, r * 0.80, r * 0.40, fill=COLORS["maple_leaf_scarlet"], puffs=7, seed=323)
    _draw_scalloped_cluster(canvas, cx + 16 * size, top_y - 10 * size, r * 0.66, r * 0.34, fill=COLORS["maple_leaf_amber"], puffs=6, seed=324)
    _draw_scalloped_cluster(canvas, cx - 14 * size, top_y - 18 * size, r * 0.56, r * 0.28, fill=COLORS["maple_leaf_peach"], puffs=5, seed=325)
    _draw_dither_pixels(canvas, cx - 6 * size, top_y - 18 * size, r * 0.65, r * 0.22, COLORS["maple_leaf_peach"], count=8, px_size=max(2, 2.4 * size), seed=326)


def draw_maple_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(144 * size), int(18 * size))
    base_y = cy + 40
    trunk_h = int(114 * size)
    top_y = base_y - trunk_h

    # Slender, graceful, winding dark-charcoal/mahogany trunk
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 24 * size,
        base_w=19 * size, top_w=7 * size, curve_dx=-9 * size, root_spread=24 * size,
        fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"],
        bark_hi=COLORS["maple_bark_light"], bark_dark=COLORS["maple_bark_shadow"],
        size=size, seed=330, gnarled=False
    )

    r = int(76 * size)
    # Shadow pads behind exposed forked branches
    _draw_scalloped_cluster(canvas, cx - 54 * size, top_y + 18 * size, r * 0.56, r * 0.28, fill=COLORS["maple_leaf_shadow"], puffs=6, seed=331)
    _draw_scalloped_cluster(canvas, cx + 52 * size, top_y + 20 * size, r * 0.54, r * 0.26, fill=COLORS["maple_leaf_shadow"], puffs=6, seed=332)

    # Delicate exposed multi-forked branches
    forks = [
        ([(cx - 4 * size, base_y - trunk_h * 0.42), (cx - 28 * size, top_y + 38 * size), (cx - 60 * size, top_y + 18 * size), (cx - 78 * size, top_y + 10 * size)], 6.5, 1.5),
        ([(cx - 38 * size, top_y + 28 * size), (cx - 48 * size, top_y + 6 * size), (cx - 56 * size, top_y - 10 * size)], 3.2, 1.0),
        ([(cx - 5 * size, base_y - trunk_h * 0.50), (cx + 26 * size, top_y + 34 * size), (cx + 58 * size, top_y + 16 * size), (cx + 76 * size, top_y + 8 * size)], 6.2, 1.5),
        ([(cx + 34 * size, top_y + 26 * size), (cx + 44 * size, top_y + 4 * size), (cx + 52 * size, top_y - 12 * size)], 3.0, 1.0),
        ([(cx - 6 * size, top_y + 28 * size), (cx - 16 * size, top_y + 2 * size), (cx - 24 * size, top_y - 20 * size)], 4.8, 1.2),
        ([(cx - 4 * size, top_y + 26 * size), (cx + 14 * size, top_y), (cx + 24 * size, top_y - 18 * size)], 4.4, 1.2),
    ]
    for pts, ws, we in forks:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["maple_bark_dark"], outline=COLORS["maple_bark_shadow"])

    # Layered, airy horizontal foliage pads (crimson -> scarlet -> amber -> golden-peach)
    pads = [
        (-62, 6, 0.56, 0.28, COLORS["maple_leaf_crimson"], 333),
        (60, 8, 0.54, 0.26, COLORS["maple_leaf_crimson"], 334),
        (-28, -4, 0.62, 0.30, COLORS["maple_leaf_scarlet"], 335),
        (30, -6, 0.58, 0.28, COLORS["maple_leaf_scarlet"], 336),
        (0, -14, 0.68, 0.32, COLORS["maple_leaf_amber"], 337),
        (-42, -18, 0.48, 0.24, COLORS["maple_leaf_amber"], 338),
        (36, -20, 0.44, 0.22, COLORS["maple_leaf_peach"], 339),
        (-12, -28, 0.52, 0.24, COLORS["maple_leaf_peach"], 340),
    ]
    for ox, oy, rxf, ryf, col, s in pads:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rxf, r * ryf, fill=col, puffs=7, seed=s)

    _draw_dither_pixels(canvas, cx - 8 * size, top_y - 26 * size, r * 0.60, r * 0.20, COLORS["maple_leaf_peach"], count=12, px_size=max(2, 2.6 * size), seed=341)

    # 5 tiny fallen red leaves scattered near the base
    for px, py, col in [
        (-44, 3, "maple_leaf_crimson"),
        (-18, 5, "maple_leaf_scarlet"),
        (8, 4, "maple_leaf_amber"),
        (32, 3, "maple_leaf_scarlet"),
        (52, 2, "maple_leaf_crimson"),
    ]:
        pw = max(1.8, 3.0 * size)
        ph = max(1.1, 1.7 * size)
        canvas.create_oval(cx + px * size - pw, base_y + py * size - ph, cx + px * size + pw, base_y + py * size + ph, fill=COLORS[col], outline="")


def draw_maple_flourishing(canvas, cx, cy, size=1.0):
    draw_maple_mature(canvas, cx, cy, size * 1.08)
    s = size * 1.08
    top_y = cy + 40 - int(114 * s)
    r = int(76 * s)
    for ox, oy in ((-r * 0.72, -r * 0.12), (r * 0.70, -r * 0.10), (0, -r * 0.42)):
        sx, sy = cx + ox, top_y + oy
        canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=COLORS["maple_leaf_peach"], outline="")


# ══════════════════════════════════════════════════════════════════
# 7. MOONLIT BLOSSOM (Rare luminous nocturnal flora)
# ══════════════════════════════════════════════════════════════════

def _draw_moon_glow_mote(canvas, sx, sy, size):
    """Draw a floating glowing cyan/starlight spore pixel with soft ambient radial glow."""
    hr1 = max(3.5, 6.0 * size)
    hr2 = max(2.2, 3.6 * size)
    cr = max(1.2, 1.8 * size)
    canvas.create_oval(sx - hr1, sy - hr1, sx + hr1, sy + hr1, fill=COLORS["moon_petal_deep"], outline="")
    canvas.create_oval(sx - hr2, sy - hr2, sx + hr2, sy + hr2, fill=COLORS["moon_petal_cyan"], outline="")
    canvas.create_oval(sx - cr, sy - cr, sx + cr, sy + cr, fill=COLORS["moon_petal_glow"], outline="")


def draw_moonlit_seed(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 20, int(56 * size), int(11 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 16, size)
    sw = max(4, int(7 * size))
    sh = max(5, int(9 * size))
    canvas.create_oval(cx - sw, cy + 16 - sh, cx + sw, cy + 16 + 2, fill=COLORS["moon_petal_deep"], outline=COLORS["moon_bark_shadow"], width=1)
    canvas.create_oval(cx - sw * 0.45, cy + 16 - sh * 0.7, cx + sw * 0.25, cy + 16 - 2, fill=COLORS["moon_petal_cyan"], outline="")


def draw_moonlit_sprout(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 25, int(62 * size), int(12 * size))
    _draw_tiny_soil_mound(canvas, cx, cy + 22, size * 0.9)
    top_y = cy + 22 - int(28 * size)
    _draw_tapered_branch(
        canvas,
        [(cx, cy + 22), (cx + 2 * size, cy + 22 - 14 * size), (cx - 1 * size, top_y)],
        4 * size, 1.6 * size, fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"]
    )
    _draw_scalloped_cluster(canvas, cx, top_y, 9 * size, 6 * size, fill=COLORS["moon_petal_mid"], puffs=4, seed=400)
    _draw_moon_glow_mote(canvas, cx - 8 * size, top_y - 4 * size, size * 0.7)


def draw_moonlit_seedling(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 30, int(72 * size), int(12 * size))
    base_y = cy + 28
    top_y = base_y - int(62 * size)
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 10 * size,
        base_w=10 * size, top_w=4 * size, curve_dx=7 * size, root_spread=13 * size,
        fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"],
        bark_hi=COLORS["moon_bark_light"], bark_dark=COLORS["moon_bark_shadow"],
        size=size, seed=410, gnarled=True
    )
    r = int(29 * size)
    _draw_scalloped_cluster(canvas, cx - 8 * size, top_y + 3 * size, r * 0.85, r * 0.55, fill=COLORS["moon_petal_deep"], puffs=5, seed=411)
    _draw_scalloped_cluster(canvas, cx + 8 * size, top_y - 2 * size, r * 0.82, r * 0.52, fill=COLORS["moon_petal_mid"], puffs=5, seed=412)
    _draw_scalloped_cluster(canvas, cx - 2 * size, top_y - 8 * size, r * 0.65, r * 0.42, fill=COLORS["moon_petal_cyan"], puffs=5, seed=413)
    _draw_moon_glow_mote(canvas, cx - 18 * size, top_y - 6 * size, size * 0.8)
    _draw_moon_glow_mote(canvas, cx + 19 * size, top_y + 2 * size, size * 0.75)


def draw_moonlit_young(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 35, int(98 * size), int(15 * size))
    base_y = cy + 33
    trunk_h = int(92 * size)
    top_y = base_y - trunk_h
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 16 * size,
        base_w=14 * size, top_w=6 * size, curve_dx=8 * size, root_spread=18 * size,
        fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"],
        bark_hi=COLORS["moon_bark_light"], bark_dark=COLORS["moon_bark_shadow"],
        size=size, seed=420, gnarled=True
    )
    for pts in (
        [(cx + 3 * size, base_y - trunk_h * 0.44), (cx - 20 * size, top_y + 24 * size), (cx - 38 * size, top_y + 10 * size)],
        [(cx + 5 * size, base_y - trunk_h * 0.54), (cx + 22 * size, top_y + 20 * size), (cx + 38 * size, top_y + 6 * size)],
    ):
        _draw_tapered_branch(canvas, pts, 5.2 * size, 1.4 * size, fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"])

    r = int(50 * size)
    _draw_scalloped_cluster(canvas, cx - 28 * size, top_y + 6 * size, r * 0.72, r * 0.48, fill=COLORS["moon_petal_deep"], puffs=6, seed=421)
    _draw_scalloped_cluster(canvas, cx + 28 * size, top_y + 4 * size, r * 0.68, r * 0.46, fill=COLORS["moon_petal_deep"], puffs=6, seed=422)
    _draw_scalloped_cluster(canvas, cx - 4 * size, top_y - 10 * size, r * 0.80, r * 0.52, fill=COLORS["moon_petal_mid"], puffs=7, seed=423)
    _draw_scalloped_cluster(canvas, cx - 14 * size, top_y - 18 * size, r * 0.58, r * 0.38, fill=COLORS["moon_petal_cyan"], puffs=5, seed=424)
    _draw_dither_pixels(canvas, cx, top_y - 18 * size, r * 0.70, r * 0.30, COLORS["moon_petal_glow"], count=10, px_size=max(2, 2.5 * size), seed=425)

    for mx, my in ((-40, -6), (42, -4), (-16, -28), (20, -24)):
        _draw_moon_glow_mote(canvas, cx + mx * size, top_y + my * size, size * 0.85)


def draw_moonlit_mature(canvas, cx, cy, size=1.0):
    _draw_shadow_and_soil(canvas, cx, cy + 42, int(146 * size), int(19 * size))
    base_y = cy + 40
    trunk_h = int(114 * size)
    top_y = base_y - trunk_h

    # Dark indigo-barked gnarled trunk with sweeping asymmetric limbs
    _draw_organic_root_trunk(
        canvas, cx, base_y, top_y + 26 * size,
        base_w=24 * size, top_w=9 * size, curve_dx=10 * size, root_spread=28 * size,
        fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"],
        bark_hi=COLORS["moon_bark_light"], bark_dark=COLORS["moon_bark_shadow"],
        size=size, seed=430, gnarled=True
    )

    r = int(78 * size)
    _draw_scalloped_cluster(canvas, cx - 54 * size, top_y + 20 * size, r * 0.56, r * 0.38, fill=COLORS["moon_petal_shadow"], puffs=6, seed=431)
    _draw_scalloped_cluster(canvas, cx + 52 * size, top_y + 22 * size, r * 0.52, r * 0.36, fill=COLORS["moon_petal_shadow"], puffs=6, seed=432)

    limbs = [
        ([(cx + 3 * size, base_y - trunk_h * 0.40), (cx - 26 * size, top_y + 40 * size), (cx - 60 * size, top_y + 20 * size), (cx - 80 * size, top_y + 6 * size)], 7.8, 1.8),
        ([(cx - 42 * size, top_y + 28 * size), (cx - 52 * size, top_y + 6 * size), (cx - 62 * size, top_y - 14 * size)], 3.8, 1.1),
        ([(cx + 7 * size, base_y - trunk_h * 0.48), (cx + 34 * size, top_y + 34 * size), (cx + 66 * size, top_y + 16 * size), (cx + 82 * size, top_y + 4 * size)], 7.2, 1.7),
        ([(cx + 42 * size, top_y + 24 * size), (cx + 48 * size, top_y + 2 * size), (cx + 54 * size, top_y - 18 * size)], 3.5, 1.1),
        ([(cx + 6 * size, top_y + 28 * size), (cx - 12 * size, top_y), (cx - 24 * size, top_y - 24 * size)], 5.6, 1.4),
    ]
    for pts, ws, we in limbs:
        _draw_tapered_branch(canvas, pts, ws * size, we * size, fill=COLORS["moon_bark_dark"], outline=COLORS["moon_bark_shadow"])

    # Ethereal starlight-lavender & bioluminescent cyan blossom clusters
    clusters = [
        (-62, 4, 0.56, 0.38, COLORS["moon_petal_deep"], 433),
        (60, 8, 0.54, 0.36, COLORS["moon_petal_deep"], 434),
        (-28, -12, 0.62, 0.42, COLORS["moon_petal_mid"], 435),
        (28, -10, 0.58, 0.40, COLORS["moon_petal_mid"], 436),
        (-4, -24, 0.64, 0.44, COLORS["moon_petal_mid"], 437),
        (-42, -24, 0.46, 0.30, COLORS["moon_petal_cyan"], 438),
        (34, -22, 0.44, 0.28, COLORS["moon_petal_cyan"], 439),
        (-10, -38, 0.48, 0.30, COLORS["moon_petal_glow"], 440),
    ]
    for ox, oy, rxf, ryf, col, s in clusters:
        _draw_scalloped_cluster(canvas, cx + ox * size, top_y + oy * size, r * rxf, r * ryf, fill=col, puffs=7, seed=s)

    _draw_dither_pixels(canvas, cx - 8 * size, top_y - 34 * size, r * 0.62, r * 0.26, COLORS["moon_petal_glow"], count=14, px_size=max(2, 2.8 * size), seed=441)

    # 6 floating glowing firefly/spore pixels around canopy
    for mx, my in ((-78, -8), (-56, -34), (-16, -50), (28, -44), (72, -16), (54, 24)):
        _draw_moon_glow_mote(canvas, cx + mx * size, top_y + my * size, size)


def draw_moonlit_flourishing(canvas, cx, cy, size=1.0):
    draw_moonlit_mature(canvas, cx, cy, size * 1.08)
    s = size * 1.08
    top_y = cy + 40 - int(114 * s)
    r = int(78 * s)
    for ox, oy in ((-r * 0.85, r * 0.12), (r * 0.84, r * 0.14), (0, -r * 0.62)):
        _draw_moon_glow_mote(canvas, cx + ox, top_y + oy, size * 1.15)


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
    "willow": {
        "seed": draw_willow_seed,
        "sprout": draw_willow_sprout,
        "seedling": draw_willow_seedling,
        "young": draw_willow_young,
        "mature": draw_willow_mature,
        "flourishing": draw_willow_flourishing,
    },
    "maple": {
        "seed": draw_maple_seed,
        "sprout": draw_maple_sprout,
        "seedling": draw_maple_seedling,
        "young": draw_maple_young,
        "mature": draw_maple_mature,
        "flourishing": draw_maple_flourishing,
    },
    "moonlit_blossom": {
        "seed": draw_moonlit_seed,
        "sprout": draw_moonlit_sprout,
        "seedling": draw_moonlit_seedling,
        "young": draw_moonlit_young,
        "mature": draw_moonlit_mature,
        "flourishing": draw_moonlit_flourishing,
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
