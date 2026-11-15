"""
scenery.py - Hand-drawn lo-fi anime / indie-comic landscape engine for Grow Your Forest.

Design goals
------------
* Painterly, cohesive 2D illustration style across four atmospheric themes
  (Morning, Afternoon, Night, Chill):
  - Smooth multi-stop sky PhotoImage with 3-4% paper grain, continuous radial
    sun/moon glow, and a faint diagonal Milky Way dust band in Night mode.
  - Wispy, flat-bottomed cel-shaded clouds (no circle clusters).
  - Irregular multi-tiered conifer treelines (no basic triangles or lollipop ovals)
    and dark ink-outlined framing foreground trees along the left/right edges.
  - Textured grass strokes, illustrated ferns, faceted pebbles, and cross-hatched
    shading along hills, path edges, and the central planting mound.
* Performance first: the static scene + cached sky bitmap build once per
  (size, theme, view), while ambient actors move a tiny fixed budget via
  canvas.move / itemconfigure grouped by screen band.
"""

import math
import random
import tkinter as tk

# ─────────────────────────────────────────────────────────────────────
#  Theme palettes (lo-fi anime / indie-comic tones)
# ─────────────────────────────────────────────────────────────────────

PALETTES = {
    "morning": dict(
        sky=["#5a929e", "#7ca7ae", "#a9c3ba", "#e2bfa4", "#fce2ce"],
        celestial="sunrise", sun_core="#fff4db", sun_glow=(255, 226, 182),
        cloud=("#fff1e6", "#d8c2b5", "#fffaf2"),
        mountains=["#9b8ea0", "#83758a", "#6a5c70"],
        mist="#f7ded0", fog_layers=True,
        treeline="#446654", treeline_shade="#2d483b",
        water=("#8eb4cc", "#e8f2f5", "#6c94ad"),
        hills=["#8fa87f", "#749267", "#5a7851"],
        rim=["#e2e3b5", "#c9d69b", "#a4bb83"], clearing_rim="#edeac0",
        path=("#c8a184", "#9e7960", "#e2bfa3"),
        rock=("#a7a49e", "#767572", "#d0cdc6"),
        bush=("#2d4838", "#42644e", "#688d6c"),
        framing_dark="#203328", framing_mid="#34523e", framing_hi="#9ac08c",
        bark="#473a35", bark_hi="#6e5a50", ink="#1d3324",
        flowers=["#f4cbd4", "#fff1c2", "#faf8f0", "#d4c8eb"],
        shadow="#3f5942", hatch="#2e4434", cast_shadows=False,
        tint=("#fce2ce", 0.08),
        grass="#527450", grass_hi="#a8c78c", leaf="#f2cad6",
        stars=False, milky_way=False, fireflies=False, birds="#525a75", butterflies=True, motes=False,
    ),
    "afternoon": dict(
        sky=["#4a7ab5", "#6a91bd", "#95acc0", "#cbb29e", "#f5b971"],
        celestial="noon", sun_core="#fff5cc", sun_glow=(255, 214, 140),
        cloud=("#fff4e3", "#c8b3b0", "#fffcf2"),
        mountains=["#748eb4", "#58739a", "#3f587c"],
        mist="#e8c8a8", fog_layers=False,
        treeline="#395642", treeline_shade="#253b2d",
        water=("#6ca2bf", "#dcecf2", "#4e819e"),
        hills=["#89a356", "#6f8942", "#556e31"],
        rim=["#e6cf7e", "#c7b665", "#a49a4e"], clearing_rim="#f0da8a",
        path=("#c99972", "#9c704f", "#e3ba92"),
        rock=("#a59e95", "#736c65", "#ccc3b8"),
        bush=("#253d29", "#37553b", "#597b50"),
        framing_dark="#1c2e1f", framing_mid="#304b33", framing_hi="#9cb360",
        bark="#42332a", bark_hi="#6c5242", ink="#172e1c",
        flowers=["#f4b2be", "#ffe494", "#faf6ea", "#c8b7e8"],
        shadow="#385029", hatch="#283d1f", cast_shadows=True,
        tint=("#f5b971", 0.07),
        grass="#496b34", grass_hi="#a7ba64", leaf="#d2d87e",
        stars=False, milky_way=False, fireflies=False, birds="#42516e", butterflies=True, motes=False,
    ),
    "night": dict(
        sky=["#0f1326", "#161d36", "#1f2746", "#2b3556"],
        celestial="moon", sun_core="#f4f2e6", sun_glow=(168, 188, 232),
        cloud=("#3d4a70", "#222a45", "#5a6b99"),
        mountains=["#283152", "#1e2540", "#161c33"],
        mist="#2c3759", fog_layers=True,
        treeline="#12172c", treeline_shade="#0a0e1d",
        water=("#212c4d", "#6e82b4", "#151d36"),
        hills=["#17233a", "#111b2e", "#0c1424"],
        rim=["#32456b", "#243454", "#192640"], clearing_rim="#3a4f7a",
        path=("#252d45", "#181e30", "#3a4566"),
        rock=("#35415e", "#1e263b", "#4e5e85"),
        bush=("#090d1c", "#10162b", "#1c2647"),
        framing_dark="#070914", framing_mid="#10152b", framing_hi="#28355e",
        bark="#111526", bark_hi="#232c4a", ink="#0c1428",
        flowers=["#92a6de", "#d4def7", "#b5a6e6", "#8fd4c0"],
        shadow="#070c17", hatch="#050812", cast_shadows=False,
        tint=("#1a2342", 0.42),
        grass="#18253d", grass_hi="#344a70", leaf="#8da5d4",
        stars="night", milky_way=True, fireflies=True, birds=None, butterflies=False, motes=False,
    ),
    "chill": dict(
        sky=["#1b162b", "#382446", "#663b5a", "#9e5c6e", "#d88c82"],
        celestial="sunset", sun_core="#ffd2b0", sun_glow=(238, 152, 134),
        cloud=("#d48d8c", "#5e3c5c", "#f3beb2"),
        mountains=["#4b324e", "#36233d", "#26192e"],
        mist="#9c6272", fog_layers=True,
        treeline="#21172e", treeline_shade="#140d1e",
        water=("#4a3652", "#d48d88", "#312238"),
        hills=["#352b38", "#27202b", "#1c1721"],
        rim=["#d4867c", "#b06d68", "#8a5252"], clearing_rim="#e39a86",
        path=("#543d45", "#38272e", "#7d585e"),
        rock=("#544354", "#332736", "#876978"),
        bush=("#140e1f", "#20172e", "#3a2947"),
        framing_dark="#100b19", framing_mid="#1f1630", framing_hi="#804c62",
        bark="#1f1629", bark_hi="#4c354c", ink="#191128",
        flowers=["#f2b29b", "#e88b82", "#f5d0c5", "#c89bc9"],
        shadow="#130e18", hatch="#0e0a12", cast_shadows=False,
        tint=("#b56468", 0.25),
        grass="#3d2c3d", grass_hi="#a6696e", leaf="#e09c96",
        stars="chill", milky_way=True, fireflies=True, birds="#382446", butterflies=False, motes=True,
        campfire=True,
    ),
}

LEAF_BY_SPECIES = {
    "cherry_blossom": "#F5C2D2",
    "oak": "#B9C46A",
    "pine": "#9C7B58",
    "angel_oak": "#A9B99A",
}

# ─────────────────────────────────────────────────────────────────────
#  Colour helpers & cached 2D grain / PPM sky generator
# ─────────────────────────────────────────────────────────────────────

_mix_cache = {}
_SKY_PPM_CACHE = {}

# Precomputed 97x53 tile of smooth deterministic 3-4% paper grain (-7..+7 RGB)
_GRAIN_W, _GRAIN_H = 97, 53
_GRAIN_TILE = None


def _init_grain_tile():
    global _GRAIN_TILE
    if _GRAIN_TILE is None:
        rng = random.Random(1337)
        _GRAIN_TILE = [
            [rng.randint(-7, 7) for _ in range(_GRAIN_W)]
            for _ in range(_GRAIN_H)
        ]
    return _GRAIN_TILE


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


def _gradient_rgb(rgb_stops, t):
    t = 0.0 if t < 0 else (0.9999 if t >= 1 else t)
    seg = t * (len(rgb_stops) - 1)
    i = int(seg)
    f = seg - i
    r0, g0, b0 = rgb_stops[i]
    r1, g1, b1 = rgb_stops[i + 1]
    return int(r0 + (r1 - r0) * f), int(g0 + (g1 - g0) * f), int(b0 + (b1 - b0) * f)


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


