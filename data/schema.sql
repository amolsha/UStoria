-- schema.sql for UStoria (UserStoryQualityEvaluator)
-- Future-ready but minimal implementation supported

PRAGMA foreign_keys = ON;

-- 🧑 Users (future multi-user support)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'user', -- user | admin | researcher
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 📂 Projects (group of user stories)
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 📝 Stories (individual user stories)
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 🔮 Providers (OpenAI, Anthropic, HuggingFace, etc.)
CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 📜 Prompts (versioned templates: minimal, rich, custom)
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    template TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 👩‍⚖️ Human Evaluations (optional benchmarking)
CREATE TABLE IF NOT EXISTS human_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER NOT NULL,
    annotator TEXT,
    passed BOOLEAN,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
);

CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS batch_stories (
    batch_id INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    PRIMARY KEY (batch_id, story_id),
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (story_id) REFERENCES stories(id)
);

-- Runs table (each evaluation attempt is a "run")
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    llm_name TEXT NOT NULL,
    prompt_type TEXT NOT NULL,       -- e.g., "context-rich", "context-minimal"
    temperature REAL,                -- optional
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,           -- set after run completes
    duration_seconds REAL,           -- total time taken
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE
);

-- Evaluations table (per story results of each run)
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    criterion TEXT NOT NULL,         -- e.g. "Clarity", "Testability"
    passed BOOLEAN NOT NULL,
    reason TEXT,
    repair TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE,
    FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
);

-- Gold_Labels table
CREATE TABLE IF NOT EXISTS gold_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    criterion TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    reason TEXT,
    repair TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

