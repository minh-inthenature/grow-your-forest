"""
scenery.py - Lightweight illustrated landscape engine for Grow Your Forest.

Design goals
------------
* Cozy, painterly 2D scenery (inspired by pixel-art dusk landscapes and
  impressionist countryside paintings): banded pastel skies, layered
  mountain ridges with atmospheric haze, a lake, a waterfall + winding river,
  rolling meadows with brush-dab texture, a winding path with sky puddles,
  bushes, rocks, mushrooms and wildflowers.
* Performance first: the whole static scene is drawn ONCE per
  (size, theme, view) as plain Tk canvas vector items.  Animation only
  moves a small, fixed budget of tagged items with canvas.move / coords,
  grouped by screen band so Tk repaints small regions instead of the
  entire canvas.  No images, no per-frame redraws, zero dependencies.
"""

import math
import random

# ─────────────────────────────────────────────────────────────────────
#  Theme palettes (soft, low-saturation, cohesive across both screens)
# ─────────────────────────────────────────────────────────────────────

PALETTES = {
    "morning": dict(
        sky=["#A9C4E4", "#C2CFE8", "#DDD3E6", "#F3D9CF", "#FBE6D2"],
        celestial="sunrise", sun_core="#FFE7B0",
        cloud=("#FFF6EE", "#E4CFD8"),
        mountains=["#B7BEDB", "#9CA7CC", "#8392B9"],
        mist="#ECE3EC",
        treeline="#6E957A",
        water=("#9EC5DB", "#E2F0F5", "#82AEC8"),
        hills=["#A6C98F", "#87B676", "#6C9F60"],
        rim=["#C6E0AA", "#A8CF90", "#8CBD79"],
        dabs=["#B8D69B", "#7EAC69", "#DCE5A6", "#5F9152"],
        path=("#DDB28E", "#BE9070", "#EBCBAA"),
        rock=("#BDB6AF", "#8E8882"),
        bush=("#4E7C4A", "#68975B", "#84B171"),
        flowers=["#F4C3D2", "#FFF0B5", "#FFFFFF", "#D6C3EE"],
        shadow="#5F8A57",
        tint=("#FFE7CF", 0.07),
        grass="#5E9150",
        leaf="#F2C6D3",
        stars=False, fireflies=False, birds="#6B6A86", butterflies=True,
    ),
    "afternoon": dict(
        sky=["#73A7D4", "#8FBBDF", "#AECFE7", "#D0E2EC", "#EDF1E6"],
        celestial="noon", sun_core="#FFF0B8",
        cloud=("#FFFFFF", "#D3DEEA"),
        mountains=["#9DB0CE", "#7F97BC", "#6681A6"],
        mist="#DCE6EC",
        treeline="#517F57",
        water=("#73AFCF", "#D5EBF3", "#5E9ABC"),
        hills=["#95C170", "#77A957", "#5C9046"],
        rim=["#B6D78E", "#96C371", "#79AD5A"],
        dabs=["#A8CE80", "#5F9245", "#D5E29C", "#4B7C3A"],
        path=("#D6A57A", "#B3855E", "#E7C39C"),
        rock=("#B6B0A8", "#86807A"),
        bush=("#3F6C3B", "#557E46", "#6F9957"),
        flowers=["#F2A9BB", "#FFE48E", "#FFFFFF", "#C8B3EC"],
        shadow="#4D7A42",
        tint=("#FFF3DA", 0.04),
        grass="#4F883F",
        leaf="#C9D27A",
        stars=False, fireflies=False, birds="#4F5D7A", butterflies=True,
    ),
    "night": dict(
        sky=["#141B3A", "#1E264F", "#2B2E61", "#3C366F", "#553F79"],
        celestial="moon", sun_core="#F4F1E2",
        cloud=("#5B5E95", "#3B3E71"),
        mountains=["#403B6C", "#302E58", "#242647"],
        mist="#3F3D6F",
        treeline="#1F3431",
        water=("#2B3667", "#8E97C9", "#202954"),
        hills=["#2D4A3B", "#234030", "#1B3327"],
        rim=["#3E5F4B", "#33533F", "#294735"],
        dabs=["#36594A", "#1D3629", "#4A6B57", "#172A20"],
        path=("#4B4159", "#393046", "#6B6181"),
        rock=("#565A7B", "#3B3E59"),
        bush=("#142B21", "#1C3629", "#254130"),
        flowers=["#9AA6E0", "#D7DCF5", "#B7A6E8", "#8FD8C0"],
        shadow="#15271D",
        tint=("#27315F", 0.40),
        grass="#2B4B37",
        leaf="#9FB3D9",
        stars=True, fireflies=True, birds=None, butterflies=False,
    ),
    "chill": dict(
        sky=["#3B2842", "#59384E", "#824B54", "#B36B56", "#DC9368"],
        celestial="sunset", sun_core="#FFD099",
        cloud=("#E8A582", "#7A4958"),
        mountains=["#5E3F53", "#4A3144", "#382535"],
        mist="#8C5D58",
        treeline="#3D4A3A",
        water=("#5E4B5E", "#E6A983", "#463748"),
        hills=["#5E6B46", "#4B5938", "#39462B"],
        rim=["#8C8556", "#747248", "#5C5E3B"],
        dabs=["#737A4C", "#425030", "#9E8456", "#313D24"],
        path=("#7A5848", "#5E4235", "#9C745E"),
        rock=("#6E5D5C", "#4E4142"),
        bush=("#2D3A24", "#3D4D31", "#526340"),
        flowers=["#F2B880", "#E88D72", "#F7DBA7", "#D49B94"],
        shadow="#252E1C",
        tint=("#D98A56", 0.22),
        grass="#4E5E3A",
        leaf="#E8A47C",
        stars=False, fireflies=True, birds="#4A3144", butterflies=False,
        motes=True,
    ),
}