def _build_sky_photo(c, w, sky_bottom, P, theme, sx, sy, cel_r):
    """Build a smooth multi-stop atmospheric sky PhotoImage with 3-4% paper
    grain, smooth radial celestial glow, and (in Night mode) a faint diagonal
    Milky Way dust band.  Rendered at 1/2 scale and upscaled 2x2 (<18ms)."""
    gw = max(64, int(math.ceil(w / 2.0)))
    gh = max(48, int(math.ceil(sky_bottom / 2.0)))
    sx_g = sx * 0.5
    sy_g = sy * 0.5
    glow_r = max(24.0, (cel_r * 3.8 if P["celestial"] != "moon" else cel_r * 3.2) * 0.5)
    key = (theme, gw, gh, int(round(sx_g)), int(round(sy_g)), int(round(glow_r)))
    ppm = _SKY_PPM_CACHE.get(key)

    if ppm is None:
        grain_rows = _init_grain_tile()
        rgb_stops = [_rgb(s) for s in P["sky"]]
        reps = gw // _GRAIN_W + 2
        row_stride = gw * 3
        rows = []
        for y in range(gh):
            br, bg, bb = _gradient_rgb(rgb_stops, y / max(1, gh - 1))
            gt = grain_rows[y % _GRAIN_H]
            tile = bytes(
                0 if (v := col + g) < 0 else (255 if v > 255 else v)
                for g in gt for col in (br, bg, bb)
            )
            rows.append((tile * reps)[:row_stride])
        buf = bytearray(b"".join(rows))

        # Faint diagonal Milky Way nebula dust band (Night mode)
        if P.get("milky_way"):
            noise_row = grain_rows[11]
            for y in range(gh):
                t = y / max(1, gh - 1)
                if t > 0.94:
                    continue
                env = math.sin(min(1.0, t / 0.94) * math.pi) ** 0.75
                cx = gw * (0.14 + 0.56 * t + 0.025 * math.sin(t * 4.5))
                half_bw = gw * (0.065 + 0.045 * env)
                x0 = max(0, int(cx - half_bw))
                x1 = min(gw - 1, int(cx + half_bw))
                r_off = y * row_stride
                for x in range(x0, x1 + 1):
                    d = min(1.0, abs(x - cx) / max(1.0, half_bw))
                    wisp = max(0.0, 1.0 - d * d) ** 1.8 * env
                    wisp *= 0.85 + 0.15 * math.sin(x * 0.19 + y * 0.11)
                    # Subtle dark dust lane near the center of the band
                    rift = 0.0
                    if d < 0.24:
                        rift = (1.0 - (d / 0.24) ** 2) * env * 0.06
                    is_chill_mw = (P.get("stars") == "chill" or P.get("milky_way") == "chill")
                    alpha = wisp * (0.13 if is_chill_mw else 0.14) - rift
                    if alpha > 0.004 or alpha < -0.004:
                        idx = r_off + x * 3
                        sp = noise_row[(x + y * 7) % _GRAIN_W]
                        if is_chill_mw:
                            # Soft translucent lavender-pink stardust across upper deep-purple sky
                            nr, ng, nb = 185 + sp, 122 + sp, 172 + sp * 2
                        else:
                            nr, ng, nb = 78 + sp, 82 + sp, 138 + sp * 2
                        buf[idx] = max(0, min(255, int(buf[idx] + (nr - buf[idx]) * alpha)))
                        buf[idx + 1] = max(0, min(255, int(buf[idx + 1] + (ng - buf[idx + 1]) * alpha)))
                        buf[idx + 2] = max(0, min(255, int(buf[idx + 2] + (nb - buf[idx + 2]) * alpha)))

        # Smooth radial sun/moon atmospheric glow (zero stepped rings)
        gr, gg, gb = P["sun_glow"]
        glow_r2 = glow_r * glow_r
        gx0 = max(0, int(sx_g - glow_r))
        gx1 = min(gw - 1, int(sx_g + glow_r))
        gy0 = max(0, int(sy_g - glow_r))
        gy1 = min(gh - 1, int(sy_g + glow_r))
        peak_a = 0.62 if P["celestial"] != "moon" else 0.42
        inv_r = 1.0 / glow_r
        for y in range(gy0, gy1 + 1):
            dy = y - sy_g
            dy2 = dy * dy
            r_off = y * row_stride
            for x in range(gx0, gx1 + 1):
                dx = x - sx_g
                dist2 = dx * dx + dy2
                if dist2 < glow_r2:
                    dist = math.sqrt(dist2)
                    a = (max(0.0, 1.0 - dist * inv_r) ** 2.3) * peak_a
                    idx = r_off + x * 3
                    buf[idx] = int(buf[idx] + (gr - buf[idx]) * a)
                    buf[idx + 1] = int(buf[idx + 1] + (gg - buf[idx + 1]) * a)
                    buf[idx + 2] = int(buf[idx + 2] + (gb - buf[idx + 2]) * a)

        hdr = f"P6\n{gw} {gh}\n255\n".encode("ascii")
        ppm = hdr + bytes(buf)
        if len(_SKY_PPM_CACHE) > 20:
            _SKY_PPM_CACHE.clear()
        _SKY_PPM_CACHE[key] = ppm

    raw_img = tk.PhotoImage(master=c, data=ppm)
    img = raw_img.zoom(2, 2)
    return img


# ─────────────────────────────────────────────────────────────────────
#  Illustrated helper painters (zero basic triangles / circle-clouds)
# ─────────────────────────────────────────────────────────────────────

def _draw_cloud(c, x, y, s, lit, shade, rim, tag):
    """Wispy, flat-bottomed cel-shaded painterly cloud with soft trailing wisps."""
    base_y = y + 0.24 * s
    # Flat-bottomed silhouette with asymmetric lofted billows
    body_pts = [
        x - 1.38 * s, base_y,
        x - 1.05 * s, y + 0.04 * s,
        x - 0.72 * s, y - 0.14 * s,
        x - 0.44 * s, y - 0.10 * s,
        x - 0.14 * s, y - 0.46 * s,
        x + 0.20 * s, y - 0.36 * s,
        x + 0.56 * s, y - 0.22 * s,
        x + 0.88 * s, y - 0.04 * s,
        x + 1.28 * s, base_y,
        x + 0.85 * s, base_y + 0.04 * s,
        x - 0.10 * s, base_y + 0.03 * s,
        x - 0.92 * s, base_y + 0.04 * s,
    ]
    c.create_polygon(body_pts, fill=lit, outline="", smooth=True, tags=(tag, "cloud"))

    # Cel-shaded flat underside band
    shade_pts = [
        x - 1.28 * s, base_y + 0.01 * s,
        x - 0.82 * s, base_y - 0.10 * s,
        x - 0.20 * s, base_y - 0.06 * s,
        x + 0.38 * s, base_y - 0.11 * s,
        x + 0.96 * s, base_y - 0.04 * s,
        x + 1.24 * s, base_y + 0.02 * s,
        x + 0.70 * s, base_y + 0.04 * s,
        x - 0.65 * s, base_y + 0.04 * s,
    ]
    c.create_polygon(shade_pts, fill=shade, outline="", smooth=True, tags=(tag, "cloud"))

    # Crisp luminous top rim stroke
    rim_pts = [
        x - 0.70 * s, y - 0.13 * s,
        x - 0.42 * s, y - 0.09 * s,
        x - 0.14 * s, y - 0.44 * s,
        x + 0.20 * s, y - 0.34 * s,
        x + 0.54 * s, y - 0.20 * s,
    ]
    c.create_line(rim_pts, fill=rim, width=max(1, int(s * 0.045)), smooth=True, tags=(tag, "cloud"))

    # Delicate trailing wisps near the flat base
    c.create_line(x - 1.62 * s, base_y - 0.03 * s, x - 0.95 * s, base_y - 0.03 * s,
                  fill=shade, width=1, tags=(tag, "cloud"))
    c.create_line(x + 1.05 * s, base_y - 0.05 * s, x + 1.56 * s, base_y - 0.05 * s,
                  fill=lit, width=1, tags=(tag, "cloud"))


def _draw_crescent_moon(c, sx, sy, r, core):
    """Crisp sunlit crescent moon polygon (no circle mask seams over sky)."""
    pts = []
    # Outer bright limb arc (-65 deg to +115 deg -> facing upper-left/right cleanly)
    n_arc = 14
    a0, a1 = -0.36 * math.pi, 0.88 * math.pi
    for i in range(n_arc + 1):
        ang = a0 + (a1 - a0) * i / n_arc
        pts.extend([sx + r * math.cos(ang), sy - r * math.sin(ang)])
    # Inner concave shadow limb
    for i in range(n_arc, -1, -1):
        t = i / n_arc
        ang = a0 + (a1 - a0) * t
        cut = math.sin(t * math.pi) * r * 0.58
        pts.extend([sx + (r * 0.86 - cut) * math.cos(ang) + r * 0.30,
                    sy - (r * 0.86 - cut) * math.sin(ang) - r * 0.14])
    c.create_polygon(pts, fill=core, outline="", smooth=True)


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


def _draw_conifer_grove(c, w, h, ridge_fn, P, rng, flank=False):
    """Organic jagged conifer silhouettes nestled behind a hill ridge."""
    tl = P["treeline"]
    tl_shade = P["treeline_shade"]
    mist = P["mist"]
    hs = P["hills"]
    pts_top = [0.0, ridge_fn(0.0) + 0.03 * h]
    x = 0.0
    while x < w:
        u = x / w
        if flank:
            dens = 0.72 if (u < 0.28 or u > 0.72) else 0.0
        else:
            dens = 0.54 + 0.46 * math.sin((2 * math.pi / w) * x * 1.9 + 0.7)
            if u < 0.36:
                dens *= 0.45
        gy = ridge_fn(x) + 0.010 * h
        if rng.random() < dens:
            th = rng.uniform(0.028, 0.072) * h * (0.82 if flank else 1.0)
            tw = th * rng.uniform(0.34, 0.48)
            lean = rng.uniform(-0.08, 0.08) * th
            pts_top.extend([
                x - tw * 0.95, gy - th * 0.16,
                x - tw * 0.45, gy - th * 0.24,
                x - tw * 0.68, gy - th * 0.48,
                x - tw * 0.26, gy - th * 0.56,
                x - tw * 0.38, gy - th * 0.76,
                x + lean, gy - th,
                x + tw * 0.34, gy - th * 0.74,
                x + tw * 0.22, gy - th * 0.54,
                x + tw * 0.72, gy - th * 0.42,
                x + tw * 0.46, gy - th * 0.20,
                x + tw, gy - th * 0.12,
            ])
        else:
            pts_top.extend([x, ridge_fn(x) + 0.024 * h])
        x += rng.uniform(0.016, 0.030) * w
    pts_top.extend([w, ridge_fn(w) + 0.03 * h])

    bot_y = h + 10
    back_col = mix(tl, mist, 0.24) if not flank else mix(hs[1], tl, 0.58)
    c.create_polygon([0.0, bot_y] + pts_top + [w, bot_y], fill=back_col, outline="", tags=("treeline",))

    if not flank:
        front_pts = [0.0, ridge_fn(0.0) + 0.03 * h]
        x = rng.uniform(0.0, 0.015 * w)
        while x < w:
            gy = ridge_fn(x) + 0.014 * h
            if (0.45 + 0.55 * math.cos((2 * math.pi / w) * x * 2.5)) > 0.35:
                th = rng.uniform(0.020, 0.046) * h
                tw = th * rng.uniform(0.36, 0.50)
                front_pts.extend([
                    x - tw * 0.85, gy - th * 0.20,
                    x - tw * 0.48, gy - th * 0.52,
                    x + rng.uniform(-0.06, 0.06) * th, gy - th,
                    x + tw * 0.50, gy - th * 0.50,
                    x + tw * 0.88, gy - th * 0.16,
                ])
            else:
                front_pts.extend([x, ridge_fn(x) + 0.024 * h])
            x += rng.uniform(0.022, 0.038) * w
        front_pts.extend([w, ridge_fn(w) + 0.03 * h])
        c.create_polygon([0.0, bot_y] + front_pts + [w, bot_y],
                         fill=mix(tl_shade, hs[0], 0.22), outline="", tags=("treeline",))


