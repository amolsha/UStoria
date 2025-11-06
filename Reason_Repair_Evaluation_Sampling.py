import pandas as pd

# ---------- CONFIGURATION ----------
INPUT_FILE = "evaluations_original.csv"
OUTPUT_FILE = "evaluations_sampled.csv"
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
    .apply(lambda x: x.sample(n=min(SAMPLES_PER_CELL, len(x)), random_state=RANDOM_STATE))
    .reset_index(drop=True)
)

# ---------- EXPORT ----------
sample_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Created stratified sample of {len(sample_df)} rows.")
print(f"Saved to '{OUTPUT_FILE}'")
