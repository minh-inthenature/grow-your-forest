"""
Database module for Grow Your Forest.
Handles all SQLite persistence for sessions, achievements, and settings.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, date, timedelta


APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def _determine_db_path():
    local_path = os.path.join(APP_DIR, "forest_data.db")
    # If app directory is writable (portable mode / local dev)
    try:
        test_file = os.path.join(APP_DIR, ".test_write")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return local_path
    except Exception:
        # System-installed / read-only location (e.g. /usr/share/grow-your-forest on Ubuntu)
        if sys.platform.startswith("win"):
            data_home = os.environ.get("APPDATA", os.path.expanduser("~"))
            target_dir = os.path.join(data_home, "GrowYourForest")
        else:
            data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
            target_dir = os.path.join(data_home, "grow-your-forest")
        os.makedirs(target_dir, exist_ok=True)
        user_db = os.path.join(target_dir, "forest_data.db")
        if not os.path.exists(user_db) and os.path.exists(local_path):
            import shutil
            try:
                shutil.copy2(local_path, user_db)
            except Exception:
                pass
        return user_db


DB_PATH = _determine_db_path()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            planned_duration INTEGER NOT NULL,
            actual_focused_seconds REAL NOT NULL DEFAULT 0,
            tree_stage TEXT NOT NULL DEFAULT 'seed',
            tree_species TEXT NOT NULL DEFAULT 'oak',
            task_name TEXT NOT NULL DEFAULT 'General Study',
            completed INTEGER NOT NULL DEFAULT 0,
            abandoned INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Migration: check if columns exist
    cursor.execute("PRAGMA table_info(sessions)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "tree_species" not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN tree_species TEXT NOT NULL DEFAULT 'oak'")
    if "task_name" not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN task_name TEXT NOT NULL DEFAULT 'General Study'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            unlocked INTEGER NOT NULL DEFAULT 0,
            unlocked_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY,
            total_seconds REAL NOT NULL DEFAULT 0,
            sessions_completed INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            tree_species TEXT NOT NULL DEFAULT 'oak',
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Insert default achievements if not exist
    achievements = [
        ("first_seed", "First Seed", "Complete your first study session", "🌱"),
        ("first_tree", "First Tree", "Accumulate 1 hour of studying", "🌳"),
        ("growing_forest", "Growing Forest", "Plant 10 trees", "🌲"),
        ("deep_focus", "Deep Focus", "Complete a 2-hour study session", "🧘"),
        ("consistency", "Consistency", "Study for 7 consecutive days", "🔥"),
        ("century", "Century", "Accumulate 100 hours of studying", "💯"),
        ("fifty_trees", "Fifty Trees", "Plant 50 trees", "🏕️"),
        ("marathon", "Marathon", "Complete a 90-minute session", "🏃"),
        ("sakura_season", "Sakura Season", "Grow a Cherry Blossom to Mature or Flourishing", "🌸"),
        ("evergreen", "Evergreen", "Grow a Pine to Mature or Flourishing", "🌲"),
        ("ancient_guardian", "Ancient Guardian", "Grow an Angel Oak to Mature or Flourishing", "🌿"),
        ("botanist", "Master Botanist", "Plant all 4 distinct tree species", "🎨"),
    ]
    for aid, name, desc, icon in achievements:
        cursor.execute(
            "INSERT OR IGNORE INTO achievements (id, name, description, icon) VALUES (?, ?, ?, ?)",
            (aid, name, desc, icon)
        )

    conn.commit()
    conn.close()


def get_tree_stage(focused_seconds):
    minutes = focused_seconds / 60
    if minutes >= 120:
        return "flourishing"
    elif minutes >= 60:
        return "mature"
    elif minutes >= 30:
        return "young"
    elif minutes >= 15:
        return "seedling"
    elif minutes >= 5:
        return "sprout"
    else:
        return "seed"


def save_session(start_time, planned_duration, actual_focused_seconds, completed=True, tree_species="oak", task_name="General Study"):
    """Save a completed or abandoned session."""
    conn = get_connection()
    cursor = conn.cursor()

    tree_stage = get_tree_stage(actual_focused_seconds)
    # Only count as completed if they actually studied for at least 1 minute
    is_completed = 1 if completed and actual_focused_seconds >= 60 else 0
    is_abandoned = 0 if is_completed else (1 if not completed else 0)

    # If less than 30 seconds of study, don't save at all
    if actual_focused_seconds < 30:
        conn.close()
        return None

    if not task_name or not task_name.strip():
        task_name = "General Study"
    task_name = task_name.strip()

    cursor.execute("""
        INSERT INTO sessions (start_time, end_time, planned_duration, actual_focused_seconds, tree_stage, tree_species, task_name, completed, abandoned)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        start_time.isoformat(),
        datetime.now().isoformat(),
        planned_duration,
        actual_focused_seconds,
        tree_stage,
        tree_species,
        task_name,
        is_completed,
        is_abandoned
    ))

    # Update daily log
    today = date.today().isoformat()
    cursor.execute("""
        INSERT INTO daily_log (date, total_seconds, sessions_completed)
        VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            total_seconds = total_seconds + ?,
            sessions_completed = sessions_completed + ?
    """, (today, actual_focused_seconds, is_completed, actual_focused_seconds, is_completed))

    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_tree(session_id):
    """Delete a tree/session by ID and reverse its time from daily_log."""
    conn = get_connection()
    cursor = conn.cursor()
    # Fetch session info first
    cursor.execute("SELECT start_time, actual_focused_seconds, completed FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if row:
        secs = row["actual_focused_seconds"]
        is_completed = row["completed"]
        try:
            day_key = row["start_time"][:10]  # YYYY-MM-DD
        except Exception:
            day_key = None
        # Subtract from daily_log
        if day_key:
            cursor.execute("""
                UPDATE daily_log SET
                    total_seconds = MAX(0, total_seconds - ?),
                    sessions_completed = MAX(0, sessions_completed - ?)
                WHERE date = ?
            """, (secs, is_completed, day_key))
        # Delete the session
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_completed_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE completed = 1 ORDER BY start_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_forest_trees():
    """Get all trees for the forest view (sessions with at least 30 seconds)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, actual_focused_seconds, tree_stage, 
               COALESCE(tree_species, 'oak') as tree_species, 
               COALESCE(task_name, 'General Study') as task_name, 
               start_time, completed
        FROM sessions
        WHERE actual_focused_seconds >= 30
        ORDER BY start_time ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_tree_task(session_id, new_task_name):
    """Update the task / subject for a specific tree."""
    if not new_task_name or not new_task_name.strip():
        new_task_name = "General Study"
    new_task_name = new_task_name.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET task_name = ? WHERE id = ?", (new_task_name, session_id))
    conn.commit()
    conn.close()
    return True


def get_task_stats():
    """Get total study time and tree count broken down by task."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(task_name, 'General Study') as task,
               SUM(actual_focused_seconds) as total_seconds,
               COUNT(*) as tree_count
        FROM sessions
        WHERE actual_focused_seconds >= 30
        GROUP BY task
        ORDER BY total_seconds DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_species_stats():
    """Get count of trees planted for each species."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(tree_species, 'oak') as species, COUNT(*) as count
        FROM sessions
        WHERE actual_focused_seconds >= 30
        GROUP BY tree_species
    """)
    rows = cursor.fetchall()
    conn.close()
    return {r["species"]: r["count"] for r in rows}


