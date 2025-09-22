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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)

        cur.execute(
            """
                CREATE TABLE IF NOT EXISTS batch_stories (
                batch_id INTEGER NOT NULL,
                story_id INTEGER NOT NULL,
                PRIMARY KEY (batch_id, story_id),
                FOREIGN KEY (batch_id) REFERENCES batches(id),
                FOREIGN KEY (story_id) REFERENCES stories(id)
            )
            """
        )

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

# --------------------
# Query functions
# --------------------

def get_stories_for_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stories WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_story(story_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    row = cur.fetchone()
    conn.close()
    return row

def insert_stories_bulk(project_id: int, stories: list[str]):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("INSERT INTO stories (project_id, text) VALUES (?, ?)",
                    [(project_id, s.strip()) for s in stories if s.strip()])
    conn.commit()
    conn.close()

def update_story(story_id: int, new_text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE stories SET text = ? WHERE id = ?", (new_text, story_id))
    conn.commit()
    conn.close()

def delete_story(story_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()

def get_story_with_evaluations(story_id: int, run_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    story = cur.fetchone()
    cur.execute("SELECT * FROM evaluations WHERE story_id = ? AND run_id = ?", (story_id, run_id))
    evaluations = cur.fetchall()
    conn.close()
    return story, evaluations

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

def create_batch(project_id: int, name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO batches (project_id, name) VALUES (?, ?)", (project_id, name))
    conn.commit()
    batch_id = cur.lastrowid
    conn.close()
    return batch_id


def assign_story_to_batch(batch_id: int, story_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO batch_stories (batch_id, story_id) VALUES (?, ?)", (batch_id, story_id))
    conn.commit()
    conn.close()


def get_batches_of_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.name, b.created_at, COUNT(bs.story_id) as story_count
        FROM batches b
        LEFT JOIN batch_stories bs ON b.id = bs.batch_id
        WHERE b.project_id = ?
        GROUP BY b.id
        ORDER BY b.created_at DESC
    """, (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_batch(batch_id: int):
    """
    Fetch a batch by its ID along with basic info like name, project_id, created_at.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, project_id, name, created_at
        FROM batches
        WHERE id = ?
    """, (batch_id,))
    batch = cur.fetchone()
    conn.close()
    return batch


def get_stories_in_batch(batch_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
            SELECT s.* FROM stories s
            JOIN batch_stories bs ON s.id = bs.story_id
            WHERE bs.batch_id = ?
            ORDER BY s.id ASC
        """, (batch_id,))
    stories = cur.fetchall()
    conn.close()
    return stories

def assign_stories_to_batch(batch_id: int, story_ids: list):
    conn = get_connection()
    cur = conn.cursor()
    for story_id in story_ids:
        cur.execute(
            "INSERT OR IGNORE INTO batch_stories (batch_id, story_id) VALUES (?, ?)",
            (batch_id, story_id)
        )
    conn.commit()
    conn.close()

def update_batch(batch_id: int, name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE batches
        SET name = ?
        WHERE id = ?
    """, (name, batch_id))
    conn.commit()
    conn.close()

def delete_batch(batch_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Delete batch-story assignments first
    cur.execute("DELETE FROM batch_stories WHERE batch_id = ?", (batch_id,))
    # Delete the batch itself
    cur.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
    conn.commit()
    conn.close()

# -------------------------------
# Run + Evaluation functions
# -------------------------------

def insert_run(project_id: int, batch_id: int, llm_name: str, prompt_type: str, temperature: float = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO runs (project_id, batch_id, llm_name, prompt_type, temperature)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, batch_id, llm_name, prompt_type, temperature))
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def finish_run(run_id: int, duration_seconds: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE runs
        SET finished_at = CURRENT_TIMESTAMP,
            duration_seconds = ?
        WHERE id = ?
    """, (duration_seconds, run_id))
    conn.commit()
    conn.close()


def get_runs_for_batch(batch_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM runs WHERE batch_id = ? ORDER BY started_at DESC", (batch_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_evaluation(run_id: int, story_id: int, criterion: str, passed: bool, reason: str, repair: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO evaluations (run_id, story_id, criterion, passed, reason, repair)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (run_id, story_id, criterion, passed, reason, repair))
    conn.commit()
    conn.close()


def get_evaluations_for_run(run_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.story_id,
               s.text AS story_text,
               e.criterion,
               e.passed,
               e.reason,
               e.repair
        FROM evaluations e
        JOIN stories s ON e.story_id = s.id
        WHERE e.run_id = ?
        ORDER BY e.story_id, e.criterion
    """, (run_id,))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "story_id": row["story_id"],
            "story_text": row["story_text"],
            "criterion": row["criterion"],
            "passed": bool(row["passed"]),
            "reason": row["reason"],
            "repair": row["repair"],
        }
        for row in rows
    ]

def get_run_summary(run_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            criterion,
            SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) as passed_count,
            SUM(CASE WHEN passed=0 THEN 1 ELSE 0 END) as failed_count,
            COUNT(*) as total
        FROM evaluations
        WHERE run_id = ?
        GROUP BY criterion
    """, (run_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

# -------------------------------------------------
# Gold label helpers (models/storage.py)
# -------------------------------------------------
def insert_gold_label(story_id: int, criterion: str, passed: bool, reason: str = None, repair: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO gold_labels (story_id, criterion, passed, reason, repair)
        VALUES (?, ?, ?, ?, ?)
    """, (story_id, criterion, int(bool(passed)), reason, repair))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid


def upsert_gold_label(story_id: int, criterion: str, passed: bool, reason: str = None, repair: str = None):
    """
    Simple upsert: delete existing label for story+criterion and insert new one.
    (Keeps behavior simple and deterministic.)
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM gold_labels WHERE story_id = ? AND criterion = ?", (story_id, criterion))
    cur.execute("""
        INSERT INTO gold_labels (story_id, criterion, passed, reason, repair)
        VALUES (?, ?, ?, ?, ?)
    """, (story_id, criterion, int(bool(passed)), reason, repair))
    conn.commit()
    conn.close()


def get_gold_labels_for_story(story_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, story_id, criterion, passed, reason, repair, created_at
        FROM gold_labels
        WHERE story_id = ?
        ORDER BY criterion
    """, (story_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_gold_labels_for_batch(batch_id: int):
    """
    Return gold labels for all stories in a batch.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT gl.*, s.text as story_text
        FROM gold_labels gl
        JOIN stories s ON gl.story_id = s.id
        JOIN batch_stories bs ON bs.story_id = s.id
        WHERE bs.batch_id = ?
        ORDER BY s.id, gl.criterion
    """, (batch_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_gold_labels_for_story(story_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM gold_labels WHERE story_id = ?", (story_id,))
    conn.commit()
    conn.close()


def insert_gold_labels_bulk(rows: list):
    """
    rows: list of dicts with keys:
       - story_id (int)
       - criterion (str)
       - passed (bool/int/str)
       - reason (str, optional)
       - repair (str, optional)
    Returns number inserted.
    """
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT INTO gold_labels (story_id, criterion, passed, reason, repair)
                VALUES (?, ?, ?, ?, ?)
            """, (r["story_id"], r["criterion"], int(bool(r["passed"])), r.get("reason"), r.get("repair")))
            inserted += 1
        except Exception:
            # skip problematic rows (log if you want)
            continue
    conn.commit()
    conn.close()
    return inserted
