"""
Grow Your Forest 🌱 — A Study-to-Growth Desktop App
Main application file.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont, messagebox
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

THEMES = {
    "morning": {
        "id": "morning",
        "name": "Morning",
        "icon": "🌅",
        "bg": "#FAF7F2",
        "bg_card": "#FFFFFF",
        "bg_sidebar": "#F0ECE4",
        "bg_dark": "#E8E2D7",
        "fg": "#2B332C",
        "fg_muted": "#6D776E",
        "fg_light": "#9CA59D",
        "accent": "#457A56",
        "accent_hover": "#366345",
        "accent_light": "#EAF2EC",
        "green_dark": "#275237",
        "green_med": "#457A56",
        "green_light": "#77A886",
        "brown": "#8D7356",
        "brown_light": "#C5B095",
        "cream": "#FAF3E8",
        "red_soft": "#D96B52",
        "blue_soft": "#588BB5",
        "yellow_soft": "#E0A638",
        "border": "#E1DBD0",
        "shadow": "#D6CEBF",
        "canvas_bg": "#F5EFE6",
        "nav_active": "#457A56",
        "nav_inactive": "#8F9790",
        "bar_bg": "#E8E2D8",
        "bar_fill": "#77A886",
        "streak_fire": "#E86C38",
    },
    "afternoon": {
        "id": "afternoon",
        "name": "Afternoon",
        "icon": "☀️",
        "bg": "#FDF9F0",
        "bg_card": "#FFFDF8",
        "bg_sidebar": "#F5EDE0",
        "bg_dark": "#EDE2D0",
        "fg": "#2E261E",
        "fg_muted": "#786B5D",
        "fg_light": "#A89A8B",
        "accent": "#387B4C",
        "accent_hover": "#2A613A",
        "accent_light": "#EBF5EE",
        "green_dark": "#225833",
        "green_med": "#387B4C",
        "green_light": "#62A875",
        "brown": "#946A44",
        "brown_light": "#D1A77E",
        "cream": "#FCF3DF",
        "red_soft": "#DB5842",
        "blue_soft": "#4889BA",
        "yellow_soft": "#E69F24",
        "border": "#E6DAC7",
        "shadow": "#D9CBAC",
        "canvas_bg": "#F7EEDC",
        "nav_active": "#387B4C",
        "nav_inactive": "#9C8E7F",
        "bar_bg": "#EBDDC8",
        "bar_fill": "#5DA670",
        "streak_fire": "#E65A28",
    },
    "night": {
        "id": "night",
        "name": "Night",
        "icon": "🌙",
        "bg": "#151922",
        "bg_card": "#1E2430",
        "bg_sidebar": "#191F2B",
        "bg_dark": "#262E3E",
        "fg": "#E8EDF2",
        "fg_muted": "#94A1B2",
        "fg_light": "#677588",
        "accent": "#4EBA87",
        "accent_hover": "#3EA373",
        "accent_light": "#1E332A",
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
        "bg_card": "#362A26",
        "bg_sidebar": "#302521",
        "bg_dark": "#443530",
        "fg": "#F5E6D8",
        "fg_muted": "#C4AC9A",
        "fg_light": "#947D6E",
        "accent": "#D98A56",
        "accent_hover": "#C07340",
        "accent_light": "#4A352B",
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

        # Try to set icon-less title bar colors on Windows
        try:
            self.root.attributes('-alpha', 0.0)
            self.root.after(50, lambda: self.root.attributes('-alpha', 1.0))
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

        # ── Start tick ──
        self._tick()

    def _on_window_unmap(self, event):
        """When minimized or obscured, pause non-critical animations to save CPU."""
        if event.widget == self.root:
            self._window_obscured = True
            for attr in ("_study_resize_after", "_forest_resize_after"):
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
        self.font_title = ("Segoe UI", 20, "bold")
        self.font_subtitle = ("Segoe UI", 13)
        self.font_body = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 9)
        self.font_timer = ("Segoe UI Semibold", 48)
        self.font_timer_label = ("Segoe UI", 11)
        self.font_button = ("Segoe UI Semibold", 12)
        self.font_nav = ("Segoe UI Semibold", 11)
        self.font_stat_num = ("Segoe UI Semibold", 22)
        self.font_stat_label = ("Segoe UI", 9)
        self.font_stage = ("Segoe UI", 13, "italic")
        self.font_emoji = ("Segoe UI Emoji", 14)
        self.font_emoji_large = ("Segoe UI Emoji", 20)
        self.font_section = ("Segoe UI Semibold", 14)
        self.font_achievement = ("Segoe UI", 10)

    # ──────────────── Layout ────────────────

    def _build_layout(self):
        # Main container
        self.main_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # Designated Top Header Frame
        self.header_frame = tk.Frame(self.main_frame, bg=THEME["bg"], height=62)
        self.header_frame.pack(fill="x", padx=20, pady=(12, 4))
        self.header_frame.pack_propagate(False)
        self._build_header()

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=THEME["bg"])
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        # Designated Bottom Navigation Frame
        self.nav_frame = tk.Frame(self.main_frame, bg=THEME["bg_sidebar"], height=55)
        self.nav_frame.pack(fill="x", side="bottom")
        self.nav_frame.pack_propagate(False)
        self._build_nav()

    def _build_header(self):
        # Clear any existing header widgets for dynamic theme refresh
        for w in self.header_frame.winfo_children():
            w.destroy()
        self.header_frame.configure(bg=THEME["bg"])

        # Left: App title
        title_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        title_frame.pack(side="left")

        tk.Label(
            title_frame, text="🌱", font=self.font_emoji_large, bg=THEME["bg"]
        ).pack(side="left", padx=(0, 6))
        tk.Label(
            title_frame, text="Grow Your Forest",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(side="left")

        # Right: Date and streak
        right_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        right_frame.pack(side="right")

        today_str = date.today().strftime("%B %d, %Y")
        tk.Label(
            right_frame, text=today_str,
            font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg"]
        ).pack(side="top", anchor="e")

        streak = db.get_streak()
        streak_text = f"🔥 {streak} day streak" if streak > 0 else "Start your streak today!"
        streak_color = THEME["streak_fire"] if streak > 0 else THEME["fg_light"]
        self.streak_label = tk.Label(
            right_frame, text=streak_text,
            font=self.font_small, fg=streak_color, bg=THEME["bg"]
        )
        self.streak_label.pack(side="top", anchor="e")

        # Center-Right: Built-in Rain Sound Control
        rain_frame = tk.Frame(self.header_frame, bg=THEME["bg"])
        rain_frame.pack(side="right", padx=(0, 16))

        is_playing = audio_player.player.is_playing
        rain_bg = "#E1F5FE" if is_playing else THEME["bg_dark"]
        rain_fg = "#0277BD" if is_playing else THEME["fg_muted"]
        rain_border = "#81D4FA" if is_playing else THEME["border"]
        rain_txt = "🌧️ Rain: ON" if is_playing else "🌧️ Rain: OFF"

        self.rain_btn = tk.Label(
            rain_frame, text=rain_txt,
            font=self.font_small,
            bg=rain_bg, fg=rain_fg,
            padx=8, pady=4, cursor="hand2", relief="flat",
            highlightbackground=rain_border, highlightthickness=1
        )
        self.rain_btn.pack(side="left")
        self.rain_btn.bind("<Button-1>", lambda e: self._toggle_rain_sound())

        # Rain volume controls
        vol_frame = tk.Frame(rain_frame, bg=THEME["bg_dark"],
                             highlightbackground=THEME["border"], highlightthickness=1)
        vol_frame.pack(side="left", padx=(5, 0))

        v_down = tk.Label(vol_frame, text="🔉 -", font=("Segoe UI", 8),
                          bg=THEME["bg_dark"], fg=THEME["fg_muted"], padx=4, pady=3, cursor="hand2")
        v_down.pack(side="left")
        v_down.bind("<Button-1>", lambda e: self._change_rain_volume(-15))

        self.vol_label = tk.Label(vol_frame, text=f"{audio_player.player.volume}%",
                                  font=("Segoe UI Semibold", 8), bg=THEME["bg_dark"], fg=THEME["fg"], padx=3)
        self.vol_label.pack(side="left")

        v_up = tk.Label(vol_frame, text="+ 🔊", font=("Segoe UI", 8),
                        bg=THEME["bg_dark"], fg=THEME["fg_muted"], padx=4, pady=3, cursor="hand2")
        v_up.pack(side="left")
        v_up.bind("<Button-1>", lambda e: self._change_rain_volume(+15))

        # Center: Sleek 4-Theme Segmented Pill Bar (Morning, Afternoon, Night, Chill)
        theme_bar = tk.Frame(self.header_frame, bg=THEME["bg_dark"],
                             highlightbackground=THEME["border"], highlightthickness=1)
        theme_bar.pack(side="right", padx=(0, 16))

        self.theme_buttons = {}
        theme_choices = [
            ("morning", "🌅 Morning"),
            ("afternoon", "☀️ Afternoon"),
            ("night", "🌙 Night"),
            ("chill", "☕ Chill"),
        ]

        for t_id, t_label in theme_choices:
            is_active = (self.current_theme == t_id)
            btn_bg = THEME["accent"] if is_active else THEME["bg_dark"]
            btn_fg = "#FFFFFF" if is_active else THEME["fg_muted"]

            btn = tk.Label(
                theme_bar, text=t_label,
                font=("Segoe UI Semibold", 8),
                bg=btn_bg, fg=btn_fg,
                padx=8, pady=4, cursor="hand2"
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, tid=t_id: self._set_theme(tid))
            self.theme_buttons[t_id] = btn

    def _set_theme(self, theme_id):
        """Switch visual mode seamlessly across the entire app and persist."""
        if theme_id not in THEMES:
            return
        self.current_theme = theme_id
        db.set_setting("theme", theme_id)
        THEME.update(THEMES[theme_id])

        # Apply root & top container backgrounds
        self.root.configure(bg=THEME["bg"])
        self.main_frame.configure(bg=THEME["bg"])
        self.content_frame.configure(bg=THEME["bg"])

        # Rebuild header & nav with new theme styling
        self._build_header()
        self._build_nav()

        # Re-render active view smoothly
        if self.current_view == "timer":
            self._show_timer_view()
        elif self.current_view == "forest":
            self._show_forest_view()
        elif self.current_view == "stats":
            self._show_stats_view()
        elif self.current_view == "achievements":
            self._show_achievements_view()

    def _toggle_rain_sound(self):
        """Toggle built-in ambient rain sound."""
        is_playing = audio_player.player.toggle()
        if is_playing:
            self.rain_btn.configure(
                text="🌧️ Rain: ON",
                bg="#E1F5FE", fg="#0277BD",
                highlightbackground="#81D4FA"
            )
        else:
            self.rain_btn.configure(
                text="🌧️ Rain: OFF",
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
        self.nav_frame.configure(bg=THEME["bg_sidebar"])

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
                cursor="hand2", padx=22, pady=10
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
        for w in self.content_frame.winfo_children():
            w.destroy()

    # ──────────────── Timer View ────────────────

    def _show_timer_view(self):
        self.current_view = "timer"
        self._clear_content()

        # Two-column layout: tree canvas left, timer right
        container = tk.Frame(self.content_frame, bg=THEME["bg"])
        container.pack(fill="both", expand=True)

        # Left: Tree canvas & Species Selector
        left = tk.Frame(container, bg=THEME["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Species Selector Bar
        spec_bar = tk.Frame(left, bg=THEME["bg"])
        spec_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            spec_bar, text="Tree:",
            font=self.font_small, fg=THEME["fg_muted"], bg=THEME["bg"]
        ).pack(side="left", padx=(0, 6))

        species_list = [
            ("cherry_blossom", "🌸 Cherry Blossom"),
            ("pine", "🌲 Pine"),
            ("angel_oak", "🌿 Angel Oak"),
            ("oak", "🌳 Classic Oak"),
        ]

        self.species_buttons = {}
        for sp_id, sp_label in species_list:
            is_active = (self.selected_species == sp_id)
            meta = SPECIES_METADATA.get(sp_id, {})
            active_bg = meta.get("theme_color", THEME["accent"])
            btn = tk.Label(
                spec_bar, text=sp_label,
                font=self.font_small,
                bg=active_bg if is_active else THEME["bg_dark"],
                fg="white" if is_active else THEME["fg"],
                padx=8, pady=4, cursor="hand2" if not self.session_active else "arrow",
                relief="flat"
            )
            btn.pack(side="left", padx=(0, 5))
            if not self.session_active:
                btn.bind("<Button-1>", lambda e, s=sp_id: self._select_species(s))
            self.species_buttons[sp_id] = btn

        # Species tagline
        curr_meta = SPECIES_METADATA.get(self.selected_species, {})
        tk.Label(
            spec_bar, text=curr_meta.get("tagline", ""),
            font=("Segoe UI", 8, "italic"), fg=THEME["fg_light"], bg=THEME["bg"]
        ).pack(side="right")

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

        # Right: Timer panel
        right = tk.Frame(container, bg=THEME["bg_card"], width=310, relief="flat",
                         highlightbackground=THEME["border"], highlightthickness=1)
        right.pack(side="right", fill="y", padx=(10, 0), pady=(5, 0))
        right.pack_propagate(False)
        right.configure(width=310)

        inner = tk.Frame(right, bg=THEME["bg_card"])
        inner.pack(expand=True, fill="both", padx=20, pady=15)

        # ── Task / Study Goal Section ──
        task_sec = tk.Frame(inner, bg=THEME["bg_card"])
        task_sec.pack(fill="x", pady=(0, 14))

        tk.Label(
            task_sec, text="🎯 Current Task / Subject",
            font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 4))

        if not self.session_active:
            entry_frame = tk.Frame(task_sec, bg=THEME["bg_dark"], padx=6, pady=4,
                                   highlightbackground=THEME["border"], highlightthickness=1)
            entry_frame.pack(fill="x", pady=(0, 5))
            self.task_entry = tk.Entry(
                entry_frame, font=self.font_small,
                relief="flat", bg=THEME["bg_dark"], fg=THEME["fg"],
                insertbackground=THEME["fg"]
            )
            self.task_entry.insert(0, self.current_task)
            self.task_entry.pack(fill="x")
            self.task_entry.bind("<KeyRelease>", self._on_task_entry_change)

            # Quick presets
            presets_frame = tk.Frame(task_sec, bg=THEME["bg_card"])
            presets_frame.pack(fill="x")
            presets = [("📚 Study", "Study"), ("💻 Code", "Coding"), ("✍️ Write", "Writing"), ("🔬 Sci", "Science"), ("🎨 Art", "Creative")]
            for label, val in presets:
                is_sel = (self.current_task == val)
                btn = tk.Label(
                    presets_frame, text=label, font=("Segoe UI", 8),
                    bg=THEME["accent_light"] if is_sel else THEME["bg_dark"],
                    fg=THEME["green_dark"] if is_sel else THEME["fg"],
                    padx=5, pady=2, cursor="hand2", relief="flat"
                )
                btn.pack(side="left", padx=(0, 3))
                btn.bind("<Button-1>", lambda e, v=val: self._set_task_preset(v))
        else:
            # When studying, display badge
            badge_frame = tk.Frame(task_sec, bg=THEME["accent_light"], padx=8, pady=5,
                                   highlightbackground=THEME["accent"], highlightthickness=1)
            badge_frame.pack(fill="x")
            tk.Label(
                badge_frame, text=f"🎯 Growing for: {self.current_task}",
                font=("Segoe UI Semibold", 9), fg=THEME["green_dark"], bg=THEME["accent_light"]
            ).pack(anchor="w")

        # Duration selector
        tk.Label(
            inner, text="Session Duration",
            font=self.font_body, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        dur_frame = tk.Frame(inner, bg=THEME["bg_card"])
        dur_frame.pack(fill="x", pady=(0, 20))

        self.duration_buttons = []
        durations = [25, 45, 60, 90]
        for mins in durations:
            is_selected = (self.planned_duration == mins * 60)
            btn = tk.Label(
                dur_frame, text=f"{mins}m",
                font=self.font_small,
                bg=THEME["accent"] if is_selected else THEME["bg_dark"],
                fg="white" if is_selected else THEME["fg"],
                padx=10, pady=5, cursor="hand2",
                relief="flat"
            )
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda e, m=mins: self._set_duration(m))
            self.duration_buttons.append((btn, mins))

        # Custom duration
        custom_frame = tk.Frame(inner, bg=THEME["bg_card"])
        custom_frame.pack(fill="x", pady=(0, 25))
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

        # Timer display
        timer_frame = tk.Frame(inner, bg=THEME["bg_card"])
        timer_frame.pack(fill="x", pady=(0, 5))

        remaining = self.planned_duration - self.focused_seconds
        if remaining < 0:
            remaining = 0
        self.timer_display = tk.Label(
            timer_frame, text=self._format_time(int(remaining)),
            font=self.font_timer, fg=THEME["fg"], bg=THEME["bg_card"]
        )
        self.timer_display.pack()

        # Progress info
        info_frame = tk.Frame(inner, bg=THEME["bg_card"])
        info_frame.pack(fill="x", pady=(0, 15))

        self.elapsed_label = tk.Label(
            info_frame, text=f"Focused: {self._format_time(int(self.focused_seconds))}",
            font=self.font_small, fg=THEME["fg_muted"], bg=THEME["bg_card"]
        )
        self.elapsed_label.pack()

        # Progress bar
        bar_frame = tk.Frame(inner, bg=THEME["bar_bg"], height=8)
        bar_frame.pack(fill="x", pady=(0, 20))
        bar_frame.pack_propagate(False)

        progress = min(1.0, self.focused_seconds / max(1, self.planned_duration))
        self.progress_bar = tk.Frame(bar_frame, bg=THEME["accent"], height=8)
        self.progress_bar.place(relx=0, rely=0, relwidth=progress, relheight=1)

        # Control buttons
        btn_frame = tk.Frame(inner, bg=THEME["bg_card"])
        btn_frame.pack(fill="x", pady=(0, 10))

        if not self.session_active:
            self._make_button(btn_frame, "▶  Start Studying", self._start_session,
                              THEME["accent"], "white").pack(fill="x", ipady=10)
        elif self.timer_paused:
            bf = tk.Frame(btn_frame, bg=THEME["bg_card"])
            bf.pack(fill="x")
            self._make_button(bf, "▶  Resume", self._resume_session,
                              THEME["accent"], "white").pack(side="left", expand=True, fill="x", ipady=8, padx=(0, 4))
            self._make_button(bf, "⏹  Stop", self._stop_session,
                              THEME["red_soft"], "white").pack(side="left", expand=True, fill="x", ipady=8, padx=(4, 0))
        else:
            bf = tk.Frame(btn_frame, bg=THEME["bg_card"])
            bf.pack(fill="x")
            self._make_button(bf, "⏸  Pause", self._pause_session,
                              THEME["yellow_soft"], "white").pack(side="left", expand=True, fill="x", ipady=8, padx=(0, 4))
            self._make_button(bf, "⏹  Stop", self._stop_session,
                              THEME["red_soft"], "white").pack(side="left", expand=True, fill="x", ipady=8, padx=(4, 0))

        # Reset button (only if session active)
        if self.session_active:
            reset = tk.Label(
                inner, text="Reset Session", font=self.font_small,
                fg=THEME["fg_light"], bg=THEME["bg_card"], cursor="hand2"
            )
            reset.pack(pady=(5, 0))
            reset.bind("<Button-1>", lambda e: self._reset_session())

        # Bottom stats row
        stats_frame = tk.Frame(inner, bg=THEME["bg_card"])
        stats_frame.pack(fill="x", side="bottom", pady=(15, 0))

        # Separator
        tk.Frame(stats_frame, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 10))

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
                col, text=value_text, font=("Segoe UI Semibold", 14),
                fg=THEME["green_dark"], bg=THEME["bg_card"]
            ).pack()
            tk.Label(
                col, text=label_text, font=self.font_small,
                fg=THEME["fg_muted"], bg=THEME["bg_card"]
            ).pack()

        # Draw tree after canvas is rendered
        self.root.after(50, self._redraw_tree)

    def _make_button(self, parent, text, command, bg, fg):
        btn = tk.Label(
            parent, text=text, font=self.font_button,
            bg=bg, fg=fg, cursor="hand2", relief="flat", padx=15
        )
        btn.bind("<Button-1>", lambda e: command())

        orig_bg = bg
        hover_bg = self._darken(bg, 0.1)
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=orig_bg))
        return btn

    def _darken(self, hex_color, factor):
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ──────────────── Timer Logic ────────────────

    def _on_task_entry_change(self, event=None):
        if hasattr(self, "task_entry"):
            val = self.task_entry.get().strip()
            self.current_task = val if val else "General Study"

    def _set_task_preset(self, task_val):
        self.current_task = task_val
        self._show_timer_view()

    def _select_species(self, species_id):
        if self.session_active:
            return
        self.selected_species = species_id
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
        if hasattr(self, "task_entry"):
            val = self.task_entry.get().strip()
            if val:
                self.current_task = val
        self.session_active = True
        self.timer_running = True
        self.timer_paused = False
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
            self.last_tick_time = None
            self._show_timer_view()

    def _resume_session(self):
        self.timer_running = True
        self.timer_paused = False
        self.last_tick_time = time.monotonic()
        self._show_timer_view()

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

        # Check achievements
        newly_unlocked = db.check_and_unlock_achievements()

        self.session_active = False
        self.timer_running = False
        self.timer_paused = False
        self.last_tick_time = None

        # Show completion message
        if session_id:
            stage = db.get_tree_stage(self.focused_seconds)
            mins = int(self.focused_seconds // 60)
            stage_name = STAGE_LABELS.get(stage, "Seed")
            curr_meta = SPECIES_METADATA.get(self.selected_species, {})
            spec_display = f"{curr_meta.get('icon', '')} {curr_meta.get('name', 'Tree')}"

            msg = f"Great job! You studied for {mins} minutes.\nYour {spec_display} reached: {stage_name}\n🎯 Focus: {self.current_task}"
            if newly_unlocked:
                ach_names = ", ".join(a["icon"] + " " + a["name"] for a in newly_unlocked)
                msg += f"\n\n🏆 New achievements: {ach_names}"

            self.root.after(100, lambda: messagebox.showinfo("Session Complete! 🌱", msg))

        self.focused_seconds = 0.0
        self._refresh_streak()
        self._show_timer_view()

    def _reset_session(self):
        """Reset without saving — no rewards."""
        if not self.session_active:
            return
        if messagebox.askyesno("Reset Session", "Are you sure? No progress will be saved."):
            self.session_active = False
            self.timer_running = False
            self.timer_paused = False
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
            self.timer_display.configure(text=self._format_time(int(remaining)))
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
            font=("Segoe UI", 9, "italic"), fg=THEME["fg_light"], bg=THEME["bg"]
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
        completed = db.get_completed_count()

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
            tk.Label(col, text=value, font=("Segoe UI Semibold", 15),
                     fg=THEME["green_dark"], bg=THEME["bg_card"]).pack()
            tk.Label(col, text=label, font=self.font_stat_label,
                     fg=THEME["fg_muted"], bg=THEME["bg_card"]).pack()

        # ── Filter Bar ──
        filter_bar = tk.Frame(self.content_frame, bg=THEME["bg"])
        filter_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            filter_bar, text="Filter Forest:", font=self.font_small,
            fg=THEME["fg_muted"], bg=THEME["bg"]
        ).pack(side="left", padx=(0, 6))

        filters = [
            ("all", "🌲 All Trees"),
            ("cherry_blossom", "🌸 Sakura"),
            ("pine", "🌲 Pine"),
            ("angel_oak", "🌿 Angel Oak"),
            ("oak", "🌳 Oak"),
        ]

        for fid, flabel in filters:
            is_active = (self.forest_filter_species == fid)
            fbtn = tk.Label(
                filter_bar, text=flabel, font=("Segoe UI", 8),
                bg=THEME["accent"] if is_active else THEME["bg_dark"],
                fg="white" if is_active else THEME["fg"],
                padx=8, pady=3, cursor="hand2", relief="flat"
            )
            fbtn.pack(side="left", padx=(0, 5))
            fbtn.bind("<Button-1>", lambda e, f=fid: self._set_forest_filter(f))

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
                badge_bg, badge_fg = "#182330", "#E2E8F0"
            elif self.current_theme == "chill":
                badge_bg, badge_fg = "#302521", "#F5E6D8"
            else:
                badge_bg, badge_fg = pal["hills"][2], "#FFFFFF"

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
                    display_task = task_name if len(task_name) <= 12 else task_name[:10] + "…"
                    pill_hw = max(24, len(display_task) * 3 + 12)
                    self.forest_canvas.create_rectangle(
                        cx_t - pill_hw, top_y - 16, cx_t + pill_hw, top_y,
                        fill=badge_bg, outline="", tags=(tag,),
                    )
                    self.forest_canvas.create_text(
                        cx_t, top_y - 8,
                        text=f"🎯 {display_task}",
                        font=("Segoe UI", 7, "bold"),
                        fill=badge_fg,
                        tags=(tag,),
                    )

                hit_r = max(24, int(48 * scale))
                self._forest_trees.append({
                    "tree": tree,
                    "cx": cx_t,
                    "cy": ground_y,
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
        """Handle click on forest canvas — find nearest tree and show popup."""
        self._dismiss_forest_popup()

        mx, my = event.x, event.y
        best = None
        best_dist = 999999
        for entry in self._forest_trees:
            d = ((mx - entry["cx"]) ** 2 + (my - entry["cy"]) ** 2) ** 0.5
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

            popup_w, popup_h = 240, 205
            px = cx - popup_w // 2
            py = cy - popup_h - 20
            if px < 5: px = 5
            if px + popup_w > w_c - 5: px = w_c - popup_w - 5
            if py < 5: py = cy + 20

            popup.place(x=px, y=py, width=popup_w, height=popup_h)

            # Header strip
            hdr = tk.Frame(popup, bg=meta.get("theme_color", THEME["accent"]), height=34)
            hdr.pack(fill="x")
            hdr.pack_propagate(False)
            tk.Label(
                hdr,
                text=f"{meta.get('icon','🌳')} {meta.get('name','Tree')}",
                font=("Segoe UI Semibold", 10), fg="white",
                bg=meta.get("theme_color", THEME["accent"])
            ).pack(side="left", padx=10, pady=5)

            # Close ×
            close_btn = tk.Label(hdr, text="✕", font=("Segoe UI", 10),
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
            tk.Label(task_row, text="Task:", font=("Segoe UI", 8),
                     fg=THEME["fg_muted"], bg=popup_bg, width=7, anchor="w").pack(side="left")
            t_lbl = tk.Label(task_row, text=task_name, font=("Segoe UI Semibold", 9),
                             fg=THEME["green_dark"], bg=popup_bg, anchor="w")
            t_lbl.pack(side="left", fill="x", expand=True)
            edit_btn = tk.Label(task_row, text="✏️", font=("Segoe UI", 8),
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
                tk.Label(row, text=text, font=("Segoe UI", 8),
                         fg=THEME["fg_muted"], bg=popup_bg, width=7, anchor="w").pack(side="left")
                tk.Label(row, text=val, font=("Segoe UI Semibold", 8),
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
                font=("Segoe UI Semibold", 8),
                bg=del_bg, fg=del_fg,
                padx=6, pady=3, cursor="hand2",
                highlightbackground=del_border, highlightthickness=1
            )
            del_btn.pack(fill="x", pady=(5, 0))
            del_btn.bind("<Button-1>", lambda e, tid=tree["id"]: self._delete_tree(tid))
            del_btn.bind("<Enter>", lambda e: del_btn.configure(bg=del_hover))
            del_btn.bind("<Leave>", lambda e: del_btn.configure(bg=del_bg))

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
            self._show_forest_view()

    # ──────────────── Statistics View ────────────────

    def _show_stats_view(self):
        self._clear_content()

        # Scrollable frame
        canvas = tk.Canvas(self.content_frame, bg=THEME["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg"])

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw",
                             width=self.content_frame.winfo_width() - 20 if self.content_frame.winfo_width() > 20 else 800)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel (scoped to this canvas, cleaned up on destroy)
        def _on_mousewheel(e):
            try:
                canvas.yview_scroll(-1 * (e.delta // 120), "units")
            except tk.TclError:
                pass

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Header
        tk.Label(
            scroll_frame, text="📊 Statistics",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(anchor="w", pady=(0, 15))

        # ── Summary cards ──
        cards = tk.Frame(scroll_frame, bg=THEME["bg"])
        cards.pack(fill="x", pady=(0, 20))

        today_secs = db.get_today_seconds()
        weekly_secs = db.get_weekly_seconds()
        total_secs = db.get_total_focused_seconds()
        total_trees = db.get_total_trees()
        completed = db.get_completed_count()
        streak = db.get_streak()

        card_data = [
            ("Today", self._format_hours(today_secs), "⏱️", THEME["blue_soft"]),
            ("This Week", self._format_hours(weekly_secs), "📅", THEME["accent"]),
            ("All Time", self._format_hours(total_secs), "🕐", THEME["brown"]),
            ("Trees", str(total_trees), "🌳", THEME["green_med"]),
            ("Sessions", str(completed), "✅", THEME["yellow_soft"]),
            ("Streak", f"{streak}d", "🔥", THEME["streak_fire"]),
        ]

        for i, (label, value, icon, color) in enumerate(card_data):
            card = tk.Frame(cards, bg=THEME["bg_card"],
                            highlightbackground=THEME["border"], highlightthickness=1)
            card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            cards.columnconfigure(i % 3, weight=1)

            inner = tk.Frame(card, bg=THEME["bg_card"])
            inner.pack(fill="x", padx=15, pady=12)

            tk.Label(inner, text=icon, font=self.font_emoji, bg=THEME["bg_card"]).pack(anchor="w")
            tk.Label(inner, text=value, font=self.font_stat_num,
                     fg=color, bg=THEME["bg_card"]).pack(anchor="w")
            tk.Label(inner, text=label, font=self.font_stat_label,
                     fg=THEME["fg_muted"], bg=THEME["bg_card"]).pack(anchor="w")

        # ── Weekly chart ──
        chart_frame = tk.Frame(scroll_frame, bg=THEME["bg_card"],
                               highlightbackground=THEME["border"], highlightthickness=1)
        chart_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            chart_frame, text="📈 This Week",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(anchor="w", padx=20, pady=(15, 10))

        chart_canvas = tk.Canvas(
            chart_frame, bg=THEME["bg_card"], highlightthickness=0, height=180
        )
        chart_canvas.pack(fill="x", padx=20, pady=(0, 15))

        self.root.after(100, lambda: self._draw_weekly_chart(chart_canvas))

        # ── Time by Task Breakdown ──
        task_stats = db.get_task_stats()
        if task_stats:
            task_card = tk.Frame(scroll_frame, bg=THEME["bg_card"],
                                 highlightbackground=THEME["border"], highlightthickness=1)
            task_card.pack(fill="x", pady=(0, 20))

            tk.Label(
                task_card, text="🎯 Study Time by Task",
                font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
            ).pack(anchor="w", padx=20, pady=(15, 10))

            max_task_sec = max(t["total_seconds"] for t in task_stats) if task_stats else 1
            if max_task_sec <= 0:
                max_task_sec = 1

            for t in task_stats[:7]:
                t_row = tk.Frame(task_card, bg=THEME["bg_card"])
                t_row.pack(fill="x", padx=20, pady=5)

                tk.Label(
                    t_row, text=f"• {t['task']}", font=self.font_body,
                    fg=THEME["fg"], bg=THEME["bg_card"], width=16, anchor="w"
                ).pack(side="left")

                bar_c = tk.Frame(t_row, bg=THEME["bg_dark"], height=12)
                bar_c.pack(side="left", fill="x", expand=True, padx=10)
                bar_c.pack_propagate(False)

                frac = min(1.0, t["total_seconds"] / max_task_sec)
                tk.Frame(bar_c, bg=THEME["accent"], height=12).place(relx=0, rely=0, relwidth=max(0.02, frac), relheight=1)

                hrs_str = self._format_hours(t["total_seconds"])
                cnt_str = f"{t['tree_count']} tree" + ("s" if t["tree_count"] != 1 else "")
                tk.Label(
                    t_row, text=f"{hrs_str} ({cnt_str})", font=self.font_small,
                    fg=THEME["fg_muted"], bg=THEME["bg_card"], width=15, anchor="e"
                ).pack(side="right")

            tk.Frame(task_card, bg=THEME["bg_card"], height=12).pack()

        # ── Recent sessions ──
        recent_frame = tk.Frame(scroll_frame, bg=THEME["bg_card"],
                                highlightbackground=THEME["border"], highlightthickness=1)
        recent_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            recent_frame, text="📋 Recent Sessions",
            font=self.font_section, fg=THEME["fg"], bg=THEME["bg_card"]
        ).pack(anchor="w", padx=20, pady=(15, 10))

        sessions = db.get_all_sessions()[:10]
        if not sessions:
            tk.Label(
                recent_frame, text="No sessions yet. Start studying! 🌱",
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
                    row, text=f"{status} {sp_icon} {stage} ({sp_name})  •  🎯 {t_name}",
                    font=self.font_body, fg=THEME["fg"], bg=THEME["bg_card"]
                ).pack(side="left")

                tk.Label(
                    row, text=f"{mins}m  •  {dt.strftime('%b %d, %H:%M')}",
                    font=self.font_small, fg=THEME["fg_muted"], bg=THEME["bg_card"]
                ).pack(side="right")

            tk.Frame(recent_frame, bg=THEME["bg_card"], height=10).pack()

    def _draw_weekly_chart(self, canvas):
        """Draw a bar chart of daily study time for the last 7 days."""
        try:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 50 or h < 50:
                self.root.after(100, lambda: self._draw_weekly_chart(canvas))
                return

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
                    text=f"{int(val)}m", font=self.font_small,
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
                        font=("Segoe UI", 8), fill=THEME["fg_muted"]
                    )
        except tk.TclError:
            pass

    # ──────────────── Achievements View ────────────────

    def _show_achievements_view(self):
        self._clear_content()

        tk.Label(
            self.content_frame, text="🏆 Achievements",
            font=self.font_title, fg=THEME["green_dark"], bg=THEME["bg"]
        ).pack(anchor="w", pady=(0, 15))

        achievements = db.get_achievements()

        grid_frame = tk.Frame(self.content_frame, bg=THEME["bg"])
        grid_frame.pack(fill="both", expand=True)

        for i, ach in enumerate(achievements):
            unlocked = ach["unlocked"]
            card = tk.Frame(
                grid_frame,
                bg=THEME["bg_card"] if unlocked else THEME["bg_dark"],
                highlightbackground=THEME["accent"] if unlocked else THEME["border"],
                highlightthickness=2 if unlocked else 1
            )
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")
            grid_frame.columnconfigure(i % 2, weight=1)

            inner = tk.Frame(card, bg=card.cget("bg"))
            inner.pack(fill="x", padx=18, pady=15)

            bg = card.cget("bg")

            # Icon and name row
            top_row = tk.Frame(inner, bg=bg)
            top_row.pack(fill="x")

            icon_text = ach["icon"] if unlocked else "🔒"
            tk.Label(
                top_row, text=icon_text, font=self.font_emoji_large, bg=bg
            ).pack(side="left", padx=(0, 10))

            name_frame = tk.Frame(top_row, bg=bg)
            name_frame.pack(side="left")

            tk.Label(
                name_frame, text=ach["name"],
                font=("Segoe UI Semibold", 12),
                fg=THEME["fg"] if unlocked else THEME["fg_muted"],
                bg=bg
            ).pack(anchor="w")

            tk.Label(
                name_frame, text=ach["description"],
                font=self.font_achievement,
                fg=THEME["fg_muted"] if unlocked else THEME["fg_light"],
                bg=bg
            ).pack(anchor="w")

            if unlocked and ach["unlocked_at"]:
                try:
                    dt = datetime.fromisoformat(ach["unlocked_at"])
                    tk.Label(
                        inner, text=f"Unlocked: {dt.strftime('%b %d, %Y')}",
                        font=("Segoe UI", 8),
                        fg=THEME["fg_light"], bg=bg
                    ).pack(anchor="w", pady=(5, 0))
                except Exception:
                    pass

    # ──────────────── Helpers ────────────────

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
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = GrowYourForestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