def _draw_fog_ribbon(c, fn, w, base_off, h, col, k, phase):
    """Soft undulating atmospheric mist veil between mountain/hill ridges."""
    step = max(18, w / 22)
    top_pts, bot_pts = [], []
    x = 0.0
    while True:
        y = fn(x) + base_off * h + 0.008 * h * math.sin(k * x * 2.4 + phase)
        thick = (0.026 + 0.010 * math.cos(k * x * 1.7 + phase)) * h
        top_pts.extend([x, y])
        bot_pts[:0] = [x, y + thick]
        if x >= w:
            break
        x = min(w, x + step)
    c.create_polygon(top_pts + bot_pts, fill=col, outline="", smooth=True, tags=("fog",))


def _draw_needle_fan(c, bx0, by0, bx1, by1, span_w, h, side, dark, mid, hi, ink_stroke, bark, rng):
    """Draw a layered feathery pine needle spray rather than a flat slab."""
    dx = bx1 - bx0
    dy = by1 - by0
    # Subtle woody branch spline underneath the needle fans
    mx, my = bx0 + dx * 0.5, by0 + dy * 0.45
    c.create_line(bx0, by0, mx, my, bx1, by1, fill=bark, width=max(1.5, abs(span_w) * 0.045),
                  smooth=True, capstyle="round", tags=("framing_tree",))

    # Build a serrated top + feathery drooping bottom contour with 7 needle sprays
    top_pts, bot_pts = [], []
    n_sprays = 6
    for i in range(n_sprays + 1):
        t = i / float(n_sprays)
        px = bx0 + dx * t
        py = by0 + dy * t
        arch = math.sin(t * math.pi)
        up = (0.008 + 0.014 * arch) * h
        droop = (0.012 + 0.020 * math.sin(t * math.pi * 0.88)) * h
        notch = 0.007 * h * (1 if i % 2 == 0 else 0.35)
        top_pts.extend([px, py - up])
        if i > 0:
            ntx = bx0 + dx * (t - 0.5 / n_sprays)
            nty = by0 + dy * (t - 0.5 / n_sprays)
            bot_pts[:0] = [
                px + side * abs(dx) * 0.04, py + droop,
                ntx - side * abs(dx) * 0.02, nty + droop * 0.42 - notch,
            ]
        else:
            bot_pts[:0] = [px, py + 0.010 * h]

    # Back deep needle silhouette with soft 1px dark-tinted organic ink outline
    c.create_polygon(top_pts + bot_pts, fill=dark, outline=ink_stroke, width=1, tags=("framing_tree",))

    # Mid-tone overlapping feathery sub-clusters (shifted slightly upward/inward)
    mid_top = [v + (-0.002 * h if k % 2 else 0.0) for k, v in enumerate(top_pts)]
    mid_bot = [v - (0.008 * h if k % 2 else 0.0) for k, v in enumerate(bot_pts)]
    c.create_polygon(mid_top + mid_bot, fill=mid, outline="", tags=("framing_tree",))

    # Delicate upper rim highlights & drooping needle wisps at tips
    if side == 1:
        hi_pts = []
        for i in range(4):
            t = 0.18 + 0.25 * i
            hi_pts.extend([bx0 + dx * t, by0 + dy * t - (0.007 + 0.008 * math.sin(t * math.pi)) * h])
        c.create_line(hi_pts, fill=hi, width=1.2, smooth=True, tags=("framing_tree",))

    for nt in (0.28, 0.48, 0.68, 0.86):
        nx = bx0 + dx * nt
        ny = by0 + dy * nt + 0.006 * h
        wisp_h = rng.uniform(0.016, 0.028) * h
        c.create_line(nx, ny, nx + side * 2.5, ny + wisp_h, fill=dark, width=1, tags=("framing_tree",))
        c.create_line(nx + side * 2, ny, nx + side * 5.0, ny + wisp_h * 0.78, fill=mid, width=1, tags=("framing_tree",))


def _draw_framing_trees(c, w, h, P, rng):
    """Tall feathered framing pine on the left and a continuous, grounded
    overhanging broadleaf tree along the right border."""
    dark = P["framing_dark"]
    mid = P["framing_mid"]
    hi = P["framing_hi"]
    ink_stroke = mix(P["ink"], dark, 0.25)
    bark = P["bark"]
    bark_hi = P["bark_hi"]

    # Optional Afternoon long cast shadows stretching diagonally across meadow
    if P.get("cast_shadows"):
        sh_col = P["shadow"]
        c.create_polygon(
            0.0, h * 0.84, 0.10 * w, h * 0.78, 0.38 * w, h * 0.86,
            0.22 * w, h * 0.96, 0.0, h * 0.98,
            fill=mix(sh_col, P["hills"][2], 0.35), outline="", smooth=True, tags=("cast_shadow",),
        )
        c.create_polygon(
            w, h * 0.80, 0.86 * w, h * 0.78, 0.64 * w, h * 0.88,
            0.78 * w, h * 0.97, w, h * 0.98,
            fill=mix(sh_col, P["hills"][2], 0.35), outline="", smooth=True, tags=("cast_shadow",),
        )

    # ── LEFT EDGE: Tall illustrated pine with feathery layered needles ──
    tx = 0.036 * w
    top_y = 0.04 * h
    bot_y = h * 1.01
    tw_b = max(9.0, 0.020 * w)
    tw_t = max(2.0, tw_b * 0.22)
    trunk_pts = [
        tx - tw_b * 0.8, bot_y,
        tx - tw_b * 0.55, h * 0.62,
        tx - tw_t * 1.2, h * 0.25,
        tx, top_y,
        tx + tw_t * 0.9, h * 0.24,
        tx + tw_b * 0.52, h * 0.64,
        tx + tw_b * 0.95, bot_y,
    ]
    c.create_polygon(trunk_pts, fill=bark, outline=ink_stroke, width=1, tags=("framing_tree",))
    c.create_polygon(
        tx + tw_t * 0.2, h * 0.22,
        tx + tw_b * 0.45, h * 0.66,
        tx + tw_b * 0.72, bot_y,
        tx + tw_b * 0.15, bot_y,
        tx + tw_t * 0.05, h * 0.40,
        fill=bark_hi, outline="", tags=("framing_tree",),
    )
    # Soft vertical bark grain strokes
    for off_f, y0_f, y1_f in ((-0.25, 0.52, 0.86), (0.08, 0.38, 0.74), (0.28, 0.66, 0.94)):
        bx = tx + tw_b * off_f
        c.create_line(bx, h * y0_f, bx, h * y1_f, fill=ink_stroke, width=1, tags=("framing_tree",))

    # Top crown needle tuft so the spire feels natural
    _draw_needle_fan(c, tx - 0.015 * w, 0.05 * h, tx + 0.036 * w, 0.068 * h,
                     0.04 * w, h, 1, dark, mid, hi, ink_stroke, bark, rng)
    # 9 sweeping asymmetrical pine boughs with layered feathery needle sprays
    boughs = [
        (0.08, 0.015, 0.052, 1),
        (0.13, -0.015, 0.058, -1),
        (0.19, 0.032, 0.078, 1),
        (0.25, -0.020, 0.082, -1),
        (0.32, 0.042, 0.098, 1),
        (0.39, -0.025, 0.092, -1),
        (0.46, 0.050, 0.112, 1),
        (0.54, -0.022, 0.095, -1),
        (0.61, 0.056, 0.115, 1),
    ]
    for fy, reach_f, span_f, side in boughs:
        by = h * fy
        bx0 = tx + side * tw_t * 0.3
        bx1 = tx + (reach_f + side * span_f) * w
        tip_y = by + 0.034 * h
        _draw_needle_fan(c, bx0, by, bx1, tip_y, span_f * w, h, side,
                         dark, mid, hi, ink_stroke, bark, rng)

    # ── RIGHT EDGE: Continuous grounded tree trunk + connected canopy branches ──
    # Main trunk rising uninterrupted from bottom-right corner all the way to top-right canopy
    r_trunk = [
        w * 0.942, bot_y,
        w * 0.950, h * 0.72,
        w * 0.946, h * 0.45,
        w * 0.952, h * 0.22,
        w * 0.945, h * 0.02,
        w * 1.015, h * 0.02,
        w * 1.015, bot_y,
    ]
    c.create_polygon(r_trunk, fill=bark, outline=ink_stroke, width=1, smooth=True, tags=("framing_tree",))
    # Lit bark highlight facing left into the clearing
    c.create_polygon(
        w * 0.945, bot_y,
        w * 0.952, h * 0.72,
        w * 0.949, h * 0.45,
        w * 0.955, h * 0.22,
        w * 0.950, h * 0.03,
        w * 0.968, h * 0.03,
        w * 0.970, h * 0.38,
        w * 0.968, bot_y,
        fill=bark_hi, outline="", smooth=True, tags=("framing_tree",),
    )

    # Connected limbs originating solidly inside the right-edge trunk
    limbs = [
        ([w * 0.964, h * 0.09, w * 0.88, h * 0.06, w * 0.78, h * 0.075], 0.008),
        ([w * 0.964, h * 0.16, w * 0.87, h * 0.15, w * 0.75, h * 0.175], 0.009),
        ([w * 0.89, h * 0.07, w * 0.83, h * 0.025], 0.004),
        ([w * 0.83, h * 0.155, w * 0.79, h * 0.205], 0.004),
        ([w * 0.964, h * 0.27, w * 0.90, h * 0.26, w * 0.85, h * 0.295], 0.006),
        ([w * 0.960, h * 0.68, w * 0.905, h * 0.64, w * 0.865, h * 0.655], 0.006),
        ([w * 0.955, h * 0.73, w * 0.90, h * 0.78], 0.004),
    ]
    for pts, w_frac in limbs:
        lw_in = max(4, int(w * w_frac))
        c.create_line(pts, fill=ink_stroke, width=lw_in + 2, smooth=True, capstyle="round", tags=("framing_tree",))
        c.create_line(pts, fill=bark, width=lw_in, smooth=True, capstyle="round", tags=("framing_tree",))

    # Foliage clusters anchored directly onto the trunk & connected limbs (no floating blobs)
    clusters = [
        (0.95, 0.045, 0.080, 0.058),
        (0.85, 0.055, 0.075, 0.052),
        (0.78, 0.082, 0.058, 0.042),
        (0.92, 0.135, 0.076, 0.055),
        (0.83, 0.155, 0.068, 0.048),
        (0.75, 0.180, 0.050, 0.036),
        (0.93, 0.235, 0.068, 0.050),
        (0.86, 0.285, 0.050, 0.038),
        (0.88, 0.645, 0.046, 0.034),
        (0.93, 0.625, 0.044, 0.032),
    ]
    for cx_f, cy_f, rx_f, ry_f in clusters:
        cx, cy = cx_f * w, cy_f * h
        rx, ry = rx_f * w, ry_f * h
        pts = []
        for i in range(14):
            ang = 2 * math.pi * i / 14.0
            rad_m = 1.0 + 0.22 * math.sin(i * 3.1 + cx_f * 17)
            pts.extend([cx + rx * rad_m * math.cos(ang), cy + ry * rad_m * math.sin(ang)])
        c.create_polygon(pts, fill=dark, outline=ink_stroke, width=1, smooth=True, tags=("framing_tree",))
        # Mid-tone cel highlight shifted toward light center
        c.create_polygon(
            [p + (-rx * 0.14 if idx % 2 == 0 else -ry * 0.10) for idx, p in enumerate(pts[:16])],
            fill=mid, outline="", smooth=True, tags=("framing_tree",),
        )
        # Rim-light leaf accent strokes
        c.create_line(cx - rx * 0.80, cy + ry * 0.12, cx - rx * 0.22, cy - ry * 0.62, cx + rx * 0.42, cy - ry * 0.68,
                      fill=hi, width=1.2, smooth=True, tags=("framing_tree",))


