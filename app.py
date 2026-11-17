"""
Grow Your Forest 🌱 — A Study-to-Growth Desktop App
Main application file.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont, messagebox, filedialog
import os
import sys
import time
import math
import random
from datetime import datetime, date, timedelta

import database as db
import audio_player
import scenery
from tree_renderer import (
    draw_tree, draw_mini_tree, STAGE_LABELS, COLORS, SPECIES_METADATA,
)


# ──────────────────── Visual Themes ────────────────────

WINDOW_TITLEBAR_THEMES = {
    "morning": {
        "background": "#F3F6F1",
        "symbols": "#1E3A2F",
        "dark": False,
    },
    "afternoon": {
        "background": "#F6EDE0",
        "symbols": "#36291E",
        "dark": False,
    },
    "night": {
        "background": "#131826",
        "symbols": "#E2E8F0",
        "dark": True,
    },
    "chill": {
        "background": "#241B18",
        "symbols": "#F4EDE8",
        "dark": True,
    },
}


def get_titlebar_overlay_config(theme_id="morning"):
    """Returns the titleBarOverlay (Electron / Tauri) & theme-color (Web / PWA) configuration."""
    cfg = WINDOW_TITLEBAR_THEMES.get(theme_id, WINDOW_TITLEBAR_THEMES["morning"])
    return {
        "color": cfg["background"],
        "symbolColor": cfg["symbols"],
        "themeColor": cfg["background"],
        "dark": cfg["dark"],
    }


def get_sprout_svg(color=None):
    """Returns the SVG markup for the header sprout logo, using currentColor or the specified accent color."""
    fill_col = color or "currentColor"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="{fill_col}">
  <path d="M12 22v-9c0-2-1-4-1-4" stroke="{fill_col}" stroke-width="2" stroke-linecap="round" fill="none"/>
  <path d="M11 12 C5 10, 3 5, 7 4 C11 4, 11 8, 11 12 Z" fill="{fill_col}"/>
  <path d="M11 10 C17 8, 21 4, 20 8 C19 12, 12 13, 11 10 Z" fill="{fill_col}"/>
</svg>'''


def get_heatmap_intensity_level(minutes):
    """Map daily studied minutes into 5 heatmap intensity buckets (0..4)."""
    m = max(0, int(minutes))
    if m == 0:
        return 0
    if m < 30:
        return 1
    if m < 60:
        return 2
    if m < 120:
        return 3
    return 4


def get_daily_goal_ring_svg(today_minutes, goal_minutes, stroke_color="#5B8FA8", track_color="#E8E2D7"):
    """Generate a 44x44 pure SVG circular progress ring using stroke-dasharray/stroke-dashoffset."""
    r = 17.0
    circ = 2.0 * math.pi * r
    frac = min(1.0, max(0.0, float(today_minutes) / max(1.0, float(goal_minutes))))
    offset = circ * (1.0 - frac)
    pct = int(round(frac * 100))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="44" height="44">'
        f'<circle cx="22" cy="22" r="{r:.1f}" fill="none" stroke="{track_color}" stroke-width="4.5"/>'
        f'<circle cx="22" cy="22" r="{r:.1f}" fill="none" stroke="{stroke_color}" stroke-width="4.5" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" '
        f'transform="rotate(-90 22 22)"/>'
        f'<text x="22" y="25" text-anchor="middle" font-size="9" font-weight="700" fill="{stroke_color}">{pct}%</text>'
        f'</svg>'
    )


def get_species_donut_svg(breakdown, empty_color="#E8E2D7", text_color="#6D776E"):
    """Generate a pure SVG stroke-dasharray donut chart for forest species breakdown."""
    r = 44.0
    circ = 2.0 * math.pi * r
    total_secs = sum(item.get("total_seconds", 0.0) for item in (breakdown or []))
    if total_secs <= 0:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124 124" width="124" height="124">'
            f'<circle cx="62" cy="62" r="{r:.1f}" fill="none" stroke="{empty_color}" stroke-width="14"/>'
            f'<text x="62" y="65" text-anchor="middle" font-size="9" fill="{text_color}">No trees planted yet</text>'
            f'</svg>'
        )

    circles = []
    offset = 0.0
    for item in breakdown:
        share = item.get("share", 0.0)
        if share <= 0:
            continue
        seg_len = share * circ
        col = item.get("color", "#688536")
        circles.append(
            f'<circle cx="62" cy="62" r="{r:.1f}" fill="none" stroke="{col}" stroke-width="14" '
            f'stroke-dasharray="{seg_len:.2f} {circ:.2f}" stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 62 62)"/>'
        )
        offset += seg_len

    total_mins = int(total_secs // 60)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124 124" width="124" height="124">'
        f'<circle cx="62" cy="62" r="{r:.1f}" fill="none" stroke="{empty_color}" stroke-width="14"/>'
        f'{"".join(circles)}'
        f'<text x="62" y="65" text-anchor="middle" font-size="11" font-weight="700" fill="{text_color}">{total_mins}m</text>'
        f'</svg>'
    )


THEMES = {
    "morning": {
        "id": "morning",
        "name": "Morning",
        "icon": "🌅",
        "bg": "#FAF7F2",
        "titlebar_bg": "#F3F6F1",
        "titlebar_fg": "#1E3A2F",
        "titlebar_dark": False,
        "bg_card": "#FFFFFF",
        "bg_sidebar": "#F0ECE4",
        "bg_dark": "#E8E2D7",
        "fg": "#2B332C",
        "fg_muted": "#6D776E",
        "fg_light": "#9CA59D",
        "accent": "#467D56",
        "accent_hover": "#386845",
        "accent_light": "#EBF2EC",
        "accent_fg": "#FFFFFF",
        "green_dark": "#275237",
        "green_med": "#467D56",
        "green_light": "#77A886",
        "brown": "#8D7356",
        "brown_light": "#C5B095",
        "cream": "#FAF3E8",
        "red_soft": "#D96B52",
        "blue_soft": "#588BB5",
        "yellow_soft": "#E0A638",
        "border": "#DDD7C8",
        "shadow": "#D5CEBD",
        "canvas_bg": "#F5EFE6",
        "nav_active": "#467D56",
        "nav_inactive": "#8F9790",
        "bar_bg": "#E8E2D8",
        "bar_fill": "#75A684",
        "streak_fire": "#E86C38",
    },
    "afternoon": {
        "id": "afternoon",
        "name": "Afternoon",
        "icon": "☀️",
        "bg": "#F6EDE0",
        "titlebar_bg": "#F6EDE0",
        "titlebar_fg": "#36291E",
        "titlebar_dark": False,
        "bg_card": "#FCF8F2",
        "bg_sidebar": "#F6EDE0",
        "bg_dark": "#EADCC9",
        "fg": "#36291E",
        "fg_muted": "#786655",
        "fg_light": "#A39180",
        "accent": "#C47435",
        "accent_hover": "#B06327",
        "accent_light": "#F7E6D3",
        "accent_fg": "#FFFBF5",
        "green_dark": "#36291E",
        "green_med": "#C47435",
        "green_light": "#D98A48",
        "brown": "#9C6E42",
        "brown_light": "#D1A578",
        "cream": "#FCF6EC",
        "red_soft": "#DB5842",
        "blue_soft": "#4889BA",
        "yellow_soft": "#E69F24",
        "border": "#DBC8B0",
        "shadow": "#CEBCA4",
        "canvas_bg": "#F6EDE0",
        "nav_active": "#C47435",
        "nav_inactive": "#8C7C6D",
        "bar_bg": "#EADCC9",
        "bar_fill": "#C47435",
        "streak_fire": "#D95A2B",
    },
    "night": {
        "id": "night",
        "name": "Night",
        "icon": "🌙",
        "bg": "#151922",
        "titlebar_bg": "#131826",
        "titlebar_fg": "#E2E8F0",
        "titlebar_dark": True,
        "bg_card": "#1E2430",
        "bg_sidebar": "#191F2B",
        "bg_dark": "#262E3E",
        "fg": "#E8EDF2",
        "fg_muted": "#94A1B2",
        "fg_light": "#677588",
        "accent": "#4EBA87",
        "accent_hover": "#3EA373",
        "accent_light": "#1E332A",
        "accent_fg": "#FFFFFF",
        "green_dark": "#74D1A3",
        "green_med": "#4EBA87",
        "green_light": "#92DFB8",
        "brown": "#B39274",
        "brown_light": "#8C735B",
        "cream": "#232B3A",
        "red_soft": "#E57373",
        "blue_soft": "#64B5F6",
        "yellow_soft": "#F6C15C",
        "border": "#2B3444",
        "shadow": "#0E1218",
        "canvas_bg": "#1A202C",
        "nav_active": "#4EBA87",
        "nav_inactive": "#6C7B90",
        "bar_bg": "#252D3C",
        "bar_fill": "#4EBA87",
        "streak_fire": "#FF8A50",
    },
    "chill": {
        "id": "chill",
        "name": "Chill",
        "icon": "☕",
        "bg": "#2B211E",
        "titlebar_bg": "#241B18",
        "titlebar_fg": "#F4EDE8",
        "titlebar_dark": True,
        "bg_card": "#362A26",
        "bg_sidebar": "#302521",
        "bg_dark": "#443530",
        "fg": "#F5E6D8",
        "fg_muted": "#C4AC9A",
        "fg_light": "#947D6E",
        "accent": "#D98A56",
        "accent_hover": "#C07340",
        "accent_light": "#4A352B",
        "accent_fg": "#FFFFFF",
        "green_dark": "#E8B88A",
        "green_med": "#C88B5A",
        "green_light": "#DFA878",
        "brown": "#C99774",
        "brown_light": "#9E7356",
        "cream": "#3F312C",
        "red_soft": "#E07A68",
        "blue_soft": "#8CA8BE",
        "yellow_soft": "#E8AE58",
        "border": "#4A3A34",
        "shadow": "#1C1513",
        "canvas_bg": "#2E2320",
        "nav_active": "#E69A64",
        "nav_inactive": "#9A8273",
        "bar_bg": "#42332E",
        "bar_fill": "#D98A56",
        "streak_fire": "#F08A4B",
    },
}

THEME = dict(THEMES["morning"])


_FONTS_LOADED = False


def _load_bundled_fonts():
    """Register bundled Google Fonts (.ttf) privately for this process on Windows."""
    global _FONTS_LOADED
    if _FONTS_LOADED:
        return
    try:
        from ctypes import windll
    except Exception:
        return
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "fonts")
    if not os.path.isdir(fonts_dir):
        return
    FR_PRIVATE = 0x10
    for fname in sorted(os.listdir(fonts_dir)):
        if fname.lower().endswith((".ttf", ".otf")):
            try:
                windll.gdi32.AddFontResourceExW(os.path.join(fonts_dir, fname), FR_PRIVATE, 0)
            except Exception:
                pass
    _FONTS_LOADED = True


def _rounded_rect_pts(x0, y0, x1, y1, r):
    """Return polygon vertices for a rounded rectangle on a tk.Canvas."""
    r = max(1.0, min(float(r), (x1 - x0) * 0.48, (y1 - y0) * 0.48))
    pts = []
    steps = (0.0, 0.3827, 0.7071, 0.9239, 1.0)
    for s in steps:
        c = math.sqrt(max(0.0, 1.0 - s * s))
        pts.extend([x1 - r + r * s, y0 + r - r * c])
    for s in steps:
        c = math.sqrt(max(0.0, 1.0 - s * s))
        pts.extend([x1 - r + r * c, y1 - r + r * s])
    for s in steps:
        c = math.sqrt(max(0.0, 1.0 - s * s))
        pts.extend([x0 + r - r * s, y1 - r + r * c])
    for s in steps:
        c = math.sqrt(max(0.0, 1.0 - s * s))
        pts.extend([x0 + r - r * c, y0 + r - r * s])
    return pts


def _normalize_hex(col):
    """Normalize named or #rgb/#rrggbb Tk colors to lowercase #rrggbb if possible."""
    if not isinstance(col, str):
        return None
    s = col.strip().lower()
    if s == "white":
        return "#ffffff"
    if s == "black":
        return "#000000"
    if len(s) == 4 and s.startswith("#"):
        return "#" + s[1] * 2 + s[2] * 2 + s[3] * 2
    if len(s) == 7 and s.startswith("#"):
        return s
    return None


def _lerp_hex(c1, c2, t):
    """Linearly interpolate between two #rrggbb colors (clamped to [0, 1])."""
    h1 = _normalize_hex(c1)
    h2 = _normalize_hex(c2)
    if not h1 or not h2:
        return c2
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = int(h1[1:3], 16), int(h1[3:5], 16), int(h1[5:7], 16)
    r2, g2, b2 = int(h2[1:3], 16), int(h2[3:5], 16), int(h2[5:7], 16)
    r = int(round(r1 + (r2 - r1) * t))
    g = int(round(g1 + (g2 - g1) * t))
    b = int(round(b1 + (b2 - b1) * t))
    return f"#{r:02x}{g:02x}{b:02x}"


class RainButton(tk.Frame):
    """Compound toggle button with icon and text strictly centered with gap: 6px."""
    def __init__(self, master, font, is_playing=False, is_tight=False, ctrl_pady=3, **kwargs):
        fg = kwargs.pop("fg", None)
        super().__init__(master, cursor="hand2", **kwargs)
        bg = self.cget("bg")
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(expand=True, anchor="center", padx=8, pady=ctrl_pady)
        self.ico = tk.Label(self.inner, text="🌧️", font=("Segoe UI Emoji", 8), bg=bg, fg=fg)
        self.ico.pack(side="left", padx=(0, 6), anchor="center")
        txt = ("ON" if is_playing else "OFF") if is_tight else ("Rain: ON" if is_playing else "Rain: OFF")
        self.lbl = tk.Label(self.inner, text=txt, font=font, bg=bg, fg=fg)
        self.lbl.pack(side="left", anchor="center")

    def configure(self, **kwargs):
        text = kwargs.pop("text", None)
        bg = kwargs.pop("bg", None)
        fg = kwargs.pop("fg", None)
        b_col = kwargs.pop("highlightbackground", None)
        if bg is not None:
            super().configure(bg=bg)
            self.inner.configure(bg=bg)
            self.ico.configure(bg=bg)
            self.lbl.configure(bg=bg)
        if b_col is not None:
            super().configure(highlightbackground=b_col)
        if fg is not None:
            self.ico.configure(fg=fg)
            self.lbl.configure(fg=fg)
        if text is not None:
            clean = text.replace("🌧️", "").strip()
            self.lbl.configure(text=clean)
        if kwargs:
            super().configure(**kwargs)
    config = configure

    def cget(self, key):
        if key == "fg":
            return self.lbl.cget("fg")
        if key == "text":
            return self.lbl.cget("text")
        return super().cget(key)
    __getitem__ = cget

    def bind(self, sequence=None, func=None, add=None):
        res = super().bind(sequence, func, add)
        if sequence in ("<Button-1>", "<Enter>", "<Leave>"):
            for w in (self.inner, self.ico, self.lbl):
                w.bind(sequence, func, add)
        return res


class ThemeModeButton(tk.Frame):
    """Compound theme mode button with icon and text strictly centered with gap: 6px."""
    def __init__(self, master, icon, text, font, ctrl_pady=4, ctrl_padx=12, **kwargs):
        fg = kwargs.pop("fg", None)
        super().__init__(master, cursor="hand2", **kwargs)
        bg = self.cget("bg")
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(expand=True, anchor="center", padx=ctrl_padx, pady=ctrl_pady)
        self.ico = tk.Label(self.inner, text=icon, font=("Segoe UI Emoji", 8), bg=bg, fg=fg)
        self.ico.pack(side="left", padx=(0, 6), anchor="center")
        self.lbl = tk.Label(self.inner, text=text, font=font, bg=bg, fg=fg)
        self.lbl.pack(side="left", anchor="center")

    def configure(self, **kwargs):
        bg = kwargs.pop("bg", None)
        fg = kwargs.pop("fg", None)
        text = kwargs.pop("text", None)
        b_col = kwargs.pop("highlightbackground", None)
        if bg is not None:
            super().configure(bg=bg)
            self.inner.configure(bg=bg)
            self.ico.configure(bg=bg)
            self.lbl.configure(bg=bg)
        if b_col is not None:
            super().configure(highlightbackground=b_col)
        if fg is not None:
            self.ico.configure(fg=fg)
            self.lbl.configure(fg=fg)
        if text is not None:
            self.lbl.configure(text=text)
        if kwargs:
            super().configure(**kwargs)
    config = configure

    def cget(self, key):
        if key == "fg":
            return self.lbl.cget("fg")
        if key == "text":
            return self.lbl.cget("text")
        return super().cget(key)
    __getitem__ = cget

    def bind(self, sequence=None, func=None, add=None):
        res = super().bind(sequence, func, add)
        if sequence in ("<Button-1>", "<Enter>", "<Leave>"):
            for w in (self.inner, self.ico, self.lbl):
                w.bind(sequence, func, add)
        return res


