import sqlite3
from pathlib import Path

DB_PATH = Path("data/evaluations.db")
SCHEMA_PATH = Path("data/schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # dict-like access
    return conn


def init_db():
    """Initialize database from schema.sql (future-proof)."""
    conn = get_connection()
    cur = conn.cursor()

    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cur.executescript(f.read())
    else:
        # fallback minimal schema (if schema.sql missing)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            config JSON,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            story_id INTEGER NOT NULL,
            criterion TEXT NOT NULL,
            passed BOOLEAN,
            reason TEXT,
            repair TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES runs(id),
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
        """)

    conn.commit()
    conn.close()


# --------------------
# Insert functions
# --------------------

def insert_project(name: str, description: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO projects (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def insert_story(project_id: int, text: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO stories (project_id, text) VALUES (?, ?)", (project_id, text))
    conn.commit()
    story_id = cur.lastrowid
    conn.close()
    return story_id


def insert_run(project_id: int, config: dict = None, status: str = "completed") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO runs (project_id, config, status) VALUES (?, ?, ?)",
                (project_id, str(config) if config else None, status))
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def insert_evaluation(run_id: int, story_id: int, criterion: str,
                      passed: bool, reason: str, repair: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO evaluations (run_id, story_id, criterion, passed, reason, repair)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (run_id, story_id, criterion, int(passed), reason, repair))
    conn.commit()
    conn.close()


# --------------------
# Query functions
# --------------------

def get_project_stories(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stories WHERE project_id = ? ORDER BY created_at", (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_story_with_evaluations(story_id: int, run_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    story = cur.fetchone()
    cur.execute("SELECT * FROM evaluations WHERE story_id = ? AND run_id = ?", (story_id, run_id))
    evaluations = cur.fetchall()
    conn.close()
    return story, evaluations


def get_run_summary(run_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id as story_id, s.text,
               COUNT(e.id) as total_criteria,
               SUM(CASE WHEN e.passed = 1 THEN 1 ELSE 0 END) as passed_criteria
        FROM stories s
        LEFT JOIN evaluations e ON s.id = e.story_id AND e.run_id = ?
        WHERE s.project_id = (SELECT project_id FROM runs WHERE id = ?)
        GROUP BY s.id
        ORDER BY s.created_at
    """, (run_id, run_id))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_projects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*,
               (SELECT COUNT(*) FROM stories s WHERE s.project_id = p.id) as story_count,
               (SELECT COUNT(*) FROM runs r WHERE r.project_id = p.id) as run_count
        FROM projects p
        ORDER BY p.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Cascade delete runs & stories
    cur.execute("DELETE FROM evaluations WHERE story_id IN (SELECT id FROM stories WHERE project_id=?)", (project_id,))
    cur.execute("DELETE FROM runs WHERE project_id=?", (project_id,))
    cur.execute("DELETE FROM stories WHERE project_id=?", (project_id,))
    cur.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


def get_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_project(project_id: int, name: str, description: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE projects
        SET name = ?, description = ?
        WHERE id = ?
    """, (name, description, project_id))
    conn.commit()
    conn.close()