def _draw_organic_bush(c, cx, cy, s, P, rng):
    """Multi-lobed serrated shrub silhouette with cel highlights & thin dark-tinted stems."""
    b0, b1, b2 = P["bush"]
    ink_stroke = mix(P["ink"], b0, 0.30)
    pts = []
    n_pts = 16
    for i in range(n_pts):
        t = i / n_pts
        ang = math.pi * (1.08 - 1.16 * t)  # arch from bottom-left to bottom-right
        rad = s * (0.95 + 0.28 * abs(math.sin(i * 2.3 + cx * 0.05)))
        pts.extend([cx - rad * math.cos(ang) * 1.25, cy - rad * math.sin(ang) * 0.95])
    pts.extend([cx + s * 1.25, cy + s * 0.20, cx - s * 1.25, cy + s * 0.20])
    c.create_polygon(pts, fill=b0, outline=ink_stroke, width=1, smooth=True, tags=("bush",))

    # Mid-tone upper cluster
    pts_m = []
    for i in range(10):
        t = i / 9.0
        ang = math.pi * (0.95 - 0.90 * t)
        rad = s * (0.72 + 0.18 * math.sin(i * 2.9 + cy * 0.05))
        pts_m.extend([cx - rad * math.cos(ang) * 1.1, cy - rad * math.sin(ang) * 0.90])
    pts_m.extend([cx + s * 0.75, cy - s * 0.05, cx - s * 0.75, cy - s * 0.05])
    c.create_polygon(pts_m, fill=b1, outline="", smooth=True, tags=("bush",))

    # Crisp top-leaf rim highlights & spiky leaf shoots
    c.create_line(cx - s * 0.75, cy - s * 0.38, cx - s * 0.18, cy - s * 0.86, cx + s * 0.58, cy - s * 0.55,
                  fill=b2, width=1.2, smooth=True, tags=("bush",))
    for _ in range(3):
        lx = cx + rng.uniform(-0.75, 0.75) * s
        ly = cy - rng.uniform(0.35, 0.78) * s
        c.create_line(lx, ly + 4, lx + rng.uniform(-4, 4), ly - 4, fill=b2, width=1, tags=("bush",))


def _draw_pebble_cluster(c, x, y, s, P):
    """Hand-drawn faceted illustrated stone + small pebble (no stacked ovals)."""
    top_col, dark_col, hi_col = P["rock"]
    ink_stroke = mix(P["ink"], dark_col, 0.35)
    c.create_polygon(
        x - s * 1.15, y + s * 0.22,
        x - s * 0.95, y - s * 0.42,
        x - s * 0.28, y - s * 0.76,
        x + s * 0.58, y - s * 0.58,
        x + s * 1.08, y - s * 0.05,
        x + s * 1.12, y + s * 0.28,
        fill=top_col, outline=ink_stroke, width=1, tags=("pebble",),
    )
    # Cel-shaded dark underside/right plane
    c.create_polygon(
        x + s * 0.05, y - s * 0.12,
        x + s * 0.58, y - s * 0.54,
        x + s * 1.04, y - s * 0.05,
        x + s * 1.08, y + s * 0.25,
        x - s * 1.08, y + s * 0.20,
        x - s * 0.55, y + s * 0.02,
        fill=dark_col, outline="", tags=("pebble",),
    )
    # Top edge highlight
    c.create_line(x - s * 0.78, y - s * 0.36, x - s * 0.26, y - s * 0.70, x + s * 0.42, y - s * 0.54,
                  fill=hi_col, width=1.2, tags=("pebble",))
    # Companion tiny pebble
    px, py, ps = x + s * 1.35, y + s * 0.20, s * 0.38
    c.create_polygon(
        px - ps, py + ps * 0.3, px - ps * 0.5, py - ps * 0.65,
        px + ps * 0.6, py - ps * 0.5, px + ps, py + ps * 0.3,
        fill=dark_col, outline=ink_stroke, width=1, tags=("pebble",),
    )


def _draw_fern(c, x, y, s, P, dir_x=1):
    """Curved illustrated fern frond with paired pointed leaflets."""
    stem_col = P["bush"][1]
    leaf_col = P["bush"][2]
    ink = P["ink"]
    tip_x = x + dir_x * s * 1.6
    tip_y = y - s * 1.15
    mid_x = x + dir_x * s * 0.72
    mid_y = y - s * 0.88
    c.create_line(x, y, mid_x, mid_y, tip_x, tip_y, fill=ink, width=1.3, smooth=True, tags=("fern",))
    for i in range(1, 6):
        t = i / 6.0
        bx = (1 - t) ** 2 * x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x
        by = (1 - t) ** 2 * y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y
        flen = s * (0.48 - 0.30 * t)
        c.create_polygon(bx, by, bx - dir_x * flen * 0.45, by - flen * 0.85,
                         bx + dir_x * flen * 0.25, by - flen * 0.35,
                         fill=leaf_col, outline="", tags=("fern",))
        c.create_polygon(bx, by, bx + dir_x * flen * 0.65, by - flen * 0.22,
                         bx + dir_x * flen * 0.20, by + flen * 0.35,
                         fill=stem_col, outline="", tags=("fern",))


def _draw_cross_hatch(c, x0, y0, width, count, col, spacing=5.5):
    """Subtle ink-style diagonal cross-hatched shading strokes."""
    for i in range(count):
        hx = x0 + i * spacing
        hy = y0 + math.sin(i * 0.8) * 1.5
        c.create_line(hx, hy, hx + 4.5, hy + 4.0, fill=col, width=1, tags=("cross_hatch",))
        if i % 2 == 0:
            c.create_line(hx + 4.2, hy, hx - 0.5, hy + 3.8, fill=col, width=1, tags=("cross_hatch",))


def _draw_distant_deer(c, x, y, s, P, facing=1):
    """Draw a peaceful distant woodland deer figure on a hill ridge."""
    tint_col, tint_amt = P["tint"]
    coat = mix("#9E633C", tint_col, min(0.65, tint_amt + 0.14))
    coat_dark = mix("#6B3F24", tint_col, min(0.70, tint_amt + 0.18))
    coat_lit = mix("#CFA077", tint_col, min(0.55, tint_amt + 0.08))
    antler_col = mix("#785942", tint_col, min(0.60, tint_amt + 0.12))
    d = facing

    c.create_oval(x - s * 1.05, y - s * 0.14, x + s * 1.05, y + s * 0.20,
                  fill=P["shadow"], outline="", tags=("wildlife",))
    lw = max(1, int(round(s * 0.13)))
    c.create_line(x - d * s * 0.58, y - s * 0.65, x - d * s * 0.66, y + s * 0.04,
                  fill=coat_dark, width=lw, tags=("wildlife",))
    c.create_line(x - d * s * 0.36, y - s * 0.62, x - d * s * 0.32, y + s * 0.05,
                  fill=coat, width=lw, tags=("wildlife",))
    c.create_line(x + d * s * 0.36, y - s * 0.65, x + d * s * 0.30, y + s * 0.04,
                  fill=coat_dark, width=lw, tags=("wildlife",))
    c.create_line(x + d * s * 0.52, y - s * 0.65, x + d * s * 0.58, y + s * 0.05,
                  fill=coat, width=lw, tags=("wildlife",))
    c.create_oval(x - s * 0.72, y - s * 1.05, x + s * 0.66, y - s * 0.48,
                  fill=coat, outline="", tags=("wildlife",))
    c.create_oval(x - s * 0.52, y - s * 1.03, x + s * 0.48, y - s * 0.72,
                  fill=coat_lit, outline="", tags=("wildlife",))
    tx = x - d * s * 0.74
    c.create_oval(tx - s * 0.15, y - s * 0.96, tx + s * 0.15, y - s * 0.74,
                  fill=coat_lit, outline="", tags=("wildlife",))
    nx0, ny0 = x + d * s * 0.42, y - s * 0.78
    nx1, ny1 = x + d * s * 0.72, y - s * 1.48
    c.create_polygon(
        nx0 - d * s * 0.18, ny0,
        nx0 + d * s * 0.18, ny0 - s * 0.05,
        nx1 + d * s * 0.11, ny1 + s * 0.06,
        nx1 - d * s * 0.12, ny1,
        fill=coat, outline="", smooth=True, tags=("wildlife",),
    )
    hx, hy = nx1 + d * s * 0.08, ny1 - s * 0.04
    c.create_oval(hx - s * 0.24, hy - s * 0.17, hx + s * 0.24, hy + s * 0.16,
                  fill=coat, outline="", tags=("wildlife",))
    c.create_oval(hx + d * s * 0.08 - s * 0.18, hy - s * 0.10,
                  hx + d * s * 0.08 + s * 0.18, hy + s * 0.13,
                  fill=coat_lit, outline="", tags=("wildlife",))
    ex, ey = hx - d * s * 0.12, hy - s * 0.14
    c.create_oval(ex - s * 0.12, ey - s * 0.22, ex + s * 0.08, ey + s * 0.02,
                  fill=coat_dark, outline="", tags=("wildlife",))
    ax, ay = hx - d * s * 0.04, hy - s * 0.15
    c.create_line(ax, ay, ax - d * s * 0.16, ay - s * 0.42, ax - d * s * 0.02, ay - s * 0.62,
                  fill=antler_col, width=1, smooth=True, tags=("wildlife",))
    c.create_line(ax - d * s * 0.10, ay - s * 0.30, ax + d * s * 0.14, ay - s * 0.48,
                  fill=antler_col, width=1, tags=("wildlife",))


