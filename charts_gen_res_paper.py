"""
=========================================================
LLM Performance Visualization Script (Updated)
For Research Paper: User Story Quality Evaluation
=========================================================

Updates:
- Supports multiple metrics dynamically (e.g., 'F1', 'Accuracy')
- Avoids label/legend overlaps
- Improved figure aesthetics for publication-quality plots
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

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

OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_DIR = "LLM_EVALUATION"

FILE_MINIMAL = os.path.join(BASE_DIR, "llm_performance_MINIMAL.xlsx")
FILE_RICH = os.path.join(BASE_DIR, "llm_performance_RICH.xlsx")
FILE_OVERALL = os.path.join(BASE_DIR, "llm_performance_ALL_OVERALL.xlsx")
FILE_COMBINED = os.path.join(BASE_DIR, "llm_performance_OVERALL_RICH+MINIMAL.xlsx")

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
# Plotting functions
# --------------------------------------------------------

def plot_grouped_bar(df, criterion_col, llm_col, metric_col, title, filename):
    pivot = df.pivot(index=criterion_col, columns=llm_col, values=metric_col)

    plt.figure(figsize=(10, 6))
    pivot.plot(kind="bar", ax=plt.gca(), rot=45)
    plt.ylabel(metric_col)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.legend(loc="upper left", bbox_to_anchor=(1,1))
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
    values = np.concatenate([values, [values[0]]])
    angles = np.concatenate([angles, [angles[0]]])

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


# Load all sheets and combine into a single DataFrame
def load_all_sheets(file_path):
    xls = pd.ExcelFile(file_path)
    df_list = [pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names]
    return pd.concat(df_list, ignore_index=True)


# --------------------------------------------------------
# Main execution
# --------------------------------------------------------

def main():
    # Load data
    df_min = load_all_sheets(FILE_MINIMAL)
    df_rich = load_all_sheets(FILE_RICH)
    df_overall = load_all_sheets(FILE_OVERALL)
    df_combined = load_all_sheets(FILE_COMBINED)

    print("✔ All Excel files loaded successfully")

    # Detect columns
    CRITERION_COL = find_column(
        df_min, ["Quality Criterion", "Criterion", "quality_criterion", "criterion"]
    )
    LLM_COL = find_column(
        df_min, ["LLM", "Model", "LLM Name", "llm"]
    )
    # Detect all metrics present
    METRIC_COLS = [c for c in df_min.columns if c.lower() in ["f1", "accuracy", "f1_score"]]

    # ----------------------------------------------------
    # Derive Category column (exclude 'Overall')
    # ----------------------------------------------------

    for df in [df_min, df_rich, df_combined]:
        non_overall = df[CRITERION_COL].str.lower() != "overall"
        df.loc[non_overall, "Category"] = df.loc[non_overall, CRITERION_COL].map(CRITERION_CATEGORY_MAP)
        if df.loc[non_overall, "Category"].isnull().any():
            missing = df.loc[non_overall].loc[df["Category"].isnull(), CRITERION_COL].unique()
            raise ValueError(f"Unmapped criteria found: {missing}")

    CATEGORY_COL = "Category"

    # Generate plots for all metrics
    for METRIC_COL in METRIC_COLS:
        # RQ1 – Grouped bar charts
        plot_grouped_bar(
            df_min, CRITERION_COL, LLM_COL, METRIC_COL,
            f"LLM Performance per Quality Criterion (Context-Minimal) - {METRIC_COL}",
            f"fig_rq1_bar_minimal_{METRIC_COL}.png"
        )
        plot_grouped_bar(
            df_rich, CRITERION_COL, LLM_COL, METRIC_COL,
            f"LLM Performance per Quality Criterion (Context-Rich) - {METRIC_COL}",
            f"fig_rq1_bar_rich_{METRIC_COL}.png"
        )

        # RQ2 – Radar charts
        for llm in df_combined[LLM_COL].unique():
            radar_chart(
                df_combined[df_combined[CRITERION_COL].str.lower() != "overall"],
                llm, LLM_COL, CATEGORY_COL, METRIC_COL,
                f"Category-wise Evaluation Strength of {llm} - {METRIC_COL}",
                f"fig_rq2_radar_{llm}_{METRIC_COL}.png"
            )

        # RQ3 – Context impact
        for llm in df_min[LLM_COL].unique():
            plot_context_impact(df_min, df_rich, LLM_COL, METRIC_COL, llm)

        # Discussion – Heatmaps
        plot_heatmap(df_combined, CRITERION_COL, LLM_COL, METRIC_COL)

        # Threats to Validity – Box plots
        plot_box(df_combined, LLM_COL, METRIC_COL)

    print("✔ All figures generated successfully in the 'figures/' directory")


if __name__ == "__main__":
    main()
