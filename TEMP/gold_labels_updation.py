import sqlite3
import pandas as pd

# Path to your database
DB_PATH = "data/evaluations.db"
# Path to your Excel file
EXCEL_PATH = "Results_Estimable_Criterion.xlsx"
EXCEL_SHEET = "USs - Shuffled"
CRITERION = "Estimable"  # specify the criterion

# Well-formed
# Atomic
# Minimal
# Unambiguous
# Full sentence
# Problem-oriented
# Conceptually sound
# Estimable
# 1️⃣ Load Excel sheet
df = pd.read_excel(EXCEL_PATH, sheet_name=EXCEL_SHEET)

# Ensure column names are trimmed
df.columns = [c.strip() for c in df.columns]

# Create a dictionary for fast lookup: {story_text: label_value}
excel_lookup = dict(zip(df["User Story"], df["Label"]))
print(excel_lookup)

# 2️⃣ Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 3️⃣ Fetch story_id and story text from gold_labels + stories for the specified criterion
cursor.execute(f"""
    SELECT g.story_id, s.text
    FROM gold_labels g
    JOIN stories s ON g.story_id = s.id
    WHERE TRIM(g.criterion) = ?
""", (CRITERION,))

rows = cursor.fetchall()
print(rows)
# 4️⃣ Update gold_labels with the label from Excel
for story_id, story_text in rows:
    label_value = excel_lookup.get(story_text)
    if label_value is not None:
        cursor.execute("""
            UPDATE gold_labels
            SET passed = ?
            WHERE story_id = ? AND criterion = ?
        """, (label_value, story_id, CRITERION))
    else:
        print(f"[WARN] Story not found in Excel: {story_text}")

# 5️⃣ Commit and close
conn.commit()
conn.close()

print("✅ gold_labels updated successfully!")