def get_total_focused_seconds():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(actual_focused_seconds), 0) FROM sessions")
    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_total_trees():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE actual_focused_seconds >= 30")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_completed_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE completed = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_today_seconds():
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("SELECT COALESCE(total_seconds, 0) FROM daily_log WHERE date = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_weekly_seconds():
    conn = get_connection()
    cursor = conn.cursor()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    cursor.execute("""
        SELECT COALESCE(SUM(total_seconds), 0)
        FROM daily_log WHERE date >= ?
    """, (week_ago,))
    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_daily_data_for_week():
    """Get daily study seconds for the last 7 days."""
    conn = get_connection()
    cursor = conn.cursor()
    result = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        cursor.execute("SELECT COALESCE(total_seconds, 0) FROM daily_log WHERE date = ?", (d,))
        row = cursor.fetchone()
        result.append({
            "date": d,
            "seconds": row[0] if row else 0,
            "day_name": (date.today() - timedelta(days=i)).strftime("%a")
        })
    conn.close()
    return result


def get_streak():
    """Calculate current daily study streak."""
    conn = get_connection()
    cursor = conn.cursor()
    streak = 0
    check_date = date.today()

    # Check if user has studied today
    cursor.execute("SELECT total_seconds FROM daily_log WHERE date = ?", (check_date.isoformat(),))
    row = cursor.fetchone()
    if not row or row[0] < 60:  # Need at least 1 minute to count
        # Check yesterday
        check_date = check_date - timedelta(days=1)
        cursor.execute("SELECT total_seconds FROM daily_log WHERE date = ?", (check_date.isoformat(),))
        row = cursor.fetchone()
        if not row or row[0] < 60:
            conn.close()
            return 0

    while True:
        cursor.execute("SELECT total_seconds FROM daily_log WHERE date = ?", (check_date.isoformat(),))
        row = cursor.fetchone()
        if row and row[0] >= 60:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    conn.close()
    return streak


def get_achievements():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM achievements ORDER BY unlocked DESC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_and_unlock_achievements():
    """Check and unlock any newly earned achievements. Returns list of newly unlocked."""
    conn = get_connection()
    cursor = conn.cursor()
    newly_unlocked = []

    total_seconds = get_total_focused_seconds()
    total_trees = get_total_trees()
    streak = get_streak()

    # Get max single session
    cursor_inner = conn.cursor()
    cursor_inner.execute("SELECT COALESCE(MAX(actual_focused_seconds), 0) FROM sessions WHERE completed = 1")
    max_session = cursor_inner.fetchone()[0]

    # Check species stats
    species_stats = get_species_stats()
    distinct_species_count = len(species_stats)

    # Check mature/flourishing trees per species
    cursor_inner.execute("""
        SELECT tree_species, COUNT(*) 
        FROM sessions 
        WHERE tree_stage IN ('mature', 'flourishing')
        GROUP BY tree_species
    """)
    mature_species = {r["tree_species"]: r[1] for r in cursor_inner.fetchall()}

    checks = {
        "first_seed": get_completed_count() >= 1,
        "first_tree": total_seconds >= 3600,
        "growing_forest": total_trees >= 10,
        "deep_focus": max_session >= 7200,
        "consistency": streak >= 7,
        "century": total_seconds >= 360000,
        "fifty_trees": total_trees >= 50,
        "marathon": max_session >= 5400,
        "sakura_season": mature_species.get("cherry_blossom", 0) >= 1,
        "evergreen": mature_species.get("pine", 0) >= 1,
        "ancient_guardian": mature_species.get("angel_oak", 0) >= 1,
        "botanist": distinct_species_count >= 4,
    }

    now = datetime.now().isoformat()
    for aid, condition in checks.items():
        if condition:
            cursor.execute("SELECT unlocked FROM achievements WHERE id = ?", (aid,))
            row = cursor.fetchone()
            if row and not row[0]:
                cursor.execute(
                    "UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE id = ?",
                    (now, aid)
                )
                cursor.execute("SELECT * FROM achievements WHERE id = ?", (aid,))
                newly_unlocked.append(dict(cursor.fetchone()))

    conn.commit()
    conn.close()
    return newly_unlocked


def get_setting(key, default=None):
    """Retrieve a persistent setting value by key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    """Store or update a persistent setting value by key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


# ──────────────── Task List Persistence ────────────────


def get_tasks():
    """Return all tasks ordered with active tasks first and completed tasks at the bottom."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, COALESCE(tree_species, 'oak') AS tree_species,
               completed, created_at, completed_at, sort_order
        FROM tasks
        ORDER BY completed ASC, completed_at DESC, sort_order ASC, id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_task_by_id(task_id):
    """Fetch a single task by ID, or None if not found."""
    if task_id is None:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, COALESCE(tree_species, 'oak') AS tree_species,
               completed, created_at, completed_at, sort_order
        FROM tasks WHERE id = ?
    """, (int(task_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_task(title, tree_species="oak"):
    """Insert a new task assigned to a tree species and return the created task dict."""
    clean_title = (title or "").strip()
    if not clean_title:
        return None
    species = tree_species or "oak"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, tree_species, completed, created_at, completed_at, sort_order)
        VALUES (?, ?, 0, ?, NULL, 0)
    """, (clean_title, species, now))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def set_task_completed(task_id, completed=True):
    """Explicitly mark a task completed or incomplete."""
    if task_id is None:
        return None
    val = 1 if completed else 0
    comp_at = datetime.now().isoformat() if val else None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET completed = ?, completed_at = ? WHERE id = ?",
        (val, comp_at, int(task_id)),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def toggle_task_completed(task_id):
    """Toggle a task's completion status and return the updated task dict."""
    task = get_task_by_id(task_id)
    if not task:
        return None
    return set_task_completed(task_id, not bool(task["completed"]))


def update_task_species(task_id, tree_species):
    """Update the tree species assigned to a task."""
    if task_id is None:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET tree_species = ? WHERE id = ?",
        (tree_species or "oak", int(task_id)),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def delete_task(task_id):
    """Delete a task by ID."""
    if task_id is None:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (int(task_id),))
    conn.commit()
    conn.close()


def get_completed_tasks_count():
    """Return total number of completed tasks in the task list."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def export_backup_data():
    """Collect sessions, daily logs, achievements, tasks, and settings into a JSON-serializable dict."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, start_time, end_time, planned_duration, actual_focused_seconds,
               tree_stage, COALESCE(tree_species, 'oak') AS tree_species,
               COALESCE(task_name, 'General Study') AS task_name,
               completed, abandoned
        FROM sessions
        ORDER BY id ASC
    """)
    sessions = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT date, total_seconds, sessions_completed
        FROM daily_log
        ORDER BY date ASC
    """)
    daily_log = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT id, name, description, icon, unlocked, unlocked_at
        FROM achievements
        ORDER BY id ASC
    """)
    achievements = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT id, title, COALESCE(tree_species, 'oak') AS tree_species,
               completed, created_at, completed_at, sort_order
        FROM tasks
        ORDER BY id ASC
    """)
    tasks = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT key, value FROM settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}

    conn.close()
    return {
        "app": "Grow Your Forest",
        "version": "1.2.0",
        "exported_at": datetime.now().isoformat(),
        "sessions": sessions,
        "daily_log": daily_log,
        "achievements": achievements,
        "tasks": tasks,
        "settings": settings,
    }