LEAF_BY_SPECIES = {
    "cherry_blossom": "#F5C2D2",
    "oak": "#B9C46A",
    "pine": "#9C7B58",
    "angel_oak": "#A9B99A",
}


# ─────────────────────────────────────────────────────────────────────
#  Colour helpers (cached)
# ─────────────────────────────────────────────────────────────────────

_mix_cache = {}


def _rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mix(a, b, t):
    """Blend hex colour a toward b by t (0..1)."""
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    key = (a, b, int(t * 1000))
    r = _mix_cache.get(key)
    if r is None:
        ra, ga, ba = _rgb(a)
        rb, gb, bb = _rgb(b)
        r = "#%02x%02x%02x" % (int(ra + (rb - ra) * t), int(ga + (gb - ga) * t), int(ba + (bb - ba) * t))
        if len(_mix_cache) < 30000:
            _mix_cache[key] = r
    return r


def gradient(stops, t):
    t = 0.0 if t < 0 else (0.9999 if t >= 1 else t)
    seg = t * (len(stops) - 1)
    i = int(seg)
    return mix(stops[i], stops[i + 1], seg - i)


def palette(theme):
    return PALETTES.get(theme, PALETTES["morning"])


def tint_range(canvas, first_id, last_id, theme):
    """Tint freshly drawn items (ids in [first_id, last_id)) toward the
    theme's ambient light so trees sit naturally inside the scene."""
    tint, amt = palette(theme)["tint"]
    if amt < 0.12:
        return
    cache = {}
    for i in range(first_id, last_id):
        upd = {}
        for opt in ("fill", "outline"):
            try:
                col = canvas.itemcget(i, opt)
            except Exception:
                continue
            if col and len(col) == 7 and col[0] == "#":
                blended = cache.get(col)
                if blended is None:
                    blended = mix(col, tint, amt)
                    cache[col] = blended
                upd[opt] = blended
        if upd:
            canvas.itemconfigure(i, **upd)


# ─────────────────────────────────────────────────────────────────────
#  Scene drawing
# ─────────────────────────────────────────────────────────────────────

def _draw_cloud(c, x, y, s, lit, shade, tag):
    hi = mix(lit, "#FFFFFF", 0.45)
    for ox, oy, rr in ((-0.95, 0.10, 0.34), (-0.50, -0.12, 0.46), (0.0, -0.30, 0.56),
                       (0.50, -0.14, 0.46), (0.92, 0.08, 0.32)):
        cx, cy = x + ox * s, y + oy * s
        c.create_oval(cx - rr * s, cy - rr * s * 0.8, cx + rr * s, cy + rr * s * 0.8,
                      fill=lit, outline="", tags=(tag, "cloud"))
    for ox in (-0.85, -0.40, 0.05, 0.50, 0.90):
        cx = x + ox * s
        c.create_oval(cx - 0.34 * s, y + 0.14 * s, cx + 0.34 * s, y + 0.42 * s,
                      fill=shade, outline="", tags=(tag, "cloud"))
    for ox, oy, rr in ((-0.48, -0.24, 0.18), (0.02, -0.46, 0.22), (0.50, -0.26, 0.15)):
        cx, cy = x + ox * s, y + oy * s
        c.create_oval(cx - rr * s, cy - rr * s * 0.7, cx + rr * s, cy + rr * s * 0.7,
                      fill=hi, outline="", tags=(tag, "cloud"))


def _ridge(w, base, amp, f, p, step):
    pts = []
    x = 0.0
    while True:
        u = x / w
        v = (0.55 * (1 - abs(math.sin(math.pi * f[0] * u + p[0])))
             + 0.30 * (1 - abs(math.sin(math.pi * f[1] * u + p[1])))
             + 0.15 * (0.5 + 0.5 * math.sin(2 * math.pi * f[2] * u + p[2])))
        pts.extend([x, base - amp * v])
        if x >= w:
            break
        x = min(w, x + step)
    return pts


def _poly_under(fn, w, bottom, step):
    pts = [0, bottom]
    x = 0.0
    while True:
        pts.extend([x, fn(x)])
        if x >= w:
            break
        x = min(w, x + step)
    pts.extend([w, bottom])
    return pts


def _line_along(fn, w, step):
    pts = []
    x = 0.0
    while True:
        pts.extend([x, fn(x)])
        if x >= w:
            break
        x = min(w, x + step)
    return pts