def _draw_distant_rabbit(c, x, y, s, P, facing=-1):
    """Draw a cozy distant meadow rabbit with upright ears and cottontail."""
    tint_col, tint_amt = P["tint"]
    fur = mix("#D8C6B4", tint_col, min(0.60, tint_amt + 0.10))
    fur_shade = mix("#B59E8A", tint_col, min(0.65, tint_amt + 0.15))
    ear_in = mix("#E5B5AE", tint_col, min(0.55, tint_amt + 0.10))
    tail_col = mix("#FBF7F2", tint_col, min(0.40, tint_amt))
    d = facing

    c.create_oval(x - s * 0.95, y - s * 0.15, x + s * 0.95, y + s * 0.22,
                  fill=P["shadow"], outline="", tags=("wildlife",))
    tx = x - d * s * 0.72
    c.create_oval(tx - s * 0.26, y - s * 0.56, tx + s * 0.26, y - s * 0.10,
                  fill=tail_col, outline="", tags=("wildlife",))
    c.create_oval(x - s * 0.70, y - s * 0.82, x + s * 0.58, y + s * 0.04,
                  fill=fur, outline="", tags=("wildlife",))
    c.create_oval(x - s * 0.55, y - s * 0.42, x + s * 0.40, y + s * 0.04,
                  fill=fur_shade, outline="", tags=("wildlife",))
    hx, hy = x + d * s * 0.50, y - s * 0.68
    c.create_oval(hx - s * 0.42, hy - s * 0.36, hx + s * 0.42, hy + s * 0.34,
                  fill=fur, outline="", tags=("wildlife",))
    for e_off, e_tilt in ((-0.12, -0.08), (0.08, 0.06)):
        ex = hx + d * e_off * s
        c.create_oval(ex - s * 0.14, hy - s * 0.98, ex + s * 0.14 + d * e_tilt * s, hy - s * 0.22,
                      fill=fur, outline="", tags=("wildlife",))
        c.create_oval(ex - s * 0.07, hy - s * 0.86, ex + s * 0.07 + d * e_tilt * s, hy - s * 0.30,
                      fill=ear_in, outline="", tags=("wildlife",))


def _draw_chill_campfire(c, S):
    """Draw a cozy, hand-drawn stone-ringed campfire with a wooden log bench and warm circular glow."""
    P = S["pal"]
    w, h, sc = S["w"], S["h"], S["sc"]
    near_fn = S["near"]

    # Grassy clearing to the right of the dirt path (away from central tree mound)
    cx = 0.74 * w
    cy = near_fn(cx) + 0.05 * h
    S["campfire_pos"] = (cx, cy)

    # 1. Soft warm circular glow onto the surrounding dark grass (#F28D6B)
    glow_coral = "#F28D6B"
    c.create_oval(cx - 38 * sc, cy - 19 * sc, cx + 38 * sc, cy + 19 * sc,
                  fill=mix(P["grass"], glow_coral, 0.12), outline="", tags=("campfire_glow",))
    c.create_oval(cx - 24 * sc, cy - 12 * sc, cx + 24 * sc, cy + 12 * sc,
                  fill=mix(P["grass"], glow_coral, 0.25), outline="", tags=("campfire_glow",))
    c.create_oval(cx - 14 * sc, cy - 7 * sc, cx + 14 * sc, cy + 7 * sc,
                  fill=mix(P["grass"], "#FFA27A", 0.42), outline="", tags=("campfire_glow",))

    # 2. Wooden log bench beside the campfire (placed slightly behind and to the right)
    bx = cx + 22 * sc
    by = cy - 2.5 * sc
    bw = 14 * sc
    bh = 3.5 * sc

    # Shadow under the log bench
    c.create_oval(bx - bw * 1.05, by + bh * 0.4, bx + bw * 1.05, by + bh * 1.4,
                  fill=mix(P["shadow"], P["grass"], 0.35), outline="", tags=("campfire_bench",))
    # Two rustic peg legs
    c.create_rectangle(bx - bw * 0.7, by + bh * 0.2, bx - bw * 0.45, by + bh * 1.0,
                       fill="#2b1a15", outline=P["ink"], width=0.8, tags=("campfire_bench",))
    c.create_rectangle(bx + bw * 0.45, by + bh * 0.2, bx + bw * 0.7, by + bh * 1.0,
                       fill="#2b1a15", outline=P["ink"], width=0.8, tags=("campfire_bench",))
    # Main log cylinder
    c.create_polygon(
        bx - bw, by - bh,
        bx + bw, by - bh,
        bx + bw + 1.5 * sc, by,
        bx + bw, by + bh,
        bx - bw, by + bh,
        bx - bw - 1.5 * sc, by,
        fill="#483025", outline=P["ink"], width=1.0, smooth=True, tags=("campfire_bench",)
    )
    # Log woodgrain striations
    c.create_line(bx - bw * 0.85, by - bh * 0.3, bx + bw * 0.85, by - bh * 0.3,
                  fill="#664434", width=1, tags=("campfire_bench",))
    c.create_line(bx - bw * 0.75, by + bh * 0.3, bx + bw * 0.75, by + bh * 0.3,
                  fill="#301f18", width=1, tags=("campfire_bench",))
    # Left cut end rings
    c.create_oval(bx - bw - 2.6 * sc, by - bh * 0.85, bx - bw + 0.8 * sc, by + bh * 0.85,
                  fill="#996e52", outline=P["ink"], width=0.8, tags=("campfire_bench",))
    c.create_oval(bx - bw - 1.6 * sc, by - bh * 0.42, bx - bw + 0.1 * sc, by + bh * 0.42,
                  fill="#664432", outline="", tags=("campfire_bench",))

    # 3. Charred ash bed in the pit
    pit_rx = 9.0 * sc
    pit_ry = 4.5 * sc
    c.create_oval(cx - pit_rx, cy - pit_ry, cx + pit_rx, cy + pit_ry,
                  fill=mix(P["path"][1], "#140a12", 0.75), outline=P["ink"], width=1, tags=("campfire",))

    # 4. Crossed small firewood logs
    c.create_line(cx - 6.5 * sc, cy + 2 * sc, cx + 6.0 * sc, cy - 2 * sc,
                  fill="#3a2217", width=max(2.0, 2.4 * sc), tags=("campfire",))
    c.create_line(cx - 5.5 * sc, cy - 2 * sc, cx + 6.5 * sc, cy + 2 * sc,
                  fill="#4c2d1f", width=max(2.0, 2.4 * sc), tags=("campfire",))
    c.create_line(cx - 4.0 * sc, cy, cx + 4.0 * sc, cy,
                  fill="#72442e", width=max(1.0, 1.4 * sc), tags=("campfire",))

    # 5. Stone ring (hand-drawn stones surrounding the pit)
    stone_angles = [0.0, 0.78, 1.57, 2.36, 3.14, 3.93, 4.71, 5.50]
    stone_cols = [P["rock"][0], P["rock"][1], P["rock"][2]]
    for idx, ang in enumerate(stone_angles):
        sx = cx + (pit_rx + 1.2 * sc) * math.cos(ang)
        sy = cy + (pit_ry + 1.2 * sc) * math.sin(ang)
        sr = (2.2 + (idx % 3) * 0.5) * sc
        c.create_oval(sx - sr, sy - sr * 0.65, sx + sr, sy + sr * 0.65,
                      fill=stone_cols[idx % 3], outline=P["ink"], width=0.9, tags=("campfire",))
        c.create_line(sx - sr * 0.5, sy - sr * 0.35, sx + sr * 0.5, sy - sr * 0.35,
                      fill=mix(stone_cols[idx % 3], "#F28D6B", 0.45), width=1, tags=("campfire",))

    # 6. Gentle, flickering coral-amber flame (#F28D6B)
    flame_outer = c.create_polygon(
        cx - 5.5 * sc, cy + 0.5 * sc,
        cx - 4.0 * sc, cy - 6.0 * sc,
        cx - 1.0 * sc, cy - 13.0 * sc,
        cx + 2.5 * sc, cy - 7.5 * sc,
        cx + 5.0 * sc, cy + 0.5 * sc,
        cx + 0.5 * sc, cy + 1.8 * sc,
        fill="#F28D6B", outline="", smooth=True, tags=("campfire_flame", "actor")
    )
    flame_mid = c.create_polygon(
        cx - 3.8 * sc, cy + 0.5 * sc,
        cx - 2.5 * sc, cy - 5.0 * sc,
        cx - 0.5 * sc, cy - 10.0 * sc,
        cx + 2.0 * sc, cy - 5.5 * sc,
        cx + 3.5 * sc, cy + 0.5 * sc,
        fill="#FFA472", outline="", smooth=True, tags=("campfire_flame", "actor")
    )
    flame_core = c.create_polygon(
        cx - 2.2 * sc, cy + 0.5 * sc,
        cx - 1.2 * sc, cy - 3.5 * sc,
        cx, cy - 6.5 * sc,
        cx + 1.5 * sc, cy - 3.5 * sc,
        cx + 2.0 * sc, cy + 0.5 * sc,
        fill="#FFF3D6", outline="", smooth=True, tags=("campfire_flame", "actor")
    )
    S["campfire_flame"] = (cx, cy, sc, flame_outer, flame_mid, flame_core)


# ─────────────────────────────────────────────────────────────────────
#  Main scene drawing
# ─────────────────────────────────────────────────────────────────────

