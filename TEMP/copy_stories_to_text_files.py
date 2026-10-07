import pandas as pd

def split_user_stories(excel_file, sheet_name="USs - Shuffled"):
    # Load Excel sheet into a DataFrame
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Ensure correct columns exist
    if not all(col in df.columns for col in ["S.No.", "User Story", "Label"]):
        raise ValueError("Excel sheet must have columns: S.No., User Story, Label")

    # Extract only the 'User Story' column
    stories = df["User Story"].dropna().tolist()

    # Check we have at least 120 stories
    if len(stories) < 120:
        raise ValueError(f"Expected at least 120 user stories, found {len(stories)}")

    # First 60 stories
    first_half = stories[:60]
    second_half = stories[60:120]

    # Save to text files
    with open("Unambiguous_Batch_1.txt", "w", encoding="utf-8") as f1:
        for story in first_half:
            f1.write(story.strip() + "\n")

    with open("Unambiguous_Batch_2.txt", "w", encoding="utf-8") as f2:
        for story in second_half:
            f2.write(story.strip() + "\n")

    print("✅ User stories successfully split into 'user_stories_1.txt' and 'user_stories_2.txt'")

# Example usage
if __name__ == "__main__":
    split_user_stories("Results_Unambiguous_Criterion.xlsx")  # replace with your Excel file path
