import sqlite3
import pandas as pd

# ---------- CONFIGURATION ----------
DB_PATH = "data\evaluations.db"       # path to your SQLite database file
OUTPUT_CSV = "evaluations.csv"

# Map prompt_type to short codes
CONTEXT_MAP = {
    "context-minimal": "CM",
    "context-rich": "CR"
}

# ---------- SQL QUERY ----------
# Adjust story_text column name if different (e.g., s.text or s.content)
QUERY = """
SELECT
    e.story_id AS story_id,
    s.text AS original_story,
    r.llm_name AS model,
    r.prompt_type AS prompt_type,
    e.criterion AS criterion,
    e.passed AS passed,
    e.reason AS reason,
    e.repair AS repair
FROM evaluations e
JOIN runs r ON e.run_id = r.id
JOIN stories s ON e.story_id = s.id
where 
r.llm_name in 
('gpt-4.1-mini',
'deepseek-chat',
'gpt-5-mini',
'qwen-turbo',
'gemini-2.5-flash',
'grok-4-fast'
)
ORDER BY r.llm_name, r.prompt_type, e.story_id;
"""

# ---------- MAIN SCRIPT ----------
def export_evaluations(db_path=DB_PATH, output_csv=OUTPUT_CSV):
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(QUERY, conn)
    conn.close()

    # Map context to CM/CR
    df["context"] = df["prompt_type"].map(CONTEXT_MAP).fillna(df["prompt_type"])

    # Convert boolean/int passed → "Yes"/"No"
    df["original_label"] = df["passed"].apply(lambda x: "Yes" if x in [1, True, "1", "true", "True"] else "No")

    # Keep and reorder columns for the meta-evaluation pipeline
    df = df[[
        "story_id",
        "model",
        "context",
        "criterion",
        "original_label",
        "reason",
        "repair",
        "original_story"
    ]]

    # Sort for readability
    df = df.sort_values(by=["model", "context", "story_id"]).reset_index(drop=True)

    # Export
    df.to_csv(output_csv, index=False)
    print(f"✅ Exported {len(df)} rows to '{output_csv}'")

    # Show preview
    print("\nSample output:")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    export_evaluations()