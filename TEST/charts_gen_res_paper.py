"""
=========================================================
LLM Performance Visualization Script (Model-wise Inputs)
For Research Paper: User Story Quality Evaluation
=========================================================

Input format (per model):
<model_name>_MINIMAL.xlsx
<model_name>_RICH.xlsx
<model_name>_OVERALL.xlsx
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# --------------------------------------------------------
# Utility: Safe column detection
# --------------------------------------------------------

def find_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of the columns {candidates} found in dataframe")

# --------------------------------------------------------
# Configuration
# --------------------------------------------------------

BASE_DIR = "LLM_EVALUATION"
OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------
# Criterion → Category mapping
# --------------------------------------------------------

CRITERION_CATEGORY_MAP = {
    # Syntactic
    "Atomic": "Syntactic",
    "Minimal": "Syntactic",
    "Well-formed": "Syntactic",

    # Semantic
    "Conceptually sound": "Semantic",
    "Problem-oriented": "Semantic",
    "Unambiguous": "Semantic",

    # Pragmatic
    "Full sentence": "Pragmatic",
    "Estimable": "Pragmatic"
}

# --------------------------------------------------------
# Plotting functions (UNCHANGED)
# --------------------------------------------------------

def plot_grouped_bar(df, criterion_col, llm_col, metric_col, title, filename):
    pivot = df.pivot(index=criterion_col, columns=llm_col, values=metric_col)
    plt.figure(figsize=(10, 6))
    pivot.plot(kind="bar", ax=plt.gca(), rot=45)
    plt.ylabel(metric_col)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

def radar_chart(df, llm_name, llm_col, category_col, metric_col, title, filename):
    categories = df[category_col].unique()
    values = [
        df[(df[llm_col] == llm_name) & (df[category_col] == c)][metric_col].mean()
        for c in categories
    ]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
    values = np.append(values, values[0])
    angles = np.append(angles, angles[0])

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, marker='o', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories)
    ax.set_title(title, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

def plot_context_impact(df_min, df_rich, llm_col, metric_col, llm):
    min_avg = df_min[df_min[llm_col] == llm][metric_col].mean()
    rich_avg = df_rich[df_rich[llm_col] == llm][metric_col].mean()

    plt.figure(figsize=(5, 4))
    plt.plot(["Context-Minimal", "Context-Rich"], [min_avg, rich_avg], marker="o")
    plt.ylabel(metric_col)
    plt.title(f"Impact of Context Richness on {llm}")
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, f"fig_rq3_context_{llm}_{metric_col}.png"),
        dpi=300
    )
    plt.close()

def plot_heatmap(df, criterion_col, llm_col, metric_col):
    pivot = df.pivot(index=criterion_col, columns=llm_col, values=metric_col)
    plt.figure(figsize=(8, 6))
    im = plt.imshow(pivot, aspect="auto", cmap="viridis")
    plt.colorbar(im, label=metric_col)
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title(f"Heatmap of {metric_col} Across LLMs and Criteria")
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, f"fig_discussion_heatmap_{metric_col}.png"),
        dpi=300
    )
    plt.close()

def plot_box(df, llm_col, metric_col):
    plt.figure(figsize=(7, 4))
    df.boxplot(column=metric_col, by=llm_col)
    plt.title(f"Distribution of {metric_col} Across Quality Criteria")
    plt.suptitle("")
    plt.ylabel(metric_col)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, f"fig_validity_box_{metric_col}.png"),
        dpi=300
    )
    plt.close()

# --------------------------------------------------------
# Load model-wise triplets
# --------------------------------------------------------

def load_model_triplets(base_dir):
    df_min_list, df_rich_list, df_overall_list = [], [], []

    minimal_files = glob.glob(os.path.join(base_dir, "*_MINIMAL.xlsx"))

    for min_file in minimal_files:
        model = os.path.basename(min_file).replace("_MINIMAL.xlsx", "")
        rich_file = os.path.join(base_dir, f"{model}_RICH.xlsx")
        overall_file = os.path.join(base_dir, f"{model}_OVERALL.xlsx")

        if not (os.path.exists(rich_file) and os.path.exists(overall_file)):
            raise FileNotFoundError(f"Missing files for model: {model}")

        def load(file):
            xls = pd.ExcelFile(file)
            return pd.concat(
                [pd.read_excel(xls, sheet) for sheet in xls.sheet_names],
                ignore_index=True
            )

        df_min = load(min_file)
        df_rich = load(rich_file)
        df_overall = load(overall_file)

        df_min["LLM"] = model
        df_rich["LLM"] = model
        df_overall["LLM"] = model

        df_min_list.append(df_min)
        df_rich_list.append(df_rich)
        df_overall_list.append(df_overall)

    return (
        pd.concat(df_min_list, ignore_index=True),
        pd.concat(df_rich_list, ignore_index=True),
        pd.concat(df_overall_list, ignore_index=True)
    )

# --------------------------------------------------------
# Main execution
# --------------------------------------------------------

def main():
    df_min, df_rich, df_overall = load_model_triplets(BASE_DIR)
    print("✔ All model-wise Excel files loaded successfully")

    CRITERION_COL = find_column(df_min, ["Quality Criterion", "Criterion"])
    LLM_COL = "LLM"
    METRIC_COLS = [c for c in df_min.columns if c.lower() in ["f1", "accuracy", "f1_score"]]

    # Derive Category
    for df in [df_min, df_rich, df_overall]:
        non_overall = df[CRITERION_COL].str.lower() != "overall"
        df.loc[non_overall, "Category"] = df.loc[non_overall, CRITERION_COL].map(CRITERION_CATEGORY_MAP)

    CATEGORY_COL = "Category"

    for METRIC_COL in METRIC_COLS:
        plot_grouped_bar(
            df_min, CRITERION_COL, LLM_COL, METRIC_COL,
            f"LLM Performance per Quality Criterion (Context-Minimal) – {METRIC_COL}",
            f"fig_rq1_bar_minimal_{METRIC_COL}.png"
        )

        plot_grouped_bar(
            df_rich, CRITERION_COL, LLM_COL, METRIC_COL,
            f"LLM Performance per Quality Criterion (Context-Rich) – {METRIC_COL}",
            f"fig_rq1_bar_rich_{METRIC_COL}.png"
        )

        for llm in df_overall[LLM_COL].unique():
            radar_chart(
                df_overall[df_overall[CRITERION_COL].str.lower() != "overall"],
                llm, LLM_COL, CATEGORY_COL, METRIC_COL,
                f"Category-wise Evaluation Strength of {llm} – {METRIC_COL}",
                f"fig_rq2_radar_{llm}_{METRIC_COL}.png"
            )

        for llm in df_min[LLM_COL].unique():
            plot_context_impact(df_min, df_rich, LLM_COL, METRIC_COL, llm)

        plot_heatmap(df_overall, CRITERION_COL, LLM_COL, METRIC_COL)
        plot_box(df_overall, LLM_COL, METRIC_COL)

    print("✔ All figures generated successfully")

if __name__ == "__main__":
    main()