class GrowYourForestApp:
    """Main application class."""

    def __init__(self, root):
        self.root = root
        self.root.title("Grow Your Forest 🌱")
        self.root.geometry("900x720")
        self.root.minsize(800, 650)

        # ── Visual Theme ──
        self.current_theme = db.get_setting("theme", "morning")
        if self.current_theme not in THEMES:
            self.current_theme = "morning"
        THEME.update(THEMES[self.current_theme])
        self.root.configure(bg=THEME["bg"])

        # Dynamic OS window title bar colors for active theme (Windows DWM / Desktop)
        self._apply_window_titlebar_theme()
        try:
            self.root.attributes('-alpha', 0.0)
            self.root.after(50, lambda: (self.root.attributes('-alpha', 1.0), self._apply_window_titlebar_theme()))
        except Exception:
            pass

        # ── Timer State ──
        self.timer_running = False
        self.timer_paused = False
        self.session_active = False
        self.planned_duration = 25 * 60  # seconds
        self.focused_seconds = 0.0
        self.last_tick_time = None
        self.session_start_time = None
        self.selected_species = "cherry_blossom"
        self.current_task = "General Study"
        self.task_draft_species = "cherry_blossom"
        self.active_task_id = None
        saved_active = db.get_setting("active_task_id")
        if saved_active and str(saved_active).isdigit():
            t_active = db.get_task_by_id(int(saved_active))
            if t_active and not t_active["completed"]:
                self.active_task_id = t_active["id"]
                self.current_task = t_active["title"]
                self.selected_species = t_active["tree_species"]
        self._task_popover = None
        self._task_tooltip = None
        self.daily_goal_minutes = db.get_daily_goal_minutes()
        self.stats_activity_mode = "both"
        self.hide_zero_min_sessions = True
        self._stats_tooltip = None
        self.forest_filter_species = "all"

        # ── Water drop animation state ──
        self.water_drops = []
        self.last_stage = "seed"

        # ── Ambient Environmental Animation & Cached Scene State ──
        self._anim_tick = 0
        self._last_anim_time = time.monotonic()
        self._study_scene = None
        self._study_actors = None
        self._forest_scene = None
        self._forest_actors = None
        self._study_resize_after = None
        self._forest_resize_after = None
        self._last_study_size = (0, 0)
        self._last_forest_size = (0, 0)
        self._window_obscured = False

        # ── Smooth Theme & Responsive Layout State ──
        self._theme_anim_after = None
        self._resize_layout_after = None
        self._last_layout_state = self._get_layout_state()

        # ── Custom Session Complete Modal State ──
        self._session_modal_backdrop = None
        self._session_modal_card = None
        self._session_modal_anim_after = None
        self._session_modal_root_binds = []
        self._session_modal_continue_btn = None
        self._session_modal_mark_complete_btn = None
        self._session_modal_info = None
        self._timer_base_pt = 44
        self._timer_avail_w = 240
        self._timer_font_cache = {}
        self._last_timer_font_pt = None
        self.session_had_pause = False
        self._daily_countdown_after = None
        self.daily_challenge_cards = []
        self.daily_countdown_label = None
        self.seed_inventory_badge = None
        self.ach_filter = "all"
        self.ach_filter_buttons = {}
        self._claim_pulse_after = None
        self._claim_pulse_phase = 0
        self._claim_pulse_buttons = []
        self.active_quest = None
        self.active_quest_banner = None
        self._species_dropdown = None
        self.species_dropdown_btn = None

        # ── Navigation ──
        self.current_view = "timer"

        # ── Fonts ──
        self._setup_fonts()

        # ── Build UI ──
        self._build_layout()
        self._show_timer_view()

        # ── Window close protocol ──
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Window visibility & iconify binding (for zero-CPU idle throttling) ──
        self.root.bind("<Unmap>", lambda e: self._on_window_unmap(e))
        self.root.bind("<Map>", lambda e: self._on_window_map(e))
        self.root.bind("<Configure>", lambda e: self._on_root_configure(e))

        # ── Start tick ──
        self._tick()

    def _get_viewport_size(self):
        """Return current (width, height) in px, falling back safely before first map."""
        try:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            if w > 100 and h > 100:
                return w, h
        except Exception:
            pass
        return 900, 720

    def _get_responsive_mode(self):
        """Classify window width into 'compact' (<980), 'laptop' (<=1200), or 'wide' (>1200)."""
        vw, _ = self._get_viewport_size()
        if vw < 980:
            return "compact"
        if vw <= 1200:
            return "laptop"
        return "wide"

    def _get_layout_state(self):
        vw, vh = self._get_viewport_size()
        if vw < 890:
            w_bucket = "tight"
        elif vw < 980:
            w_bucket = "compact"
        elif vw <= 1200:
            w_bucket = "laptop"
        else:
            w_bucket = "wide"
        h_bucket = "short" if vh < 690 else "tall"
        return (w_bucket, h_bucket)

    def _on_root_configure(self, event):
        """Adapt header, sidebar, and nav breakpoints smoothly when crossing responsive thresholds."""
        if event.widget != self.root:
            return
        new_state = self._get_layout_state()
        if new_state == self._last_layout_state:
            return
        if self._resize_layout_after is not None:
            try:
                self.root.after_cancel(self._resize_layout_after)
            except tk.TclError:
                pass
        self._resize_layout_after = self.root.after(90, self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        self._resize_layout_after = None
        new_state = self._get_layout_state()
        if new_state == self._last_layout_state:
            return
        self._last_layout_state = new_state
        w_bucket, _ = new_state
        outer_padx = 8 if w_bucket == "tight" else (12 if w_bucket == "compact" else (18 if w_bucket == "laptop" else 20))
        hdr_h = 56 if w_bucket in ("tight", "compact") else (60 if w_bucket == "laptop" else 62)
        try:
            self.header_frame.configure(height=hdr_h)
            self.header_frame.pack_configure(padx=outer_padx)
            self.content_frame.pack_configure(padx=outer_padx)
        except tk.TclError:
            pass
        self._build_header()
        self._build_nav()
        if self.current_view == "timer":
            self._show_timer_view()

    def _on_window_unmap(self, event):
        """When minimized or obscured, pause non-critical animations to save CPU."""
        if event.widget == self.root:
            self._window_obscured = True
            for attr in ("_study_resize_after", "_forest_resize_after", "_resize_layout_after"):
                aid = getattr(self, attr, None)
                if aid is not None:
                    try:
                        self.root.after_cancel(aid)
                    except tk.TclError:
                        pass
                    setattr(self, attr, None)

    def _on_window_map(self, event):
        """Resume animations when un-minimized."""
        if event.widget == self.root:
            self._window_obscured = False

    # ──────────────── Fonts ────────────────

    def _setup_fonts(self):
        _load_bundled_fonts()
        try:
            available = set(tkfont.families(self.root))
        except Exception:
            available = set()

        def pick(preferred, prefix, fallback):
            if preferred in available:
                return preferred
            matches = sorted(f for f in available if f.startswith(prefix))
            return matches[0] if matches else fallback

        self.family_serif = pick("Fraunces SemiBold", "Fraunces", "Georgia")
        self.family_sans = pick("Plus Jakarta Sans", "Plus Jakarta Sans", "Segoe UI")
        self.family_sans_semi = pick("Plus Jakarta Sans SemiBold", "Plus Jakarta Sans", self.family_sans)
        self.family_mono = pick("Space Mono", "Space Mono", "Consolas")

        # Fraunces (soft serif, weight 600) for headings & botanical tree status labels
        self.font_title = (self.family_serif, 20, "bold")
        self.font_subtitle = (self.family_serif, 13, "bold")
        self.font_section = (self.family_serif, 14, "bold")
        self.font_stage = (self.family_serif, 13, "bold")

        # Plus Jakarta Sans for clean, calm UI controls & labels
        self.font_body = (self.family_sans, 11)
        self.font_small = (self.family_sans, 9)
        self.font_small_bold = (self.family_sans_semi, 9, "bold")
        self.font_small_italic = (self.family_sans, 9, "italic")
        self.font_small_strike = (self.family_sans, 9, "overstrike")
        self.font_xs = (self.family_sans, 8)
        self.font_xs_bold = (self.family_sans_semi, 8, "bold")
        self.font_xs_italic = (self.family_sans, 8, "italic")
        self.font_button = (self.family_sans_semi, 11, "bold")
        self.font_nav = (self.family_sans_semi, 11, "bold")
        self.font_card_title = (self.family_sans_semi, 11, "bold")
        self.font_achievement = (self.family_sans, 10)
        self.font_stat_label = (self.family_sans, 9)

        # Space Mono for jitter-free tabular countdown & statistics digits
        self.font_timer = (self.family_mono, 44, "bold")
        self.font_timer_label = (self.family_mono, 10)
        self.font_stat_inline = (self.family_mono, 14, "bold")
        self.font_stat_strip = (self.family_mono, 15, "bold")
        self.font_stat_num = (self.family_mono, 22, "bold")

        self.font_emoji = ("Segoe UI Emoji", 14)
        self.font_emoji_large = ("Segoe UI Emoji", 20)
        self._forest_label_font = tkfont.Font(root=self.root, family=self.family_sans_semi, size=8, weight="bold")
        self._species_pill_font = tkfont.Font(root=self.root, family=self.family_sans_semi, size=9, weight="bold")

    # ──────────────── Layout ────────────────

    def _build_layout(self):
        mode = self._get_responsive_mode()
        outer_padx = 12 if mode == "compact" else (18 if mode == "laptop" else 20)
        hdr_h = 56 if mode == "compact" else (60 if mode == "laptop" else 62)
        nav_h = 48 if mode == "compact" else 54

        # Main container
        self.main_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # Designated Top Header Frame (pinned before content_frame)
        self.header_frame = tk.Frame(self.main_frame, bg=THEME["bg"], height=hdr_h)
        self.header_frame.pack(fill="x", side="top", padx=outer_padx, pady=(10, 4))
        self.header_frame.pack_propagate(False)
        self._build_header()

        # Designated Bottom Navigation Frame (pinned before content_frame so tall views never push it off-screen)
        self.nav_frame = tk.Frame(self.main_frame, bg=THEME["bg_sidebar"], height=nav_h)
        self.nav_frame.pack(fill="x", side="bottom")
        self.nav_frame.pack_propagate(False)
        self._build_nav()

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=THEME["bg"])
        self.content_frame.pack(side="top", fill="both", expand=True, padx=outer_padx, pady=(4, 8))

    def _build_header(self):
        # Clear any existing header widgets for dynamic theme refresh
        for w in self.header_frame.winfo_children():
            w.destroy()
        self.header_frame.configure(bg=THEME["bg"])

        vw, _ = self._get_viewport_size()
        mode = self._get_responsive_mode()
        is_compact = (mode == "compact")
        is_laptop = (mode == "laptop")
        is_tight = (vw < 890)

        title_font = (self.family_serif, 14, "bold") if is_tight else (
            (self.family_serif, 15, "bold") if is_compact else (
                (self.family_serif, 17, "bold") if is_laptop else self.font_title
            )
        )
        emoji_font = ("Segoe UI Emoji", 14) if is_tight else (
            ("Segoe UI Emoji", 15) if is_compact else (
                ("Segoe UI Emoji", 18) if is_laptop else self.font_emoji_large
            )
        )
        group_gap = 6 if is_tight else (8 if is_compact else (12 if is_laptop else 16))
        right_margin = 6 if is_tight else (8 if is_compact else (12 if is_laptop else 16))
        ctrl_pady = 2 if is_compact else 3

        # Left: App title (vertically centered)
        title_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        title_frame.pack(side="left", anchor="center")

        # Sprout logo dynamically colored with theme title accent color (never hardcoded black #000)
        icon_size = 18 if is_tight else (20 if is_compact else (22 if is_laptop else 24))
        sprout_c = tk.Canvas(
            title_frame, width=icon_size, height=icon_size,
            bg=THEME["bg"], highlightthickness=0
        )
        sprout_c.pack(side="left", anchor="center", padx=(0, 4 if is_compact else 6))
        self.sprout_icon = sprout_c
        sc = icon_size / 24.0
        accent = THEME["green_dark"]
        sprout_c.sprout_color = accent
        # Smooth curved stem
        sprout_c.create_line(
            12 * sc, 22 * sc, 12 * sc, 12 * sc, 11 * sc, 8 * sc,
            fill=accent, width=max(1.5, 2.0 * sc), smooth=True
        )
        # Left curved sprout leaf
        sprout_c.create_polygon(
            11 * sc, 12 * sc,
            5 * sc, 10 * sc,
            3 * sc, 5 * sc,
            7 * sc, 4 * sc,
            11 * sc, 8 * sc,
            fill=accent, outline="", smooth=True
        )
        # Right curved sprout leaf
        sprout_c.create_polygon(
            11 * sc, 10 * sc,
            17 * sc, 8 * sc,
            21 * sc, 4 * sc,
            20 * sc, 8 * sc,
            12 * sc, 13 * sc,
            fill=accent, outline="", smooth=True
        )
        # Leaf highlight node
        sprout_c.create_oval(
            10 * sc, 7 * sc, 13 * sc, 10 * sc,
            fill=THEME.get("green_primary", accent), outline=""
        )

        tk.Label(
            title_frame, text="Grow Your Forest",
            font=title_font, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(side="left", anchor="center")

        # Right: Date and streak with guaranteed right margin (vertically centered)
        right_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        right_frame.pack(side="right", anchor="center", padx=(0, right_margin))

        today_fmt = "%b %d, %Y" if (is_tight or is_compact) else "%B %d, %Y"
        today_str = date.today().strftime(today_fmt)
        date_lbl = tk.Label(
            right_frame, text=today_str,
            font=self.font_small if (is_tight or is_compact) else self.font_body,
            fg=THEME["fg_muted"], bg=THEME["bg"]
        )
        date_lbl.pack(side="top", anchor="e", padx=(0, 2))

        streak = db.get_streak()
        streak_text = f"🔥 {streak}d streak" if is_tight else (
            f"🔥 {streak} day streak" if streak > 0 else (
                "Start streak!" if is_compact else "Start your streak today!"
            )
        )
        streak_color = THEME["streak_fire"] if streak > 0 else THEME["fg_light"]
        self.streak_label = tk.Label(
            right_frame, text=streak_text,
            font=self.font_xs if is_compact else self.font_small,
            fg=streak_color, bg=THEME["bg"]
        )
        self.streak_label.pack(side="top", anchor="e", padx=(0, 2))

        # Center-Right: Built-in Rain Sound Control (vertically centered, uniform height)
        rain_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        rain_frame.pack(side="right", anchor="center", padx=(0, group_gap))

        is_playing = audio_player.player.is_playing
        rain_bg = "#E1F5FE" if is_playing else THEME["bg_dark"]
        rain_fg = "#0277BD" if is_playing else THEME["fg_muted"]
        rain_border = "#81D4FA" if is_playing else THEME["border"]

        self.rain_btn = RainButton(
            rain_frame,
            font=self.font_xs_bold if is_compact else self.font_small_bold,
            is_playing=is_playing,
            is_tight=is_tight,
            ctrl_pady=ctrl_pady,
            bg=rain_bg, fg=rain_fg,
            highlightbackground=rain_border, highlightthickness=1
        )
        self.rain_btn.pack(side="left", anchor="center")
        self.rain_btn.bind("<Button-1>", lambda e: self._toggle_rain_sound())

        # Rain volume controls: [ 🔉 ] [ − ] [ 70% ] [ + ] [ 🔊 ] evenly spaced and vertically centered
        self.vol_frame = tk.Frame(rain_frame, bg=THEME["bg_dark"],
                                  highlightbackground=THEME["border"], highlightthickness=1)
        self.vol_frame.pack(side="left", anchor="center", padx=(5, 0))

        v_btn_font = (self.family_sans_semi, 8 if is_compact else 9, "bold")
        v_icon_font = ("Segoe UI Emoji", 8)
        v_mono_font = (self.family_mono, 8 if is_compact else 9, "bold")

        v_down_icon = tk.Label(self.vol_frame, text="🔉", font=v_icon_font,
                               bg=THEME["bg_dark"], fg=THEME["fg_muted"],
                               pady=ctrl_pady, cursor="hand2", anchor="center")
        v_down_icon.pack(side="left", anchor="center", padx=(4, 2))
        v_down_icon.bind("<Button-1>", lambda e: self._change_rain_volume(-15))
        v_down_icon.bind("<Enter>", lambda e: v_down_icon.configure(fg=THEME["fg"]))
        v_down_icon.bind("<Leave>", lambda e: v_down_icon.configure(fg=THEME["fg_muted"]))

        v_down_btn = tk.Label(self.vol_frame, text="−", font=v_btn_font,
                              bg=THEME["bg_dark"], fg=THEME["fg_muted"],
                              pady=ctrl_pady, cursor="hand2", anchor="center")
        v_down_btn.pack(side="left", anchor="center", padx=2)
        v_down_btn.bind("<Button-1>", lambda e: self._change_rain_volume(-15))
        v_down_btn.bind("<Enter>", lambda e: v_down_btn.configure(fg=THEME["accent"]))
        v_down_btn.bind("<Leave>", lambda e: v_down_btn.configure(fg=THEME["fg_muted"]))

        self.vol_label = tk.Label(self.vol_frame, text=f"{audio_player.player.volume}%",
                                  font=v_mono_font, bg=THEME["bg_dark"], fg=THEME["fg"],
                                  width=5, anchor="center", pady=ctrl_pady)
        self.vol_label.pack(side="left", anchor="center", padx=2)

        v_up_btn = tk.Label(self.vol_frame, text="+", font=v_btn_font,
                            bg=THEME["bg_dark"], fg=THEME["fg_muted"],
                            pady=ctrl_pady, cursor="hand2", anchor="center")
        v_up_btn.pack(side="left", anchor="center", padx=2)
        v_up_btn.bind("<Button-1>", lambda e: self._change_rain_volume(+15))
        v_up_btn.bind("<Enter>", lambda e: v_up_btn.configure(fg=THEME["accent"]))
        v_up_btn.bind("<Leave>", lambda e: v_up_btn.configure(fg=THEME["fg_muted"]))

        v_up_icon = tk.Label(self.vol_frame, text="🔊", font=v_icon_font,
                             bg=THEME["bg_dark"], fg=THEME["fg_muted"],
                             pady=ctrl_pady, cursor="hand2", anchor="center")
        v_up_icon.pack(side="left", anchor="center", padx=(2, 4))
        v_up_icon.bind("<Button-1>", lambda e: self._change_rain_volume(+15))
        v_up_icon.bind("<Enter>", lambda e: v_up_icon.configure(fg=THEME["fg"]))
        v_up_icon.bind("<Leave>", lambda e: v_up_icon.configure(fg=THEME["fg_muted"]))

        # Center: Sleek 4-Theme Segmented Pill Bar with auto content-fit widths (no clipping)
        theme_bar = tk.Frame(self.header_frame, bg=THEME["border"], bd=0,
                             highlightbackground=THEME["border"], highlightthickness=1)
        theme_bar.pack(side="right", anchor="center", padx=(0, group_gap))

        self.theme_buttons = {}
        theme_choices = [
            ("morning", "🌅", "Morning"),
            ("afternoon", "☀️", "Afternoon"),
            ("night", "🌙", "Night"),
            ("chill", "☕", "Chill"),
        ]
        tab_padx = 8 if is_tight else 12
        tab_pady = 4 if not is_compact else 3

        for col_idx, (t_id, t_ico, t_text) in enumerate(theme_choices):
            is_active = (self.current_theme == t_id)
            btn_bg = THEME["accent"] if is_active else THEME["bg_dark"]
            btn_fg = THEME.get("accent_fg", "#FFFFFF") if is_active else THEME["fg_muted"]

            btn = ThemeModeButton(
                theme_bar,
                icon=t_ico,
                text=t_text,
                font=self.font_xs_bold,
                ctrl_pady=tab_pady,
                ctrl_padx=tab_padx,
                bg=btn_bg,
                fg=btn_fg,
            )
            btn.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
            btn.bind("<Button-1>", lambda e, tid=t_id: self._set_theme(tid))
            if not is_active:
                hover_bg = scenery.mix(THEME["bg_dark"], THEME["fg"], 0.08)
                btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.configure(bg=h, fg=THEME["fg"]))
                btn.bind("<Leave>", lambda e, b=btn, bg_orig=btn_bg, fg_orig=btn_fg: b.configure(bg=bg_orig, fg=fg_orig))
            self.theme_buttons[t_id] = btn

    def _collect_theme_transition_targets(self, old_pal, new_pal):
        """Capture UI widgets matching new_pal tokens so we can smoothly ease from old_pal."""
        theme_keys = (
            "bg", "bg_card", "bg_sidebar", "bg_dark", "fg", "fg_muted", "fg_light",
            "accent", "accent_light", "accent_fg", "green_dark", "green_med", "border",
            "nav_active", "nav_inactive", "bar_bg", "bar_fill", "streak_fire",
        )
        reverse_map = {}
        for k in theme_keys:
            new_h = _normalize_hex(new_pal.get(k))
            old_h = _normalize_hex(old_pal.get(k))
            if new_h and old_h and new_h != old_h and new_h not in reverse_map:
                reverse_map[new_h] = old_h

        skip_canvases = {
            getattr(self, "tree_canvas", None),
            getattr(self, "forest_canvas", None),
        }
        targets = []
        queue_w = [self.root]
        while queue_w:
            w = queue_w.pop()
            try:
                if not w.winfo_exists():
                    continue
                queue_w.extend(w.winfo_children())
            except tk.TclError:
                continue
            if w in skip_canvases:
                continue
            for attr in ("bg", "fg", "highlightbackground"):
                try:
                    cur_val = _normalize_hex(w.cget(attr))
                except tk.TclError:
                    continue
                if cur_val and cur_val in reverse_map:
                    targets.append((w, attr, reverse_map[cur_val], cur_val))
        return targets

    def _animate_theme_transition(self, targets, step, total_steps):
        """Ease widget palette colors across frames (~350ms total) for smooth theme switching."""
        if step > total_steps:
            self._theme_anim_after = None
            return
        u = step / float(total_steps)
        eased = 1.0 - (1.0 - u) ** 3
        for w, attr, old_h, new_h in targets:
            try:
                if w.winfo_exists():
                    w.configure(**{attr: _lerp_hex(old_h, new_h, eased)})
            except tk.TclError:
                pass
        if step < total_steps:
            try:
                self._theme_anim_after = self.root.after(
                    50, lambda s=step + 1: self._animate_theme_transition(targets, s, total_steps)
                )
            except tk.TclError:
                self._theme_anim_after = None
        else:
            self._theme_anim_after = None

    def _apply_window_titlebar_theme(self, theme_id=None):
        """Apply dynamic OS window title bar colors (Windows 10/11 DWM)
        and update titlebar overlay settings for the active theme."""
        theme_id = theme_id or self.current_theme
        cfg = WINDOW_TITLEBAR_THEMES.get(theme_id, WINDOW_TITLEBAR_THEMES["morning"])
        bg_hex = cfg["background"]
        fg_hex = cfg["symbols"]
        is_dark = cfg["dark"]

        if sys.platform == "win32":
            try:
                import ctypes
                self.root.update_idletasks()
                wid = self.root.winfo_id()
                if not wid:
                    return
                hwnd = ctypes.windll.user32.GetParent(wid)
                if not hwnd:
                    hwnd = ctypes.windll.user32.GetAncestor(wid, 2)  # GA_ROOT
                if not hwnd:
                    hwnd = wid

                def hex_to_colorref(hex_str):
                    hex_str = hex_str.lstrip("#")
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    return r | (g << 8) | (b << 16)

                bg_ref = hex_to_colorref(bg_hex)
                fg_ref = hex_to_colorref(fg_hex)

                # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 build 18985+ / 19041+)
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                # DWMWA_CAPTION_COLOR = 35 (Windows 11 build 22000+)
                DWMWA_CAPTION_COLOR = 35
                # DWMWA_TEXT_COLOR = 36 (Windows 11 build 22000+)
                DWMWA_TEXT_COLOR = 36

                dark_val = ctypes.c_int(1 if is_dark else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark_val), ctypes.sizeof(dark_val)
                )

                caption_val = ctypes.c_int(bg_ref)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_val), ctypes.sizeof(caption_val)
                )

                text_val = ctypes.c_int(fg_ref)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_val), ctypes.sizeof(text_val)
                )
            except Exception:
                pass
        elif sys.platform.startswith("linux"):
            try:
                import subprocess
                variant = "dark" if is_dark else "light"
                wid = self.root.winfo_id()
                if wid:
                    subprocess.Popen(
                        ["xprop", "-id", str(wid), "-f", "_GTK_THEME_VARIANT", "8s", "-set", "_GTK_THEME_VARIANT", variant],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            except Exception:
                pass

    def _set_theme(self, theme_id):
        """Switch visual mode with a smooth palette transition across the app and persist."""
        if theme_id not in THEMES:
            return
        if self._theme_anim_after is not None:
            try:
                self.root.after_cancel(self._theme_anim_after)
            except tk.TclError:
                pass
            self._theme_anim_after = None

        old_pal = dict(THEME)
        new_pal = dict(THEMES[theme_id])
        changed = (old_pal.get("id") != theme_id)

        self.current_theme = theme_id
        db.set_setting("theme", theme_id)
        THEME.update(new_pal)

        # Dynamically update the OS window title bar to match active theme
        self._apply_window_titlebar_theme(theme_id)

        # Apply root & top container backgrounds
        self.root.configure(bg=THEME["bg"])
        self.main_frame.configure(bg=THEME["bg"])
        self.content_frame.configure(bg=THEME["bg"])

        # Rebuild header & nav with new theme styling
        self._build_header()
        self._build_nav()

        # Re-render active view cleanly
        if self.current_view == "timer":
            self._show_timer_view()
        elif self.current_view == "forest":
            self._show_forest_view()
        elif self.current_view == "stats":
            self._show_stats_view()
        elif self.current_view == "achievements":
            self._show_achievements_view()

        # Run smooth color interpolation (~350ms across 7 frames)
        if changed:
            targets = self._collect_theme_transition_targets(old_pal, new_pal)
            if targets:
                for w, attr, old_h, _ in targets:
                    try:
                        if w.winfo_exists():
                            w.configure(**{attr: old_h})
                    except tk.TclError:
                        pass
                self._theme_anim_after = self.root.after(
                    45, lambda t=targets: self._animate_theme_transition(t, 1, 7)
                )

    def _toggle_rain_sound(self):
        """Toggle built-in ambient rain sound."""
        is_playing = audio_player.player.toggle()
        vw, _ = self._get_viewport_size()
        is_tight = (vw < 890)
        rain_txt = ("🌧️ ON" if is_playing else "🌧️ OFF") if is_tight else ("🌧️ Rain: ON" if is_playing else "🌧️ Rain: OFF")
        if is_playing:
            self.rain_btn.configure(
                text=rain_txt,
                bg="#E1F5FE", fg="#0277BD",
                highlightbackground="#81D4FA"
            )
        else:
            self.rain_btn.configure(
                text=rain_txt,
                bg=THEME["bg_dark"], fg=THEME["fg_muted"],
                highlightbackground=THEME["border"]
            )
        # Toggle rain visual particles in-place without rebuilding static scenery
        try:
            if self.current_view == "timer":
                if (self._study_scene and self._study_actors
                        and hasattr(self, "tree_canvas") and self.tree_canvas.winfo_exists()):
                    scenery.remove_rain(self.tree_canvas, self._study_actors)
                    if is_playing:
                        scenery.add_rain(self.tree_canvas, self._study_scene, self._study_actors)
                else:
                    self._redraw_tree()
            elif self.current_view == "forest":
                if (self._forest_scene and self._forest_actors
                        and hasattr(self, "forest_canvas") and self.forest_canvas.winfo_exists()):
                    scenery.remove_rain(self.forest_canvas, self._forest_actors)
                    if is_playing:
                        scenery.add_rain(self.forest_canvas, self._forest_scene, self._forest_actors)
                else:
                    self._draw_forest()
        except tk.TclError:
            pass

    def _change_rain_volume(self, delta):
        """Change rain sound volume."""
        new_vol = max(0, min(100, audio_player.player.volume + delta))
        audio_player.player.set_volume(new_vol)
        self.vol_label.configure(text=f"{new_vol}%")

    def _on_close(self):
        """Clean shutdown when closing window."""
        try:
            audio_player.player.stop()
        except Exception:
            pass
        self.root.destroy()

    def _build_nav(self):
        for w in self.nav_frame.winfo_children():
            w.destroy()
        mode = self._get_responsive_mode()
        nav_h = 48 if mode == "compact" else 54
        nav_padx = 14 if mode == "compact" else (18 if mode == "laptop" else 22)
        nav_pady = 8 if mode == "compact" else 10
        self.nav_frame.configure(bg=THEME["bg_sidebar"], height=nav_h)

        # Separator line
        tk.Frame(self.nav_frame, bg=THEME["border"], height=1).pack(fill="x")

        btn_frame = tk.Frame(self.nav_frame, bg=THEME["bg_sidebar"])
        btn_frame.pack(expand=True)

        self.nav_buttons = {}
        nav_items = [
            ("timer", "🌱 Study", self._show_timer_view),
            ("forest", "🌲 My Forest", self._show_forest_view),
            ("stats", "📊 Statistics", self._show_stats_view),
            ("achievements", "🏆 Achievements", self._show_achievements_view),
        ]

        for key, label, cmd in nav_items:
            is_cur = (key == self.current_view)
            btn = tk.Label(
                btn_frame, text=label,
                font=self.font_nav, bg=THEME["bg_sidebar"],
                fg=THEME["nav_active"] if is_cur else THEME["nav_inactive"],
                cursor="hand2", padx=nav_padx, pady=nav_pady
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key, c=cmd: self._nav_click(k, c))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=THEME["accent"]))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.configure(
                fg=THEME["nav_active"] if k == self.current_view else THEME["nav_inactive"]
            ))
            self.nav_buttons[key] = btn

    def _nav_click(self, key, cmd):
        self.current_view = key
        for k, btn in self.nav_buttons.items():
            btn.configure(fg=THEME["nav_active"] if k == key else THEME["nav_inactive"])
        cmd()

    def _clear_content(self):
        if self._daily_countdown_after is not None:
            try:
                self.root.after_cancel(self._daily_countdown_after)
            except tk.TclError:
                pass
            self._daily_countdown_after = None
        if self._claim_pulse_after is not None:
            try:
                self.root.after_cancel(self._claim_pulse_after)
            except tk.TclError:
                pass
            self._claim_pulse_after = None
        self._claim_pulse_buttons = []
        self._close_species_dropdown()
        self._close_task_popover()
        self._hide_task_tooltip()
        self._hide_stats_tooltip()
        self._dismiss_forest_popup()
        self._dismiss_session_complete_modal()
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _draw_species_icon(self, cv, sp_id, cx, cy, is_active):
        """Draw a centered 14x14 botanical emblem aligned cleanly inside a pill button."""
        trunk = "#F3E5D8" if is_active else "#7A5942"
        if sp_id == "cherry_blossom":
            petal = "#FFE8EF" if is_active else "#EC88A4"
            center = "#FFE38E"
            for k in range(5):
                ang = -math.pi / 2.0 + k * (2.0 * math.pi / 5.0)
                px = cx + 3.6 * math.cos(ang)
                py = cy + 3.6 * math.sin(ang)
                cv.create_oval(px - 2.6, py - 2.6, px + 2.6, py + 2.6,
                               fill=petal, outline="", tags=("species_icon",))
            cv.create_oval(cx - 2.0, cy - 2.0, cx + 2.0, cy + 2.0,
                           fill=center, outline="", tags=("species_icon",))
        elif sp_id == "pine":
            fol = "#FFFFFF" if is_active else "#3C8A5C"
            cv.create_rectangle(cx - 1.2, cy + 3.0, cx + 1.2, cy + 6.5,
                                fill=trunk, outline="", tags=("species_icon",))
            for y_top, hw, h_t in ((cy - 6.8, 3.6, 4.6), (cy - 3.6, 5.0, 5.0), (cy - 0.5, 6.2, 5.2)):
                cv.create_polygon(cx, y_top, cx + hw, y_top + h_t, cx - hw, y_top + h_t,
                                  fill=fol, outline="", tags=("species_icon",))
        elif sp_id == "angel_oak":
            fol = "#FFFFFF" if is_active else "#5E9C58"
            moss = "#E2F2D5" if is_active else "#8FC17D"
            cv.create_rectangle(cx - 1.5, cy + 2.0, cx + 1.5, cy + 6.5,
                                fill=trunk, outline="", tags=("species_icon",))
            cv.create_oval(cx - 6.6, cy - 4.2, cx + 6.6, cy + 2.8,
                           fill=fol, outline="", tags=("species_icon",))
            cv.create_oval(cx - 4.5, cy - 6.2, cx + 4.5, cy + 0.5,
                           fill=fol, outline="", tags=("species_icon",))
            for mx in (cx - 4.5, cx + 4.2):
                cv.create_line(mx, cy + 1.2, mx, cy + 4.8,
                               fill=moss, width=1.4, tags=("species_icon",))
        elif sp_id == "all":
            fol = "#FFFFFF" if is_active else THEME["accent"]
            fol2 = "#DDF2E3" if is_active else THEME["green_light"]
            cv.create_polygon(cx - 2.5, cy - 5.5, cx + 2.0, cy + 4.0, cx - 6.5, cy + 4.0,
                              fill=fol, outline="", tags=("species_icon",))
            cv.create_polygon(cx + 2.8, cy - 4.2, cx + 6.6, cy + 4.5, cx - 1.2, cy + 4.5,
                              fill=fol2, outline="", tags=("species_icon",))
            cv.create_rectangle(cx - 3.2, cy + 4.0, cx - 1.8, cy + 6.5,
                                fill=trunk, outline="", tags=("species_icon",))
            cv.create_rectangle(cx + 2.1, cy + 4.5, cx + 3.5, cy + 6.5,
                                fill=trunk, outline="", tags=("species_icon",))
        else:  # classic oak
            fol = "#FFFFFF" if is_active else "#4A8C56"
            cv.create_rectangle(cx - 1.5, cy + 2.0, cx + 1.5, cy + 6.5,
                                fill=trunk, outline="", tags=("species_icon",))
            cv.create_oval(cx - 5.8, cy - 3.0, cx + 0.8, cy + 3.2,
                           fill=fol, outline="", tags=("species_icon",))
            cv.create_oval(cx - 0.8, cy - 3.0, cx + 5.8, cy + 3.2,
                           fill=fol, outline="", tags=("species_icon",))
            cv.create_oval(cx - 4.5, cy - 6.2, cx + 4.5, cy + 1.5,
                           fill=fol, outline="", tags=("species_icon",))

    def _make_species_pill(self, parent, sp_id, label_text, is_active, active_bg, command, enabled=True):
        """Build a fixed-34px-height selector pill with centered icon + gap + label."""
        mode = self._get_responsive_mode()
        btn_h = 34
        pad_x = 8 if mode == "compact" else (10 if mode == "laptop" else 12)
        icon_w = 14
        gap = 5 if mode == "compact" else 6
        text_px = self._species_pill_font.measure(label_text)
        btn_w = pad_x + icon_w + gap + text_px + pad_x

        base_bg = active_bg if is_active else THEME["bg_dark"]
        border_col = active_bg if is_active else THEME["border"]
        fg_col = THEME.get("accent_fg", "#FFFFFF") if is_active else THEME["fg"]

        cv = tk.Canvas(
            parent, width=btn_w, height=btn_h, bg=THEME["bg"],
            bd=0, highlightthickness=0, relief="flat",
            cursor="hand2" if enabled else "arrow",
        )
        pill_id = cv.create_polygon(
            _rounded_rect_pts(1, 1, btn_w - 2, btn_h - 2, 9),
            fill=base_bg, outline=border_col, width=1, tags=("species_pill_bg",),
        )
        self._draw_species_icon(cv, sp_id, pad_x + icon_w * 0.5, btn_h * 0.5, is_active)
        cv.create_text(
            pad_x + icon_w + gap, btn_h * 0.5,
            text=label_text, font=self.font_small_bold,
            fill=fg_col, anchor="w", tags=("species_pill_text",),
        )
        if enabled:
            hover_bg = scenery.mix(base_bg, THEME["fg"] if not is_active else "#000000", 0.09)
            cv.bind("<Button-1>", lambda e: command())
            cv.bind("<Enter>", lambda e: cv.itemconfigure(pill_id, fill=hover_bg))
            cv.bind("<Leave>", lambda e: cv.itemconfigure(pill_id, fill=base_bg))
        return cv

    # ──────────────── Timer View ────────────────

    def _show_timer_view(self):
        self.current_view = "timer"
        self._clear_content()

        mode = self._get_responsive_mode()
        _, vh = self._get_viewport_size()
        is_compact = (mode == "compact")
        is_laptop = (mode == "laptop")
        is_short = (vh < 690)

        sidebar_w = 268 if is_compact else (292 if is_laptop else 310)
        col_gap = 8 if is_compact else 10
        inner_padx = 14 if is_compact else (16 if is_laptop else 20)
        inner_pady = 10 if (is_compact or is_short) else 15
        timer_pt = 36 if (is_compact or is_short) else (40 if is_laptop else 44)
        pill_gap = 4 if is_compact else 6

        # Two-column layout: tree canvas left, timer right
        container = tk.Frame(self.content_frame, bg=THEME["bg"])
        container.pack(fill="both", expand=True)

        # Left: Tree canvas & Species Selector
        left = tk.Frame(container, bg=THEME["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, col_gap))

        # Species Selector Bar (fixed 34px height for clean inline alignment)
        spec_bar = tk.Frame(left, bg=THEME["bg"], height=34)
        spec_bar.pack(fill="x", pady=(0, 6))
        spec_bar.pack_propagate(False)

        tk.Label(
            spec_bar, text="Tree:",
            font=self.font_small, fg=THEME["fg_muted"], bg=THEME["bg"]
        ).pack(side="left", padx=(0, 5 if is_compact else 8))

        species_order = [
            "cherry_blossom", "pine", "angel_oak", "oak",
            "willow", "maple", "moonlit_blossom",
        ]
        if not db.is_species_unlocked(self.selected_species):
            self.selected_species = "oak"

        self.species_buttons = {}
        curr_meta = SPECIES_METADATA.get(self.selected_species, SPECIES_METADATA["oak"])
        seed_inv = db.get_seed_inventory()
        sp_seeds = seed_inv.get(self.selected_species, 0)
        rarity = curr_meta.get("rarity", "Common")
        seed_part = f"  •  🌱{sp_seeds}" if sp_seeds > 0 else ""
        drop_text = f"{curr_meta['icon']} {curr_meta['name']}  •  {rarity}{seed_part}   ▾"

        is_dark = self.current_theme in ("night", "chill")
        drop_bg = THEME["bg_card"]
        drop_fg = THEME["fg"]
        drop_border = curr_meta.get("theme_color", THEME["border"])

        self.species_dropdown_btn = tk.Label(
            spec_bar, text=drop_text,
            font=self.font_small_bold,
            bg=drop_bg, fg=drop_fg,
            padx=12, pady=4,
            cursor="hand2" if not self.session_active else "",
            highlightbackground=drop_border, highlightthickness=1,
        )
        self.species_dropdown_btn.pack(side="left")
        if not self.session_active:
            self.species_dropdown_btn.bind("<Button-1>", lambda e: self._toggle_species_dropdown())
            self.species_dropdown_btn.bind(
                "<Enter>", lambda e: self.species_dropdown_btn.configure(bg=THEME["bg_dark"])
            )
            self.species_dropdown_btn.bind(
                "<Leave>", lambda e: self.species_dropdown_btn.configure(bg=drop_bg)
            )
        else:
            self.species_dropdown_btn.configure(fg=THEME["fg_muted"])

        # Species tagline (automatically hidden below 680px bar width so it never overlaps pills)
        curr_meta = SPECIES_METADATA.get(self.selected_species, {})
        self.species_tagline_label = tk.Label(
            spec_bar, text=curr_meta.get("tagline", ""),
            font=self.font_xs_italic, fg=THEME["fg_light"], bg=THEME["bg"]
        )

        def _sync_tagline_visibility(event=None):
            try:
                bar_w = event.width if event else spec_bar.winfo_width()
                if bar_w >= 680:
                    if not self.species_tagline_label.winfo_manager():
                        self.species_tagline_label.pack(side="right", padx=(4, 0))
                elif bar_w > 10:
                    if self.species_tagline_label.winfo_manager():
                        self.species_tagline_label.pack_forget()
            except tk.TclError:
                pass

        spec_bar.bind("<Configure>", _sync_tagline_visibility)
        if not is_compact:
            self.species_tagline_label.pack(side="right", padx=(4, 0))

        self._study_scene = None
        self._study_actors = None
        self._study_resize_after = None
        self._last_study_size = (0, 0)
        sky_bg = scenery.palette(self.current_theme)["sky"][0]
        self.tree_canvas = tk.Canvas(
            left, bg=sky_bg, highlightthickness=0,
            relief="flat"
        )
        self.tree_canvas.pack(fill="both", expand=True, pady=(2, 0))
        self.tree_canvas.bind("<Configure>", self._on_study_canvas_configure)

        # Stage label below canvas
        stage = db.get_tree_stage(self.focused_seconds) if self.session_active else "seed"
        spec_display = f"{curr_meta.get('icon', '')} {curr_meta.get('name', 'Tree')}"
        self.stage_label = tk.Label(
            left, text=f"{STAGE_LABELS.get(stage, '🌱 Seed')}  •  {spec_display}",
            font=self.font_stage, fg=THEME["green_med"], bg=THEME["bg"]
        )
        self.stage_label.pack(pady=(5, 0))

        # Right: Timer panel (responsive width/spacing for compact & laptop viewports)
        right = tk.Frame(container, bg=THEME["bg_card"], width=sidebar_w, relief="flat",
                         highlightbackground=THEME["border"], highlightthickness=1)
        right.pack(side="right", fill="y", padx=(col_gap, 0), pady=(4, 0))
        right.pack_propagate(False)
        right.configure(width=sidebar_w)

        inner = tk.Frame(right, bg=THEME["bg_card"])
        inner.pack(expand=True, fill="both", padx=inner_padx, pady=inner_pady)

        # ── Task List with Tree Assignment Section ──
        task_sec = tk.Frame(inner, bg=THEME["bg_card"])
        task_sec.pack(fill="x", pady=(0, 8 if (is_compact or is_short) else 12))

        tk.Label(
            task_sec, text="🎯 Current Task / Subject",
            font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 4))

        if not self.session_active:
            self._task_placeholder = "Add a task..."
            input_row = tk.Frame(task_sec, bg=THEME["bg_card"])
            input_row.pack(fill="x", pady=(0, 5))
            input_row.columnconfigure(0, weight=1, minsize=0)
            input_row.columnconfigure(1, weight=0)
            input_row.columnconfigure(2, weight=0)
            input_row.rowconfigure(0, minsize=34)

            entry_frame = tk.Frame(
                input_row, bg=THEME["bg_dark"], padx=8, pady=4,
                highlightbackground=THEME["border"], highlightthickness=1
            )
            entry_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            self.task_entry = tk.Entry(
                entry_frame, font=self.font_small, width=1,
                relief="flat", bg=THEME["bg_dark"], fg=THEME["fg_light"],
                insertbackground=THEME["fg"]
            )
            self.task_entry.insert(0, self._task_placeholder)
            self.task_entry._is_placeholder = True
            self.task_entry.pack(fill="both", expand=True)
            self.task_entry.bind("<FocusIn>", self._on_task_entry_focus_in)
            self.task_entry.bind("<FocusOut>", self._on_task_entry_focus_out)
            self.task_entry.bind("<KeyRelease>", self._on_task_entry_change)
            self.task_entry.bind("<Return>", lambda e: self._add_task_from_entry())

            draft_meta = SPECIES_METADATA.get(self.task_draft_species, SPECIES_METADATA["oak"])
            self.draft_species_btn = tk.Label(
                input_row, text=f"{draft_meta['icon']} ▾",
                font=self.font_small, bg=THEME["bg_dark"], fg=THEME["fg"],
                padx=10, pady=0, cursor="hand2", anchor="center",
                highlightbackground=THEME["border"], highlightthickness=1
            )
            self.draft_species_btn.grid(row=0, column=1, sticky="ns", padx=(0, 6))
            self.draft_species_btn.bind(
                "<Button-1>",
                lambda e, w=self.draft_species_btn: self._open_species_popover(
                    w, self.task_draft_species, self._set_draft_species
                )
            )

            add_task_btn = tk.Label(
                input_row, text="Add", font=self.font_xs_bold,
                bg=THEME["accent"], fg=THEME.get("accent_fg", "#FFFFFF"),
                padx=10, pady=0, cursor="hand2", anchor="center"
            )
            add_task_btn.grid(row=0, column=2, sticky="ns")
            add_task_btn.bind("<Button-1>", lambda e: self._add_task_from_entry())

            # Quick presets (category prefixes / quick-fill helpers)
            presets_frame = tk.Frame(task_sec, bg=THEME["bg_card"])
            presets_frame.pack(fill="x", pady=(0, 5))
            presets = [
                ("📚 Study", "Study"),
                ("💻 Code", "Coding"),
                ("✍️ Write", "Writing"),
                ("🔬 Science", "Science"),
                ("🎨 Art", "Creative"),
            ]
            row_frames = {}
            for idx, (label, val) in enumerate(presets):
                row_idx = idx // 3
                if row_idx not in row_frames:
                    rf = tk.Frame(presets_frame, bg=THEME["bg_card"])
                    rf.pack(fill="x", pady=(0, 3))
                    row_frames[row_idx] = rf
                is_sel = (self.current_task == val or self.current_task.startswith(f"{val}:"))
                btn = tk.Label(
                    row_frames[row_idx], text=label, font=self.font_xs,
                    bg=THEME["accent_light"] if is_sel else THEME["bg_dark"],
                    fg=THEME["green_dark"] if is_sel else THEME["fg"],
                    padx=5 if is_compact else 6, pady=2, cursor="hand2", relief="flat"
                )
                btn.pack(side="left", padx=(0, 4))
                btn.bind("<Button-1>", lambda e, v=val: self._set_task_preset(v))

            # Scrollable Task List (capped height so timer & Start Studying stay centered)
            self._build_task_list_widget(task_sec, is_compact, is_short)
        else:
            # When studying, display badge
            badge_frame = tk.Frame(task_sec, bg=THEME["accent_light"], padx=8, pady=5,
                                   highlightbackground=THEME["accent"], highlightthickness=1)
            badge_frame.pack(fill="x")
            tk.Label(
                badge_frame, text=f"🎯 Growing for: {self.current_task}",
                font=self.font_small_bold, fg=THEME["green_dark"], bg=THEME["accent_light"]
            ).pack(anchor="w")

        # Duration selector
        tk.Label(
            inner, text="Session Duration",
            font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 5 if (is_compact or is_short) else 8))

        dur_frame = tk.Frame(inner, bg=THEME["bg_card"])
        dur_frame.pack(fill="x", pady=(0, 10 if (is_compact or is_short) else 20))

        self.duration_buttons = []
        durations = [25, 45, 60, 90]
        for mins in durations:
            is_selected = (self.planned_duration == mins * 60)
            btn = tk.Label(
                dur_frame, text=f"{mins}m",
                font=self.font_small,
                bg=THEME["accent"] if is_selected else THEME["bg_dark"],
                fg=THEME.get("accent_fg", "#FFFFFF") if is_selected else THEME["fg"],
                padx=8 if is_compact else 10, pady=4 if (is_compact or is_short) else 5,
                cursor="hand2", relief="flat"
            )
            btn.pack(side="left", padx=(0, 5 if is_compact else 6))
            btn.bind("<Button-1>", lambda e, m=mins: self._set_duration(m))
            self.duration_buttons.append((btn, mins))

        # Custom duration
        custom_frame = tk.Frame(inner, bg=THEME["bg_card"])
        custom_frame.pack(fill="x", pady=(0, 12 if (is_compact or is_short) else 22))
        tk.Label(
            custom_frame, text="Custom (min):",
            font=self.font_small, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(side="left")
        self.custom_entry = tk.Entry(
            custom_frame, width=5, font=self.font_small,
            relief="flat", bg=THEME["bg_dark"], fg=THEME["fg"],
            insertbackground=THEME["fg"]
        )
        self.custom_entry.pack(side="left", padx=(5, 5))
        self.custom_entry.bind("<Return>", self._set_custom_duration)
        custom_btn = tk.Label(
            custom_frame, text="Set", font=self.font_small,
            fg=THEME["accent"], bg=THEME["bg_card"], cursor="hand2"
        )
        custom_btn.pack(side="left")
        custom_btn.bind("<Button-1>", self._set_custom_duration)

        # Optional Active Quest Banner when launched from a Daily Challenge
        if self.active_quest:
            aq_bg = scenery.mix(THEME["bg_card"], THEME["accent"], 0.14)
            aq_pill = tk.Frame(
                inner, bg=aq_bg,
                highlightbackground=THEME["accent"], highlightthickness=1
            )
            aq_pill.pack(fill="x", pady=(0, 6))
            self.active_quest_banner = aq_pill

            aq_txt = f"🎯 Active Quest: {self.active_quest['title']} ({self.active_quest['duration']}m)"
            tk.Label(
                aq_pill, text=aq_txt, font=self.font_xs_bold,
                fg=THEME["fg"], bg=aq_bg, anchor="w", padx=8, pady=4
            ).pack(side="left", fill="x", expand=True)

            aq_close = tk.Label(
                aq_pill, text="×", font=self.font_small_bold,
                fg=THEME["fg_muted"], bg=aq_bg, padx=7, pady=2, cursor="hand2"
            )
            aq_close.pack(side="right")
            aq_close.bind("<Button-1>", lambda e: self._dismiss_active_quest())
        else:
            self.active_quest_banner = None

        # Timer display (scales down cleanly for HH:MM:SS >= 60m & stays centered)
        timer_frame = tk.Frame(inner, bg=THEME["bg_card"])
        timer_frame.pack(fill="x", pady=(0, 4))

        self._timer_base_pt = timer_pt
        self._timer_avail_w = max(160, sidebar_w - 2 * inner_padx - 12)
        self._last_timer_font_pt = None

        remaining = self.planned_duration - self.focused_seconds
        if remaining < 0:
            remaining = 0
        timer_str = self._format_time(int(remaining))
        t_font = self._get_timer_font(timer_str)
        self._last_timer_font_pt = t_font[1]
        self.timer_display = tk.Label(
            timer_frame, text=timer_str,
            font=t_font, fg=THEME["fg"], bg=THEME["bg_card"],
            anchor="center", justify="center"
        )
        self.timer_display.pack(fill="x", padx=4)

        # Progress info
        info_frame = tk.Frame(inner, bg=THEME["bg_card"])
        info_frame.pack(fill="x", pady=(0, 8 if (is_compact or is_short) else 14))

        self.elapsed_label = tk.Label(
            info_frame, text=f"Focused: {self._format_time(int(self.focused_seconds))}",
            font=self.font_timer_label, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        )
        self.elapsed_label.pack()

        # Progress bar
        bar_frame = tk.Frame(inner, bg=THEME["bar_bg"], height=8)
        bar_frame.pack(fill="x", pady=(0, 12 if (is_compact or is_short) else 20))
        bar_frame.pack_propagate(False)

        progress = min(1.0, self.focused_seconds / max(1, self.planned_duration))
        self.progress_bar = tk.Frame(bar_frame, bg=THEME["accent"], height=8)
        self.progress_bar.place(relx=0, rely=0, relwidth=progress, relheight=1)

        # Control buttons
        btn_frame = tk.Frame(inner, bg=THEME["bg_card"])
        btn_frame.pack(fill="x", pady=(0, 6 if (is_compact or is_short) else 10))

        if not self.session_active:
            self._make_button(btn_frame, "▶  Start Studying", self._start_session,
                              THEME["accent"], THEME.get("accent_fg", "#FFFFFF")).pack(fill="x", ipady=8 if (is_compact or is_short) else 10)
        elif self.timer_paused:
            bf = tk.Frame(btn_frame, bg=THEME["bg_card"])
            bf.pack(fill="x")
            self._make_button(bf, "▶  Resume", self._resume_session,
                              THEME["accent"], THEME.get("accent_fg", "#FFFFFF")).pack(side="left", expand=True, fill="x", ipady=7 if is_compact else 8, padx=(0, 4))
            self._make_button(bf, "⏹  Stop", self._stop_session,
                              THEME["red_soft"], "white").pack(side="left", expand=True, fill="x", ipady=7 if is_compact else 8, padx=(4, 0))
        else:
            bf = tk.Frame(btn_frame, bg=THEME["bg_card"])
            bf.pack(fill="x")
            self._make_button(bf, "⏸  Pause", self._pause_session,
                              THEME["yellow_soft"], "white").pack(side="left", expand=True, fill="x", ipady=7 if is_compact else 8, padx=(0, 4))
            self._make_button(bf, "⏹  Stop", self._stop_session,
                              THEME["red_soft"], "white").pack(side="left", expand=True, fill="x", ipady=7 if is_compact else 8, padx=(4, 0))

        # Reset button (only if session active)
        if self.session_active:
            reset = tk.Label(
                inner, text="Reset Session", font=self.font_small,
                fg=THEME["fg_light"], bg=THEME["bg_card"], cursor="hand2"
            )
            reset.pack(pady=(4, 0))
            reset.bind("<Button-1>", lambda e: self._reset_session())

        # Bottom stats row
        stats_frame = tk.Frame(inner, bg=THEME["bg_card"])
        stats_frame.pack(fill="x", side="bottom", pady=(8 if (is_compact or is_short) else 14, 0))

        # Separator
        tk.Frame(stats_frame, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 8 if (is_compact or is_short) else 10))

        row = tk.Frame(stats_frame, bg=THEME["bg_card"])
        row.pack(fill="x")

        today_secs = db.get_today_seconds()
        total_trees = db.get_total_trees()

        for label_text, value_text in [
            ("Today", self._format_hours(today_secs)),
            ("Trees", str(total_trees)),
            ("Total", self._format_hours(db.get_total_focused_seconds())),
        ]:
            col = tk.Frame(row, bg=THEME["bg_card"])
            col.pack(side="left", expand=True)
            tk.Label(
                col, text=value_text, font=self.font_stat_inline,
                fg=THEME["green_dark"], bg=THEME["bg_card"]
            ).pack()
            tk.Label(
                col, text=label_text, font=self.font_small,
                fg=THEME["fg_muted"], bg=THEME["bg_card"]
            ).pack()

        # Draw tree after canvas is rendered
        self.root.after(50, self._redraw_tree)

    def _make_button(self, parent, text, command, bg, fg=None):
        if fg is None:
            fg = THEME.get("accent_fg", "#FFFFFF") if bg == THEME.get("accent") else "#FFFFFF"
        btn = tk.Label(
            parent, text=text, font=self.font_button,
            bg=bg, fg=fg, cursor="hand2", relief="flat", padx=15
        )
        btn.bind("<Button-1>", lambda e: command())

        orig_bg = bg
        hover_bg = THEME.get("accent_hover") if bg == THEME.get("accent") and "accent_hover" in THEME else self._darken(bg, 0.1)
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=orig_bg))
        return btn

    def _make_secondary_button(self, parent, text, command):
        """Subtle bordered secondary action button matching the active theme."""
        base_bg = THEME["bg_card"]
        hover_bg = THEME["bg_dark"]
        base_border = THEME["border"]
        hover_border = THEME["accent"]
        btn = tk.Label(
            parent, text=text, font=self.font_small_bold,
            bg=base_bg, fg=THEME["fg"],
            cursor="hand2", relief="flat", padx=12, pady=6,
            highlightbackground=base_border, highlightthickness=1,
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg, highlightbackground=hover_border))
        btn.bind("<Leave>", lambda e: btn.configure(bg=base_bg, highlightbackground=base_border))
        return btn

    def _darken(self, hex_color, factor):
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ──────────────── Task List & Tree Assignment Logic ────────────────

    def _on_task_entry_focus_in(self, event=None):
        if hasattr(self, "task_entry") and getattr(self.task_entry, "_is_placeholder", False):
            self.task_entry.delete(0, "end")
            self.task_entry.configure(fg=THEME["fg"])
            self.task_entry._is_placeholder = False

    def _on_task_entry_focus_out(self, event=None):
        if hasattr(self, "task_entry") and not self.task_entry.get().strip():
            self.task_entry.delete(0, "end")
            self.task_entry.insert(0, self._task_placeholder)
            self.task_entry.configure(fg=THEME["fg_light"])
            self.task_entry._is_placeholder = True

    def _on_task_entry_change(self, event=None):
        if hasattr(self, "task_entry") and not getattr(self.task_entry, "_is_placeholder", False):
            val = self.task_entry.get().strip()
            if val:
                self.current_task = val
            elif self.active_task_id is None:
                self.current_task = "General Study"

    def _set_draft_species(self, species_id):
        self.task_draft_species = species_id
        if hasattr(self, "draft_species_btn") and self.draft_species_btn.winfo_exists():
            meta = SPECIES_METADATA.get(species_id, SPECIES_METADATA["oak"])
            self.draft_species_btn.configure(text=f"{meta['icon']} ▾")

    def _close_task_popover(self):
        if self._task_popover is not None:
            try:
                if self._task_popover.winfo_exists():
                    self._task_popover.destroy()
            except Exception:
                pass
            self._task_popover = None

    def _open_species_popover(self, anchor_widget, current_species, on_select):
        """Open a compact themed tree-species picker popover anchored to a button/badge."""
        self._close_task_popover()
        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.configure(bg=THEME["border"], padx=1, pady=1)
        try:
            pop.attributes("-topmost", True)
        except Exception:
            pass

        inner = tk.Frame(pop, bg=THEME["bg_card"], padx=4, pady=4)
        inner.pack(fill="both", expand=True)

        unlocked_list = [
            sp_id for sp_id in (
                "cherry_blossom", "pine", "angel_oak", "oak",
                "willow", "maple", "moonlit_blossom",
            )
            if db.is_species_unlocked(sp_id)
        ]
        for sp_id in unlocked_list:
            meta = SPECIES_METADATA[sp_id]
            is_sel = (sp_id == current_species)
            row_bg = THEME["accent_light"] if is_sel else THEME["bg_card"]
            row_fg = THEME["green_dark"] if is_sel else THEME["fg"]
            lbl = tk.Label(
                inner, text=f"{meta['icon']}  {meta['name']}",
                font=self.font_xs_bold if is_sel else self.font_xs,
                bg=row_bg, fg=row_fg, anchor="w", padx=8, pady=4, cursor="hand2"
            )
            lbl.pack(fill="x", pady=1)
            lbl.bind("<Enter>", lambda e, w=lbl, sel=is_sel: w.configure(
                bg=THEME["accent_light"] if sel else THEME["bg_dark"]
            ))
            lbl.bind("<Leave>", lambda e, w=lbl, rb=row_bg: w.configure(bg=rb))
            lbl.bind("<Button-1>", lambda e, sid=sp_id: (self._close_task_popover(), on_select(sid)))

        pop.update_idletasks()
        ax = anchor_widget.winfo_rootx()
        ay = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 3
        pw = pop.winfo_reqwidth()
        ph = pop.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if ax + pw > sw - 12:
            ax = max(12, sw - pw - 12)
        if ay + ph > sh - 12:
            ay = max(12, anchor_widget.winfo_rooty() - ph - 3)
        pop.geometry(f"+{ax}+{ay}")

        pop.bind("<FocusOut>", lambda e: self.root.after(80, self._close_task_popover))
        pop.bind("<Escape>", lambda e: self._close_task_popover())
        pop.focus_set()
        self._task_popover = pop

    def _add_task_from_entry(self):
        if not hasattr(self, "task_entry"):
            return
        if getattr(self.task_entry, "_is_placeholder", False):
            return
        title = self.task_entry.get().strip()
        if not title:
            return
        new_task = db.add_task(title, self.task_draft_species)
        if new_task:
            self.active_task_id = new_task["id"]
            db.set_setting("active_task_id", str(new_task["id"]))
            self.current_task = new_task["title"]
            self.selected_species = new_task["tree_species"]
        self._show_timer_view()

    def _set_task_preset(self, task_val):
        """Use quick-subject tags as category prefixes or quick-fill helpers."""
        if hasattr(self, "task_entry") and self.task_entry.winfo_exists():
            is_ph = getattr(self.task_entry, "_is_placeholder", False)
            raw = "" if is_ph else self.task_entry.get().strip()
            known_prefixes = ("Study:", "Coding:", "Writing:", "Science:", "Creative:")
            if not raw:
                self._on_task_entry_focus_in()
                self.task_entry.insert(0, f"{task_val}: ")
                self.task_entry.icursor("end")
                self.task_entry.focus_set()
                self.current_task = task_val
                return
            replaced = False
            for kp in known_prefixes:
                if raw.startswith(kp):
                    rest = raw[len(kp):].lstrip()
                    new_text = f"{task_val}: {rest}" if rest else f"{task_val}: "
                    self.task_entry.delete(0, "end")
                    self.task_entry.insert(0, new_text)
                    self.task_entry.icursor("end")
                    self.task_entry.focus_set()
                    self.current_task = new_text.strip().rstrip(":") or task_val
                    replaced = True
                    break
            if not replaced:
                new_text = f"{task_val}: {raw}"
                self.task_entry.delete(0, "end")
                self.task_entry.insert(0, new_text)
                self.task_entry.icursor("end")
                self.task_entry.focus_set()
                self.current_task = new_text
                return
        else:
            self.current_task = task_val
            self._show_timer_view()

    def _activate_task(self, task_id):
        """Click-to-focus: highlight task, set session label, and sync tree species."""
        if self.session_active:
            return
        task = db.get_task_by_id(task_id)
        if not task:
            return
        self.active_task_id = task["id"]
        db.set_setting("active_task_id", str(task["id"]))
        self.current_task = task["title"]
        self.selected_species = task["tree_species"]
        self._show_timer_view()

    def _change_task_species(self, task_id, species_id):
        updated = db.update_task_species(task_id, species_id)
        if updated and self.active_task_id == task_id:
            self.selected_species = updated["tree_species"]
        self._show_timer_view()

    def _toggle_task_item(self, task_id, text_label=None, check_label=None):
        """Toggle completion with a smooth strikethrough animation when checking off."""
        task = db.get_task_by_id(task_id)
        if not task:
            return
        if not task["completed"] and text_label is not None and text_label.winfo_exists():
            # Smooth strikethrough & dim animation (~180ms across 4 steps)
            try:
                if check_label is not None and check_label.winfo_exists():
                    check_label.configure(text="☑", fg=THEME["accent"])
                text_label.configure(font=self.font_small_strike)
            except tk.TclError:
                pass

            def _anim_step(step):
                if step >= 4:
                    db.set_task_completed(task_id, True)
                    db.record_daily_challenge_task_completed(1)
                    if self.active_task_id == task_id:
                        self.active_task_id = None
                        db.set_setting("active_task_id", "")
                    self._show_timer_view()
                    return
                try:
                    if text_label.winfo_exists():
                        col = self._lerp_hex(THEME["fg"], THEME["fg_light"], step / 3.0)
                        text_label.configure(fg=col)
                except tk.TclError:
                    pass
                self.root.after(45, lambda s=step + 1: _anim_step(s))

            self.root.after(30, lambda: _anim_step(1))
        else:
            new_state = db.toggle_task_completed(task_id)
            if new_state:
                db.record_daily_challenge_task_completed(1)
            self._show_timer_view()

    def _delete_task_item(self, task_id):
        db.delete_task(task_id)
        if self.active_task_id == task_id:
            self.active_task_id = None
            db.set_setting("active_task_id", "")
            self.current_task = "General Study"
        self._show_timer_view()

    def _hide_task_tooltip(self):
        if self._task_tooltip is not None:
            try:
                if self._task_tooltip.winfo_exists():
                    self._task_tooltip.destroy()
            except Exception:
                pass
            self._task_tooltip = None

    def _show_task_tooltip(self, widget, full_text):
        self._hide_task_tooltip()
        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tip.configure(bg=THEME["border"], padx=1, pady=1)
        try:
            tip.attributes("-topmost", True)
        except Exception:
            pass
        lbl = tk.Label(
            tip, text=full_text, font=self.font_xs,
            bg=THEME["bg_card"], fg=THEME["fg"], padx=7, pady=3, wraplength=240, justify="left"
        )
        lbl.pack()
        tip.update_idletasks()
        x = widget.winfo_rootx() + 6
        y = widget.winfo_rooty() - tip.winfo_reqheight() - 4
        if y < 10:
            y = widget.winfo_rooty() + widget.winfo_height() + 4
        tip.geometry(f"+{x}+{y}")
        self._task_tooltip = tip

    def _build_task_list_widget(self, parent, is_compact=False, is_short=False):
        """Render the compact scrollable task list (capped at ~155px height)."""
        tasks = db.get_tasks()
        max_h = 108 if (is_compact or is_short) else 155

        if not tasks:
            empty_box = tk.Frame(
                parent, bg=THEME["bg_dark"], padx=12, pady=10,
                highlightbackground=THEME["border"], highlightthickness=1
            )
            empty_box.pack(fill="x", pady=(2, 0))
            empty_lbl = tk.Label(
                empty_box, text="No tasks yet — add one above & assign a tree 🌱",
                font=self.font_xs, fg=THEME["fg_light"], bg=THEME["bg_dark"],
                anchor="w", justify="left", wraplength=200
            )
            empty_lbl.pack(fill="x")
            empty_box.bind(
                "<Configure>",
                lambda e, lbl=empty_lbl: lbl.configure(wraplength=max(120, e.width - 26))
            )
            return

        list_wrap = tk.Frame(parent, bg=THEME["bg_card"])
        list_wrap.pack(fill="x", pady=(2, 0))

        row_h = 31
        est_h = min(max_h, len(tasks) * row_h + 4)

        canvas = tk.Canvas(
            list_wrap, bg=THEME["bg_card"], highlightthickness=0, height=est_h
        )
        scrollbar = tk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview, width=8)
        inner = tk.Frame(canvas, bg=THEME["bg_card"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_cfg(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            req_h = inner.winfo_reqheight()
            canvas.configure(height=min(max_h, max(32, req_h)))

        inner.bind("<Configure>", _on_inner_cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="x", expand=True)
        if len(tasks) * row_h > max_h:
            scrollbar.pack(side="right", fill="y", padx=(2, 0))

        def _on_wheel(e):
            if len(tasks) * row_h > max_h:
                canvas.yview_scroll(-1 * (e.delta // 120), "units")

        canvas.bind("<MouseWheel>", _on_wheel)

        max_chars = 18 if is_compact else 23
        for task in tasks:
            tid = task["id"]
            is_done = bool(task["completed"])
            is_active = (tid == self.active_task_id and not is_done)

            if is_active:
                row_bg = THEME["accent_light"]
                row_bd = THEME["accent"]
            elif is_done:
                row_bg = THEME["bg_card"]
                row_bd = THEME["border"]
            else:
                row_bg = THEME["bg_dark"]
                row_bd = THEME["border"]

            row = tk.Frame(
                inner, bg=row_bg, padx=6, pady=4,
                highlightbackground=row_bd, highlightthickness=1, cursor="hand2"
            )
            row.pack(fill="x", pady=(0, 3))
            row.bind("<MouseWheel>", _on_wheel)

            # Checkbox
            chk_txt = "☑" if is_done else "☐"
            chk_fg = THEME["accent"] if is_done else (THEME["green_dark"] if is_active else THEME["fg_muted"])
            chk_lbl = tk.Label(
                row, text=chk_txt, font=self.font_small_bold,
                bg=row_bg, fg=chk_fg, cursor="hand2", padx=2
            )
            chk_lbl.pack(side="left", padx=(0, 4))

            # Task title (truncated cleanly with tooltip on hover)
            full_title = task["title"]
            disp_title = full_title if len(full_title) <= max_chars else (full_title[:max_chars - 1].rstrip() + "…")
            txt_font = self.font_small_strike if is_done else (self.font_small_bold if is_active else self.font_small)
            txt_fg = THEME["fg_light"] if is_done else (THEME["green_dark"] if is_active else THEME["fg"])
            txt_lbl = tk.Label(
                row, text=disp_title, font=txt_font,
                bg=row_bg, fg=txt_fg, anchor="w", cursor="hand2"
            )
            txt_lbl.pack(side="left", fill="x", expand=True)

            # Delete (×) button (appears subtly on hover)
            del_lbl = tk.Label(
                row, text="×", font=self.font_small_bold,
                bg=row_bg, fg=row_bg, cursor="hand2", padx=3
            )
            del_lbl.pack(side="right", padx=(2, 0))

            # Assigned Tree Badge (clickable to reassign tree)
            sp_meta = SPECIES_METADATA.get(task["tree_species"], SPECIES_METADATA["oak"])
            badge_bg = THEME["bg_card"] if not is_done else THEME["bg_dark"]
            tree_badge = tk.Label(
                row, text=sp_meta["icon"], font=self.font_xs,
                bg=badge_bg, fg=THEME["fg"], padx=4, pady=1, cursor="hand2",
                highlightbackground=THEME["border"], highlightthickness=1
            )
            tree_badge.pack(side="right", padx=(4, 0))

            # Bindings
            chk_lbl.bind(
                "<Button-1>",
                lambda e, i=tid, tl=txt_lbl, cl=chk_lbl: self._toggle_task_item(i, tl, cl)
            )
            del_lbl.bind("<Button-1>", lambda e, i=tid: self._delete_task_item(i))
            del_lbl.bind("<Enter>", lambda e, w=del_lbl: w.configure(fg="#C95B48"))
            del_lbl.bind("<Leave>", lambda e, w=del_lbl: w.configure(fg=THEME["fg_muted"]))

            tree_badge.bind(
                "<Button-1>",
                lambda e, w=tree_badge, i=tid, sp=task["tree_species"]: self._open_species_popover(
                    w, sp, lambda new_sp, task_id=i: self._change_task_species(task_id, new_sp)
                )
            )

            # Click-to-focus on row & title
            row.bind("<Button-1>", lambda e, i=tid: self._activate_task(i))
            txt_lbl.bind("<Button-1>", lambda e, i=tid: self._activate_task(i))

            # Hover reveal for delete button + tooltip for task name
            def _on_row_enter(e, d=del_lbl, tl=txt_lbl, full=full_title):
                try:
                    d.configure(fg=THEME["fg_muted"])
                except tk.TclError:
                    pass
                if len(full) > max_chars:
                    self._show_task_tooltip(tl, full)

            def _on_row_leave(e, r=row, d=del_lbl, rb=row_bg):
                try:
                    px, py = r.winfo_pointerxy()
                    w_under = r.winfo_containing(px, py)
                    if w_under is not None and (w_under == r or w_under.master == r):
                        return
                except Exception:
                    pass
                try:
                    d.configure(fg=rb)
                except tk.TclError:
                    pass
                self._hide_task_tooltip()

            row.bind("<Enter>", _on_row_enter)
            row.bind("<Leave>", _on_row_leave)
            txt_lbl.bind("<Enter>", _on_row_enter)
            txt_lbl.bind("<Leave>", _on_row_leave)
            txt_lbl.bind("<MouseWheel>", _on_wheel)

    # ──────────────── Timer Logic ────────────────

    def _close_species_dropdown(self):
        """Close the top Tree Selector dropdown menu if open."""
        self._hide_stats_tooltip()
        bind_id = getattr(self, "_species_dropdown_root_bind", None)
        if bind_id is not None:
            try:
                self.root.unbind("<Button-1>", bind_id)
            except tk.TclError:
                pass
            self._species_dropdown_root_bind = None
        if self._species_dropdown is not None:
            try:
                self._species_dropdown.destroy()
            except tk.TclError:
                pass
            self._species_dropdown = None

    def _toggle_species_dropdown(self):
        """Open/close the Tree Selector dropdown listing all 7 species + unlock states."""
        if self.session_active:
            return
        if self._species_dropdown is not None:
            self._close_species_dropdown()
            return
        if self.species_dropdown_btn is None or not self.species_dropdown_btn.winfo_exists():
            return

        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.configure(bg=THEME["border"], padx=1, pady=1)
        try:
            pop.attributes("-topmost", True)
        except Exception:
            pass
        self._species_dropdown = pop

        body = tk.Frame(pop, bg=THEME["bg_card"], padx=6, pady=6)
        body.pack(fill="both", expand=True)

        unlock_map = db.get_species_unlock_status()
        seed_inv = db.get_seed_inventory()
        species_order = [
            "cherry_blossom", "pine", "angel_oak", "oak",
            "willow", "maple", "moonlit_blossom",
        ]

        for sp_id in species_order:
            meta = SPECIES_METADATA.get(sp_id, {})
            unlocked, req_txt = unlock_map.get(sp_id, (False, "Locked"))
            is_sel = (self.selected_species == sp_id)
            cnt = seed_inv.get(sp_id, 0)
            rarity = meta.get("rarity", "Common")

            row_bg = scenery.mix(THEME["bg_card"], THEME["accent"], 0.16) if is_sel else THEME["bg_card"]
            row = tk.Frame(
                body, bg=row_bg, padx=8, pady=5,
                cursor="hand2" if unlocked else ""
            )
            row.pack(fill="x", pady=1)

            left_txt = f"{meta.get('icon', '🌱')} {meta.get('name', sp_id)}"
            if not unlocked:
                left_txt = f"🔒 {left_txt}"
            lbl = tk.Label(
                row, text=left_txt,
                font=self.font_small_bold if is_sel else self.font_small,
                fg=THEME["fg"] if unlocked else THEME["fg_light"],
                bg=row_bg, anchor="w", width=20,
                cursor="hand2" if unlocked else ""
            )
            lbl.pack(side="left")

            right_parts = [rarity]
            if cnt > 0:
                right_parts.append(f"🌱{cnt}")
            if is_sel:
                right_parts.append("✓")
            meta_lbl = tk.Label(
                row, text="  •  ".join(right_parts),
                font=self.font_xs_bold if is_sel else self.font_xs,
                fg=THEME["accent"] if is_sel else (THEME["fg_muted"] if unlocked else THEME["fg_light"]),
                bg=row_bg, anchor="e",
                cursor="hand2" if unlocked else ""
            )
            meta_lbl.pack(side="right", padx=(10, 0))

            if unlocked:
                def _pick(e, sid=sp_id):
                    self._close_species_dropdown()
                    self._select_species(sid)
                    return "break"
                hover_bg = THEME["bg_dark"]
                for w in (row, lbl, meta_lbl):
                    w.bind("<Button-1>", _pick)
                    w.bind("<Enter>", lambda e, r=row, l=lbl, m=meta_lbl, hb=hover_bg: (
                        r.configure(bg=hb), l.configure(bg=hb), m.configure(bg=hb)
                    ))
                    w.bind("<Leave>", lambda e, r=row, l=lbl, m=meta_lbl, rb=row_bg: (
                        r.configure(bg=rb), l.configure(bg=rb), m.configure(bg=rb)
                    ))
            else:
                tip = f"Locked — {req_txt}"
                for w in (row, lbl, meta_lbl):
                    w.bind("<Enter>", lambda e, p=row, t=tip: self._show_stats_tooltip(p, t, e.x_root, e.y_root))
                    w.bind("<Leave>", lambda e: self._hide_stats_tooltip())

        pop.update_idletasks()
        bx = self.species_dropdown_btn.winfo_rootx()
        by = self.species_dropdown_btn.winfo_rooty() + self.species_dropdown_btn.winfo_height() + 4
        pw = pop.winfo_reqwidth()
        ph = pop.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if bx + pw > sw - 12:
            bx = max(12, sw - pw - 12)
        if by + ph > sh - 12:
            by = max(12, self.species_dropdown_btn.winfo_rooty() - ph - 4)
        pop.geometry(f"+{bx}+{by}")
        pop.lift()
        pop.focus_set()
        pop.bind("<Escape>", lambda e: self._close_species_dropdown())

        def _on_root_click(e):
            if self._species_dropdown is None:
                return
            w = e.widget
            if w is self.species_dropdown_btn:
                return
            try:
                if w.winfo_toplevel() is self._species_dropdown:
                    return
            except Exception:
                pass
            self._close_species_dropdown()

        self._species_dropdown_root_bind = self.root.bind("<Button-1>", _on_root_click, add="+")

    def _select_species(self, species_id):
        if self.session_active:
            return
        if not db.is_species_unlocked(species_id):
            return
        self.selected_species = species_id
        db.set_setting("selected_species", species_id)
        self._show_timer_view()

    def _set_duration(self, minutes):
        if self.session_active:
            return
        self.planned_duration = minutes * 60
        self._show_timer_view()

    def _set_custom_duration(self, event=None):
        if self.session_active:
            return
        try:
            mins = int(self.custom_entry.get())
            if 1 <= mins <= 480:
                self.planned_duration = mins * 60
                self._show_timer_view()
        except ValueError:
            pass

    def _start_session(self):
        self._close_task_popover()
        self._hide_task_tooltip()
        if hasattr(self, "task_entry") and not getattr(self.task_entry, "_is_placeholder", False):
            val = self.task_entry.get().strip()
            if val:
                self.current_task = val
        self.session_active = True
        self.timer_running = True
        self.timer_paused = False
        self.session_had_pause = False
        self.focused_seconds = 0.0
        self.last_tick_time = time.monotonic()
        self.session_start_time = datetime.now()
        self.last_stage = "seed"
        self.water_drops = []
        self._show_timer_view()

    def _pause_session(self):
        if self.timer_running:
            # Accumulate time before pausing
            now = time.monotonic()
            if self.last_tick_time:
                self.focused_seconds += now - self.last_tick_time
            self.timer_running = False
            self.timer_paused = True
            self.session_had_pause = True
            self.last_tick_time = None
            self._show_timer_view()

    def _resume_session(self):
        self.timer_running = True
        self.timer_paused = False
        self.last_tick_time = time.monotonic()
        self._show_timer_view()

    def _clean_session_task_label(self, raw_task):
        """Strip trailing whitespace/colons from task labels (e.g. 'Coding:' -> 'Coding')."""
        txt = (raw_task or "").strip()
        while txt.endswith(":"):
            txt = txt[:-1].strip()
        return txt or "General Study"

    def _dismiss_session_complete_modal(self):
        """Close the custom Session Complete modal overlay and card cleanly."""
        if self._session_modal_anim_after is not None:
            try:
                self.root.after_cancel(self._session_modal_anim_after)
            except tk.TclError:
                pass
            self._session_modal_anim_after = None

        for seq, funcid in self._session_modal_root_binds:
            try:
                self.root.unbind(seq, funcid)
            except tk.TclError:
                pass
        self._session_modal_root_binds = []

        for attr in ("_session_modal_card", "_session_modal_backdrop"):
            win = getattr(self, attr, None)
            if win is not None:
                try:
                    win.destroy()
                except tk.TclError:
                    pass
                setattr(self, attr, None)

        self._session_modal_continue_btn = None
        self._session_modal_mark_complete_btn = None

    def _show_session_complete_modal(self, mins, species_id, stage, task_name, newly_unlocked=None, active_task=None):
        """Show a centered, theme-matched modal card when a focus session completes."""
        self._dismiss_session_complete_modal()
        try:
            self.root.update_idletasks()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = max(360, self.root.winfo_width())
            rh = max(280, self.root.winfo_height())
        except tk.TclError:
            return

        # ── Dimmed modal overlay ──
        backdrop = tk.Toplevel(self.root)
        backdrop.overrideredirect(True)
        backdrop.transient(self.root)
        backdrop.configure(bg="#000000")
        backdrop.geometry(f"{rw}x{rh}+{rx}+{ry}")
        try:
            backdrop.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        backdrop.bind("<Button-1>", lambda e: self._dismiss_session_complete_modal())
        self._session_modal_backdrop = backdrop

        # ── Modal card surface (max-width 380px, padding 24px, radius 16px) ──
        card_w = min(380, max(280, rw - 48))
        use_trans = sys.platform == "win32"
        trans_key = "#010203"

        card = tk.Toplevel(self.root)
        card.overrideredirect(True)
        card.transient(backdrop)
        try:
            card.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        if use_trans:
            card.configure(bg=trans_key)
            try:
                card.attributes("-transparentcolor", trans_key)
            except tk.TclError:
                use_trans = False
                card.configure(bg=THEME["bg_card"])
        else:
            card.configure(bg=THEME["bg_card"])
        self._session_modal_card = card

        sp_meta = SPECIES_METADATA.get(species_id, {})
        sp_icon = sp_meta.get("icon", "🌱")
        sp_name = sp_meta.get("name", "Tree")
        stage_raw = STAGE_LABELS.get(stage, "🌱 Seed")
        clean_stage = stage_raw.split(" ", 1)[1] if " " in stage_raw else stage_raw
        clean_task = self._clean_session_task_label(task_name)
        mins_text = f"You focused for {mins} minute" + ("" if mins == 1 else "s")
        species_stage_text = f"{sp_icon} {sp_name} • {clean_stage}"

        self._session_modal_info = {
            "mins": mins,
            "mins_text": mins_text,
            "species_id": species_id,
            "species_name": sp_name,
            "stage": stage,
            "stage_label": clean_stage,
            "species_stage_text": species_stage_text,
            "task_label": clean_task,
            "active_task_id": active_task["id"] if active_task else None,
        }

        inner = tk.Frame(card, bg=THEME["bg_card"])

        # 1. Header: themed icon badge + Fraunces 'Session Complete!'
        badge_cv = tk.Canvas(
            inner, width=44, height=44, bg=THEME["bg_card"], highlightthickness=0
        )
        badge_cv.pack(pady=(0, 10))
        badge_cv.create_oval(
            2, 2, 42, 42,
            fill=THEME["accent_light"], outline=THEME["border"], width=1
        )
        badge_cv.create_text(
            22, 22, text=sp_icon, font=(self.family_sans, 17), fill=THEME["fg"]
        )

        tk.Label(
            inner, text="Session Complete!",
            font=(self.family_serif, 17, "bold"),
            fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(pady=(0, 12))

        # 2. Summary details in Plus Jakarta Sans
        tk.Label(
            inner, text=mins_text,
            font=(self.family_sans_semi, 11, "bold"),
            fg=THEME["fg"], bg=THEME["bg_card"],
            wraplength=card_w - 56, justify="center"
        ).pack(pady=(0, 8))

        pill_fg = THEME["accent"] if self.current_theme in ("night", "chill") else THEME["green_dark"]
        species_pill = tk.Label(
            inner, text=species_stage_text,
            font=(self.family_sans_semi, 10, "bold"),
            fg=pill_fg, bg=THEME["bg_dark"],
            padx=12, pady=6,
            highlightbackground=THEME["border"], highlightthickness=1
        )
        species_pill.pack(pady=(0, 8))

        tk.Label(
            inner, text=f"🎯 {clean_task}",
            font=self.font_small,
            fg=THEME["fg_muted"], bg=THEME["bg_card"],
            wraplength=card_w - 56, justify="center"
        ).pack(pady=(0, 4))

        if newly_unlocked:
            ach_names = ", ".join(f"{a['icon']} {a['name']}" for a in newly_unlocked)
            tk.Label(
                inner, text=f"🏆 Unlocked: {ach_names}",
                font=self.font_xs_bold,
                fg=THEME.get("yellow_soft", THEME["accent"]), bg=THEME["bg_card"],
                wraplength=card_w - 56, justify="center"
            ).pack(pady=(6, 0))

        # 3. Action Buttons
        btn_row = tk.Frame(inner, bg=THEME["bg_card"])
        btn_row.pack(pady=(18, 0))

        if active_task and not active_task.get("completed"):
            def _mark_complete():
                db.set_task_completed(active_task["id"], True)
                db.record_daily_challenge_task_completed(1)
                if self.active_task_id == active_task["id"]:
                    self.active_task_id = None
                    db.set_setting("active_task_id", "")
                self._dismiss_session_complete_modal()
                if self.current_view == "timer":
                    self._show_timer_view()
                elif self.current_view == "forest":
                    self._show_forest_view()

            mark_btn = tk.Label(
                btn_row, text="Mark Task Complete",
                font=self.font_small_bold,
                bg=THEME["bg_dark"], fg=THEME["fg"],
                padx=14, pady=8, cursor="hand2",
                highlightbackground=THEME["border"], highlightthickness=1
            )
            mark_btn.pack(side="left", padx=(0, 10))
            mark_btn.bind("<Button-1>", lambda e: _mark_complete())
            mark_btn.bind("<Enter>", lambda e: mark_btn.configure(bg=THEME["border"]))
            mark_btn.bind("<Leave>", lambda e: mark_btn.configure(bg=THEME["bg_dark"]))
            self._session_modal_mark_complete_btn = mark_btn

        cont_btn = tk.Label(
            btn_row, text="Continue",
            font=self.font_small_bold,
            bg=THEME["accent"], fg=THEME.get("accent_fg", "#FFFFFF"),
            padx=20, pady=8, cursor="hand2"
        )
        cont_btn.pack(side="left")
        cont_btn.bind("<Button-1>", lambda e: self._dismiss_session_complete_modal())
        cont_btn.bind("<Enter>", lambda e: cont_btn.configure(bg=THEME.get("accent_hover", THEME["accent"])))
        cont_btn.bind("<Leave>", lambda e: cont_btn.configure(bg=THEME["accent"]))
        self._session_modal_continue_btn = cont_btn

        # Measure content and size rounded card (padding 24px all around)
        inner.update_idletasks()
        card_h = inner.winfo_reqheight() + 48

        if use_trans:
            card_cv = tk.Canvas(
                card, width=card_w, height=card_h,
                bg=trans_key, highlightthickness=0
            )
            card_cv.pack(fill="both", expand=True)
            card_cv.create_polygon(
                _rounded_rect_pts(1, 1, card_w - 2, card_h - 2, 16),
                smooth=True, fill=THEME["bg_card"], outline=THEME["border"], width=1
            )
            card_cv.create_window(
                card_w // 2, card_h // 2,
                window=inner, width=card_w - 48
            )
        else:
            card.configure(highlightbackground=THEME["border"], highlightthickness=1)
            inner.pack(fill="both", expand=True, padx=24, pady=24)

        target_x = rx + (rw - card_w) // 2
        target_y = ry + (rh - card_h) // 2
        card.geometry(f"{card_w}x{card_h}+{target_x}+{target_y + 10}")

        # Keyboard shortcuts: Enter or Escape dismisses modal
        for seq in ("<Return>", "<Escape>"):
            card.bind(seq, lambda e: self._dismiss_session_complete_modal())
            fid = self.root.bind(seq, lambda e: self._dismiss_session_complete_modal(), add="+")
            if fid:
                self._session_modal_root_binds.append((seq, fid))

        try:
            card.lift()
            card.focus_set()
            card.focus_force()
        except tk.TclError:
            pass

        # Smooth ~0.25s fade & gentle rise-in transition (8 steps x 30ms = 240ms)
        total_steps = 8

        def _animate(step=1):
            if self._session_modal_card is not card or self._session_modal_backdrop is not backdrop:
                return
            t = step / total_steps
            ease = 1.0 - (1.0 - t) ** 2
            y_off = int(round(10 * (1.0 - ease)))
            try:
                backdrop.attributes("-alpha", 0.45 * ease)
                card.attributes("-alpha", 1.0 * ease)
                card.geometry(f"{card_w}x{card_h}+{target_x}+{target_y + y_off}")
            except tk.TclError:
                return
            if step < total_steps:
                self._session_modal_anim_after = self.root.after(30, lambda: _animate(step + 1))
            else:
                self._session_modal_anim_after = None

        _animate(1)

    def _stop_session(self):
        """Stop and save the session."""
        if not self.session_active:
            return

        # Accumulate final time
        if self.timer_running and self.last_tick_time:
            self.focused_seconds += time.monotonic() - self.last_tick_time

        completed = self.focused_seconds >= self.planned_duration * 0.8  # 80% counts as complete
        session_id = db.save_session(
            self.session_start_time,
            self.planned_duration,
            self.focused_seconds,
            completed,
            tree_species=self.selected_species,
            task_name=self.current_task
        )

        # Check achievements & daily challenges
        newly_unlocked = db.check_and_unlock_achievements()
        db.record_daily_challenge_session(
            minutes=int(self.focused_seconds // 60),
            completed=completed,
            paused=self.session_had_pause,
            abandoned=(not completed),
            task_name=self.current_task,
            theme_mode=self.current_theme,
            rain_enabled=bool(audio_player.player.is_playing),
            planted_tree=(session_id is not None),
        )

        self.session_active = False
        self.timer_running = False
        self.timer_paused = False
        self.session_had_pause = False
        self.active_quest = None
        self.last_tick_time = None

        # Show custom themed completion modal
        if session_id:
            stage = db.get_tree_stage(self.focused_seconds)
            mins = int(self.focused_seconds // 60)
            active_t = db.get_task_by_id(self.active_task_id) if self.active_task_id is not None else None
            modal_task = self.current_task
            modal_species = self.selected_species
            self.root.after(
                80,
                lambda m=mins, sp=modal_species, st=stage, tk_name=modal_task, ach=newly_unlocked, at=active_t: (
                    self._show_session_complete_modal(m, sp, st, tk_name, ach, at)
                )
            )

        self.focused_seconds = 0.0
        self._refresh_streak()
        self._show_timer_view()

    def _reset_session(self):
        """Reset without saving — no rewards."""
        if not self.session_active:
            return
        if messagebox.askyesno("Reset Session", "Are you sure? No progress will be saved."):
            db.record_daily_challenge_session(
                minutes=0,
                completed=False,
                paused=self.session_had_pause,
                abandoned=True,
                task_name=self.current_task,
                theme_mode=self.current_theme,
                rain_enabled=bool(audio_player.player.is_playing),
                planted_tree=False,
            )
            self.session_active = False
            self.timer_running = False
            self.timer_paused = False
            self.session_had_pause = False
            self.active_quest = None
            self.focused_seconds = 0.0
            self.last_tick_time = None
            self._show_timer_view()

    def _tick(self):
        """Main timer tick — runs every 200ms."""
        self._anim_tick += 1

        if self.timer_running and self.last_tick_time:
            now = time.monotonic()
            elapsed = now - self.last_tick_time
            self.last_tick_time = now
            self.focused_seconds += elapsed

            # Check if session time completed
            if self.focused_seconds >= self.planned_duration:
                self._stop_session()
                self.root.after(200, self._tick)
                return

            # Update UI elements if timer view is showing
            if self.current_view == "timer":
                self._update_timer_display()

        # Step lightweight ambient animations only when window is visible
        try:
            is_iconic = (self.root.state() == "iconic")
        except tk.TclError:
            is_iconic = False
        if not self._window_obscured and not is_iconic:
            self._step_ambient_animations()
        else:
            self._last_anim_time = time.monotonic()

        self.root.after(200, self._tick)

    def _step_ambient_animations(self):
        """Step ambient scenic actors in-place via delta canvas coordinate updates."""
        now = time.monotonic()
        dt = min(0.5, max(0.01, now - self._last_anim_time))
        self._last_anim_time = now
        try:
            if (self.current_view == "timer"
                    and self._study_scene and self._study_actors
                    and hasattr(self, "tree_canvas") and self.tree_canvas.winfo_exists()):
                scenery.step(
                    self.tree_canvas, self._study_scene, self._study_actors,
                    now, dt, flush=self.tree_canvas.update_idletasks,
                )
            elif (self.current_view == "forest"
                    and self._forest_scene and self._forest_actors
                    and hasattr(self, "forest_canvas") and self.forest_canvas.winfo_exists()):
                scenery.step(
                    self.forest_canvas, self._forest_scene, self._forest_actors,
                    now, dt, flush=self.forest_canvas.update_idletasks,
                )
        except tk.TclError:
            pass

    def _update_timer_display(self):
        """Update timer display without rebuilding the view."""
        try:
            remaining = max(0, self.planned_duration - self.focused_seconds)
            timer_str = self._format_time(int(remaining))
            t_font = self._get_timer_font(timer_str)
            if t_font[1] != self._last_timer_font_pt:
                self._last_timer_font_pt = t_font[1]
                self.timer_display.configure(text=timer_str, font=t_font)
            else:
                self.timer_display.configure(text=timer_str)
            self.elapsed_label.configure(
                text=f"Focused: {self._format_time(int(self.focused_seconds))}"
            )

            # Update progress bar
            progress = min(1.0, self.focused_seconds / max(1, self.planned_duration))
            self.progress_bar.place(relx=0, rely=0, relwidth=max(0.005, progress), relheight=1)

            # Update tree stage
            stage = db.get_tree_stage(self.focused_seconds)
            curr_meta = SPECIES_METADATA.get(self.selected_species, {})
            spec_display = f"{curr_meta.get('icon', '')} {curr_meta.get('name', 'Tree')}"
            self.stage_label.configure(text=f"{STAGE_LABELS.get(stage, '🌱 Seed')}  •  {spec_display}")

            # Redraw tree only when growth stage actually changes
            if stage != self.last_stage:
                self.last_stage = stage
                self._redraw_tree(animate_transition=True)
                self._show_water_animation()
        except tk.TclError:
            pass  # Widget was destroyed during view switch

    def _on_study_canvas_configure(self, event):
        """Debounce study canvas resize redraws when geometry changes > 4px."""
        try:
            if self._window_obscured or self.root.state() == "iconic":
                return
        except tk.TclError:
            return
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return
        lw, lh = self._last_study_size
        if abs(w - lw) <= 4 and abs(h - lh) <= 4 and self._study_scene is not None:
            return
        if self._study_resize_after is not None:
            try:
                self.root.after_cancel(self._study_resize_after)
            except tk.TclError:
                pass
            self._study_resize_after = None
        self._study_resize_after = self.root.after(120, self._redraw_tree)

    def _pulse_study_tree(self, gx, gy, step_idx=0, prev_scale=1.0):
        """3-step growth transition pulse on the study tree anchored at (gx, gy)."""
        targets = (1.06, 1.03, 1.0)
        if step_idx >= len(targets):
            return
        try:
            if not hasattr(self, "tree_canvas") or not self.tree_canvas.winfo_exists():
                return
            target = targets[step_idx]
            ratio = target / prev_scale
            self.tree_canvas.scale("study_tree", gx, gy, ratio, ratio)
            if step_idx + 1 < len(targets):
                self._study_pulse_after = self.root.after(
                    55, lambda: self._pulse_study_tree(gx, gy, step_idx + 1, target)
                )
        except tk.TclError:
            pass

    def _redraw_tree(self, animate_transition=False):
        """Redraw the tree on the canvas with themed illustrated sanctuary scenery."""
        try:
            if not hasattr(self, "tree_canvas") or not self.tree_canvas.winfo_exists():
                return
            if self._study_resize_after is not None:
                try:
                    self.root.after_cancel(self._study_resize_after)
                except tk.TclError:
                    pass
                self._study_resize_after = None
            if getattr(self, "_study_pulse_after", None) is not None:
                try:
                    self.root.after_cancel(self._study_pulse_after)
                except tk.TclError:
                    pass
                self._study_pulse_after = None

            w = self.tree_canvas.winfo_width()
            h = self.tree_canvas.winfo_height()
            if w < 10 or h < 10:
                self.root.after(100, self._redraw_tree)
                return

            self._last_study_size = (w, h)
            self.tree_canvas.delete("all")

            stage = db.get_tree_stage(self.focused_seconds) if self.session_active else "seed"
            richness = min(1.0, db.get_total_trees() / 20.0)

            self._study_scene = scenery.draw_landscape(
                self.tree_canvas, w, h, self.current_theme,
                mode="study", richness=richness,
            )

            # Draw central botanical tree grounded at scene horizon knoll
            scale = min(w / 280, h / 280)
            scale = max(0.85, min(scale, 1.85))
            gx, gy = self._study_scene.get("study_ground", (w // 2, int(h * 0.72)))

            before_ids = set(self.tree_canvas.find_all())
            draw_tree(self.tree_canvas, stage, gx, gy, scale, species=self.selected_species)
            new_ids = [iid for iid in self.tree_canvas.find_all() if iid not in before_ids]
            for iid in new_ids:
                self.tree_canvas.addtag_withtag("study_tree", iid)
            if new_ids:
                scenery.tint_range(
                    self.tree_canvas, min(new_ids), max(new_ids) + 1, self.current_theme
                )

            leaf_col = scenery.LEAF_BY_SPECIES.get(self.selected_species)
            sway_amp = 0.0 if stage in ("seed", "sprout") else (0.55 if stage == "seedling" else 0.9)
            self._study_actors = scenery.spawn_actors(
                self.tree_canvas, self._study_scene,
                rain=audio_player.player.is_playing,
                leaf_color=leaf_col,
                sway_tag="study_tree",
                sway_amp=sway_amp,
            )

            if animate_transition and new_ids:
                self._pulse_study_tree(gx, gy, 0, 1.0)
        except tk.TclError:
            pass

    def _show_water_animation(self):
        """Show water drop or species particle animation when milestone reached."""
        try:
            w = self.tree_canvas.winfo_width()
            h = self.tree_canvas.winfo_height()
            cx, cy = w // 2, h // 2

            curr_meta = SPECIES_METADATA.get(self.selected_species, SPECIES_METADATA["oak"])
            particle_choices = curr_meta.get("particles", ["💧"]) + ["💧"]

            drops = []
            for i in range(6):
                x = cx + random.randint(-65, 65)
                y = cy + random.randint(-45, 45)
                particle = random.choice(particle_choices)
                drop = self.tree_canvas.create_text(
                    x, y - 30, text=particle,
                    font=("Segoe UI Emoji", 14)
                )
                drops.append((drop, y - 30))

            self._animate_drops(drops, 0)
        except tk.TclError:
            pass

    def _animate_drops(self, drops, step):
        """Animate water drops falling."""
        if step > 15:
            for drop, _ in drops:
                try:
                    self.tree_canvas.delete(drop)
                except Exception:
                    pass
            return

        for drop, start_y in drops:
            try:
                self.tree_canvas.move(drop, 0, 3)
                if step > 10:
                    # Fade by reducing font size
                    pass
            except Exception:
                pass

        self.root.after(60, lambda: self._animate_drops(drops, step + 1))

    # ──────────────── Forest View ────────────────

    def _show_forest_view(self):
        self.current_view = "forest"
        self._clear_content()
        self._forest_popup = None   # active tooltip/delete popup
        self._forest_trees = []     # list of (tree_dict, canvas_bbox) for hit-testing

        # ── Top bar ──
        topbar = tk.Frame(self.content_frame, bg=THEME["bg"])
        topbar.pack(fill="x", pady=(0, 6))

        tk.Label(
            topbar, text="🌲 My Forest",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(side="left")

        hint = tk.Label(
            topbar,
            text="✦ Click any tree to view task, edit notes, or remove it",
            font=self.font_small_italic, fg=THEME["fg_light"], bg=THEME["bg"]
        )
        hint.pack(side="right")

        # ── Stats strip ──
        stats_card = tk.Frame(self.content_frame, bg=THEME["bg_card"],
                              highlightbackground=THEME["border"], highlightthickness=1)
        stats_card.pack(fill="x", pady=(0, 6))

        inner_s = tk.Frame(stats_card, bg=THEME["bg_card"])
        inner_s.pack(fill="x", padx=16, pady=8)

        total_trees = db.get_total_trees()
        total_hours = db.get_total_focused_seconds() / 3600
        streak = db.get_streak()
        completed = db.get_completed_count() + db.get_completed_tasks_count()

        for icon, value, label in [
            ("🌳", str(total_trees), "Trees"),
            ("⏱️", f"{total_hours:.1f}h", "Study Time"),
            ("🔥", str(streak), "Streak"),
            ("✅", str(completed), "Completed"),
            ("💧", str(int(total_hours * 10)), "Water"),
        ]:
            col = tk.Frame(inner_s, bg=THEME["bg_card"])
            col.pack(side="left", expand=True)
            tk.Label(col, text=icon, font=self.font_emoji, bg=THEME["bg_card"]).pack()
            tk.Label(col, text=value, font=self.font_stat_strip,
                     fg=THEME["green_dark"], bg=THEME["bg_card"]).pack()
            tk.Label(col, text=label, font=self.font_stat_label,
                     fg=THEME["fg_muted"], bg=THEME["bg_card"]).pack()

        # ── Filter Bar (uniform 34px height pills matching Tree Selector) ──
        filter_bar = tk.Frame(self.content_frame, bg=THEME["bg"], height=34)
        filter_bar.pack(fill="x", pady=(0, 6))
        filter_bar.pack_propagate(False)

        tk.Label(
            filter_bar, text="Filter Forest:", font=self.font_small,
            fg=THEME["fg_muted"], bg=THEME["bg"]
        ).pack(side="left", padx=(0, 8))

        filters = [
            ("all", "All Trees"),
            ("cherry_blossom", "Sakura"),
            ("pine", "Pine"),
            ("angel_oak", "Angel Oak"),
            ("oak", "Oak"),
        ]

        for fid, flabel in filters:
            is_active = (self.forest_filter_species == fid)
            fbtn = self._make_species_pill(
                filter_bar, fid, flabel, is_active, THEME["accent"],
                command=lambda f=fid: self._set_forest_filter(f),
            )
            fbtn.pack(side="left", padx=(0, 6))

        # ── Enhanced 3D/Pixel Forest Canvas ──
        self._forest_scene = None
        self._forest_actors = None
        self._forest_resize_after = None
        self._last_forest_size = (0, 0)
        sky_bg = scenery.palette(self.current_theme)["sky"][0]
        forest_outer = tk.Frame(self.content_frame, bg=sky_bg,
                                highlightbackground=THEME["border"], highlightthickness=1)
        forest_outer.pack(fill="both", expand=True)

        self.forest_canvas = tk.Canvas(
            forest_outer, bg=sky_bg, highlightthickness=0, cursor="hand2"
        )
        self.forest_canvas.pack(fill="both", expand=True)

        # Bind click for tree inspection and debounced resize
        self.forest_canvas.bind("<Button-1>", self._on_forest_click)
        self.forest_canvas.bind("<Configure>", self._on_forest_canvas_configure)

        self.root.after(80, self._draw_forest)

    def _set_forest_filter(self, filter_id):
        self.forest_filter_species = filter_id
        self._show_forest_view()

    def _on_forest_canvas_configure(self, event):
        """Debounce forest canvas resize redraws when geometry changes > 4px."""
        try:
            if self._window_obscured or self.root.state() == "iconic":
                return
        except tk.TclError:
            return
        w, h = event.width, event.height
        if w < 20 or h < 20:
            return
        lw, lh = self._last_forest_size
        if abs(w - lw) <= 4 and abs(h - lh) <= 4 and self._forest_scene is not None:
            return
        if self._forest_resize_after is not None:
            try:
                self.root.after_cancel(self._forest_resize_after)
            except tk.TclError:
                pass
            self._forest_resize_after = None
        self._forest_resize_after = self.root.after(120, self._draw_forest)

    def _draw_forest(self):
        """Draw the themed illustrated forest sanctuary with natural perspective slots."""
        try:
            if not hasattr(self, "forest_canvas") or not self.forest_canvas.winfo_exists():
                return
            if self._forest_resize_after is not None:
                try:
                    self.root.after_cancel(self._forest_resize_after)
                except tk.TclError:
                    pass
                self._forest_resize_after = None

            w = self.forest_canvas.winfo_width()
            h = self.forest_canvas.winfo_height()
            if w < 20 or h < 20:
                self.root.after(100, self._draw_forest)
                return

            self._last_forest_size = (w, h)
            self.forest_canvas.delete("all")
            self._forest_trees = []

            all_trees = db.get_forest_trees()
            if self.forest_filter_species == "all":
                trees = all_trees
            else:
                trees = [t for t in all_trees if t.get("tree_species", "oak") == self.forest_filter_species]

            richness = min(1.0, len(all_trees) / 25.0)
            self._forest_scene = scenery.draw_landscape(
                self.forest_canvas, w, h, self.current_theme,
                mode="forest", richness=richness,
            )
            pal = self._forest_scene["pal"]

            # Empty sanctuary card (still keeps animated clouds/water/ambient actors active)
            if not trees:
                filter_msg = (
                    f"No {self.forest_filter_species.replace('_', ' ')} trees found."
                    if self.forest_filter_species != "all"
                    else "Your forest is peaceful and waiting for growth.\nComplete your first study session to plant a tree! 🌱"
                )
                box_w, box_h = min(w - 40, 460), 96
                bx = (w - box_w) // 2
                by = int(h * 0.62)
                if self.current_theme == "night":
                    banner_bg, banner_fg = "#141D26", "#E6EEF8"
                elif self.current_theme == "chill":
                    banner_bg, banner_fg = "#2B211E", "#F5E6D8"
                else:
                    banner_bg, banner_fg = pal["hills"][2], "#F7FBF2"
                self.forest_canvas.create_rectangle(
                    bx, by, bx + box_w, by + box_h,
                    fill=banner_bg, outline=THEME["border"], width=1
                )
                self.forest_canvas.create_text(
                    w // 2, by + box_h // 2,
                    text=f"✦  {filter_msg}",
                    font=self.font_subtitle, fill=banner_fg, justify="center"
                )
                self._forest_actors = scenery.spawn_actors(
                    self.forest_canvas, self._forest_scene,
                    rain=audio_player.player.is_playing,
                )
                return

            slots = scenery.forest_slots(self._forest_scene, len(trees))
            paired = [
                {"tree": tree, "x": slot[0], "y": slot[1], "scale": slot[2]}
                for tree, slot in zip(trees, slots)
            ]
            paired.sort(key=lambda item: item["y"])

            shadow_col = pal["shadow"]
            if self.current_theme == "night":
                badge_bg = scenery.mix("#182330", pal["hills"][1], 0.32)
                badge_border = scenery.mix("#6C82A3", badge_bg, 0.55)
                badge_fg = "#EDF2F7"
            elif self.current_theme == "chill":
                badge_bg = scenery.mix("#302521", pal["hills"][1], 0.34)
                badge_border = scenery.mix("#C48A78", badge_bg, 0.55)
                badge_fg = "#F7E9DC"
            else:
                badge_bg = scenery.mix(THEME["bg_card"], pal["hills"][2], 0.16)
                badge_border = scenery.mix(pal["hills"][2], THEME["bg_card"], 0.45)
                badge_fg = "#1B3526"
            pill_shadow = scenery.mix(pal["shadow"], pal["hills"][2], 0.48)
            w_canvas = max(400, self.forest_canvas.winfo_width())

            for item in paired:
                tree = item["tree"]
                cx_t = int(item["x"])
                ground_y = int(item["y"])
                scale = item["scale"]
                sp = tree.get("tree_species", "oak")
                stage = tree["tree_stage"]
                task_name = tree.get("task_name", "General Study")
                tag = f"tree_{tree['id']}"

                sh_w = int(42 * scale)
                sh_h = max(3, int(9 * scale))
                self.forest_canvas.create_oval(
                    cx_t - sh_w, ground_y - sh_h,
                    cx_t + sh_w, ground_y + sh_h + 2,
                    fill=shadow_col, outline="", tags=(tag,),
                )

                before_items = set(self.forest_canvas.find_all())
                draw_mini_tree(self.forest_canvas, stage, cx_t, ground_y, scale, species=sp)
                new_items = [iid for iid in self.forest_canvas.find_all() if iid not in before_items]

                if new_items:
                    scenery.tint_range(
                        self.forest_canvas, min(new_items), max(new_items) + 1, self.current_theme
                    )
                for c_item in new_items:
                    self.forest_canvas.addtag_withtag(tag, c_item)
                    self.forest_canvas.addtag_withtag("forest_trees_sway", c_item)

                if stage in ("young", "mature", "flourishing") and scale >= 0.32 and len(trees) <= 28:
                    top_y = ground_y - int(105 * scale)
                    display_task = task_name if len(task_name) <= 18 else task_name[:16] + "…"
                    label_str = f"🎯 {display_task}"
                    text_px = self._forest_label_font.measure(label_str)
                    pill_hw = max(30, int(text_px * 0.5) + 12)
                    px_c = max(pill_hw + 6, min(w_canvas - pill_hw - 6, cx_t))
                    self.forest_canvas.create_polygon(
                        _rounded_rect_pts(px_c - pill_hw, top_y - 21, px_c + pill_hw, top_y + 1, 9),
                        fill=pill_shadow, outline="", tags=(tag,),
                    )
                    self.forest_canvas.create_polygon(
                        _rounded_rect_pts(px_c - pill_hw, top_y - 22, px_c + pill_hw, top_y, 9),
                        fill=badge_bg, outline=badge_border, width=1, tags=(tag,),
                    )
                    self.forest_canvas.create_text(
                        px_c, top_y - 11,
                        text=label_str,
                        font=(self.family_sans_semi, 8, "bold"),
                        fill=badge_fg,
                        tags=(tag,),
                    )

                hit_r = max(30, int(56 * scale))
                self._forest_trees.append({
                    "tree": tree,
                    "cx": cx_t,
                    "cy": ground_y,
                    "scale": scale,
                    "hit_r": hit_r,
                    "tag": tag,
                })

            dominant_sp = self.forest_filter_species
            if dominant_sp == "all" and trees:
                counts = {}
                for t in trees:
                    s_k = t.get("tree_species", "oak")
                    counts[s_k] = counts.get(s_k, 0) + 1
                dominant_sp = max(counts, key=counts.get)
            leaf_col = scenery.LEAF_BY_SPECIES.get(dominant_sp)

            self._forest_actors = scenery.spawn_actors(
                self.forest_canvas, self._forest_scene,
                rain=audio_player.player.is_playing,
                leaf_color=leaf_col,
                sway_tag="forest_trees_sway",
                sway_amp=0.35,
            )
        except tk.TclError:
            pass

    # ── Forest click / popup with Task Support ────────────────

    def _on_forest_click(self, event):
        """Handle click on forest canvas — find clicked or nearest tree and show popup."""
        self._dismiss_forest_popup()

        mx, my = event.x, event.y
        best = None

        # 1. Exact canvas tag hit check (clicking anywhere on tree trunk, canopy, or label pill)
        overlaps = self.forest_canvas.find_overlapping(mx - 4, my - 4, mx + 4, my + 4)
        tag_map = {entry["tag"]: entry for entry in self._forest_trees if "tag" in entry}
        for item_id in reversed(overlaps):
            for t in self.forest_canvas.gettags(item_id):
                if t in tag_map:
                    best = tag_map[t]
                    break
            if best:
                break

        # 2. Fallback proximity check along trunk-to-canopy vertical span
        if not best:
            best_dist = 999999
            for entry in self._forest_trees:
                sc = entry.get("scale", 0.5)
                y_top = entry["cy"] - int(85 * sc)
                y_bot = entry["cy"] + 10
                clamped_y = max(y_top, min(y_bot, my))
                d = ((mx - entry["cx"]) ** 2 + (my - clamped_y) ** 2) ** 0.5
                if d < entry["hit_r"] and d < best_dist:
                    best_dist = d
                    best = entry

        if best:
            self._show_tree_popup(best["tree"], best["cx"], best["cy"])

    def _show_tree_popup(self, tree, cx, cy):
        """Show a floating info card with task editing and delete button."""
        try:
            w_c = self.forest_canvas.winfo_width()
            h_c = self.forest_canvas.winfo_height()

            sp_id = tree.get("tree_species", "oak")
            meta = SPECIES_METADATA.get(sp_id, {})
            stage = STAGE_LABELS.get(tree["tree_stage"], "Seed")
            task_name = tree.get("task_name", "General Study")
            dt = datetime.fromisoformat(tree["start_time"])
            mins = int(tree["actual_focused_seconds"] // 60)
            secs_rem = int(tree["actual_focused_seconds"] % 60)
            status = "Completed ✅" if tree["completed"] else "Partial ⏸️"

            # Popup frame on top of canvas via place
            popup_bg = THEME["bg_card"]
            popup_border = THEME["border"]
            popup = tk.Frame(
                self.forest_canvas,
                bg=popup_bg,
                highlightbackground=popup_border, highlightthickness=1,
                padx=0, pady=0
            )

            popup_w = 248
            # Build contents first, then size popup to its natural reqheight so Remove button is never clipped
            # Header strip
            hdr = tk.Frame(popup, bg=meta.get("theme_color", THEME["accent"]), height=34)
            hdr.pack(fill="x")
            hdr.pack_propagate(False)
            tk.Label(
                hdr,
                text=f"{meta.get('icon','🌳')} {meta.get('name','Tree')}",
                font=self.font_small_bold, fg="white",
                bg=meta.get("theme_color", THEME["accent"])
            ).pack(side="left", padx=10, pady=5)

            # Close ×
            close_btn = tk.Label(hdr, text="✕", font=self.font_small,
                                 fg="white", bg=meta.get("theme_color", THEME["accent"]),
                                 cursor="hand2", padx=8)
            close_btn.pack(side="right")
            close_btn.bind("<Button-1>", lambda e: self._dismiss_forest_popup())

            # Body
            body = tk.Frame(popup, bg=popup_bg, padx=10, pady=6)
            body.pack(fill="both", expand=True)

            # Task row with Rename button
            task_row = tk.Frame(body, bg=popup_bg)
            task_row.pack(fill="x", pady=1)
            tk.Label(task_row, text="Task:", font=self.font_xs,
                     fg=THEME["fg_muted"], bg=popup_bg, width=7, anchor="w").pack(side="left")
            t_lbl = tk.Label(task_row, text=task_name, font=self.font_small_bold,
                             fg=THEME["green_dark"], bg=popup_bg, anchor="w")
            t_lbl.pack(side="left", fill="x", expand=True)
            edit_btn = tk.Label(task_row, text="✏️", font=self.font_xs,
                                fg=THEME["accent"], bg=popup_bg, cursor="hand2")
            edit_btn.pack(side="right")
            edit_btn.bind("<Button-1>", lambda e, tid=tree["id"], cur=task_name: self._prompt_rename_tree(tid, cur))

            for text, val in [
                ("Stage:", stage),
                ("Studied:", f"{mins}m {secs_rem}s"),
                ("Planted:", dt.strftime("%b %d, %Y  %H:%M")),
                ("Status:", status),
            ]:
                row = tk.Frame(body, bg=popup_bg)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=text, font=self.font_xs,
                         fg=THEME["fg_muted"], bg=popup_bg, width=7, anchor="w").pack(side="left")
                tk.Label(row, text=val, font=self.font_xs_bold,
                         fg=THEME["fg"], bg=popup_bg).pack(side="left")

            # Delete button (adapted for light vs dark mode)
            is_dark = self.current_theme in ("night", "chill")
            del_bg = "#3A1B1B" if is_dark else "#FFEBEE"
            del_fg = "#F87171" if is_dark else "#C62828"
            del_border = "#5C2626" if is_dark else "#FFCDD2"
            del_hover = "#4E2424" if is_dark else "#FFCDD2"

            del_btn = tk.Label(
                body,
                text="🗑  Remove this tree",
                font=self.font_xs_bold,
                bg=del_bg, fg=del_fg,
                padx=8, pady=5, cursor="hand2",
                highlightbackground=del_border, highlightthickness=1
            )
            del_btn.pack(fill="x", pady=(6, 2))
            del_btn.bind("<Button-1>", lambda e, tid=tree["id"]: self._delete_tree(tid))
            del_btn.bind("<Enter>", lambda e: del_btn.configure(bg=del_hover))
            del_btn.bind("<Leave>", lambda e: del_btn.configure(bg=del_bg))

            popup.update_idletasks()
            popup_h = max(220, popup.winfo_reqheight() + 4)
            px = cx - popup_w // 2
            py = cy - popup_h - 20
            if px < 5:
                px = 5
            if px + popup_w > w_c - 5:
                px = max(5, w_c - popup_w - 5)
            if py < 5:
                py = cy + 20
            if py + popup_h > h_c - 5:
                py = max(5, h_c - popup_h - 5)
            popup.place(x=px, y=py, width=popup_w, height=popup_h)

            self._forest_popup = popup
        except tk.TclError:
            pass

    def _prompt_rename_tree(self, session_id, current_name):
        """Prompt user to rename the task assigned to this tree."""
        from tkinter import simpledialog
        new_name = simpledialog.askstring(
            "Edit Tree Task",
            "Enter the new task/subject for this tree:",
            initialvalue=current_name,
            parent=self.root
        )
        if new_name is not None and new_name.strip():
            db.update_tree_task(session_id, new_name.strip())
            self._dismiss_forest_popup()
            self._show_forest_view()

    def _dismiss_forest_popup(self):
        """Destroy the active tree popup."""
        try:
            if self._forest_popup:
                self._forest_popup.destroy()
                self._forest_popup = None
        except Exception:
            pass

    def _delete_tree(self, session_id):
        """Confirm and delete a tree from the forest."""
        from tkinter import messagebox as _mb
        self._dismiss_forest_popup()
        if _mb.askyesno(
            "Remove Tree 🗑",
            "Are you sure you want to remove this tree?\n\n"
            "This marks it as a session you feel you didn't truly learn.\n"
            "The study time will be deducted from your log.",
            icon="warning"
        ):
            db.delete_tree(session_id)
            self._refresh_streak()
            self._show_forest_view()

    # ──────────────── Statistics View ────────────────

    def _hide_stats_tooltip(self):
        if getattr(self, "_stats_tooltip", None) is not None:
            try:
                if self._stats_tooltip.winfo_exists():
                    self._stats_tooltip.destroy()
            except Exception:
                pass
            self._stats_tooltip = None

    def _show_stats_tooltip(self, widget, text, x_root, y_root):
        self._hide_stats_tooltip()
        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tip.configure(bg=THEME["border"], padx=1, pady=1)
        try:
            tip.attributes("-topmost", True)
        except Exception:
            pass
        lbl = tk.Label(
            tip, text=text, font=self.font_xs_bold,
            bg=THEME["bg_card"], fg=THEME["fg"], padx=8, pady=4
        )
        lbl.pack()
        tip.update_idletasks()
        px = x_root + 10
        py = y_root - tip.winfo_reqheight() - 8
        sw = self.root.winfo_screenwidth()
        if px + tip.winfo_reqwidth() > sw - 8:
            px = max(8, x_root - tip.winfo_reqwidth() - 8)
        if py < 8:
            py = y_root + 12
        tip.geometry(f"+{px}+{py}")
        self._stats_tooltip = tip

    def _set_stats_activity_mode(self, mode):
        if mode in ("week", "heatmap", "both") and self.stats_activity_mode != mode:
            self.stats_activity_mode = mode
            self._show_stats_view()

    def _toggle_hide_zero_sessions(self):
        self.hide_zero_min_sessions = not self.hide_zero_min_sessions
        self._show_stats_view()

    def _edit_daily_goal_inline(self, holder):
        """Replace goal label inline with a numeric entry to edit dailyGoalMinutes."""
        if not holder.winfo_exists():
            return
        for w in holder.winfo_children():
            w.destroy()

        entry = tk.Entry(
            holder, width=5, font=self.font_xs_bold,
            bg=THEME["bg_dark"], fg=THEME["fg"], insertbackground=THEME["fg"],
            relief="flat", highlightthickness=1, highlightbackground=THEME["accent"]
        )
        entry.insert(0, str(self.daily_goal_minutes))
        entry.select_range(0, "end")
        entry.pack(side="left")
        tk.Label(
            holder, text="m", font=self.font_xs,
            fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(side="left", padx=(2, 0))

        saved = {"done": False}

        def _commit(e=None):
            if saved["done"]:
                return
            saved["done"] = True
            try:
                raw = entry.get().strip()
                if raw:
                    val = int(float(raw))
                    self.daily_goal_minutes = db.set_daily_goal_minutes(val)
            except (TypeError, ValueError, tk.TclError):
                pass
            if self.current_view == "stats":
                self._show_stats_view()

        entry.bind("<Return>", _commit)
        entry.bind("<FocusOut>", _commit)
        entry.bind("<Escape>", lambda e: (saved.__setitem__("done", True), self._show_stats_view()))
        entry.focus_set()

    def _draw_goal_ring_canvas(self, canvas, today_minutes, goal_minutes, ring_color):
        """Draw the compact 44x44 circular daily goal progress ring."""
        try:
            canvas.delete("all")
            track = THEME["bg_dark"]
            canvas.create_oval(4, 4, 40, 40, outline=track, width=4.5)
            frac = min(1.0, max(0.0, float(today_minutes) / max(1.0, float(goal_minutes))))
            if frac > 0:
                if frac >= 0.999:
                    canvas.create_oval(4, 4, 40, 40, outline=ring_color, width=4.5)
                else:
                    extent = -frac * 360.0
                    canvas.create_arc(
                        4, 4, 40, 40, start=90, extent=extent,
                        style="arc", outline=ring_color, width=4.5
                    )
            pct = int(round(frac * 100))
            canvas.create_text(
                22, 22, text=f"{pct}%", font=(self.family_mono, 8, "bold"),
                fill=ring_color
            )
        except tk.TclError:
            pass

    def _draw_heatmap_grid(self, canvas, heatmap_data):
        """Draw a 13 columns x 7 rows (91 days up to today) GitHub-style activity heatmap."""
        try:
            w = canvas.winfo_width()
            if w < 100:
                self.root.after(80, lambda: self._draw_heatmap_grid(canvas, heatmap_data))
                return
            canvas.delete("all")

            cols = 13
            rows = 7
            cell = 12
            gap = 4
            step = cell + gap
            grid_w = cols * step - gap
            grid_h = rows * step - gap

            left_lbl_w = 28
            total_w = left_lbl_w + grid_w
            x0 = max(16, (w - total_w) // 2 + left_lbl_w)
            y0 = 18

            # Color ramp: 5 levels of active theme's primary accent
            base = THEME["bg_dark"]
            acc = THEME["accent"]
            level_colors = [
                base,
                scenery.mix(base, acc, 0.30),
                scenery.mix(base, acc, 0.52),
                scenery.mix(base, acc, 0.76),
                acc,
            ]

            # Subtle day-of-week hints (show every other row cleanly)
            if heatmap_data:
                for r in range(rows):
                    if r in (0, 2, 4, 6):
                        sample = heatmap_data[r]
                        try:
                            d_short = datetime.fromisoformat(sample["date"]).strftime("%a")[:2]
                        except Exception:
                            d_short = ""
                        canvas.create_text(
                            x0 - 8, y0 + r * step + cell / 2,
                            text=d_short, font=(self.family_sans, 7),
                            fill=THEME["fg_light"], anchor="e"
                        )

            # Month header markers above columns when month starts
            last_month = None
            for col in range(cols):
                idx = col * rows
                if idx < len(heatmap_data):
                    try:
                        dt_col = datetime.fromisoformat(heatmap_data[idx]["date"])
                        m_lbl = dt_col.strftime("%b")
                        if m_lbl != last_month:
                            canvas.create_text(
                                x0 + col * step, y0 - 9,
                                text=m_lbl, font=(self.family_sans, 8),
                                fill=THEME["fg_muted"], anchor="w"
                            )
                            last_month = m_lbl
                    except Exception:
                        pass

            cell_boxes = []
            for entry in heatmap_data:
                c = entry["col"]
                r = entry["row"]
                mins = entry["minutes"]
                lvl = get_heatmap_intensity_level(mins)
                fill_c = level_colors[lvl]
                cx0 = x0 + c * step
                cy0 = y0 + r * step
                cx1 = cx0 + cell
                cy1 = cy0 + cell
                pts = _rounded_rect_pts(cx0, cy0, cx1, cy1, 3)
                is_today = (entry["date"] == date.today().isoformat())
                outline_c = THEME["fg_muted"] if is_today else ""
                canvas.create_polygon(
                    pts, smooth=True, fill=fill_c, outline=outline_c,
                    width=1 if is_today else 0
                )
                tip_txt = f"{entry['display_date']}: {mins} min" + ("" if mins == 1 else "s")
                cell_boxes.append((cx0, cy0, cx1, cy1, tip_txt))

            # Legend ("Less [][][][][] More") below bottom-right of grid
            ly = y0 + grid_h + 12
            lx = x0 + grid_w - 5 * 14 - 36
            canvas.create_text(lx - 6, ly + 5, text="Less", font=(self.family_sans, 7), fill=THEME["fg_light"], anchor="e")
            for k, col_hex in enumerate(level_colors):
                bx0 = lx + k * 14
                canvas.create_polygon(
                    _rounded_rect_pts(bx0, ly, bx0 + 10, ly + 10, 2),
                    smooth=True, fill=col_hex, outline=""
                )
            canvas.create_text(lx + 5 * 14 + 4, ly + 5, text="More", font=(self.family_sans, 7), fill=THEME["fg_light"], anchor="w")

            canvas._heatmap_boxes = cell_boxes
            canvas._last_hover_idx = None

            def _on_motion(e):
                hit_idx = None
                for i, (bx0, by0, bx1, by1, tip_txt) in enumerate(canvas._heatmap_boxes):
                    if bx0 <= e.x <= bx1 and by0 <= e.y <= by1:
                        hit_idx = i
                        if canvas._last_hover_idx != i:
                            canvas._last_hover_idx = i
                            self._show_stats_tooltip(canvas, tip_txt, e.x_root, e.y_root)
                        break
                if hit_idx is None and canvas._last_hover_idx is not None:
                    canvas._last_hover_idx = None
                    self._hide_stats_tooltip()

            def _on_leave(e):
                canvas._last_hover_idx = None
                self._hide_stats_tooltip()

            canvas.bind("<Motion>", _on_motion)
            canvas.bind("<Leave>", _on_leave)
        except tk.TclError:
            pass

    def _draw_species_donut_canvas(self, canvas, breakdown):
        """Draw the Forest Species Breakdown donut chart mirroring get_species_donut_svg."""
        try:
            canvas.delete("all")
            w = 124
            h = 124
            cx, cy = w / 2, h / 2
            pad = 14
            x0, y0, x1, y1 = pad, pad, w - pad, h - pad
            track_col = THEME["bg_dark"]

            total_secs = sum(item.get("total_seconds", 0.0) for item in (breakdown or []))
            canvas.create_oval(x0, y0, x1, y1, outline=track_col, width=14)

            if total_secs <= 0:
                canvas.create_text(
                    cx, cy, text="No trees\nplanted yet",
                    font=(self.family_sans, 8), fill=THEME["fg_light"], justify="center"
                )
                return

            non_zero = [item for item in breakdown if item.get("total_seconds", 0.0) > 0]
            if len(non_zero) == 1:
                canvas.create_oval(x0, y0, x1, y1, outline=non_zero[0]["color"], width=14)
            else:
                start_deg = 90.0
                for item in non_zero:
                    extent_deg = -(item["share"] * 360.0)
                    if abs(extent_deg) < 0.5:
                        continue
                    canvas.create_arc(
                        x0, y0, x1, y1,
                        start=start_deg, extent=extent_deg,
                        style="arc", outline=item["color"], width=14
                    )
                    start_deg += extent_deg

            total_mins = int(total_secs // 60)
            canvas.create_text(
                cx, cy - 5, text=f"{total_mins}m",
                font=(self.family_mono, 10, "bold"), fill=THEME["fg"]
            )
            canvas.create_text(
                cx, cy + 9, text="total",
                font=(self.family_sans, 7), fill=THEME["fg_muted"]
            )
        except tk.TclError:
            pass

    def _show_stats_view(self):
        self.current_view = "stats"
        self._clear_content()
        self.daily_goal_minutes = db.get_daily_goal_minutes()

        vw, _ = self._get_viewport_size()
        mode = self._get_responsive_mode()
        is_compact = (mode == "compact")

        # Scrollable container so the bottom navigation bar is never pushed off-screen
        canvas = tk.Canvas(self.content_frame, bg=THEME["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg"])

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        init_w = self.content_frame.winfo_width() - 20 if self.content_frame.winfo_width() > 20 else 800
        win_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=init_w)
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(win_id, width=max(320, e.width))
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(e):
            try:
                canvas.yview_scroll(-1 * (e.delta // 120), "units")
            except tk.TclError:
                pass

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Destroy>", lambda e: (canvas.unbind_all("<MouseWheel>"), self._hide_stats_tooltip()))

        stats_wrap = tk.Frame(
            scroll_frame, bg=THEME["bg"],
            padx=12 if is_compact else 20, pady=8
        )
        stats_wrap.pack(fill="both", expand=True)

        # ── Header + Peak Focus Window Badge + JSON Backup buttons ──
        stats_hdr = tk.Frame(stats_wrap, bg=THEME["bg"])
        stats_hdr.pack(fill="x", pady=(0, 14))

        tk.Label(
            stats_hdr, text="📊 Statistics",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(side="left", anchor="center")

        backup_bar = tk.Frame(stats_hdr, bg=THEME["bg"])
        backup_bar.pack(side="right", anchor="e")

        self.import_backup_btn = self._make_secondary_button(
            backup_bar, "📥 Import Backup", self._import_forest_backup
        )
        self.import_backup_btn.pack(side="right", padx=(6 if is_compact else 8, 0))

        self.export_backup_btn = self._make_secondary_button(
            backup_bar, "📤 Export Forest (.json)", self._export_forest_json
        )
        self.export_backup_btn.pack(side="right")

        peak = db.get_peak_focus_window()
        self.peak_focus_badge = tk.Label(
            stats_hdr, text=f"{peak['icon']} {peak['text']}",
            font=self.font_xs_bold,
            bg=THEME["accent_light"], fg=THEME["green_dark"],
            padx=8 if is_compact else 10, pady=4,
            highlightbackground=THEME["border"], highlightthickness=1
        )
        self.peak_focus_badge.pack(side="right", padx=(0, 8))

        # ── Compact 6-Card KPI Row & Editable Daily Goal Ring ──
        cards = tk.Frame(stats_wrap, bg=THEME["bg"])
        cards.pack(fill="x", pady=(0, 16))
        self.stats_kpi_frame = cards

        today_secs = db.get_today_seconds()
        today_mins = int(today_secs // 60)
        weekly_secs = db.get_weekly_seconds()
        total_secs = db.get_total_focused_seconds()
        total_trees = db.get_total_trees()
        completed = db.get_completed_count() + db.get_completed_tasks_count()
        streak = db.get_streak()

        card_data = [
            ("Today", self._format_hours(today_secs), "⏱️", THEME["blue_soft"]),
            ("This Week", self._format_hours(weekly_secs), "📅", THEME["accent"]),
            ("All Time", self._format_hours(total_secs), "🕐", THEME["brown"]),
            ("Trees", str(total_trees), "🌳", THEME["green_med"]),
            ("Sessions", str(completed), "✅", THEME["yellow_soft"]),
            ("Streak", f"{streak}d", "🔥", THEME["streak_fire"]),
        ]

        kpi_cols = 6 if vw >= 960 else 3
        for col_idx in range(kpi_cols):
            cards.columnconfigure(col_idx, weight=1, uniform="kpi_col")

        self.daily_goal_ring_svg = get_daily_goal_ring_svg(
            today_mins, self.daily_goal_minutes, THEME["blue_soft"], THEME["bg_dark"]
        )

        self.stats_kpi_cards = []
        for i, (label, value, icon, color) in enumerate(card_data):
            r_idx = i // kpi_cols
            c_idx = i % kpi_cols
            card = tk.Frame(
                cards, bg=THEME["bg_card"],
                highlightbackground=THEME["border"], highlightthickness=1
            )
            card.grid(row=r_idx, column=c_idx, padx=5, pady=5, sticky="nsew")
            self.stats_kpi_cards.append(card)

            inner = tk.Frame(card, bg=THEME["bg_card"])
            inner.pack(fill="both", expand=True, padx=14, pady=12)

            if i == 0:
                # Today card with 44x44 circular progress ring + inline-editable Goal
                top_kpi = tk.Frame(inner, bg=THEME["bg_card"])
                top_kpi.pack(fill="x")

                left_kpi = tk.Frame(top_kpi, bg=THEME["bg_card"])
                left_kpi.pack(side="left", fill="both", expand=True)
                tk.Label(left_kpi, text=icon, font=self.font_emoji, bg=THEME["bg_card"]).pack(anchor="w")
                tk.Label(
                    left_kpi, text=value, font=self.font_stat_inline if kpi_cols == 6 else self.font_stat_num,
                    fg=color, bg=THEME["bg_card"]
                ).pack(anchor="w")
                tk.Label(
                    left_kpi, text=label, font=self.font_stat_label,
                    fg=THEME["fg_muted"], bg=THEME["bg_card"]
                ).pack(anchor="w")

                ring_cv = tk.Canvas(
                    top_kpi, width=44, height=44, bg=THEME["bg_card"], highlightthickness=0
                )
                ring_cv.pack(side="right", anchor="ne", padx=(4, 0))
                self.daily_goal_ring_canvas = ring_cv
                self._draw_goal_ring_canvas(ring_cv, today_mins, self.daily_goal_minutes, color)

                goal_holder = tk.Frame(inner, bg=THEME["bg_card"])
                goal_holder.pack(fill="x", pady=(4, 0))
                self.daily_goal_label = tk.Label(
                    goal_holder, text=f"Goal: {self.daily_goal_minutes}m ✏️",
                    font=self.font_xs, fg=THEME["fg_muted"], bg=THEME["bg_card"],
                    cursor="hand2", anchor="w"
                )
                self.daily_goal_label.pack(side="left")
                self.daily_goal_label.bind(
                    "<Button-1>", lambda e, h=goal_holder: self._edit_daily_goal_inline(h)
                )
                self.daily_goal_label.bind(
                    "<Enter>", lambda e: self.daily_goal_label.configure(fg=THEME["accent"])
                )
                self.daily_goal_label.bind(
                    "<Leave>", lambda e: self.daily_goal_label.configure(fg=THEME["fg_muted"])
                )
            else:
                tk.Label(inner, text=icon, font=self.font_emoji, bg=THEME["bg_card"]).pack(anchor="w")
                tk.Label(
                    inner, text=value, font=self.font_stat_inline if kpi_cols == 6 else self.font_stat_num,
                    fg=color, bg=THEME["bg_card"]
                ).pack(anchor="w")
                tk.Label(
                    inner, text=label, font=self.font_stat_label,
                    fg=THEME["fg_muted"], bg=THEME["bg_card"]
                ).pack(anchor="w")

        # ── 90-Day Forest Activity Heatmap & Weekly Bar Toggle ──
        activity_card = tk.Frame(
            stats_wrap, bg=THEME["bg_card"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        activity_card.pack(fill="x", pady=(0, 16))

        act_hdr = tk.Frame(activity_card, bg=THEME["bg_card"])
        act_hdr.pack(fill="x", padx=20, pady=(14, 10))

        act_title = "📈 This Week & 90-Day Activity" if self.stats_activity_mode == "both" else (
            "🟩 90-Day Forest Activity Heatmap" if self.stats_activity_mode == "heatmap" else "📈 This Week"
        )
        tk.Label(
            act_hdr, text=act_title,
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(side="left", anchor="center")

        toggle_bar = tk.Frame(
            act_hdr, bg=THEME["border"], padx=1, pady=1
        )
        toggle_bar.pack(side="right", anchor="center")
        self.activity_toggle_buttons = {}
        for m_id, m_label in [("week", "This Week"), ("heatmap", "90-Day Heatmap"), ("both", "Both")]:
            is_act = (self.stats_activity_mode == m_id)
            t_btn = tk.Label(
                toggle_bar, text=m_label, font=self.font_xs_bold,
                bg=THEME["accent"] if is_act else THEME["bg_dark"],
                fg=THEME.get("accent_fg", "#FFFFFF") if is_act else THEME["fg_muted"],
                padx=9, pady=4, cursor="hand2"
            )
            t_btn.pack(side="left", padx=1)
            t_btn.bind("<Button-1>", lambda e, mid=m_id: self._set_stats_activity_mode(mid))
            self.activity_toggle_buttons[m_id] = t_btn

        if self.stats_activity_mode in ("heatmap", "both"):
            heatmap_data = db.get_heatmap_data(days=91)
            self.heatmap_data = heatmap_data
            hm_canvas = tk.Canvas(
                activity_card, bg=THEME["bg_card"], highlightthickness=0, height=156
            )
            hm_canvas.pack(fill="x", padx=20, pady=(0, 8))
            self.heatmap_canvas = hm_canvas
            hm_canvas.bind("<Configure>", lambda e, d=heatmap_data: self._draw_heatmap_grid(hm_canvas, d))
            self.root.after(80, lambda d=heatmap_data: self._draw_heatmap_grid(hm_canvas, d))
        else:
            self.heatmap_canvas = None

        if self.stats_activity_mode in ("week", "both"):
            chart_canvas = tk.Canvas(
                activity_card, bg=THEME["bg_card"], highlightthickness=0, height=168
            )
            chart_canvas.pack(fill="x", padx=20, pady=(0, 14))
            self.weekly_chart_canvas = chart_canvas
            chart_canvas.bind("<Configure>", lambda e: self._draw_weekly_chart(chart_canvas))
            self.root.after(100, lambda: self._draw_weekly_chart(chart_canvas))
        else:
            self.weekly_chart_canvas = None

        # ── Two-Column Breakdown: Study Time by Task (1.4fr) & Species Donut Chart (1fr) ──
        breakdown_row = tk.Frame(stats_wrap, bg=THEME["bg"])
        breakdown_row.pack(fill="x", pady=(0, 16))
        self.stats_breakdown_row = breakdown_row

        if vw >= 780:
            breakdown_row.columnconfigure(0, weight=14, uniform="bd_col")
            breakdown_row.columnconfigure(1, weight=10, uniform="bd_col")
            task_grid_kw = {"row": 0, "column": 0, "padx": (0, 8), "sticky": "nsew"}
            species_grid_kw = {"row": 0, "column": 1, "padx": (8, 0), "sticky": "nsew"}
        else:
            breakdown_row.columnconfigure(0, weight=1)
            task_grid_kw = {"row": 0, "column": 0, "pady": (0, 12), "sticky": "nsew"}
            species_grid_kw = {"row": 1, "column": 0, "sticky": "nsew"}

        # Left Column: Study Time by Task
        task_card = tk.Frame(
            breakdown_row, bg=THEME["bg_card"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        task_card.grid(**task_grid_kw)

        tk.Label(
            task_card, text="🎯 Study Time by Task",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(anchor="w", padx=18, pady=(14, 10))

        task_stats = db.get_task_stats()
        if not task_stats:
            tk.Label(
                task_card, text="Complete a focus session to see study breakdown by task.",
                font=self.font_small, fg=THEME["fg_light"], bg=THEME["bg_card"],
                wraplength=260, justify="left"
            ).pack(anchor="w", padx=18, pady=(4, 16))
        else:
            max_task_sec = max(t["total_seconds"] for t in task_stats) or 1
            for t in task_stats[:7]:
                t_row = tk.Frame(task_card, bg=THEME["bg_card"])
                t_row.pack(fill="x", padx=18, pady=4)

                t_title = t["task"]
                if len(t_title) > 18:
                    t_title = t_title[:17].rstrip() + "…"
                tk.Label(
                    t_row, text=f"• {t_title}", font=self.font_small,
                    fg=THEME["fg"], bg=THEME["bg_card"], width=16, anchor="w"
                ).pack(side="left")

                bar_c = tk.Frame(t_row, bg=THEME["bg_dark"], height=10)
                bar_c.pack(side="left", fill="x", expand=True, padx=8)
                bar_c.pack_propagate(False)

                frac = min(1.0, t["total_seconds"] / max_task_sec)
                tk.Frame(bar_c, bg=THEME["accent"], height=10).place(
                    relx=0, rely=0, relwidth=max(0.03, frac), relheight=1
                )

                hrs_str = self._format_hours(t["total_seconds"])
                cnt_str = f"{t['tree_count']} tree" + ("s" if t["tree_count"] != 1 else "")
                tk.Label(
                    t_row, text=f"{hrs_str} ({cnt_str})", font=(self.family_mono, 8),
                    fg=THEME["fg_muted"], bg=THEME["bg_card"], anchor="e"
                ).pack(side="right")

            tk.Frame(task_card, bg=THEME["bg_card"], height=12).pack()

        # Right Column: Forest Species Breakdown Donut Chart
        species_card = tk.Frame(
            breakdown_row, bg=THEME["bg_card"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        species_card.grid(**species_grid_kw)

        tk.Label(
            species_card, text="🌲 Species Breakdown",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(anchor="w", padx=18, pady=(14, 10))

        breakdown = db.get_species_breakdown()
        self.species_breakdown_data = breakdown
        self.species_donut_svg = get_species_donut_svg(breakdown, THEME["bg_dark"], THEME["fg_muted"])

        sp_body = tk.Frame(species_card, bg=THEME["bg_card"])
        sp_body.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        donut_cv = tk.Canvas(
            sp_body, width=124, height=124, bg=THEME["bg_card"], highlightthickness=0
        )
        donut_cv.pack(side="left", anchor="center", padx=(0, 12))
        self.species_donut_canvas = donut_cv
        self._draw_species_donut_canvas(donut_cv, breakdown)

        legend_box = tk.Frame(sp_body, bg=THEME["bg_card"])
        legend_box.pack(side="left", fill="both", expand=True, anchor="center")

        total_sp_secs = sum(item["total_seconds"] for item in breakdown)
        if total_sp_secs <= 0:
            tk.Label(
                legend_box, text="No trees planted yet",
                font=self.font_small_bold, fg=THEME["fg_muted"], bg=THEME["bg_card"], anchor="w"
            ).pack(anchor="w", pady=(0, 4))

        for item in breakdown:
            l_row = tk.Frame(legend_box, bg=THEME["bg_card"])
            l_row.pack(fill="x", pady=3)
            tk.Frame(l_row, bg=item["color"], width=10, height=10).pack(side="left", padx=(0, 6))
            tk.Label(
                l_row, text=item["name"], font=self.font_xs_bold,
                fg=THEME["fg"], bg=THEME["bg_card"], anchor="w"
            ).pack(side="left")
            pct = int(round(item["share"] * 100)) if total_sp_secs > 0 else 0
            val_txt = f"{item['minutes']}m ({pct}%) • {item['tree_count']}"
            tk.Label(
                l_row, text=val_txt, font=(self.family_mono, 8),
                fg=THEME["fg_muted"], bg=THEME["bg_card"], anchor="e"
            ).pack(side="right")

        # ── Clean Recent Sessions Log (filters out 0m sessions by default) ──
        recent_frame = tk.Frame(
            stats_wrap, bg=THEME["bg_card"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        recent_frame.pack(fill="x", pady=(0, 18))

        recent_hdr = tk.Frame(recent_frame, bg=THEME["bg_card"])
        recent_hdr.pack(fill="x", padx=20, pady=(14, 10))

        tk.Label(
            recent_hdr, text="📋 Recent Sessions",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(side="left", anchor="w")

        chk_txt = ("☑ Hide 0m sessions" if self.hide_zero_min_sessions else "☐ Hide 0m sessions")
        self.hide_zero_sessions_btn = tk.Label(
            recent_hdr, text=chk_txt, font=self.font_xs_bold,
            bg=THEME["bg_dark"], fg=THEME["fg_muted"],
            padx=8, pady=3, cursor="hand2",
            highlightbackground=THEME["border"], highlightthickness=1
        )
        self.hide_zero_sessions_btn.pack(side="right", anchor="e")
        self.hide_zero_sessions_btn.bind("<Button-1>", lambda e: self._toggle_hide_zero_sessions())

        all_sessions = db.get_all_sessions()
        if self.hide_zero_min_sessions:
            sessions = [
                s for s in all_sessions
                if s.get("completed") == 1 and int(s.get("actual_focused_seconds", 0) // 60) > 0
            ][:10]
        else:
            sessions = all_sessions[:10]

        if not sessions:
            empty_msg = (
                "No completed sessions (> 0m) yet. Start studying! 🌱"
                if self.hide_zero_min_sessions else "No sessions yet. Start studying! 🌱"
            )
            tk.Label(
                recent_frame, text=empty_msg,
                font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg_card"]
            ).pack(padx=20, pady=(0, 15))
        else:
            for s in sessions:
                row = tk.Frame(recent_frame, bg=THEME["bg_card"])
                row.pack(fill="x", padx=20, pady=3)

                stage = STAGE_LABELS.get(s["tree_stage"], "🌱 Seed")
                sp_id = s.get("tree_species", "oak") if isinstance(s, dict) else s["tree_species"]
                sp_meta = SPECIES_METADATA.get(sp_id, {})
                sp_icon = sp_meta.get("icon", "🌳")
                sp_name = sp_meta.get("name", "Tree")
                t_name = s.get("task_name", "General Study")
                dt = datetime.fromisoformat(s["start_time"])
                mins = int(s["actual_focused_seconds"] // 60)
                status = "✅" if s["completed"] else "⏸️"

                tk.Label(
                    row, text=f"{mins}m  •  {dt.strftime('%b %d, %H:%M')}",
                    font=(self.family_mono, 9), fg=THEME["fg_muted"], bg=THEME["bg_card"]
                ).pack(side="right", padx=(8, 0))

                tk.Label(
                    row, text=f"{status} {sp_icon} {stage} ({sp_name})  •  🎯 {t_name}",
                    font=self.font_body, fg=THEME["fg"], bg=THEME["bg_card"], anchor="w"
                ).pack(side="left", fill="x", expand=True)

            tk.Frame(recent_frame, bg=THEME["bg_card"], height=10).pack()

    def _export_forest_json(self, filepath=None, silent=False):
        """Export planted trees, study history, streaks, and achievements to JSON."""
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Forest Backup",
                defaultextension=".json",
                initialfile=f"grow-your-forest-backup-{date.today().isoformat()}.json",
                filetypes=[("JSON Backup", "*.json"), ("All Files", "*.*")],
            )
        if not filepath:
            return None
        try:
            data = db.export_to_json_file(filepath)
            if not silent:
                messagebox.showinfo(
                    "Export Complete 🌱",
                    f"Saved your forest backup cleanly!\n\n"
                    f"• Planted sessions: {len(data.get('sessions', []))}\n"
                    f"• Study days logged: {len(data.get('daily_log', []))}\n"
                    f"• File: {os.path.basename(filepath)}",
                    parent=self.root,
                )
            return data
        except Exception as e:
            if not silent:
                messagebox.showerror(
                    "Export Failed",
                    f"Could not save backup file:\n{e}",
                    parent=self.root,
                )
            return None

    def _import_forest_backup(self, filepath=None, silent=False):
        """Restore planted trees, study history, streaks, and achievements from JSON."""
        if not filepath:
            filepath = filedialog.askopenfilename(
                parent=self.root,
                title="Import Forest Backup",
                filetypes=[("JSON Backup", "*.json"), ("All Files", "*.*")],
            )
        if not filepath:
            return None
        try:
            summary = db.import_from_json_file(filepath)
            self.daily_goal_minutes = db.get_daily_goal_minutes()
            saved_theme = db.get_setting("theme", self.current_theme)
            if saved_theme in THEMES and saved_theme != self.current_theme:
                self._set_theme(saved_theme)
            else:
                self._build_header()
                if self.current_view == "stats":
                    self._show_stats_view()
                elif self.current_view == "forest":
                    self._show_forest_view()
                elif self.current_view == "achievements":
                    self._show_achievements_view()
                elif self.current_view == "timer":
                    self._show_timer_view()
            if not silent:
                messagebox.showinfo(
                    "Backup Restored 🌳",
                    f"Your forest data was restored successfully!\n\n"
                    f"• Sessions restored: {summary.get('sessions_restored', 0)}\n"
                    f"• Study days restored: {summary.get('days_restored', 0)}\n"
                    f"• Unlocked achievements: {summary.get('achievements_restored', 0)}",
                    parent=self.root,
                )
            return summary
        except Exception as e:
            if not silent:
                messagebox.showerror(
                    "Import Failed",
                    f"Could not restore backup file:\n{e}",
                    parent=self.root,
                )
            return None

    def _draw_weekly_chart(self, canvas):
        """Draw a bar chart of daily study time for the last 7 days."""
        try:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 50 or h < 50:
                self.root.after(100, lambda: self._draw_weekly_chart(canvas))
                return
            canvas.delete("all")

            data = db.get_daily_data_for_week()
            max_val = max((d["seconds"] for d in data), default=1)
            if max_val < 1:
                max_val = 1

            bar_width = (w - 60) / 7
            chart_h = h - 50
            left_margin = 30

            # Y-axis labels
            for i in range(5):
                y = 15 + chart_h * (1 - i / 4)
                val = max_val * i / 4 / 60  # in minutes
                canvas.create_text(
                    left_margin - 5, y,
                    text=f"{int(val)}m", font=(self.family_mono, 8),
                    fill=THEME["fg_light"], anchor="e"
                )
                canvas.create_line(
                    left_margin, y, w - 10, y,
                    fill=THEME["bg_dark"], dash=(2, 4)
                )

            for i, d in enumerate(data):
                x = left_margin + i * bar_width + bar_width * 0.2
                bw = bar_width * 0.6
                bar_h = (d["seconds"] / max_val) * chart_h if max_val > 0 else 0
                bar_h = max(bar_h, 2)

                y_top = 15 + chart_h - bar_h
                y_bot = 15 + chart_h

                # Highlight today
                is_today = d["date"] == date.today().isoformat()
                color = THEME["accent"] if is_today else THEME["bar_fill"]

                canvas.create_rectangle(
                    x, y_top, x + bw, y_bot,
                    fill=color, outline=""
                )

                # Day label
                canvas.create_text(
                    x + bw / 2, y_bot + 12,
                    text=d["day_name"], font=self.font_small,
                    fill=THEME["fg"] if is_today else THEME["fg_muted"]
                )

                # Value on top
                if d["seconds"] > 0:
                    canvas.create_text(
                        x + bw / 2, y_top - 8,
                        text=f"{int(d['seconds'] // 60)}m",
                        font=(self.family_mono, 8), fill=THEME["fg_muted"]
                    )
        except tk.TclError:
            pass

    # ──────────────── Achievements View ────────────────

    def _get_achievement_progress_map(self):
        """Return {achievement_id: (current, target, suffix)} from persisted study data."""
        sessions = db.get_all_sessions()
        total_trees = sum(1 for s in sessions if s["actual_focused_seconds"] >= 30)
        completed_count = sum(1 for s in sessions if s["completed"] == 1)
        total_seconds = sum(s["actual_focused_seconds"] for s in sessions)
        max_session = max((s["actual_focused_seconds"] for s in sessions if s["completed"] == 1), default=0)
        streak = db.get_streak()
        species_used = {s.get("tree_species") or "oak" for s in sessions if s["actual_focused_seconds"] >= 30}
        mature_species = {
            s.get("tree_species") or "oak"
            for s in sessions
            if s.get("tree_stage") in ("mature", "flourishing")
        }
        return {
            "first_seed": (min(completed_count, 1), 1, ""),
            "first_tree": (min(int(total_seconds // 60), 60), 60, "m"),
            "growing_forest": (min(total_trees, 10), 10, ""),
            "deep_focus": (min(int(max_session // 60), 120), 120, "m"),
            "consistency": (min(streak, 7), 7, "d"),
            "century": (min(int(total_seconds // 3600), 100), 100, "h"),
            "fifty_trees": (min(total_trees, 50), 50, ""),
            "marathon": (min(int(max_session // 60), 90), 90, "m"),
            "sakura_season": (1 if "cherry_blossom" in mature_species else 0, 1, ""),
            "evergreen": (1 if "pine" in mature_species else 0, 1, ""),
            "ancient_guardian": (1 if "angel_oak" in mature_species else 0, 1, ""),
            "botanist": (min(len(species_used), 7), 7, ""),
        }

    def _get_midnight_countdown_text(self):
        """Return 'Time Left: Xh Ym' until local midnight."""
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        rem_secs = max(0, int((tomorrow - now).total_seconds()))
        hrs = rem_secs // 3600
        mins = (rem_secs % 3600) // 60
        return f"Time Left: {hrs}h {mins:02d}m"

    def _tick_daily_countdown(self, active_date_str):
        """Live tick countdown to midnight while on Achievements view; auto-rotates at midnight."""
        if self.current_view != "achievements":
            self._daily_countdown_after = None
            return
        if date.today().isoformat() != active_date_str:
            self._show_achievements_view()
            return
        try:
            if self.daily_countdown_label is not None and self.daily_countdown_label.winfo_exists():
                self.daily_countdown_label.configure(text=self._get_midnight_countdown_text())
        except tk.TclError:
            self._daily_countdown_after = None
            return
        self._daily_countdown_after = self.root.after(15000, lambda d=active_date_str: self._tick_daily_countdown(d))

    def _claim_daily_challenge(self, challenge_id):
        """Claim a completed daily challenge reward and grant its tree seed."""
        ok, inv, sp_id, _ = db.claim_daily_challenge_reward(challenge_id)
        if ok:
            if sp_id in SPECIES_METADATA:
                self.selected_species = sp_id
                db.set_setting("selected_species", sp_id)
            if self.current_view == "achievements":
                self._show_achievements_view()
        return ok

    def _reroll_daily_challenge(self, challenge_id):
        """Swap one unclaimed daily challenge for another random quest (1/day)."""
        ok, _ = db.reroll_daily_challenge(challenge_id)
        if ok and self.current_view == "achievements":
            self._show_achievements_view()
        return ok

    def _dismiss_active_quest(self):
        """Dismiss the active Daily Quest banner on the Study tab."""
        self.active_quest = None
        if self.current_view == "timer":
            self._show_timer_view()

    def _launch_daily_challenge(self, ch):
        """Pre-configure the Study tab from a Daily Challenge preset and switch to it."""
        if not ch or ch.get("completed") or ch.get("claimed"):
            return
        if self.session_active:
            self._show_timer_view()
            return

        preset = db.get_challenge_preset(ch)
        dur_mins = preset["duration_minutes"]
        self.planned_duration = dur_mins * 60
        self.focused_seconds = 0.0

        tag = preset.get("tag")
        preset_task = preset.get("task")
        cur = (self.current_task or "").strip()
        if tag:
            if not db._task_matches_tag(cur, tag.lower()):
                self.current_task = f"{tag}:"
        elif preset_task:
            if not cur or cur == "General Study" or cur in {c["title"] for c in db.DAILY_CHALLENGE_POOL}:
                self.current_task = preset_task

        target_sp = preset.get("species")
        if target_sp in SPECIES_METADATA and db.is_species_unlocked(target_sp):
            self.selected_species = target_sp
            db.set_setting("selected_species", target_sp)

        if preset.get("rain") and not audio_player.player.is_playing:
            self._toggle_rain_sound()

        self.active_quest = {
            "id": ch["id"],
            "title": ch["title"],
            "icon": ch["icon"],
            "duration": dur_mins,
        }

        target_theme = preset.get("theme")
        if target_theme in THEMES and target_theme != self.current_theme:
            self._set_theme(target_theme)
        self._show_timer_view()

    def _set_ach_filter(self, filter_mode):
        """Switch milestone filter between 'all', 'unlocked', and 'in_progress'."""
        if filter_mode in ("all", "unlocked", "in_progress"):
            self.ach_filter = filter_mode
            if self.current_view == "achievements":
                self._show_achievements_view()

    def _tick_claim_pulse(self):
        """Animate ready Claim Reward buttons with a subtle golden/emerald glow pulse."""
        if self.current_view != "achievements" or not self._claim_pulse_buttons:
            self._claim_pulse_after = None
            return
        self._claim_pulse_phase = (self._claim_pulse_phase + 1) % 2
        is_dark = self.current_theme in ("night", "chill")
        if self._claim_pulse_phase == 0:
            bg_c = "#2E7D32" if not is_dark else "#3B7A57"
            bd_c = "#E5B454"
        else:
            bg_c = "#3D8F41" if not is_dark else "#49946A"
            bd_c = "#F7D99C"
        alive = []
        for btn in self._claim_pulse_buttons:
            try:
                if btn.winfo_exists():
                    btn.configure(bg=bg_c, highlightbackground=bd_c)
                    alive.append(btn)
            except tk.TclError:
                pass
        self._claim_pulse_buttons = alive
        if alive:
            self._claim_pulse_after = self.root.after(480, self._tick_claim_pulse)
        else:
            self._claim_pulse_after = None

    def _configure_darkwood_scrollbar(self):
        """Style vertical scrollbar with dark espresso track (#231B16) and warm bronze thumb (#5C4938)."""
        try:
            style = ttk.Style(self.root)
            if "clam" in style.theme_names():
                style.theme_use("clam")
            is_dark = self.current_theme in ("night", "chill")
            trough = "#231B16" if is_dark else scenery.mix(THEME["bg_dark"], "#231B16", 0.35)
            thumb = "#5C4938" if is_dark else scenery.mix(THEME["border"], "#5C4938", 0.55)
            thumb_active = "#745C48" if is_dark else scenery.mix(THEME["accent"], "#5C4938", 0.45)
            style.configure(
                "DarkWood.Vertical.TScrollbar",
                troughcolor=trough,
                background=thumb,
                bordercolor=trough,
                darkcolor=thumb,
                lightcolor=thumb,
                arrowcolor="#B89B7E" if is_dark else THEME["fg_muted"],
                gripcount=0,
                width=10,
                relief="flat",
            )
            style.map(
                "DarkWood.Vertical.TScrollbar",
                background=[("active", thumb_active), ("pressed", "#8A7058")],
            )
            return "DarkWood.Vertical.TScrollbar"
        except tk.TclError:
            return "Vertical.TScrollbar"

    def _get_medallion_palette(self, ach_id, unlocked):
        """Return themed botanical medallion colors (bg, glow, outline, icon) for an achievement."""
        if not unlocked:
            return {
                "bg": THEME["bg_dark"],
                "glow": None,
                "outline": THEME["border"],
                "icon": THEME["fg_light"],
            }
        palettes = {
            "botanist": {
                "bg": "#3B7A6B",
                "glow": "#4C9482",
                "outline": "#E6B85C",
                "icon": "#E6B85C",
            },
            "evergreen": {
                "bg": "#2E6F40",
                "glow": "#3D8A53",
                "outline": "#7BC98F",
                "icon": "#7BC98F",
            },
            "growing_forest": {
                "bg": "#2E6F40",
                "glow": "#3D8A53",
                "outline": "#7BC98F",
                "icon": "#7BC98F",
            },
            "first_seed": {
                "bg": "#4B8B3B",
                "glow": "#60A34E",
                "outline": "#A3D977",
                "icon": "#A3D977",
            },
            "first_tree": {
                "bg": "#4B8B3B",
                "glow": "#60A34E",
                "outline": "#A3D977",
                "icon": "#A3D977",
            },
            "sakura_season": {
                "bg": "#9E3B62",
                "glow": "#B84E77",
                "outline": "#FFB7D5",
                "icon": "#FFB7D5",
            },
            "marathon": {
                "bg": "#B86B28",
                "glow": "#CF803B",
                "outline": "#FFD180",
                "icon": "#FFD180",
            },
        }
        return palettes.get(
            ach_id,
            {
                "bg": "#7D5A2A",
                "glow": "#9C7338",
                "outline": "#F5C26B",
                "icon": "#F7D99C",
            },
        )

    def _render_achievement_card(self, card_canvas, w, h, ach, cur, target, suffix):
        """Render a clean r=12 milestone card with themed medallion, radial glow, and gold pill."""
        card_canvas.delete("all")
        if w < 40 or h < 40:
            return
        unlocked = bool(ach["unlocked"])
        is_dark = self.current_theme in ("night", "chill")
        med = self._get_medallion_palette(ach.get("id", ""), unlocked)

        if unlocked:
            card_bg = scenery.mix(THEME["bg_card"], "#F5C26B", 0.11 if is_dark else 0.16)
            card_border = scenery.mix(THEME["bg_card"], "#F5C26B", 0.42)
            title_fg = THEME["fg"]
            desc_fg = THEME["fg_muted"]
            shadow_col = scenery.mix(THEME["bg"], "#000000", 0.28 if is_dark else 0.12)
            card_canvas.create_polygon(
                _rounded_rect_pts(2, 3, w - 1, h - 1, 12),
                fill=shadow_col, outline="", tags=("ach_card_shadow",),
            )
        else:
            card_bg = scenery.mix(THEME["bg_card"], THEME["bg_dark"], 0.44)
            card_border = THEME["border"]
            title_fg = THEME["fg_muted"]
            desc_fg = THEME["fg_light"]

        # Single smooth 1px rounded card border
        card_canvas.create_polygon(
            _rounded_rect_pts(1, 1, w - 2, h - 3 if unlocked else h - 2, 12),
            fill=card_bg, outline=card_border, width=1, tags=("ach_card_border",),
        )
        if unlocked:
            hi_col = scenery.mix(card_border, "#FFF4D6", 0.42 if is_dark else 0.65)
            card_canvas.create_line(14, 2, max(16, w - 14), 2, fill=hi_col, width=1)

        # Left 42x42 circular medallion with inner radial glow when unlocked
        iy0 = max(16, (h - 42) // 2 - 2)
        iy1 = iy0 + 42
        card_canvas.create_oval(
            16, iy0, 58, iy1,
            fill=med["bg"], outline=med["outline"], width=1, tags=("ach_icon_bg",),
        )
        if unlocked and med["glow"]:
            card_canvas.create_oval(
                21, iy0 + 5, 53, iy1 - 5,
                fill=med["glow"], outline="", tags=("ach_icon_glow",),
            )
        card_canvas.create_text(
            37, (iy0 + iy1) / 2, text=(ach["icon"] if unlocked else "🔒"),
            font=self.font_emoji_large, fill=med["icon"], tags=("ach_icon_text",),
        )

        # Top-right borderless gold-amber pill when unlocked, progress fraction when locked
        if unlocked:
            pill_lbl = "✦ Unlocked"
            pill_w = max(78, self._forest_label_font.measure(pill_lbl) + 20)
            bx1 = w - 16
            bx0 = bx1 - pill_w
            by0, by1 = 15, 37
            pill_bg = (scenery.mix(card_bg, "#F5C26B", 0.20) if is_dark
                       else scenery.mix("#2C2218", "#F5C26B", 0.24))
            card_canvas.create_polygon(
                _rounded_rect_pts(bx0, by0, bx1, by1, 11),
                fill=pill_bg, outline="", width=0, tags=("ach_unlocked_pill",),
            )
            card_canvas.create_text(
                (bx0 + bx1) / 2, (by0 + by1) / 2,
                text=pill_lbl, font=(self.family_sans_semi, 8, "bold"),
                fill="#F7D99C", tags=("ach_unlocked_text",),
            )
            if ach["unlocked_at"]:
                try:
                    dt = datetime.fromisoformat(ach["unlocked_at"])
                    card_canvas.create_text(
                        w - 16, h - 18, text=dt.strftime("%b %d, %Y"),
                        anchor="e", font=self.font_xs, fill=THEME["fg_light"],
                    )
                except Exception:
                    pass
            desc_right_pad = pill_w + 26
        else:
            frac_txt = f"{cur}{suffix}/{target}{suffix}"
            card_canvas.create_text(
                w - 16, 25, text=frac_txt, anchor="e",
                font=(self.family_mono, 9, "bold"), fill=THEME["fg"],
            )
            bar_x0, bar_x1 = 72, max(92, w - 16)
            bar_y0, bar_y1 = h - 22, h - 15
            track_col = "#1A1411" if is_dark else scenery.mix(THEME["bar_bg"], THEME["border"], 0.45)
            fill_col = "#E5B454" if is_dark else THEME["accent"]
            card_canvas.create_polygon(
                _rounded_rect_pts(bar_x0, bar_y0, bar_x1, bar_y1, 3),
                fill=track_col, outline=THEME["border"], width=1,
            )
            ratio = min(1.0, max(0.0, cur / float(max(1, target))))
            if ratio > 0:
                fill_w = max(8.0, (bar_x1 - bar_x0) * ratio)
                card_canvas.create_polygon(
                    _rounded_rect_pts(bar_x0, bar_y0, min(bar_x1, bar_x0 + fill_w), bar_y1, 3),
                    fill=fill_col, outline="",
                )
            desc_right_pad = 90

        text_x = 72
        text_w = max(120, w - text_x - desc_right_pad)
        card_canvas.create_text(
            text_x, 18, text=ach["name"], anchor="nw",
            font=self.font_card_title, fill=title_fg, width=text_w,
        )
        card_canvas.create_text(
            text_x, 42, text=ach["description"], anchor="nw",
            font=self.font_small, fill=desc_fg, width=text_w,
        )

    def _show_achievements_view(self):
        self.current_view = "achievements"
        self._clear_content()

        achievements = db.get_achievements()
        unlocked_count = sum(1 for a in achievements if a["unlocked"])
        locked_count = len(achievements) - unlocked_count
        progress_map = self._get_achievement_progress_map()
        daily_state = db.get_daily_challenges_state()
        rerolls_left = daily_state.get("rerolls_left", 0)
        seed_inv = db.get_seed_inventory()
        total_seeds = sum(seed_inv.values())
        is_dark = self.current_theme in ("night", "chill")
        vw, _ = self._get_viewport_size()
        use_two_cols = vw >= 860

        # ── Top Header Row ──
        hdr = tk.Frame(self.content_frame, bg=THEME["bg"])
        hdr.pack(fill="x", pady=(0, 12))

        tk.Label(
            hdr, text="🏆 Achievements & Daily Hub",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(side="left")

        hdr_badge_bg = (scenery.mix(THEME["bg_card"], "#F5C26B", 0.18) if is_dark
                        else scenery.mix("#2C2218", "#F5C26B", 0.22))
        tk.Label(
            hdr, text=f"✦ {unlocked_count} / {len(achievements)} Unlocked",
            font=self.font_small_bold, fg="#F7D99C",
            bg=hdr_badge_bg, padx=12, pady=4, highlightthickness=0,
        ).pack(side="right", pady=4)

        self.seed_inventory_badge = tk.Label(
            hdr, text=f"🌱 Seed Bag: {total_seeds}",
            font=self.font_small_bold, fg=THEME["green_dark"],
            bg=THEME["accent_light"], padx=10, pady=4,
            highlightbackground=THEME["border"], highlightthickness=1
        )
        self.seed_inventory_badge.pack(side="right", padx=(0, 8), pady=4)

        # ── 2-Column Progression Hub (~40% Daily Challenges | ~60% Milestones) ──
        hub_row = tk.Frame(self.content_frame, bg=THEME["bg"])
        hub_row.pack(fill="both", expand=True)

        if use_two_cols:
            hub_row.columnconfigure(0, weight=4, uniform="hub_col")
            hub_row.columnconfigure(1, weight=6, uniform="hub_col")
            hub_row.rowconfigure(0, weight=1)
            left_grid_kw = {"row": 0, "column": 0, "padx": (0, 12), "sticky": "nsew"}
            right_grid_kw = {"row": 0, "column": 1, "sticky": "nsew"}
        else:
            hub_row.columnconfigure(0, weight=1)
            hub_row.rowconfigure(1, weight=1)
            left_grid_kw = {"row": 0, "column": 0, "pady": (0, 12), "sticky": "ew"}
            right_grid_kw = {"row": 1, "column": 0, "sticky": "nsew"}

        # ── LEFT COLUMN: Daily Challenges (~40% width) ──
        daily_panel = tk.Frame(
            hub_row, bg=THEME["bg_card"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        daily_panel.grid(**left_grid_kw)

        d_hdr = tk.Frame(daily_panel, bg=THEME["bg_card"])
        d_hdr.pack(fill="x", padx=16, pady=(14, 10))

        tk.Label(
            d_hdr, text="🎯 Daily Challenges",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(side="left", anchor="w")

        self.daily_countdown_label = tk.Label(
            d_hdr, text=self._get_midnight_countdown_text(),
            font=(self.family_mono, 8, "bold"),
            fg=THEME["fg_muted"], bg=THEME["bg_dark"],
            padx=8, pady=3, highlightbackground=THEME["border"], highlightthickness=1
        )
        self.daily_countdown_label.pack(side="right", anchor="e")

        self.daily_challenge_cards = []
        self._claim_pulse_buttons = []
        gold_accent = "#E5B454" if is_dark else "#D99B26"
        claim_ready_bg = "#2E7D32" if not is_dark else "#3B7A57"
        track_bg = "#1E1713" if is_dark else THEME["bar_bg"]
        fill_amber = "#E5B454"
        fill_emerald = "#4CAF50" if not is_dark else "#5CC970"

        reward_styles = {
            "pine": {
                "border": "#3B7A57",
                "bg": scenery.mix(THEME["bg_card"], "#3B7A57", 0.18 if is_dark else 0.12),
                "fg": "#8FD9AD" if is_dark else "#1E5236",
            },
            "angel_oak": {
                "border": "#D4A24C",
                "bg": scenery.mix(THEME["bg_card"], "#E5B454", 0.18 if is_dark else 0.13),
                "fg": "#F7D99C" if is_dark else "#7A5616",
            },
            "cherry_blossom": {
                "border": "#D46A92",
                "bg": scenery.mix(THEME["bg_card"], "#F48FB1", 0.18 if is_dark else 0.14),
                "fg": "#FFB7D5" if is_dark else "#8C244E",
            },
            "oak": {
                "border": "#5E9E55",
                "bg": scenery.mix(THEME["bg_card"], "#688536", 0.18 if is_dark else 0.12),
                "fg": "#B5E092" if is_dark else "#2D5222",
            },
            "willow": {
                "border": "#5E9C71",
                "bg": scenery.mix(THEME["bg_card"], "#3A6B4C", 0.22 if is_dark else 0.14),
                "fg": "#8BC499" if is_dark else "#244A33",
            },
            "maple": {
                "border": "#C93B3B",
                "bg": scenery.mix(THEME["bg_card"], "#C93B3B", 0.18 if is_dark else 0.12),
                "fg": "#F4A261" if is_dark else "#8E2430",
            },
            "moonlit_blossom": {
                "border": "#6C63A6",
                "bg": scenery.mix(THEME["bg_card"], "#3B3561", 0.24 if is_dark else 0.14),
                "fg": "#7CE8FF" if is_dark else "#3B3561",
            },
        }

        for ch in daily_state["challenges"]:
            is_done = bool(ch["completed"])
            is_claimed = bool(ch["claimed"])
            is_launchable = (not is_done and not is_claimed)
            c_bg = scenery.mix(THEME["bg_card"], "#F5C26B", 0.08 if is_dark else 0.10) if (is_done and not is_claimed) else THEME["bg_dark"]
            c_border = gold_accent if (is_done and not is_claimed) else THEME["border"]

            c_card = tk.Frame(
                daily_panel, bg=c_bg,
                highlightbackground=c_border, highlightthickness=1,
                cursor="hand2" if is_launchable else ""
            )
            c_card.pack(fill="x", padx=14, pady=(0, 9))
            self.daily_challenge_cards.append(c_card)

            c_inner = tk.Frame(c_card, bg=c_bg, cursor="hand2" if is_launchable else "")
            c_inner.pack(fill="x", padx=12, pady=9)

            top_line = tk.Frame(c_inner, bg=c_bg, cursor="hand2" if is_launchable else "")
            top_line.pack(fill="x")

            title_lbl = tk.Label(
                top_line, text=f"{ch['icon']} {ch['title']}",
                font=self.font_small_bold, fg=THEME["fg"], bg=c_bg, anchor="w",
                cursor="hand2" if is_launchable else ""
            )
            title_lbl.pack(side="left")

            can_reroll = (rerolls_left > 0 and not is_claimed)
            reroll_lbl = f"↻ Reroll ({rerolls_left} left)" if can_reroll else "↻ Reroll (0)"
            reroll_btn = tk.Label(
                top_line, text=reroll_lbl,
                font=(self.family_sans, 7, "bold"),
                fg=THEME["fg_muted"] if can_reroll else THEME["fg_light"],
                bg=THEME["bg_card"], padx=6, pady=1,
                cursor="hand2" if can_reroll else "",
                highlightbackground=THEME["border"], highlightthickness=1
            )
            reroll_btn.pack(side="right", padx=(6, 0))
            if can_reroll:
                def _on_reroll_click(e, cid=ch["id"]):
                    self._reroll_daily_challenge(cid)
                    return "break"
                reroll_btn.bind("<Button-1>", _on_reroll_click)
                reroll_btn.bind("<Enter>", lambda e, b=reroll_btn: b.configure(fg=THEME["fg"]))
                reroll_btn.bind("<Leave>", lambda e, b=reroll_btn: b.configure(fg=THEME["fg_muted"]))
            c_card._reroll_btn = reroll_btn

            unit = ch.get("unit", "")
            prog_txt = f"{ch['progress']}{unit} / {ch['target']}{unit}"
            prog_lbl = tk.Label(
                top_line, text=prog_txt,
                font=(self.family_mono, 8, "bold"),
                fg=gold_accent if is_done else THEME["fg_muted"],
                bg=c_bg, anchor="e", cursor="hand2" if is_launchable else ""
            )
            prog_lbl.pack(side="right")

            desc_lbl = tk.Label(
                c_inner, text=ch["description"],
                font=self.font_xs, fg=THEME["fg_muted"], bg=c_bg,
                anchor="w", justify="left", wraplength=270 if use_two_cols else 420,
                cursor="hand2" if is_launchable else ""
            )
            desc_lbl.pack(fill="x", pady=(3, 6))

            # Sleek 6px horizontal progress bar right above reward row
            p_track = tk.Frame(
                c_inner, bg=track_bg, height=6,
                highlightbackground=THEME["border"], highlightthickness=1,
                cursor="hand2" if is_launchable else ""
            )
            p_track.pack(fill="x", pady=(0, 8))
            p_track.pack_propagate(False)
            ratio = min(1.0, max(0.0, ch["progress"] / float(max(1, ch["target"]))))
            p_fill = None
            if ratio > 0:
                bar_col = fill_emerald if is_done else fill_amber
                p_fill = tk.Frame(p_track, bg=bar_col, height=6, cursor="hand2" if is_launchable else "")
                p_fill.place(relx=0, rely=0, relwidth=max(0.03, ratio), relheight=1)

            bot_line = tk.Frame(c_inner, bg=c_bg, cursor="hand2" if is_launchable else "")
            bot_line.pack(fill="x")

            r_style = reward_styles.get(ch.get("reward_species", "oak"), reward_styles["oak"])
            reward_lbl = tk.Label(
                bot_line, text=f"Reward: {ch['reward_label']}",
                font=self.font_xs_bold, fg=r_style["fg"],
                bg=r_style["bg"], padx=7, pady=3,
                highlightbackground=r_style["border"], highlightthickness=1,
                cursor="hand2" if is_launchable else ""
            )
            reward_lbl.pack(side="left", anchor="w")

            start_quest_pill = None
            if is_claimed:
                claim_btn = tk.Label(
                    bot_line, text="✓ Claimed",
                    font=self.font_xs_bold,
                    bg=THEME["bg_card"], fg=THEME["green_med"],
                    padx=10, pady=4,
                    highlightbackground=THEME["border"], highlightthickness=1
                )
            elif is_done:
                claim_btn = tk.Label(
                    bot_line, text="✦ Claim Reward",
                    font=self.font_xs_bold,
                    bg=claim_ready_bg, fg="#FFFFFF",
                    padx=10, pady=4, cursor="hand2",
                    highlightbackground=gold_accent, highlightthickness=2
                )
                def _on_claim_click(e, cid=ch["id"]):
                    self._claim_daily_challenge(cid)
                    return "break"
                claim_btn.bind("<Button-1>", _on_claim_click)
                self._claim_pulse_buttons.append(claim_btn)
            else:
                claim_btn = tk.Label(
                    bot_line, text="▶ Start Quest",
                    font=self.font_xs_bold,
                    bg=scenery.mix(THEME["bg_card"], THEME["accent"], 0.16),
                    fg=THEME["accent"] if is_dark else THEME["green_dark"],
                    padx=9, pady=4, cursor="hand2",
                    highlightbackground=THEME["accent"], highlightthickness=1
                )
                start_quest_pill = claim_btn

            claim_btn.pack(side="right", anchor="e")
            c_card._claim_btn = claim_btn
            c_card._start_quest_pill = start_quest_pill

            if is_launchable:
                hover_border = gold_accent if is_dark else THEME["accent"]
                clickable_parts = [
                    c_card, c_inner, top_line, title_lbl, prog_lbl,
                    desc_lbl, p_track, bot_line, reward_lbl, claim_btn
                ]
                if p_fill is not None:
                    clickable_parts.append(p_fill)
                for w in clickable_parts:
                    w.bind("<Button-1>", lambda e, item=ch: self._launch_daily_challenge(item))
                c_card.bind("<Enter>", lambda e, card=c_card, hc=hover_border: card.configure(highlightbackground=hc))
                c_card.bind("<Leave>", lambda e, card=c_card, bc=c_border: card.configure(highlightbackground=bc))

        if self._claim_pulse_buttons:
            self._claim_pulse_phase = 0
            self._claim_pulse_after = self.root.after(480, self._tick_claim_pulse)

        # Compact 7-pill seed inventory bar at bottom of Daily Challenges panel
        inv_bar = tk.Frame(daily_panel, bg=THEME["bg_card"])
        inv_bar.pack(fill="x", padx=14, pady=(2, 12))
        self.seed_inventory_pills = {}
        seed_specs = [
            ("cherry_blossom", "🌸", "Cherry Blossom Seeds"),
            ("pine", "🌲", "Pine Seeds"),
            ("angel_oak", "🌿", "Angel Oak Seeds"),
            ("oak", "🌳", "Classic Oak Seeds"),
            ("willow", "🪴", "Weeping Willow Seeds"),
            ("maple", "🍁", "Japanese Maple Seeds"),
            ("moonlit_blossom", "💠", "Moonlit Blossom Seeds"),
        ]
        for c_i in range(4):
            inv_bar.columnconfigure(c_i, weight=1, uniform="seed_pill_col")
        for idx, (sp_key, sp_ico, sp_title) in enumerate(seed_specs):
            r_i, c_i = idx // 4, idx % 4
            rs = reward_styles[sp_key]
            cnt = seed_inv.get(sp_key, 0)
            pill = tk.Label(
                inv_bar, text=f"{sp_ico} {cnt}",
                font=(self.family_mono, 8, "bold"),
                fg=rs["fg"], bg=rs["bg"],
                padx=6, pady=4,
                highlightbackground=rs["border"], highlightthickness=1
            )
            pill.grid(row=r_i, column=c_i, padx=(0 if c_i == 0 else 4, 0), pady=(0 if r_i == 0 else 4, 0), sticky="ew")
            tip_str = f"{sp_title}: {cnt}"
            pill.bind("<Enter>", lambda e, p=pill, t=tip_str: self._show_stats_tooltip(p, t, e.x_root, e.y_root))
            pill.bind("<Leave>", lambda e: self._hide_stats_tooltip())
            self.seed_inventory_pills[sp_key] = pill

        self._daily_countdown_after = self.root.after(
            15000, lambda d=daily_state["date"]: self._tick_daily_countdown(d)
        )

        # ── RIGHT COLUMN: Glorified Milestones (~60% width, filter bar + dark-wood scrollbar) ──
        right_panel = tk.Frame(hub_row, bg=THEME["bg"])
        right_panel.grid(**right_grid_kw)

        filter_bar = tk.Frame(right_panel, bg=THEME["bg"])
        filter_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            filter_bar, text="🌿 Milestones",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg"]
        ).pack(side="left", anchor="center")

        self.ach_filter_buttons = {}
        filter_pills_wrap = tk.Frame(filter_bar, bg=THEME["bg"])
        filter_pills_wrap.pack(side="right", anchor="e")

        filter_defs = [
            ("all", f"All ({len(achievements)})"),
            ("unlocked", f"Unlocked ({unlocked_count})"),
            ("in_progress", f"In Progress ({locked_count})"),
        ]
        for f_id, f_txt in filter_defs:
            is_act = (self.ach_filter == f_id)
            f_btn = tk.Label(
                filter_pills_wrap, text=f_txt,
                font=self.font_xs_bold,
                bg=THEME["accent"] if is_act else THEME["bg_card"],
                fg=THEME.get("accent_fg", "#FFFFFF") if is_act else THEME["fg_muted"],
                padx=9, pady=4, cursor="hand2",
                highlightbackground=THEME["accent"] if is_act else THEME["border"],
                highlightthickness=1
            )
            f_btn.pack(side="left", padx=(6, 0))
            f_btn.bind("<Button-1>", lambda e, fid=f_id: self._set_ach_filter(fid))
            self.ach_filter_buttons[f_id] = f_btn

        if self.ach_filter == "unlocked":
            filtered_achievements = [a for a in achievements if a["unlocked"]]
        elif self.ach_filter == "in_progress":
            filtered_achievements = [a for a in achievements if not a["unlocked"]]
        else:
            filtered_achievements = list(achievements)

        scroll_host = tk.Frame(right_panel, bg=THEME["bg"])
        scroll_host.pack(fill="both", expand=True)

        sb_style = self._configure_darkwood_scrollbar()
        canvas = tk.Canvas(scroll_host, bg=THEME["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_host, orient="vertical", command=canvas.yview, style=sb_style)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg"])

        cw_est = max(420, int((vw - 72) * (0.58 if use_two_cols else 0.94)))
        win_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=cw_est)
        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(win_id, width=max(300, e.width))
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(e):
            try:
                canvas.yview_scroll(-1 * (e.delta // 120), "units")
            except tk.TclError:
                pass

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        grid_frame = tk.Frame(scroll_frame, bg=THEME["bg"])
        grid_frame.pack(fill="both", expand=True)
        grid_frame.columnconfigure(0, weight=1, uniform="ach_col")
        grid_frame.columnconfigure(1, weight=1, uniform="ach_col")

        if not filtered_achievements:
            tk.Label(
                grid_frame, text="No milestones in this filter yet 🌱",
                font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg"], pady=24
            ).grid(row=0, column=0, columnspan=2)
        else:
            init_card_w = max(220, (cw_est - 28) // 2)
            for i, ach in enumerate(filtered_achievements):
                cur, target, suffix = progress_map.get(ach["id"], (0, 1, ""))
                card_cv = tk.Canvas(
                    grid_frame, height=102, bg=THEME["bg"], highlightthickness=0
                )
                card_cv.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")
                self._render_achievement_card(card_cv, init_card_w, 102, ach, cur, target, suffix)
                card_cv.bind(
                    "<Configure>",
                    lambda e, cv=card_cv, a=ach, c=cur, t=target, s=suffix:
                        self._render_achievement_card(cv, e.width, e.height, a, c, t, s)
                )

        # Bottom breathing room matching padding-bottom: 24px
        tk.Frame(scroll_frame, bg=THEME["bg"], height=24).pack(fill="x")

    # ──────────────── Helpers ────────────────

    def _get_timer_font(self, text_str):
        """Return a tabular monospace font tuple scaled to fit within sidebar bounds."""
        char_len = len(text_str)
        base_pt = self._timer_base_pt
        avail_w = self._timer_avail_w
        key = (char_len, base_pt, avail_w)
        cached = self._timer_font_cache.get(key)
        if cached is not None:
            return cached

        pt = base_pt
        if char_len >= 8:
            pt = max(18, int(round(base_pt * 0.66)))
        elif char_len == 7:
            pt = max(20, int(round(base_pt * 0.74)))

        probe_str = "8" * char_len
        while pt > 16:
            f = tkfont.Font(root=self.root, family=self.family_mono, size=pt, weight="bold")
            if f.measure(probe_str) <= avail_w:
                break
            pt -= 1

        spec = (self.family_mono, pt, "bold")
        self._timer_font_cache[key] = spec
        return spec

    def _format_time(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS."""
        if seconds < 0:
            seconds = 0
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def _format_hours(self, seconds):
        """Format seconds as friendly hours/minutes string."""
        hours = seconds / 3600
        if hours >= 1:
            return f"{hours:.1f}h"
        else:
            return f"{int(seconds // 60)}m"

    def _refresh_streak(self):
        """Refresh the streak display in the header."""
        try:
            streak = db.get_streak()
            streak_text = f"🔥 {streak} day streak" if streak > 0 else "Start your streak today!"
            streak_color = THEME["streak_fire"] if streak > 0 else THEME["fg_light"]
            self.streak_label.configure(text=streak_text, fg=streak_color)
        except Exception:
            pass


def main():
    # Set Windows AppUserModelID and DPI awareness so the app has its own taskbar icon
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("GrowYourForest.Desktop.App.1")
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "forest.ico")
    png_path = os.path.join(base_dir, "forest.png")
    if sys.platform.startswith("win") and os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass
    elif os.path.exists(png_path):
        try:
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, img)
            root._icon_img = img
        except Exception:
            pass

    app = GrowYourForestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