def draw_landscape(c, w, h, theme, mode="forest", richness=0.0):
    """Draw the full static landscape.  Returns a scene dict describing
    geometry (for tree placement / avoidance) and animatable items."""
    P = palette(theme)
    study = (mode == "study")
    rng = random.Random(77 if study else 2024)
    richness = max(0.0, min(1.0, richness))
    S = {"w": w, "h": h, "theme": theme, "mode": mode, "pal": P,
         "clouds": [], "grass": [], "twinkle": [], "shimmer": [], "falls": []}

    hz = h * 0.50
    S["hz"] = hz
    sky_bottom = hz + h * 0.12
    k = 2 * math.pi / w
    sc = max(0.6, min(1.6, h / 520.0))      # detail scale
    S["sc"] = sc

    def sky_at(y):
        return gradient(P["sky"], y / sky_bottom)
    S["sky_at"] = sky_at

    # ── 1. Banded sky (soft, slightly pixel-art in feel) ──
    n = 10
    for i in range(n):
        y0 = sky_bottom * i / n
        y1 = sky_bottom * (i + 1) / n + 1
        c.create_rectangle(0, y0, w, y1, fill=gradient(P["sky"], (i + 0.5) / n), outline="")

    # ── 2. Stars (night) ──
    if P["stars"]:
        for _ in range(28):
            x = rng.uniform(0, w)
            y = hz * 0.92 * (rng.random() ** 1.5)
            s = 2 if rng.random() < 0.18 else 1
            c.create_rectangle(x, y, x + s, y + s, outline="",
                               fill=mix(sky_at(y), "#FFFFFF", rng.uniform(0.45, 0.95)))
        for _ in range(3):
            x = rng.uniform(0.05 * w, 0.95 * w)
            y = rng.uniform(0.04 * h, hz * 0.6)
            bright, dim = "#FFF8E0", mix(sky_at(y), "#FFF8E0", 0.35)
            iid = c.create_text(x, y, text="✦", fill=bright, font=("Segoe UI", 7))
            S["twinkle"].append([iid, bright, dim, rng.uniform(0, 6.28), -1])

    # ── 3. Sun / moon with soft halo ──
    cel = P["celestial"]
    pos = {"sunrise": (0.23, hz - 0.045 * h, 0.046),
           "noon": (0.80, 0.13 * h, 0.040),
           "sunset": (0.73, hz - 0.015 * h, 0.060),
           "moon": (0.80, 0.15 * h, 0.034)}[cel]
    sx, sy, r = pos[0] * w, pos[1], pos[2] * h
    base = sky_at(sy)
    core = P["sun_core"]
    rings = ((3.3, 0.12), (2.4, 0.24), (1.65, 0.42)) if cel != "moon" else ((3.0, 0.10), (2.1, 0.20), (1.45, 0.34))
    inner = base
    for mult, t in rings:
        inner = mix(base, core, t)
        c.create_oval(sx - r * mult, sy - r * mult, sx + r * mult, sy + r * mult, fill=inner, outline="")
    c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=core, outline="")
    if cel == "moon":
        off = r * 0.48
        c.create_oval(sx - r * 0.95 + off, sy - r * 0.95 - r * 0.22,
                      sx + r * 0.95 + off, sy + r * 0.95 - r * 0.22, fill=inner, outline="")
    S["sun"] = (sx, sy, r, cel)

    # ── 4. Big illustrated clouds (drifting) ──
    lit, shade = P["cloud"]
    specs = ([(0.18, 0.12, 0.095, 3.0), (0.60, 0.07, 0.070, 2.0), (0.92, 0.23, 0.060, 3.6)] if study else
             [(0.13, 0.12, 0.075, 3.0), (0.42, 0.07, 0.055, 2.2), (0.64, 0.22, 0.085, 2.6), (0.93, 0.10, 0.050, 3.4)])
    unit = min(w, 1.6 * h)
    for idx, (fx, fy, fs, spd) in enumerate(specs):
        tag = "cloud_%d" % idx
        _draw_cloud(c, fx * w, fy * h, fs * unit, lit, shade, tag)
        S["clouds"].append([tag, spd * sc])

    # ── 5. Layered mountain ridges with atmospheric haze ──
    m = P["mountains"]
    mbottom = hz + 0.16 * h
    step = max(14, w / 28)
    ridges = [
        (hz + 0.05 * h, (0.18 if study else 0.20) * h, (1.1, 2.7, 5.3), (0.4, 1.3, 0.2)),
        (hz + 0.065 * h, 0.12 * h, (1.7, 3.9, 7.1), (1.9, 0.6, 2.4)),
        (hz + 0.08 * h, 0.06 * h, (2.3, 5.2, 9.0), (0.9, 2.2, 1.1)),
    ]
    rim_target = core if cel != "noon" else "#FFFFFF"
    for i, (b, amp, f, p) in enumerate(ridges):
        pts = _ridge(w, b, amp, f, p, step)
        c.create_polygon([0, mbottom] + pts + [w, mbottom], fill=m[i], outline="", smooth=True)
        c.create_line(pts, fill=mix(m[i], rim_target, 0.22 if i == 0 else 0.12), width=2, smooth=True)
        if i < 2:
            haze_top = lambda x, b=b, amp=amp, i=i: b - amp * 0.16 + 0.008 * h * math.sin(k * x * 3 + i)
            c.create_polygon(_poly_under(haze_top, w, mbottom, step * 2),
                             fill=mix(m[i], P["mist"], 0.45), outline="", smooth=True)

    # ── 6. Lake at the foot of the mountains (with shimmer) ──
    lake_top = hz + 0.072 * h
    lx1 = (0.36 if study else 0.44) * w
    c.create_polygon([-0.05 * w, lake_top, lx1, lake_top, lx1 + 0.03 * w, lake_top + 0.02 * h,
                      lx1 - 0.04 * w, lake_top + 0.07 * h, -0.05 * w, lake_top + 0.07 * h],
                     fill=P["water"][0], outline="", smooth=True)
    c.create_line(-0.05 * w, lake_top, lx1, lake_top, fill=mix(P["water"][0], P["mist"], 0.5), width=1)
    if 0 < sx < lx1 and cel != "noon":
        for j in range(6):
            yy = lake_top + 0.006 * h + j * 0.008 * h
            half = r * (1.0 - j * 0.13)
            c.create_line(sx - half, yy, sx + half, yy, fill=mix(P["water"][0], core, 0.65 - j * 0.06), width=2)
    for j in range(6):
        x = rng.uniform(0.01 * w, lx1 - 0.04 * w)
        y = rng.uniform(lake_top + 0.005 * h, lake_top + 0.045 * h)
        ln = rng.uniform(5, 15) * sc
        iid = c.create_line(x, y, x + ln, y, fill=P["water"][1], width=1)
        if j < 2:
            S["shimmer"].append([iid, P["water"][1], P["water"][0], rng.uniform(0, 6.28), -1])

    # ── 7. Cliff + small waterfall (forest view) ──
    river_fn = None
    if not study:
        rock_d = mix(P["rock"][1], m[2], 0.45)
        c.create_polygon([0.785 * w, hz + 0.14 * h, 0.80 * w, hz + 0.05 * h, 0.83 * w, hz + 0.0 * h,
                          0.875 * w, hz - 0.02 * h, 0.915 * w, hz + 0.025 * h, 0.94 * w, hz + 0.14 * h],
                         fill=rock_d, outline="", smooth=True)
        c.create_line(0.82 * w, hz + 0.03 * h, 0.835 * w, hz + 0.11 * h, fill=mix(rock_d, "#FFFFFF", 0.15), width=2)
        c.create_line(0.895 * w, hz + 0.02 * h, 0.905 * w, hz + 0.10 * h, fill=mix(rock_d, "#000000", 0.15), width=2)
        fx0, fx1 = 0.855 * w, 0.875 * w
        ftop, fbot = hz + 0.005 * h, hz + 0.118 * h
        fall_col = mix(P["water"][1], P["water"][0], 0.25)
        c.create_rectangle(fx0, ftop, fx1, fbot, fill=fall_col, outline="")
        c.create_line(fx0, ftop, fx0, fbot, fill=P["water"][2], width=1)
        c.create_line(fx1, ftop, fx1, fbot, fill=P["water"][2], width=1)
        foam = mix(P["water"][1], "#FFFFFF", 0.5)
        for j in range(2):
            x = fx0 + (fx1 - fx0) * (0.3 + 0.4 * j)
            y = ftop + (fbot - ftop) * j / 2.0
            iid = c.create_line(x, y, x, y + 0.02 * h, fill=foam, width=1)
            S["falls"].append([iid, y, ftop, fbot - 0.02 * h, 0.06 * h])
        S["pool"] = (0.865 * w, hz + 0.122 * h)

        y_top = hz + 0.122 * h

        def river_fn(y, y_top=y_top):
            if y < y_top or y > h:
                return None
            t = (y - y_top) / (h - y_top)
            xc = w * (0.865 - 0.12 * t + 0.045 * math.sin(t * math.pi * 2.2))
            return xc, w * (0.010 + 0.048 * t ** 1.3)
    S["river"] = river_fn

    # ── 8. Rolling meadow hills ──
    hs = P["hills"]
    rims = P["rim"]

    def far_fn(x):
        return hz + 0.07 * h + 0.045 * h * (1 - x / w) ** 1.5 + 0.012 * h * math.sin(k * x * 1.6 + 1.0)

    def mid_fn(x):
        return hz + 0.19 * h + 0.028 * h * math.sin(k * x * 0.9 + 0.7) + 0.016 * h * math.sin(k * x * 2.3 + 2.0)

    if study:
        def near_fn(x):
            return (hz + 0.31 * h + 0.018 * h * math.sin(k * x * 1.3 + 2.1)
                    - 0.045 * h * math.exp(-((x - 0.5 * w) / (0.24 * w)) ** 2))
    else:
        def near_fn(x):
            return hz + 0.34 * h + 0.022 * h * math.sin(k * x * 1.2 + 2.1)
    S["far"], S["mid"], S["near"] = far_fn, mid_fn, near_fn

    hstep = max(16, w / 22)
    # far hill
    c.create_polygon(_poly_under(far_fn, w, h, hstep), fill=hs[0], outline="", smooth=True)

    # distant tree line with groves & clearings (varied silhouettes)
    tl = P["treeline"]
    x = rng.uniform(0, 0.01 * w)
    while x < w:
        dens = 0.5 + 0.5 * math.sin(k * x * 2.1 + 0.8)
        if x < 0.42 * w:
            dens *= 0.35
        if rng.random() < dens:
            gy = far_fn(x) + 0.004 * h
            th = rng.uniform(0.024, 0.058) * h
            col = mix(tl, P["mist"], rng.uniform(0.0, 0.28))
            if rng.random() < 0.55:
                tw = th * rng.uniform(0.32, 0.42)
                c.create_polygon(x - tw, gy, x, gy - th, x + tw, gy, fill=col, outline="")
            else:
                rr = th * rng.uniform(0.38, 0.5)
                c.create_oval(x - rr, gy - rr * 2.1, x + rr, gy, fill=col, outline="")
        x += rng.uniform(0.032, 0.060) * w
    c.create_line(_line_along(far_fn, w, hstep), fill=rims[0], width=2, smooth=True)
    for _ in range(6):
        x = rng.uniform(0, w)
        y = rng.uniform(far_fn(x) + 3, mid_fn(x) - 2)
        d = 3.0 * sc
        c.create_oval(x - d, y - d * 0.5, x + d, y + d * 0.5, fill=rng.choice(P["dabs"][:3]), outline="")

    # mid hill
    c.create_polygon(_poly_under(mid_fn, w, h, hstep), fill=hs[1], outline="", smooth=True)
    # framing grove on the left of the mid hill
    for gx in (0.015, 0.05, 0.085):
        gy = mid_fn(gx * w) + 0.01 * h
        rr = (0.045 + 0.01 * math.sin(gx * 40)) * h
        cx = gx * w
        c.create_oval(cx - rr, gy - rr * 1.9, cx + rr, gy + rr * 0.1, fill=P["bush"][0], outline="")
        c.create_oval(cx - rr * 0.7, gy - rr * 2.0, cx + rr * 0.5, gy - rr * 0.7, fill=P["bush"][1], outline="")
    c.create_line(_line_along(mid_fn, w, hstep), fill=rims[1], width=2, smooth=True)
    for _ in range(10):
        x = rng.uniform(0, w)
        y = rng.uniform(mid_fn(x) + 4, near_fn(x) - 2)
        d = 4.2 * sc
        c.create_oval(x - d, y - d * 0.45, x + d, y + d * 0.45, fill=rng.choice(P["dabs"]), outline="")

    # near hill
    c.create_polygon(_poly_under(near_fn, w, h, hstep), fill=hs[2], outline="", smooth=True)
    c.create_line(_line_along(near_fn, w, hstep), fill=rims[2], width=2, smooth=True)
    for _ in range(12):
        x = rng.uniform(0, w)
        y = rng.uniform(near_fn(x) + 4, h)
        d = 6.0 * sc
        c.create_oval(x - d, y - d * 0.4, x + d, y + d * 0.4, fill=rng.choice(P["dabs"]), outline="")

    # ── 9. Winding river (forest) ──
    if river_fn:
        y_top = hz + 0.122 * h
        left, right = [], []
        for i in range(13):
            y = y_top + (h - y_top) * i / 12.0
            xc, hw = river_fn(y)
            left.extend([xc - hw, y])
            right[:0] = [xc + hw, y]
        c.create_polygon(left + [left[-2], h + 4, right[0], h + 4] + right,
                         fill=P["water"][0], outline=P["water"][2], width=2, smooth=True)
        px, py = S["pool"]
        c.create_oval(px - 0.05 * w, py - 0.016 * h, px + 0.05 * w, py + 0.016 * h,
                      fill=P["water"][0], outline=P["water"][2])
        c.create_oval(px - 0.02 * w, py - 0.006 * h, px + 0.02 * w, py + 0.006 * h,
                      fill=mix(P["water"][1], "#FFFFFF", 0.3), outline="")
        for j in range(5):
            y = y_top + (h - y_top) * (0.10 + 0.18 * j)
            xc, hw = river_fn(y)
            ln = hw * 0.6
            iid = c.create_line(xc - ln + rng.uniform(-2, 2), y, xc + ln * 0.3, y, fill=P["water"][1], width=1)
            if j < 2:
                S["shimmer"].append([iid, P["water"][1], P["water"][0], rng.uniform(0, 6.28), -1])

    # ── 10. Winding path with sky puddles ──
    if study:
        p_far = hz + 0.17 * h

        def path_xw(t):
            return w * (0.30 + 0.30 * t - 0.06 * math.sin(t * math.pi * 2.0)), w * (0.070 * (1 - t) ** 1.3 + 0.004)
    else:
        p_far = hz + 0.10 * h

        def path_xw(t):
            return w * (0.42 + 0.10 * math.sin(t * math.pi * 1.4 + 0.3) - 0.05 * t), w * (0.075 * (1 - t) ** 1.4 + 0.004)

    def path_fn(y):
        if y < p_far or y > h:
            return None
        return path_xw((h - y) / (h - p_far))
    S["path"] = path_fn

    pf, pe, ph = P["path"]
    left, right, centre = [], [], []
    for i in range(13):
        t = i / 12.0
        y = h - t * (h - p_far)
        xc, hw = path_xw(t)
        left.extend([xc - hw, y])
        right[:0] = [xc + hw, y]
        if t < 0.75:
            centre.extend([xc - hw * 0.15, y])
    c.create_polygon([left[0], h + 4] + left + right + [right[-2], h + 4],
                     fill=pf, outline=pe, width=2, smooth=True)
    c.create_line(centre, fill=ph, width=max(1, int(2 * sc)), smooth=True)
    puddle = mix(sky_at(hz * 0.6), pf, 0.15)
    for t in (0.12, 0.30, 0.52):
        y = h - t * (h - p_far)
        xc, hw = path_xw(t)
        pw, phh = hw * 0.55, max(2, hw * 0.12)
        ox = hw * 0.15 * (1 if t != 0.30 else -1)
        c.create_oval(xc + ox - pw, y - phh, xc + ox + pw, y + phh, fill=puddle, outline=pe)
        c.create_line(xc + ox - pw * 0.5, y - phh * 0.2, xc + ox + pw * 0.1, y - phh * 0.2,
                      fill=mix(puddle, "#FFFFFF", 0.45), width=1)

    def blocked(x, y, pad=0.0):
        pr = path_fn(y)
        if pr and abs(x - pr[0]) < pr[1] + pad:
            return True
        if river_fn:
            rr = river_fn(y)
            if rr and abs(x - rr[0]) < rr[1] + pad:
                return True
            px, py = S["pool"]
            if abs(y - py) < 0.04 * h and abs(x - px) < 0.07 * w + pad:
                return True
        return False
    S["blocked"] = blocked

    # ── 11. Rocks ──
    def rock(x, y, s):
        rb, rd = P["rock"]
        c.create_oval(x - s * 1.2, y - s * 0.15, x + s * 1.2, y + s * 0.45, fill=P["shadow"], outline="")
        c.create_oval(x - s, y - s * 0.75, x + s, y + s * 0.35, fill=rd, outline="")
        c.create_oval(x - s * 0.85, y - s * 0.8, x + s * 0.55, y + s * 0.05, fill=rb, outline="")
        c.create_oval(x - s * 0.55, y - s * 0.65, x - s * 0.05, y - s * 0.35, fill=mix(rb, "#FFFFFF", 0.3), outline="")

    if river_fn:
        for t, side, s in ((0.25, -1, 6), (0.45, 1, 8), (0.72, -1, 10), (0.9, 1, 12)):
            y = hz + 0.122 * h + (h - hz - 0.122 * h) * t
            xc, hw = river_fn(y)
            rock(xc + side * (hw + s * sc * 1.3), y, s * sc)
    for t, side, s in ((0.20, 1, 7), (0.45, -1, 5)):
        y = h - t * (h - p_far)
        xc, hw = path_xw(t)
        rock(xc + side * (hw + s * sc * 1.6), y, s * sc)

    # ── 12. Foreground framing bushes ──
    def bush(cx, cy, s):
        b0, b1, b2 = P["bush"]
        for ox, oy, rr, col in ((-0.6, 0.1, 0.55, b0), (0.55, 0.15, 0.5, b0), (0.0, -0.15, 0.65, b0),
                                (-0.35, -0.25, 0.45, b1), (0.3, -0.2, 0.42, b1), (-0.1, -0.5, 0.35, b2),
                                (0.35, -0.42, 0.25, b2)):
            x, y = cx + ox * s, cy + oy * s
            c.create_oval(x - rr * s, y - rr * s * 0.85, x + rr * s, y + rr * s * 0.85, fill=col, outline="")
        for _ in range(2):
            x = cx + rng.uniform(-0.6, 0.6) * s
            y = cy + rng.uniform(-0.6, 0.0) * s
            d = 0.06 * s
            c.create_oval(x - d, y - d * 0.6, x + d, y + d * 0.6, fill=mix(b2, "#FFFFFF", 0.18), outline="")

    bs = 0.085 * h
    bush(0.02 * w, h - 0.02 * h, bs * 1.25)
    bush(0.10 * w, h + 0.01 * h, bs * 0.9)
    bush(0.985 * w, h - 0.01 * h, bs * 1.15)
    if study:
        bush(0.90 * w, h + 0.02 * h, bs * 0.8)

    # ── 13. Wildflower patches (grow with study history) ──
    fl = P["flowers"]
    n_patches = int((4 if study else 6) + (5 if study else 8) * richness)
    for _ in range(n_patches):
        for _try in range(6):
            x = rng.uniform(0.04 * w, 0.96 * w)
            y = rng.uniform(mid_fn(x) + 0.02 * h, h - 0.02 * h)
            if not blocked(x, y, 10 * sc):
                break
        col = rng.choice(fl)
        depth = (y - hz) / (h - hz)
        d = (1.2 + 2.0 * depth) * sc
        for _ in range(rng.randint(2, 4)):
            fx = x + rng.uniform(-14, 14) * sc * depth
            fy = y + rng.uniform(-4, 4) * sc * depth
            if blocked(fx, fy, 2):
                continue
            c.create_oval(fx - d, fy - d, fx + d, fy + d, fill=col, outline="")
            if d > 2.6:
                c.create_oval(fx - d * 0.35, fy - d * 0.35, fx + d * 0.35, fy + d * 0.35,
                              fill="#F7E08A" if col != "#FFF0B5" else "#E8B85C", outline="")

    # ── 14. Mushrooms (appear as the forest matures) ──
    n_mush = int((2 if study else 1) + (4 if study else 7) * richness)
    cap_col = mix("#C9574B", P["tint"][0], P["tint"][1] + 0.1)
    stem_col = mix("#F3E6D2", P["tint"][0], P["tint"][1])
    for _ in range(n_mush):
        for _try in range(8):
            if study:
                x = w * (0.5 + rng.choice((-1, 1)) * rng.uniform(0.14, 0.32))
                y = near_fn(x) + rng.uniform(0.03, 0.10) * h
            else:
                x = rng.uniform(0.06 * w, 0.94 * w)
                y = rng.uniform(near_fn(x) - 0.08 * h, h - 0.03 * h)
            if not blocked(x, y, 14 * sc):
                break
        s = rng.uniform(3.0, 5.0) * sc * (0.6 + 0.6 * (y - hz) / (h - hz))
        c.create_rectangle(x - s * 0.3, y - s * 1.1, x + s * 0.3, y, fill=stem_col, outline="")
        c.create_arc(x - s, y - s * 1.9, x + s, y - s * 0.4, start=0, extent=180, style="chord",
                     fill=cap_col, outline="")
        c.create_oval(x - s * 0.45, y - s * 1.55, x - s * 0.15, y - s * 1.3, fill="#FFF6EA", outline="")

    # ── 15. Grass: compact single-polyline tufts (static to avoid idle repaints) ──
    gcol = P["grass"]
    n_static = 8 if study else 10
    for _ in range(n_static):
        x = rng.uniform(0, w)
        y = rng.uniform(near_fn(x) + 0.01 * h, h)
        if blocked(x, y, 4):
            continue
        L = rng.uniform(5, 10) * sc * (0.6 + (y - hz) / (h - hz))
        c.create_line(
            x - 3, y - L * 0.75, x, y, x, y - L, x, y, x + 3, y - L * 0.75,
            fill=gcol, width=1,
        )

    # Ground anchor for the study tree (sits on the central knoll)
    S["study_ground"] = (0.5 * w, near_fn(0.5 * w) + 0.075 * h)
    return S


