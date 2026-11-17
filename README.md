# Grow Your Forest

A cozy desktop focus timer built with Python & Tkinter. Complete study/focus sessions to grow distinct trees (Cherry Blossom, Pine, Angel Oak, Classic Oak) across a layered 2D forest sanctuary with ambient rain sound and four atmospheric themes: **Morning**, **Afternoon**, **Night**, and **Chill**.

## Features

- **Focus Timer & 7 Tree Species**: Watch your active tree evolve across 6 stages (*Seed → Sprout → Small Sapling → Young Tree → Mature Tree → Flourishing*) across 7 procedural species: **Cherry Blossom**, **Pine**, **Angel Oak**, **Classic Oak**, plus unlockable **Weeping Willow**, **Japanese Maple**, and **Moonlit Blossom** via the compact Tree Selector dropdown.
- **Daily Challenges & Achievements Hub**: 2-column progression hub with 16 rotating Daily Challenges, 1/day reroll, Seed Bag rewards, 1-click quest launching, and redesigned Milestones.
- **Task List with Tree Assignment**: Add tasks with an assigned tree species (Cherry Blossom, Pine, Angel Oak, Classic Oak), click any task to focus and auto-sync its tree species, tick off completed tasks, or reassign species anytime.
- **Living 2D Sanctuary**: Multi-layer distant mountains, rolling hills, winding river, stepping stones, flowers, grass, clouds, and subtle wildlife/particles — with responsive laptop viewport scaling (`800x650` to `1200px+`).
- **Four Smoothly Transitioning Themes**: Smooth color easing across **Morning**, **Afternoon**, **Night**, and **Chill** modes.
- **Infinite Ambient Rain Audio**: Continuous seamless looping rain backdrop (`winmm` MCI worker + WPF fallback) with volume control and a smooth 400ms volume fade-in/out on toggle (`user_rain.mp3` + fallback `rain_master.wav`).
- **Upgraded Statistics & Analytics**: Scrollable analytics dashboard with a 6-card KPI row, editable Daily Goal progress ring, 90-Day Forest Activity Heatmap & Weekly Bar toggle, Study Time by Task, Species Breakdown donut chart, Peak Focus Window badge, clean session log (`Hide 0m sessions` toggle), and **Export Forest (`.json`) / Import Backup**.
- **My Forest & Achievements**: Local SQLite persistence (`forest_data.db`), daily streak tracking, tree inspection and removal inside **My Forest**, and unlockable achievements.

---

## Quick Setup

### Option 1: Standalone Windows Executable (.exe)
1. Download **`GrowYourForest.exe`** from [**Releases**](../../releases).
2. Double-click **`GrowYourForest.exe`** directly — no Python installation required! Your progress is saved in `forest_data.db` right next to the executable.

### Option 2: Ubuntu / Debian (.deb Package)
1. Download **`grow-your-forest_2.0.0_all.deb`** from [**Releases**](../../releases).
2. Install via terminal:
   ```bash
   sudo apt update
   sudo apt install ./grow-your-forest_2.0.0_all.deb
   ```
   *(or double-click the `.deb` file to open in Ubuntu Software / App Center)*.
3. Launch **Grow Your Forest** directly from your application dock, or run `grow-your-forest` in terminal!

### Option 3: Portable Release ZIP (Windows)
1. Go to the [**Releases**](../../releases) page and download **`GrowYourForest-Portable.zip`**.
2. Right-click `GrowYourForest-Portable.zip` → **Extract All...** into a folder you want to keep.
3. Double-click **`run.bat`** to start the app (or **`create_shortcut.bat`** to put an icon on your Desktop). Requires standard Python 3.

### Option 4: Clone with Git (Cross-Platform)

```bash
git clone https://github.com/minh-inthenature/grow-your-forest.git
cd grow-your-forest
# Windows:
run.bat
# Linux / macOS:
python3 app.py
```

Zero third-party Python dependencies are required — only Python's standard library (`tkinter`, `sqlite3`, `math`, `random`, etc.) plus Windows PowerShell / MediaPlayer for background rain audio.