def draw_landscape(c, w, h, theme, mode="forest", richness=0.0):
    """Draw the full static illustrated landscape.  Returns a scene dict
    describing geometry and animatable items."""
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
    sc = max(0.6, min(1.6, h / 520.0))
    S["sc"] = sc

    def sky_at(y):
        return gradient(P["sky"], y / sky_bottom)
    S["sky_at"] = sky_at

    cel = P["celestial"]
    pos = {"sunrise": (0.24, hz - 0.045 * h, 0.044),
           "noon": (0.76, 0.14 * h, 0.038),
           "sunset": (0.70, hz - 0.012 * h, 0.056),
           "moon": (0.56, 0.135 * h, 0.032)}[cel]
    sx, sy, r = pos[0] * w, pos[1], pos[2] * h
    core = P["sun_core"]

    # ── 1. Smooth multi-stop sky + 3-4% grain + Milky Way + radial glow ──
    sky_img = _build_sky_photo(c, w, sky_bottom, P, theme, sx, sy, r)
    S["_sky_photo"] = sky_img
    c._gyf_sky_photo = sky_img
    c.create_image(0, 0, anchor="nw", image=sky_img, tags=("sky_bg",))

    # ── 2. Crisp multi-sized twinkling stars (Night & upper Chill sky) ──
    star_mode = P.get("stars")
    if star_mode:
        max_y = hz * (0.86 if star_mode == "night" else 0.60)
        n_stars = 74 if star_mode == "night" else 72
        for _ in range(n_stars):
            x = rng.uniform(0.02 * w, 0.98 * w)
            y = max_y * (rng.random() ** (1.35 if star_mode == "night" else 1.25))
            fade = max(0.26, 1.0 - 0.58 * (y / max(1.0, max_y)))
            sz = 2 if rng.random() < (0.22 if star_mode == "night" else 0.18) else 1
            star_base = "#FFFFFF" if star_mode == "night" else "#FFF8F2"
            col = mix(sky_at(y), star_base, rng.uniform(0.55, 0.98) * fade)
            c.create_rectangle(x, y, x + sz, y + sz, outline="", fill=col, tags=("stars",))
        n_twinkle = 6 if star_mode == "night" else 5
        for _ in range(n_twinkle):
            x = rng.uniform(0.10 * w, 0.90 * w)
            y = rng.uniform(0.04 * h, max_y * 0.72)
            bright = "#FFFDF4" if star_mode == "night" else "#FFF6F0"
            dim = mix(sky_at(y), "#DCE8FF" if star_mode == "night" else "#F0D0DE", 0.30)
            # Crisp 4-point pixel sparkle cross (no emoji dependency)
            iid = c.create_line(x - 3, y, x + 3, y, x, y, x, y - 3, x, y + 3,
                                fill=bright, width=1, tags=("stars",))
            S["twinkle"].append([iid, bright, dim, rng.uniform(0, 6.28), -1])

    # ── 3. Crisp celestial body over smooth pixel halo ──
    if cel == "moon":
        _draw_crescent_moon(c, sx, sy, r, core)
    else:
        c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=core, outline="")
    S["sun"] = (sx, sy, r, cel)

    # ── 4. Wispy, flat-bottomed cel-shaded clouds (drifting) ──
    lit, shade, cloud_rim = P["cloud"]
    specs = ([(0.20, 0.13, 0.088, 2.8), (0.37, 0.085, 0.064, 2.0), (0.85, 0.25, 0.054, 3.3)] if study else
             [(0.16, 0.13, 0.072, 2.8), (0.38, 0.085, 0.052, 2.1), (0.70, 0.22, 0.076, 2.5), (0.88, 0.11, 0.048, 3.2)])
    unit = min(w, 1.6 * h)
    for idx, (fx, fy, fs, spd) in enumerate(specs):
        tag = "cloud_%d" % idx
        _draw_cloud(c, fx * w, fy * h, fs * unit, lit, shade, cloud_rim, tag)
        S["clouds"].append([tag, spd * sc])

    # ── 5. Lineless layered mountain ridges + atmospheric mist veils ──
    m = P["mountains"]
    mbottom = hz + 0.16 * h
    step = max(14, w / 28)
    ridges = [
        (hz + 0.05 * h, (0.18 if study else 0.20) * h, (1.1, 2.7, 5.3), (0.4, 1.3, 0.2)),
        (hz + 0.065 * h, 0.12 * h, (1.7, 3.9, 7.1), (1.9, 0.6, 2.4)),
        (hz + 0.08 * h, 0.06 * h, (2.3, 5.2, 9.0), (0.9, 2.2, 1.1)),
    ]
    mist_amt_mtn = 0.56 if P.get("fog_layers") else 0.34
    for i, (b, amp, f, p) in enumerate(ridges):
        pts = _ridge(w, b, amp, f, p, step)
        c.create_polygon([0, mbottom] + pts + [w, mbottom], fill=m[i], outline="", smooth=True)
        if i < 2:
            _draw_fog_ribbon(
                c, lambda x, b=b, amp=amp, i=i: b - amp * (0.22 if i == 0 else 0.14),
                w, 0.0, h, mix(m[i], P["mist"], mist_amt_mtn), k, i * 1.4,
            )

    # ── 6. Lake at the foot of the mountains ──
    lake_top = hz + 0.072 * h
    lx1 = (0.36 if study else 0.44) * w
    c.create_polygon([-0.05 * w, lake_top, lx1, lake_top, lx1 + 0.03 * w, lake_top + 0.02 * h,
                      lx1 - 0.04 * w, lake_top + 0.07 * h, -0.05 * w, lake_top + 0.07 * h],
                     fill=P["water"][0], outline="", smooth=True)
    c.create_line(-0.05 * w, lake_top, lx1, lake_top, fill=mix(P["water"][0], P["mist"], 0.55), width=1)
    if 0 < sx < lx1 and cel != "noon":
        for j in range(6):
            yy = lake_top + 0.006 * h + j * 0.008 * h
            half = r * (1.0 - j * 0.13)
            c.create_line(sx - half, yy, sx + half, yy, fill=mix(P["water"][0], core, 0.60 - j * 0.06), width=2)
    # Soft rose-peach sunset reflection shimmer across the lake in Chill mode
    if theme == "chill":
        rose_tones = ["#ECA199", "#F7B2A6", "#D48D88", "#FFAEA0"]
        for j in range(5):
            yy = lake_top + 0.008 * h + j * 0.009 * h
            x_mid = lx1 * 0.42 + (j % 2) * 8 * sc
            w_refl = lx1 * (0.32 - j * 0.035)
            c.create_line(x_mid - w_refl, yy, x_mid + w_refl, yy,
                          fill=mix(P["water"][0], rose_tones[j % len(rose_tones)], 0.55),
                          width=1.6, smooth=True)
            iid = c.create_line(x_mid - w_refl * 0.7, yy, x_mid + w_refl * 0.7, yy,
                                fill=rose_tones[j % len(rose_tones)], width=1.0)
            S["shimmer"].append([iid, rose_tones[j % len(rose_tones)], P["water"][0], rng.uniform(0, 6.28), -1])
    for j in range(6):
        x = rng.uniform(0.02 * w, lx1 - 0.04 * w)
        y = rng.uniform(lake_top + 0.005 * h, lake_top + 0.045 * h)
        ln = rng.uniform(6, 16) * sc
        iid = c.create_line(x, y, x + ln, y, fill=P["water"][1], width=1)
        if j < 2:
            S["shimmer"].append([iid, P["water"][1], P["water"][0], rng.uniform(0, 6.28), -1])

    # ── 7. Cliff + small waterfall (forest view) ──
    river_fn = None
    if not study:
        rock_d = mix(P["rock"][1], m[2], 0.45)
        c.create_polygon([0.785 * w, hz + 0.14 * h, 0.80 * w, hz + 0.05 * h, 0.83 * w, hz + 0.0 * h,
                          0.875 * w, hz - 0.02 * h, 0.915 * w, hz + 0.025 * h, 0.94 * w, hz + 0.14 * h],
                         fill=rock_d, outline=P["ink"], width=1.0, smooth=True)
        c.create_line(0.82 * w, hz + 0.03 * h, 0.835 * w, hz + 0.11 * h, fill=mix(rock_d, P["rock"][2], 0.35), width=2)
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

    # ── 8. Lineless painterly meadow hills + mist veils + conifer groves ──
    hs = P["hills"]

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
    mist_amt = 0.38 if P.get("fog_layers") else 0.24
    # Conifer silhouettes and soft mist nestled BEHIND far hill (so far hill cleanly covers their base)
    _draw_conifer_grove(c, w, h, far_fn, P, rng)
    _draw_fog_ribbon(c, far_fn, w, -0.020, h, mix(m[2], P["mist"], mist_amt), k, 0.8)
    c.create_polygon(_poly_under(far_fn, w, h, hstep), fill=hs[0], outline="", smooth=True)

    if not study:
        dx = 0.25 * w
        dy = far_fn(dx) + 0.45 * (mid_fn(dx) - far_fn(dx))
        _draw_distant_deer(c, dx, dy, 8.5 * sc, P, facing=1)

    # Flanking conifers and subtle mist nestled BEHIND mid hill (zero cut across middle slope)
    _draw_conifer_grove(c, w, h, mid_fn, P, rng, flank=True)
    _draw_fog_ribbon(c, mid_fn, w, -0.020, h, mix(hs[0], P["mist"], mist_amt), k, 2.7)
    c.create_polygon(_poly_under(mid_fn, w, h, hstep), fill=hs[1], outline="", smooth=True)
    _draw_organic_bush(c, 0.065 * w, mid_fn(0.065 * w) + 0.008 * h, 0.046 * h, P, rng)
    for hx_f in (0.16, 0.35, 0.65, 0.84):
        hx = hx_f * w
        _draw_cross_hatch(c, hx, mid_fn(hx) + 0.025 * h, 24, 5, mix(P["hatch"], hs[1], 0.45), spacing=5.0 * sc)

    # Near hill with soft lineless atmospheric transition into foreground clearing
    _draw_fog_ribbon(c, near_fn, w, -0.016, h, mix(hs[1], P["mist"], mist_amt * 0.65), k, 1.3)
    c.create_polygon(_poly_under(near_fn, w, h, hstep), fill=hs[2], outline="", smooth=True)

    # Distant woodland animals resting peacefully on the mid-hill slopes in study view
    if study:
        dx = 0.22 * w
        dy = mid_fn(dx) + 0.42 * (near_fn(dx) - mid_fn(dx))
        _draw_distant_deer(c, dx, dy, 10.5 * sc, P, facing=1)
        rx1 = 0.77 * w
        ry1 = mid_fn(rx1) + 0.48 * (near_fn(rx1) - mid_fn(rx1))
        _draw_distant_rabbit(c, rx1, ry1, 5.2 * sc, P, facing=-1)
        rx2 = 0.815 * w
        ry2 = mid_fn(rx2) + 0.62 * (near_fn(rx2) - mid_fn(rx2))
        _draw_distant_rabbit(c, rx2, ry2, 4.0 * sc, P, facing=-1)

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
        c.create_line(px - 0.025 * w, py, px + 0.025 * w, py,
                      fill=mix(P["water"][1], "#FFFFFF", 0.35), width=2)
        for j in range(5):
            y = y_top + (h - y_top) * (0.10 + 0.18 * j)
            xc, hw = river_fn(y)
            ln = hw * 0.6
            iid = c.create_line(xc - ln + rng.uniform(-2, 2), y, xc + ln * 0.3, y, fill=P["water"][1], width=1)
            if j < 2:
                S["shimmer"].append([iid, P["water"][1], P["water"][0], rng.uniform(0, 6.28), -1])

    # ── 10. Winding dirt path + sky puddles + cross-hatched verge shading ──
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

    # Cross-hatched shading along the winding dirt path edges
    hatch_path_col = mix(P["hatch"], pe, 0.35)
    for t in (0.14, 0.28, 0.44):
        py = h - t * (h - p_far)
        xc, hw = path_xw(t)
        _draw_cross_hatch(c, xc - hw - 10 * sc, py, 16, 3, hatch_path_col, spacing=4.5 * sc)
        _draw_cross_hatch(c, xc + hw - 2 * sc, py + 2, 16, 3, hatch_path_col, spacing=4.5 * sc)

    puddle = mix(sky_at(hz * 0.6), pf, 0.15)
    for t in (0.12, 0.30, 0.52):
        y = h - t * (h - p_far)
        xc, hw = path_xw(t)
        pw, phh = hw * 0.52, max(2, hw * 0.11)
        ox = hw * 0.15 * (1 if t != 0.30 else -1)
        c.create_polygon(
            xc + ox - pw, y,
            xc + ox - pw * 0.4, y - phh,
            xc + ox + pw * 0.55, y - phh * 0.8,
            xc + ox + pw, y + phh * 0.2,
            xc + ox + pw * 0.3, y + phh,
            xc + ox - pw * 0.5, y + phh * 0.75,
            fill=puddle, outline=pe, smooth=True,
        )
        c.create_line(xc + ox - pw * 0.45, y - phh * 0.2, xc + ox + pw * 0.15, y - phh * 0.2,
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
        if theme == "chill" and P.get("campfire"):
            cpx = 0.74 * w
            cpy = near_fn(cpx) + 0.05 * h
            if abs(x - cpx) < 42 * sc + pad and abs(y - cpy) < 22 * sc + pad:
                return True
        return False
    S["blocked"] = blocked

    # ── 11. Central study planting mound + framing trees ──
    gx, gy = 0.5 * w, near_fn(0.5 * w) + 0.075 * h
    S["study_ground"] = (gx, gy)
    if study:
        mw = max(32.0, 0.068 * w)
        mh = max(8.0, 0.018 * h)
        knoll_shade = mix(pf, P["grass"], 0.55)
        # Soft natural knoll blend behind the stone-ringed garden plot (no harsh dark ink outline or floating rim)
        c.create_polygon(
            gx - mw, gy + 2,
            gx - mw * 0.65, gy - mh * 0.75,
            gx, gy - mh,
            gx + mw * 0.65, gy - mh * 0.70,
            gx + mw, gy + 2,
            gx + mw * 0.55, gy + mh * 0.72,
            gx - mw * 0.55, gy + mh * 0.75,
            fill=knoll_shade, outline="", smooth=True, tags=("mound",),
        )
        _draw_fern(c, gx - mw * 1.05, gy + 2, 10.5 * sc, P, dir_x=-1)
        _draw_fern(c, gx + mw * 1.05, gy + 2, 10.0 * sc, P, dir_x=1)

    _draw_framing_trees(c, w, h, P, rng)

    # ── 12. Illustrated faceted pebbles & rocks ──
    if river_fn:
        for t, side, s in ((0.25, -1, 6), (0.45, 1, 8), (0.72, -1, 10), (0.9, 1, 12)):
            y = hz + 0.122 * h + (h - hz - 0.122 * h) * t
            xc, hw = river_fn(y)
            _draw_pebble_cluster(c, xc + side * (hw + s * sc * 1.3), y, s * sc, P)
    for t, side, s in ((0.20, 1, 7), (0.45, -1, 5)):
        y = h - t * (h - p_far)
        xc, hw = path_xw(t)
        _draw_pebble_cluster(c, xc + side * (hw + s * sc * 1.5), y, s * sc, P)

    # ── 13. Foreground serrated bushes & ferns ──
    bs = 0.072 * h
    _draw_organic_bush(c, 0.055 * w, h - 0.025 * h, bs * 1.15, P, rng)
    _draw_organic_bush(c, 0.12 * w, h - 0.005 * h, bs * 0.85, P, rng)
    _draw_organic_bush(c, 0.945 * w, h - 0.02 * h, bs * 1.10, P, rng)
    _draw_fern(c, 0.155 * w, h - 0.015 * h, 13 * sc, P, dir_x=1)
    _draw_fern(c, 0.855 * w, h - 0.015 * h, 12.5 * sc, P, dir_x=-1)
    if study:
        _draw_organic_bush(c, 0.885 * w, h - 0.005 * h, bs * 0.80, P, rng)

    # ── 14. Textured grass strokes, wildflowers & mushrooms ──
    gcol = P["grass"]
    ghi = P["grass_hi"]
    n_grass = 28 if study else 34
    for i in range(n_grass):
        x = rng.uniform(0.06 * w, 0.94 * w)
        y = rng.uniform(mid_fn(x) + 0.02 * h, h - 0.01 * h)
        if blocked(x, y, 6):
            continue
        depth = 0.55 + 0.85 * ((y - hz) / (h - hz))
        L = rng.uniform(5.5, 11.5) * sc * depth
        col = ghi if i % 4 == 0 else gcol
        c.create_line(x - 3.5, y - L * 0.72, x - 0.5, y, x + 0.4, y - L, x + 0.8, y, x + 3.8, y - L * 0.68,
                      fill=col, width=1.1, tags=("grass_tuft",))

    fl = P["flowers"]
    n_patches = int((4 if study else 6) + (4 if study else 7) * richness)
    for _ in range(n_patches):
        for _try in range(6):
            x = rng.uniform(0.10 * w, 0.90 * w)
            y = rng.uniform(mid_fn(x) + 0.03 * h, h - 0.03 * h)
            if not blocked(x, y, 10 * sc):
                break
        col = rng.choice(fl)
        depth = (y - hz) / (h - hz)
        d = (1.6 + 1.8 * depth) * sc
        for _ in range(rng.randint(2, 3)):
            fx = x + rng.uniform(-12, 12) * sc * depth
            fy = y + rng.uniform(-4, 4) * sc * depth
            if blocked(fx, fy, 2):
                continue
            # Delicate 4-petal cross blossom + green stem (no circle blobs)
            c.create_line(fx, fy, fx, fy + d * 1.4, fill=gcol, width=1)
            c.create_line(fx - d, fy, fx + d, fy, fill=col, width=max(1.5, d * 0.65))
            c.create_line(fx, fy - d, fx, fy + d, fill=col, width=max(1.5, d * 0.65))

    n_mush = int((2 if study else 1) + (4 if study else 6) * richness)
    cap_col = mix("#C9574B", P["tint"][0], P["tint"][1] + 0.1)
    stem_col = mix("#F3E6D2", P["tint"][0], P["tint"][1])
    for _ in range(n_mush):
        for _try in range(8):
            if study:
                x = w * (0.5 + rng.choice((-1, 1)) * rng.uniform(0.14, 0.30))
                y = near_fn(x) + rng.uniform(0.03, 0.10) * h
            else:
                x = rng.uniform(0.10 * w, 0.90 * w)
                y = rng.uniform(near_fn(x) - 0.08 * h, h - 0.03 * h)
            if not blocked(x, y, 14 * sc):
                break
        s = rng.uniform(3.0, 4.8) * sc * (0.6 + 0.6 * (y - hz) / (h - hz))
        c.create_rectangle(x - s * 0.28, y - s * 1.05, x + s * 0.28, y, fill=stem_col, outline=P["ink"], width=0.8)
        c.create_polygon(
            x - s, y - s * 0.85,
            x - s * 0.65, y - s * 1.55,
            x, y - s * 1.75,
            x + s * 0.65, y - s * 1.52,
            x + s, y - s * 0.85,
            fill=cap_col, outline=P["ink"], width=0.9, smooth=True,
        )

    # ── 15. Night warm firefly glows / Chill side campfire & glow ──
    if theme == "night":
        for _ in range(7):
            fx = rng.uniform(0.08 * w, 0.92 * w)
            fy = rng.uniform(near_fn(fx) - 0.04 * h, h - 0.04 * h)
            ro = rng.uniform(2.4, 3.8) * sc
            c.create_oval(fx - ro * 1.8, fy - ro * 1.6, fx + ro * 1.8, fy + ro * 1.6,
                          fill=mix(hs[2], "#F2A83B", 0.36), outline="", tags=("night_orbs",))
            c.create_oval(fx - ro * 0.55, fy - ro * 0.55, fx + ro * 0.55, fy + ro * 0.55,
                          fill="#FFF2B0", outline="", tags=("night_orbs",))

    if theme == "chill" and P.get("campfire"):
        _draw_chill_campfire(c, S)

    return S


# ─────────────────────────────────────────────────────────────────────
#  Forest tree placement (natural staggered rows, clear of framing edges)
# ─────────────────────────────────────────────────────────────────────

def forest_slots(S, n):
    """Return n placements [(x, ground_y, scale)] spread naturally across the
    meadow, avoiding the path, river, and framing foreground trunks."""
    if n <= 0:
        return []
    w, h = S["w"], S["h"]
    mid_fn = S["mid"]
    hz = S["hz"]
    y0 = hz + 0.22 * h
    y1 = h * 0.955
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
            x = 0.12 * w + (spacing * 0.5 if r % 2 else 0.0)
            while x < 0.88 * w:
                jx = x + rng.uniform(-0.18, 0.18) * spacing
                jy = y + rng.uniform(-6, 6) * base
                if (jy > mid_fn(jx) + 8 and not S["blocked"](jx, jy, 30 * s)
                        and not (jx < 0.17 * w and jy > 0.82 * h)
                        and not (jx > 0.86 * w and jy > 0.82 * h)):
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
    while len(out) < n and slots:
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

    # Warm glowing fireflies (night) or twilight fireflies/motes (chill) near the grass & bushes
    if P.get("fireflies") or P.get("motes"):
        is_night = (S["theme"] == "night")
        is_chill = (S["theme"] == "chill")
        glow, core = (("#6E5028", "#FFE89C") if is_night else (("#854A3B", "#FFC88A") if is_chill else ("#683B48", "#FFD8C2")))
        count = 6 if (is_night or is_chill) else 4
        near_fn = S.get("near", lambda x: h * 0.75)
        for i in range(count):
            if is_chill:
                x = rng.uniform(0.12 * w, 0.88 * w)
                y = rng.uniform(near_fn(x) - 0.04 * h, h - 0.04 * h)
            else:
                x = rng.uniform(0.10 * w, 0.90 * w)
                y = rng.uniform(S["mid"](x) + 0.02 * h, h - 0.06 * h)
            tag = "ff_%d" % i
            c.create_oval(x - 4.5, y - 4.5, x + 4.5, y + 4.5, fill=glow, outline="", tags=(tag, "actor"))
            c.create_oval(x - 1.7, y - 1.7, x + 1.7, y + 1.7, fill=core, outline="", tags=(tag, "actor"))
            A["fire"].append([tag, rng.uniform(0, 6.28), rng.uniform(8, 16) * sc, rng.uniform(5, 11) * sc, 0.0, 0.0])

    # Campfire drifting embers (Chill mode: 3-4 tiny glowing embers)
    if S["theme"] == "chill" and S.get("campfire_pos"):
        cx, cy = S["campfire_pos"]
        A["embers"] = []
        ember_cols = ["#F28D6B", "#FFA27A", "#FFD2A0", "#F28D6B"]
        for i in range(4):
            ex = cx + rng.uniform(-3.5, 3.5) * sc
            ey = cy - rng.uniform(4.0, 26.0) * sc
            iid = c.create_oval(ex - 1.2, ey - 1.2, ex + 1.2, ey + 1.2,
                                fill=ember_cols[i], outline="", tags=("ember", "actor"))
            A["embers"].append([iid, cx, ey, rng.uniform(14, 22) * sc, rng.uniform(0, 6.28), rng.uniform(0, 1.0)])

    # Single gentle shooting star gliding across upper sky once every 20 seconds (Chill mode)
    if S["theme"] == "chill":
        star_line = c.create_line(-50, -50, -50, -50, fill="#FFE4DB", width=1.5, tags=("actor", "shooting_star"))
        star_head = c.create_oval(-50, -50, -50, -50, fill="#FFFBF5", outline="", tags=("actor", "shooting_star"))
        A["shooting_star"] = [star_line, star_head, False, 0.0, 1.35, 0.0, 0.0, 0.0, 0.0, 3.0]

    # Butterflies (day themes)
    if P.get("butterflies"):
        for i in range(2):
            x = w * (0.28 + 0.42 * i)
            y = S["near"](x) - 0.05 * h
            col = P["flowers"][i % len(P["flowers"])]
            if col == "#FFFFFF":
                col = "#F6E7A6"
            tag = "bf_%d" % i
            d = 3.2 * sc
            c.create_oval(x - d * 2, y - d, x, y + d * 0.6, fill=col, outline="", tags=(tag, "actor"))
            c.create_oval(x, y - d, x + d * 2, y + d * 0.6, fill=col, outline="", tags=(tag, "actor"))
            c.create_line(x, y - d, x, y + d * 0.8, fill=P["ink"], width=1, tags=(tag, "actor"))
            A["fly"].append([tag, rng.uniform(0, 6.28), 36 * sc, 12 * sc, 0.0, 0.0])

    # Birds drifting across the sky
    if P.get("birds"):
        for i in range(2):
            x = w * (0.32 + 0.11 * i)
            y = h * (0.16 + 0.03 * i)
            tag = "bird_%d" % i
            s = 4 * sc
            c.create_line(x - s, y - s * 0.5, x - s * 0.3, y, x, y - s * 0.2, x + s * 0.3, y, x + s, y - s * 0.5,
                          fill=P["birds"], width=1.2, smooth=True, tags=(tag, "actor"))
            A["birds"].append([tag, 6 + 2 * i, rng.uniform(0, 6.28), 0.0])

    # Occasional falling leaves / petals
    lc = leaf_color or P["leaf"]
    for i in range(2):
        x = rng.uniform(0.18 * w, 0.82 * w)
        y = rng.uniform(0.35 * h, 0.9 * h)
        d = 2.6 * sc
        iid = c.create_polygon(x - d, y, x, y - d * 0.65, x + d, y, x, y + d * 0.65,
                               fill=lc, outline="", tags=("actor",))
        A["leaves"].append([iid, x, y, rng.uniform(10, 18) * sc, rng.uniform(0, 6.28), 0.0])

    if rain:
        add_rain(c, S, A)

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

    # ── Shooting Star (Chill mode: glides once every 20 seconds) ──
    ss = A.get("shooting_star")
    if ss:
        s_line, s_head, active, t_start, dur, x0, y0, x1, y1, next_t = ss
        if not active:
            if now >= next_t:
                ss[2] = True
                ss[3] = now
                ss[4] = 1.35
                rng_s = random.Random(int(now * 10) % 9999)
                x_start = rng_s.uniform(0.18 * w, 0.45 * w)
                y_start = rng_s.uniform(0.04 * h, 0.12 * h)
                x_len = rng_s.uniform(0.24 * w, 0.34 * w)
                y_len = x_len * rng_s.uniform(0.38, 0.50)
                ss[5], ss[6] = x_start, y_start
                ss[7], ss[8] = x_start + x_len, y_start + y_len
                active = True
                t_start = now
                dur = 1.35
                x0, y0 = x_start, y_start
                x1, y1 = x_start + x_len, y_start + y_len
        if active:
            prog = (now - t_start) / dur
            if prog >= 1.0:
                ss[2] = False
                c.coords(s_line, -50, -50, -50, -50)
                c.coords(s_head, -50, -50, -50, -50)
                ss[9] = now + 20.0  # triggers once every 20 seconds
            else:
                p = prog
                cur_x = x0 + (x1 - x0) * p
                cur_y = y0 + (y1 - y0) * p
                sc = S["sc"]
                tl = min(p * 38 * sc, 34 * sc) * (1.0 - max(0.0, p - 0.70) / 0.30)
                dx, dy = (x1 - x0), (y1 - y0)
                dist = max(1.0, math.hypot(dx, dy))
                tail_x = cur_x - (dx / dist) * tl
                tail_y = cur_y - (dy / dist) * tl
                c.coords(s_line, tail_x, tail_y, cur_x, cur_y)
                c.coords(s_head, cur_x - 1.4, cur_y - 1.4, cur_x + 1.4, cur_y + 1.4)

    # ── Campfire Embers (Chill mode: drifting upward) ──
    if A.get("embers") and S.get("campfire_pos"):
        cx, cy = S["campfire_pos"]
        c_sc = S["sc"]
        for emb in A["embers"]:
            iid, bx, ey, vy, ph, _ = emb
            ey -= vy * dt
            ox = bx + math.sin(now * 2.8 + ph) * (4.5 * c_sc) + (ph % 3.0 - 1.5) * 2.8 * c_sc
            if ey < cy - 36 * c_sc:
                ey = cy - random.uniform(3, 7) * c_sc
                emb[4] = random.uniform(0, 6.28)
            emb[2] = ey
            c.coords(iid, ox - 1.2, ey - 1.2, ox + 1.2, ey + 1.2)

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
        # Animate campfire flame flickers (Chill mode)
        cf = S.get("campfire_flame")
        if cf:
            cx, cy, c_sc, f_out, f_mid, f_core = cf
            h_flick = math.sin(now * 7.5) * 1.5 * c_sc + math.cos(now * 12.0) * 0.8 * c_sc
            w_flick = math.cos(now * 6.0) * 0.7 * c_sc
            c.coords(f_out,
                cx - 5.5 * c_sc + w_flick * 0.5, cy + 0.5 * c_sc,
                cx - 4.0 * c_sc + w_flick, cy - 6.0 * c_sc + h_flick * 0.5,
                cx - 1.0 * c_sc + w_flick * 1.2, cy - (13.0 * c_sc + h_flick),
                cx + 2.5 * c_sc + w_flick * 0.8, cy - 7.5 * c_sc + h_flick * 0.4,
                cx + 5.0 * c_sc + w_flick * 0.5, cy + 0.5 * c_sc,
                cx + 0.5 * c_sc, cy + 1.8 * c_sc
            )
            c.coords(f_mid,
                cx - 3.8 * c_sc + w_flick * 0.4, cy + 0.5 * c_sc,
                cx - 2.5 * c_sc + w_flick * 0.7, cy - 5.0 * c_sc + h_flick * 0.4,
                cx - 0.5 * c_sc + w_flick * 0.9, cy - (10.0 * c_sc + h_flick * 0.7),
                cx + 2.0 * c_sc + w_flick * 0.5, cy - 5.5 * c_sc + h_flick * 0.3,
                cx + 3.5 * c_sc + w_flick * 0.4, cy + 0.5 * c_sc
            )
            c.coords(f_core,
                cx - 2.2 * c_sc, cy + 0.5 * c_sc,
                cx - 1.2 * c_sc, cy - 3.5 * c_sc + h_flick * 0.2,
                cx, cy - (6.5 * c_sc + h_flick * 0.4),
                cx + 1.5 * c_sc, cy - 3.5 * c_sc + h_flick * 0.2,
                cx + 2.0 * c_sc, cy + 0.5 * c_sc
            )

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
