import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
from pathlib import Path
# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
DB_PATH = BASE_DIR / "data" / "evaluations.db"
print(DB_PATH)
OUTPUT_DIR = "figures"      # where charts will be saved

# Ensure seaborn style
sns.set(style="whitegrid", palette="muted", font_scale=1.1)


def load_data():
    conn = sqlite3.connect(DB_PATH)

    runs = pd.read_sql_query("SELECT * FROM runs", conn)
    evaluations = pd.read_sql_query("SELECT * FROM evaluations", conn)

    conn.close()
    return runs, evaluations


# -----------------------------
# FIGURE 1: Pass rate per QUS criterion across LLMs and prompt types
# -----------------------------
def figure1_passrate_bar(evals, runs):
    df = evals.merge(runs, left_on="run_id", right_on="id", suffixes=("_eval", "_run"))
    agg = df.groupby(["llm_name", "prompt_type", "criterion"])["passed"].mean().reset_index()

    plt.figure(figsize=(12, 6))
    sns.barplot(data=agg, x="criterion", y="passed", hue="llm_name")
    plt.title("Pass rate per QUS criterion across LLMs")
    plt.xticks(rotation=30)
    plt.ylabel("Pass rate")
    plt.savefig(f"{OUTPUT_DIR}/figure1_passrate_bar.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 2: Radar chart of QUS profile per LLM
# -----------------------------
def figure2_radar(evals, runs):
    import numpy as np

    df = evals.merge(runs, left_on="run_id", right_on="id", suffixes=("_eval", "_run"))
    agg = df.groupby(["llm_name", "criterion"])["passed"].mean().reset_index()

    criteria = evals["criterion"].unique().tolist()
    N = len(criteria)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()

    plt.figure(figsize=(8, 8), dpi=120)
    ax = plt.subplot(111, polar=True)

    for llm, subdf in agg.groupby("llm_name"):
        values = [subdf[subdf["criterion"] == c]["passed"].mean() for c in criteria]
        values += values[:1]  # close loop
        ax.plot(angles + [angles[0]], values, label=llm)
        ax.fill(angles + [angles[0]], values, alpha=0.25)

    ax.set_xticks(angles)
    ax.set_xticklabels(criteria, fontsize=10)
    plt.title("Radar Chart: QUS Profile per LLM")
    plt.legend(loc="upper right", bbox_to_anchor=(1.1, 1.1))
    plt.savefig(f"{OUTPUT_DIR}/figure2_radar.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 3: Average pass rate per criterion
# -----------------------------
def figure3_criterion_bar(evals):
    agg = evals.groupby("criterion")["passed"].mean().reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(data=agg, x="criterion", y="passed")
    plt.title("Average Pass Rate per QUS Criterion")
    plt.xticks(rotation=30)
    plt.ylabel("Pass rate")
    plt.savefig(f"{OUTPUT_DIR}/figure3_criterion_bar.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 4: Heatmap (stories × criteria)
# -----------------------------
def figure4_heatmap(evals):
    pivot = evals.pivot_table(index="story_id", columns="criterion", values="passed", aggfunc="mean")

    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot, cmap="YlGnBu", cbar=True)
    plt.title("Heatmap: Story × Criterion Pass Rates")
    plt.savefig(f"{OUTPUT_DIR}/figure4_heatmap.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 7: Word cloud for reasons
# -----------------------------
def figure7_wordcloud(evals):
    text = " ".join([str(r) for r in evals["reason"].dropna()])
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)

    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Word Cloud of Failure Reasons")
    plt.savefig(f"{OUTPUT_DIR}/figure7_wordcloud.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 9: QUS score distribution
# -----------------------------
def figure9_boxplot(evals, runs):
    df = evals.merge(runs, left_on="run_id", right_on="id", suffixes=("_eval", "_run"))
    score = df.groupby(["story_id", "llm_name", "prompt_type"])["passed"].sum().reset_index()
    score.rename(columns={"passed": "qus_score"}, inplace=True)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=score, x="llm_name", y="qus_score", hue="prompt_type")
    plt.title("Distribution of QUS Scores (0–8)")
    plt.ylabel("QUS Score")
    plt.savefig(f"{OUTPUT_DIR}/figure9_boxplot.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 10: Batch progression line chart
# -----------------------------
def figure10_batch_trend(evals, runs):
    df = evals.merge(runs, left_on="run_id", right_on="id", suffixes=("_eval", "_run"))
    agg = df.groupby("batch_id")["passed"].mean().reset_index()

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=agg, x="batch_id", y="passed", marker="o")
    plt.title("Batch Progression: Average QUS Score over Time")
    plt.ylabel("Average Pass Rate")
    plt.savefig(f"{OUTPUT_DIR}/figure10_batch_trend.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# MAIN
# -----------------------------
def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    runs, evals = load_data()

    # Call selected figures
    figure1_passrate_bar(evals, runs)
    figure2_radar(evals, runs)
    figure3_criterion_bar(evals)
    figure4_heatmap(evals)
    figure7_wordcloud(evals)
    figure9_boxplot(evals, runs)
    figure10_batch_trend(evals, runs)

    print("Figures generated in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
