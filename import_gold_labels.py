import sqlite3
import pandas as pd

DB_PATH = "data\evaluations.db"
EXCEL_PATH = "Results_Unambiguous_Criterion.xlsx"
SHEET_NAME = "USs - Shuffled"

def import_gold_labels(annotator="human1"):
    # Load Excel
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

    # Ensure columns exist
    assert {"User Story", "Label"}.issubset(df.columns), "Missing required columns in Excel"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for _, row in df.iterrows():
        story_text = str(row["User Story"]).strip()
        label = str(row["Label"]).strip().lower()

        # Convert label to boolean
        passed = label in ["yes", "true", "1", "pass"]

        # 1. Find the evaluation entry for this story
        cur.execute("""
            SELECT e.id 
            FROM evaluations e
            JOIN stories s ON e.story_id = s.id
            WHERE s.text = ?
        """, (story_text,))
        evaluation_row = cur.fetchone()

        if not evaluation_row:
            print(f"⚠️ No evaluation found for story: {story_text[:50]}...")
            continue

        evaluation_id = evaluation_row[0]

        # 2. Insert into human_evaluations
        cur.execute("""
            INSERT INTO human_evaluations (evaluation_id, annotator, passed, explanation)
            VALUES (?, ?, ?, ?)
        """, (evaluation_id, annotator, passed, "Imported from Excel"))

    conn.commit()
    conn.close()
    print("✅ Gold labels imported successfully.")


if __name__ == "__main__":
    import_gold_labels()
