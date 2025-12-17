import pandas as pd

# ---------- CONFIGURATION ----------
#INPUT_FILE = "evaluations.csv"
INPUT_FILE = "evaluations_correct_failed.csv"
OUTPUT_FILE = "evaluations_sampled.xlsx"
SAMPLES_PER_CELL = 10
RANDOM_STATE = 42

# ---------- LOAD DATA ----------
df = pd.read_csv(INPUT_FILE)

# ---------- FILTER ----------
# Only failed stories (original_label == "No")
failed_df = df[df["original_label"].str.lower() == "no"].copy()

# Keep only rows where both reason and repair are non-empty / non-null
filtered_df = failed_df[
    failed_df["reason"].notna()
    & failed_df["repair"].notna()
    & (failed_df["reason"].astype(str).str.strip() != "")
    & (failed_df["repair"].astype(str).str.strip() != "")
].copy()

print(f"Total failed cases: {len(failed_df)}")
print(f"After removing empty reason/repair: {len(filtered_df)}")

# ---------- STRATIFIED SAMPLING ----------
# Group by model, context, and criterion, then sample up to SAMPLES_PER_CELL per group
sample_df = (
    filtered_df.groupby(["model", "context", "criterion"], group_keys=False)
    .apply(lambda x: x.sample(n=min(SAMPLES_PER_CELL, len(x)), random_state=RANDOM_STATE),
        include_groups=True)
    .reset_index(drop=True)
)

# ---------- SAMPLE COUNTS PER CELL ----------
counts_df = (
    sample_df
    .groupby(["model", "context", "criterion"])
    .size()
    .reset_index(name="samples_drawn")
)

print("\n📊 Samples drawn per (model, context, criterion):")
print(counts_df.to_string(index=False))

# ---------- OVERALL SUMMARY ----------
summary_df = pd.DataFrame({
    "Metric": [
        "Total failed cases",
        "After removing empty reason/repair",
        "Total sampled rows"
    ],
    "Value": [
        len(failed_df),
        len(filtered_df),
        len(sample_df)
    ]
})

# ---------- EXPORT ----------
sample_df.to_csv("evaluations_sampled.csv", index=False)
# ---------- EXPORT TO EXCEL (MULTI-SHEET) ----------
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    # Sheet 1: Sampled data
    sample_df.to_excel(writer, sheet_name="Sampled Data", index=False)

    # Sheet 2: Sampling summary
    counts_df.to_excel(writer, sheet_name="Sampling Summary", index=False)

    # Sheet 3: Overall statistics
    summary_df.to_excel(writer, sheet_name="Overall Stats", index=False)

print(f"✅ Excel file created with sampling summary: '{OUTPUT_FILE}'")

print(f"✅ Created stratified sample of {len(sample_df)} rows.")
print(f"Saved to '{OUTPUT_FILE}'")