def export_to_json_file(filepath):
    """Write a complete local forest backup to a JSON file."""
    data = export_backup_data()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def import_backup_data(data):
    """Restore sessions, daily study history, streaks, achievements, tasks, and settings from a backup dict."""
    if not isinstance(data, dict) or not any(
        k in data for k in ("sessions", "daily_log", "achievements", "tasks", "settings")
    ):
        raise ValueError("Invalid Grow Your Forest backup file.")

    sessions = data.get("sessions") or []
    daily_log = data.get("daily_log") or []
    achievements = data.get("achievements") or []
    tasks = data.get("tasks") or []
    settings = data.get("settings") or {}

    if not isinstance(sessions, list) or not isinstance(daily_log, list):
        raise ValueError("Backup sessions or daily_log format is invalid.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        for s in sessions:
            if not isinstance(s, dict) or not s.get("start_time"):
                continue
            sid = s.get("id")
            if sid is not None:
                cursor.execute("""
                    INSERT OR REPLACE INTO sessions (
                        id, start_time, end_time, planned_duration, actual_focused_seconds,
                        tree_stage, tree_species, task_name, completed, abandoned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(sid),
                    s["start_time"],
                    s.get("end_time"),
                    int(s.get("planned_duration", 1500)),
                    float(s.get("actual_focused_seconds", 0.0)),
                    s.get("tree_stage", "seed"),
                    s.get("tree_species", "oak") or "oak",
                    s.get("task_name", "General Study") or "General Study",
                    int(s.get("completed", 0)),
                    int(s.get("abandoned", 0)),
                ))
            else:
                cursor.execute("""
                    INSERT INTO sessions (
                        start_time, end_time, planned_duration, actual_focused_seconds,
                        tree_stage, tree_species, task_name, completed, abandoned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s["start_time"],
                    s.get("end_time"),
                    int(s.get("planned_duration", 1500)),
                    float(s.get("actual_focused_seconds", 0.0)),
                    s.get("tree_stage", "seed"),
                    s.get("tree_species", "oak") or "oak",
                    s.get("task_name", "General Study") or "General Study",
                    int(s.get("completed", 0)),
                    int(s.get("abandoned", 0)),
                ))

        for d in daily_log:
            if not isinstance(d, dict) or not d.get("date"):
                continue
            cursor.execute("""
                INSERT OR REPLACE INTO daily_log (date, total_seconds, sessions_completed)
                VALUES (?, ?, ?)
            """, (
                d["date"],
                float(d.get("total_seconds", 0.0)),
                int(d.get("sessions_completed", 0)),
            ))

        unlocked_restored = 0
        if isinstance(achievements, list):
            for a in achievements:
                if not isinstance(a, dict) or not a.get("id"):
                    continue
                is_unlocked = 1 if a.get("unlocked") else 0
                if is_unlocked:
                    unlocked_restored += 1
                    cursor.execute(
                        "UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE id = ?",
                        (a.get("unlocked_at") or datetime.now().isoformat(), a["id"]),
                    )

        tasks_restored = 0
        if isinstance(tasks, list):
            for t in tasks:
                if not isinstance(t, dict) or not t.get("title"):
                    continue
                tid = t.get("id")
                if tid is not None:
                    cursor.execute("""
                        INSERT OR REPLACE INTO tasks (
                            id, title, tree_species, completed, created_at, completed_at, sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(tid),
                        str(t["title"]),
                        t.get("tree_species", "oak") or "oak",
                        1 if t.get("completed") else 0,
                        t.get("created_at") or datetime.now().isoformat(),
                        t.get("completed_at"),
                        int(t.get("sort_order", 0)),
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO tasks (
                            title, tree_species, completed, created_at, completed_at, sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(t["title"]),
                        t.get("tree_species", "oak") or "oak",
                        1 if t.get("completed") else 0,
                        t.get("created_at") or datetime.now().isoformat(),
                        t.get("completed_at"),
                        int(t.get("sort_order", 0)),
                    ))
                tasks_restored += 1

        if isinstance(settings, dict):
            for k, v in settings.items():
                if k and v is not None:
                    cursor.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (str(k), str(v)),
                    )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    # Re-evaluate milestone unlocks cleanly in case streak/total thresholds match
    check_and_unlock_achievements()
    return {
        "sessions_restored": len(sessions),
        "days_restored": len(daily_log),
        "achievements_restored": unlocked_restored,
        "tasks_restored": tasks_restored,
    }


def import_from_json_file(filepath):
    """Load and restore a local JSON backup created by export_to_json_file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_backup_data(data)


# Initialize DB on import
init_db()
