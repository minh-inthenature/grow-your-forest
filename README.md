# Grow Your Forest

A cozy desktop focus timer built with Python & Tkinter. Complete study/focus sessions to grow distinct trees (Cherry Blossom, Pine, Angel Oak, Classic Oak) across a layered 2D forest sanctuary with ambient rain sound and four atmospheric themes: **Morning**, **Afternoon**, **Night**, and **Chill**.

## Features

- **Focus Timer & Study Growth**: Watch your active tree evolve across 5 stages — *Seed → Sprout → Small Sapling → Young Tree → Mature Tree* — as you study.
- **Living 2D Sanctuary**: Multi-layer distant mountains, rolling hills, winding river, stepping stones, flowers, grass, clouds, and subtle wildlife/particles.
- **Four Themes**:
  - **Morning**: Crisp meadow light and fresh morning sky
  - **Afternoon**: Golden-hour warmth
  - **Night**: Starry twilight with fireflies and dark indigo UI
  - **Chill**: Cozy, darker roasted-cocoa & warm dusk atmosphere
- **Ambient Rain Audio**: Continuous seamless looping rain backdrop with volume control (`user_rain.mp3` + fallback `rain_master.wav`).
- **Progress & Achievements**: Local SQLite persistence (`forest_data.db`), daily streak tracking, focus statistics, and tree inspection inside **My Forest**.

---

## Quick Setup on Another Windows Computer

### Option 1: Portable Release ZIP (Recommended — No Git needed)

1. Go to the [**Releases**](../../releases) page and download **`GrowYourForest-Portable.zip`** (or **`GrowYourForest.exe`** if attached).
2. Right-click `GrowYourForest-Portable.zip` → **Extract All...** into a folder you want to keep (for example `Documents\GrowYourForest`).
3. **If using `GrowYourForest-Portable.zip`**:
   - Requires Python 3 with Tkinter (standard on the official [Python for Windows](https://www.python.org/downloads/) installer — check **"Add Python to PATH"** during setup, no `pip install` packages required!).
   - Double-click **`run.bat`** to start the app.
   - *(Optional)* Double-click **`create_shortcut.bat`** to place a **Grow Your Forest** icon on your Desktop.
4. **If using standalone `GrowYourForest.exe`** *(built automatically by GitHub Actions)*:
   - Double-click **`GrowYourForest.exe`** directly — no Python installation required! Your progress is saved in `forest_data.db` right next to the `.exe`.

### Option 2: Clone with Git

```bat
git clone https://github.com/minh-inthenature/grow-your-forest.git
cd grow-your-forest
run.bat
```

Zero third-party Python dependencies are required — only Python's standard library (`tkinter`, `sqlite3`, `math`, `random`, etc.) plus Windows PowerShell / MediaPlayer for background rain audio.