# ─────────────────────────────────────────────────────────────────────
#  Forest tree placement (natural staggered rows, stable ordering)
# ─────────────────────────────────────────────────────────────────────

def forest_slots(S, n):
    """Return n placements [(x, ground_y, scale)] spread naturally across the
    meadow, avoiding the path and river.  Earlier trees keep good spots."""
    if n <= 0:
        return []
    w, h = S["w"], S["h"]
    mid_fn = S["mid"]
    hz = S["hz"]
    y0 = hz + 0.22 * h
    y1 = h * 0.965
    boost = 1.30 if n <= 4 else (1.15 if n <= 10 else (1.0 if n <= 24 else 0.88))
    base = max(0.55, min(1.5, h / 520.0))
    density = 1.0
    slots = []
    for _attempt in range(9):
        rng = random.Random(4242)
        slots = []
        y, r = y0, 0
        while y < y1:
            depth = (y - y0) / max(1.0, (y1 - y0))
            s = (0.24 + 0.30 * depth) * base * boost
            spacing = max(24.0, 150.0 * s * density)
            x = 0.06 * w + (spacing * 0.5 if r % 2 else 0.0)
            while x < 0.94 * w:
                jx = x + rng.uniform(-0.18, 0.18) * spacing
                jy = y + rng.uniform(-6, 6) * base
                if (jy > mid_fn(jx) + 8 and not S["blocked"](jx, jy, 30 * s)
                        and not (jx < 0.13 * w and jy > 0.86 * h)
                        and not (jx > 0.90 * w and jy > 0.84 * h)):
                    pri = rng.random() + 0.45 * abs(depth - 0.55)
                    slots.append((pri, jx, jy, s))
                x += spacing
            y += max(16.0, 70.0 * s * density)
            r += 1
        if len(slots) >= n:
            break
        density *= 0.82
    slots.sort(key=lambda t: t[0])
    out = [(sx, sy, ss) for _, sx, sy, ss in slots[:n]]
    i = 0
    while len(out) < n and slots:          # extreme counts: gently reuse with offsets
        _, sx, sy, ss = slots[i % len(slots)]
        out.append((sx + 9 * (1 + i // len(slots)), sy + 4, ss * 0.9))
        i += 1
    return out


# ─────────────────────────────────────────────────────────────────────
#  Animated actors (fixed small budget)
# ─────────────────────────────────────────────────────────────────────

def spawn_actors(c, S, rain=False, leaf_color=None, sway_tag=None, sway_amp=0.0):
    P = S["pal"]
    w, h, hz, sc = S["w"], S["h"], S["hz"], S["sc"]
    rng = random.Random(9)
    A = {"fire": [], "fly": [], "birds": [], "leaves": [], "rain": [], "sway": None}

    # Fireflies (night) or magical motes (chill)
    if P.get("fireflies") or P.get("motes"):
        glow, core = (("#3C6B4E", "#D9F99D") if P.get("fireflies") else ("#F3DDE6", "#FFFFFF"))
        count = 4 if P.get("fireflies") else 3
        for i in range(count):
            x = rng.uniform(0.06 * w, 0.94 * w)
            y = rng.uniform(S["mid"](x) - 0.03 * h, h - 0.06 * h)
            tag = "ff_%d" % i
            c.create_oval(x - 4, y - 4, x + 4, y + 4, fill=glow, outline="", tags=(tag, "actor"))
            c.create_oval(x - 1.5, y - 1.5, x + 1.5, y + 1.5, fill=core, outline="", tags=(tag, "actor"))
            A["fire"].append([tag, rng.uniform(0, 6.28), rng.uniform(8, 18) * sc, rng.uniform(6, 12) * sc, 0.0, 0.0])

    # Butterflies (day themes)
    if P.get("butterflies"):
        for i in range(2):
            x = w * (0.25 + 0.45 * i)
            y = S["near"](x) - 0.05 * h
            col = P["flowers"][i % len(P["flowers"])]
            if col == "#FFFFFF":
                col = "#F6E7A6"
            tag = "bf_%d" % i
            d = 3.2 * sc
            c.create_oval(x - d * 2, y - d, x, y + d * 0.6, fill=col, outline="", tags=(tag, "actor"))
            c.create_oval(x, y - d, x + d * 2, y + d * 0.6, fill=col, outline="", tags=(tag, "actor"))
            c.create_line(x, y - d, x, y + d * 0.8, fill="#4A3B33", width=1, tags=(tag, "actor"))
            A["fly"].append([tag, rng.uniform(0, 6.28), 40 * sc, 14 * sc, 0.0, 0.0])

    # Birds drifting in the sky
    if P.get("birds"):
        for i in range(2):
            x = w * (0.30 + 0.12 * i)
            y = h * (0.16 + 0.03 * i)
            tag = "bird_%d" % i
            s = 4 * sc
            c.create_line(x - s, y - s * 0.5, x - s * 0.3, y, x, y - s * 0.2, x + s * 0.3, y, x + s, y - s * 0.5,
                          fill=P["birds"], width=1, smooth=True, tags=(tag, "actor"))
            A["birds"].append([tag, 6 + 2 * i, rng.uniform(0, 6.28), 0.0])

    # Occasional falling leaves / petals
    lc = leaf_color or P["leaf"]
    for i in range(2):
        x = rng.uniform(0.15 * w, 0.85 * w)
        y = rng.uniform(0.35 * h, 0.9 * h)
        d = 2.6 * sc
        iid = c.create_oval(x - d, y - d * 0.55, x + d, y + d * 0.55, fill=lc, outline="", tags=("actor",))
        A["leaves"].append([iid, x, y, rng.uniform(10, 18) * sc, rng.uniform(0, 6.28), 0.0])

    if rain:
        add_rain(c, S, A)

    # Keep trees stationary to avoid full-canvas dirty-rect repaints on idle ticks
    A["sway"] = None
    return A


def add_rain(c, S, A):
    w, h = S["w"], S["h"]
    rng = random.Random(31)
    col = mix(S["pal"]["water"][1], S["sky_at"](S["hz"] * 0.5), 0.3)
    A["rain"] = []
    for _ in range(10):
        x = rng.uniform(0, w + 40)
        y = rng.uniform(-h * 0.1, h)
        L = rng.uniform(10, 18)
        iid = c.create_line(x, y, x - 3, y + L, fill=col, width=1, tags=("rain",))
        A["rain"].append([iid, y])


def remove_rain(c, A):
    c.delete("rain")
    A["rain"] = []


def step(c, S, A, now, dt, flush=None):
    """Advance animations with staggered small-region updates so Tk never
    unions distant screen bands into a full-canvas repaint."""
    w, h = S["w"], S["h"]
    tick = S.get("_tick", 0) + 1
    S["_tick"] = tick

    rain_list = A["rain"]
    if rain_list:
        if tick % 2 != 0:
            return
        n_r = len(rain_list)
        vy = 430 * dt * 2 * n_r
        vx = -75 * dt * 2 * n_r
        rd = rain_list[(tick // 2) % n_r]
        rd[1] += vy
        if rd[1] > h:
            c.move(rd[0], w * 0.08 + random.uniform(-20, 20), -(h + 30))
            rd[1] -= h + 30
        else:
            c.move(rd[0], vx, vy)
        if tick % 8 != 0:
            return
        if flush:
            flush()

    if not rain_list and tick % 3 != 0:
        return

    if rain_list or tick % 6 == 0:
        # Sky band: step 1 cloud round-robin + birds + twinkle stars
        clouds = S["clouds"]
        if clouds:
            cl = clouds[(tick // 6) % len(clouds)]
            tag, spd = cl
            c.move(tag, spd * dt * 6 * len(clouds), 0)
            bb = c.bbox(tag)
            if bb and bb[0] > w + 4:
                c.move(tag, -(w + (bb[2] - bb[0]) + 8), 0)
        for b in A["birds"]:
            tag, spd, ph, prev = b
            bob = 2.0 * math.sin(now * 0.9 + ph)
            c.move(tag, spd * dt * 6, bob - prev)
            b[3] = bob
            bb = c.bbox(tag)
            if bb and bb[0] > w + 4:
                c.move(tag, -(w + 30), 0)
        for tw in S["twinkle"]:
            state = 1 if math.sin(now * 1.3 + tw[3]) > 0.55 else 0
            if state != tw[4]:
                tw[4] = state
                c.itemconfigure(tw[0], fill=tw[2] if state else tw[1])
        if flush:
            flush()

        # Water shimmer (flushed separately from sky band)
        shimmer_changed = False
        for sh in S["shimmer"]:
            state = 1 if math.sin(now * 0.8 + sh[3]) > 0.3 else 0
            if state != sh[4]:
                sh[4] = state
                c.itemconfigure(sh[0], fill=sh[2] if state else sh[1])
                shimmer_changed = True
        if shimmer_changed and flush:
            flush()
        return

    # tick % 6 == 3: localized waterfall foam, then 1 ground actor round-robin
    if S["falls"]:
        for f in S["falls"]:
            iid, y, top, bottom, spd = f
            ny = y + spd * dt * 6
            if ny > bottom:
                c.move(iid, 0, top - y)
                ny = top
            else:
                c.move(iid, 0, ny - y)
            f[1] = ny
        if flush:
            flush()

    ground_actors = (
        [("fire", ff) for ff in A["fire"]]
        + [("fly", bf) for bf in A["fly"]]
        + [("leaf", lf) for lf in A["leaves"]]
    )
    if ground_actors:
        kind, obj = ground_actors[(tick // 6) % len(ground_actors)]
        if kind == "fire":
            tag, ph, ax, ay, px, py = obj
            ox = ax * math.sin(now * 0.55 + ph)
            oy = ay * math.sin(now * 0.8 + ph * 1.7)
            c.move(tag, ox - px, oy - py)
            obj[4], obj[5] = ox, oy
        elif kind == "fly":
            tag, ph, ax, ay, px, py = obj
            ox = ax * math.sin(now * 0.4 + ph)
            oy = ay * math.sin(now * 1.1 + ph * 1.3) + 3 * math.sin(now * 9 + ph)
            c.move(tag, ox - px, oy - py)
            obj[4], obj[5] = ox, oy
        else:
            iid, x, y, vy, ph, pdx = obj
            eff_dt = dt * 6 * len(ground_actors)
            dx = 10 * math.sin(now * 1.1 + ph)
            ny = y + vy * eff_dt
            if ny > h * 0.96:
                nx = random.uniform(0.15 * w, 0.85 * w)
                c.move(iid, nx - x + dx - pdx, h * 0.32 - y)
                obj[1], obj[2] = nx, h * 0.32
            else:
                c.move(iid, dx - pdx, ny - y)
                obj[2] = ny
            obj[5] = dx
