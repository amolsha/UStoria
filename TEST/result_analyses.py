import pandas as pd
import os
import numpy as np

# ==================================================
# Configuration
# ==================================================
MODEL_NAME = "qwen-turbo"
BASE_DIR = os.path.join(os.getcwd(), "RESULTS")
OUTPUT_FILE = os.path.join(BASE_DIR, MODEL_NAME+"_full_qualitative_analysis.xlsx")

# Thresholds for interpretations (tunable)
HIGH_F1 = 0.90
MODERATE_F1 = 0.75
PR_GAP = 0.15
CONTEXT_SENSITIVE = 0.05

# ==================================================
# Step 1: Load Data
# ==================================================
df_min = pd.read_excel(os.path.join(BASE_DIR, MODEL_NAME+"_MINIMAL.xlsx"))
df_rich = pd.read_excel(os.path.join(BASE_DIR, MODEL_NAME+"_rich.xlsx"))
df_overall = pd.read_excel(os.path.join(BASE_DIR, MODEL_NAME+"_OVERALL.xlsx"))

df_min["Context"] = "Minimal"
df_rich["Context"] = "Rich"
df_overall["Context"] = "Overall"

df = pd.concat([df_min, df_rich, df_overall], ignore_index=True)

# ==================================================
# Step 2: Add Criterion Dimensions
# ==================================================
DIMENSION_MAP = {
    "Well-formed": "Syntactic",
    "Atomic": "Syntactic",
    "Minimal": "Syntactic",
    "Conceptually sound": "Semantic",
    "Problem-oriented": "Semantic",
    "Unambiguous": "Semantic",
    "Full sentence": "Pragmatic",
    "Estimable": "Pragmatic"
}

df["Dimension"] = df["Criterion"].map(DIMENSION_MAP)

# ==================================================
# Step 3: Precision–Recall Asymmetry
# ==================================================
df["PR_Gap"] = (df["precision"] - df["recall"]).round(3)

def pr_gap_comment(row):
    if abs(row.PR_Gap) < PR_GAP:
        return "Balanced precision–recall behavior."
    elif row.PR_Gap > 0:
        return "Conservative evaluation: high precision but missed positives."
    else:
        return "Overgeneralized evaluation: higher recall than precision."

df["PR_Interpretation"] = df.apply(pr_gap_comment, axis=1)

# ==================================================
# Step 4: Context Sensitivity (Minimal vs Rich)
# ==================================================
pivot_f1 = df[df["Context"].isin(["Minimal", "Rich"])].pivot(
    index="Criterion",
    columns="Context",
    values="f1"
)

pivot_acc = df[df["Context"].isin(["Minimal", "Rich"])].pivot(
    index="Criterion",
    columns="Context",
    values="accuracy"
)

context_impact = pd.DataFrame({
    "ΔF1 (Rich - Minimal)": (pivot_f1["Rich"] - pivot_f1["Minimal"]).round(3),
    "ΔAccuracy (Rich - Minimal)": (pivot_acc["Rich"] - pivot_acc["Minimal"]).round(3)
})

def context_comment(val):
    if abs(val) < CONTEXT_SENSITIVE:
        return "Context-invariant criterion."
    elif val > 0:
        return "Benefits from context-rich prompting."
    else:
        return "Performance degrades with added context."

context_impact["Context_Interpretation"] = context_impact["ΔF1 (Rich - Minimal)"].apply(context_comment)

# ==================================================
# Step 5: Criterion Competence Assessment
# ==================================================
overall_df = df[df["Context"] == "Overall"].copy()

def competence_comment(row):
    if row.f1 >= HIGH_F1:
        return "Model evaluates this criterion reliably and robustly."
    elif row.f1 >= MODERATE_F1:
        return "Model shows moderate competence; some inconsistencies observed."
    else:
        return "Model struggles to evaluate this criterion accurately."

overall_df["Competence_Assessment"] = overall_df.apply(competence_comment, axis=1)

# ==================================================
# Step 6: Dimension-wise Insights (NO averaging for Overall)
# ==================================================
dimension_summary = (
    overall_df
    .groupby("Dimension")[["precision", "recall", "f1", "accuracy"]]
    .mean()
    .round(3)
)

def dimension_comment(f1):
    if f1 >= HIGH_F1:
        return "Dimension is well-handled by the model."
    elif f1 >= MODERATE_F1:
        return "Dimension poses moderate semantic challenges."
    else:
        return "Dimension requires deeper reasoning beyond surface patterns."

dimension_summary["Interpretation"] = dimension_summary["f1"].apply(dimension_comment)

# ==================================================
# Step 7: Focus Recommendation Engine
# ==================================================
def focus_priority(row):
    if row.f1 < MODERATE_F1:
        return "High priority for improvement."
    elif row.PR_Gap > PR_GAP:
        return "Needs recall improvement."
    else:
        return "Low priority; evaluation stable."

overall_df["Research_Focus_Recommendation"] = overall_df.apply(focus_priority, axis=1)

# ==================================================
# Step 8: Save Everything
# ==================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Raw_Combined_Data", index=False)
    context_impact.to_excel(writer, sheet_name="Context_Impact")
    overall_df.to_excel(writer, sheet_name="Overall_Criterion_Assessment", index=False)
    dimension_summary.to_excel(writer, sheet_name="Dimension_Summary")

print("✅ Deep qualitative + quantitative analysis completed.")
print(f"📄 Output saved at: {OUTPUT_FILE}")
