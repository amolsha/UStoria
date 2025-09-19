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

-- ▶️ Runs (one execution of evaluation on a project)
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    prompt_id INTEGER,
    provider_id INTEGER,
    config JSON, -- temperature, max_tokens, etc.
    status TEXT DEFAULT 'completed', -- pending | running | completed | failed
    progress REAL DEFAULT 1.0, -- useful if async in future
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (prompt_id) REFERENCES prompts(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- ✅ Evaluations (criteria results for one story in one run)
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

