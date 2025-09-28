import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
import plotly.graph_objects as go
from pathlib import Path
# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
DB_PATH = BASE_DIR / "data" / "evaluations.db"
print(DB_PATH)

OUTPUT_DIR = "figures_adv"  # folder for advanced figures


def load_data():
    conn = sqlite3.connect(DB_PATH)
    runs = pd.read_sql_query("SELECT * FROM runs", conn)
    evals = pd.read_sql_query("SELECT * FROM evaluations", conn)
    conn.close()
    return runs, evals


# -----------------------------
# FIGURE 5: Agreement heatmap
# -----------------------------
def figure5_agreement_heatmap(evals):
    pivot = evals.pivot_table(
        index="story_id",
        columns=["run_id", "criterion"],
        values="passed",
        aggfunc="first"
    )

    # collapse criterion dimension → story × run matrix
    run_pass = evals.groupby(["run_id", "story_id"])["passed"].mean().unstack(fill_value=0)

    # compute pairwise agreement
    runs = run_pass.index
    n = len(runs)
    agreement_matrix = pd.DataFrame(0.0, index=runs, columns=runs)

    for i in range(n):
        for j in range(n):
            same = (run_pass.iloc[i] == run_pass.iloc[j]).mean()
            agreement_matrix.iloc[i, j] = same

    plt.figure(figsize=(10, 8))
    sns.heatmap(agreement_matrix, annot=True, fmt=".2f", cmap="Blues")
    plt.title("Agreement Heatmap Between Runs")
    plt.savefig(f"{OUTPUT_DIR}/figure5_agreement_heatmap.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 6: Clustering of runs
# -----------------------------
def figure6_clustering(evals):
    run_pass = evals.groupby(["run_id", "story_id"])["passed"].mean().unstack(fill_value=0)

    # distance and clustering
    dist = pdist(run_pass, metric="euclidean")
    link = linkage(dist, method="ward")

    plt.figure(figsize=(10, 6))
    dendrogram(link, labels=run_pass.index.astype(str).tolist())
    plt.title("Cluster Dendrogram of Runs (based on evaluation similarity)")
    plt.ylabel("Distance")
    plt.savefig(f"{OUTPUT_DIR}/figure6_dendrogram.png", bbox_inches="tight")
    plt.close()


# -----------------------------
# FIGURE 8: Sankey diagram (Criterion → Reason → Repair)
# -----------------------------
def figure8_sankey(evals):
    df = evals.dropna(subset=["reason", "repair"])

    # limit to top 10 reasons/repairs for readability
    top_reasons = df["reason"].value_counts().head(10).index
    top_repairs = df["repair"].value_counts().head(10).index
    df = df[df["reason"].isin(top_reasons) & df["repair"].isin(top_repairs)]

    sources, targets, values = [], [], []
    label_list = []

    def add_label(lab):
        if lab not in label_list:
            label_list.append(lab)
        return label_list.index(lab)

    # criterion → reason
    for _, row in df.iterrows():
        s = add_label(row["criterion"])
        t = add_label(row["reason"])
        sources.append(s)
        targets.append(t)
        values.append(1)

    # reason → repair
    for _, row in df.iterrows():
        s = add_label(row["reason"])
        t = add_label(row["repair"])
        sources.append(s)
        targets.append(t)
        values.append(1)

    sankey = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                  label=label_list),
        link=dict(source=sources, target=targets, value=values)
    )])

    sankey.update_layout(title_text="Sankey Diagram: Criterion → Reason → Repair", font_size=10)
    sankey.write_html(f"{OUTPUT_DIR}/figure8_sankey.html")  # interactive
    print("Figure 8 saved as HTML (interactive):", f"{OUTPUT_DIR}/figure8_sankey.html")


# -----------------------------
# MAIN
# -----------------------------
def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    runs, evals = load_data()

    figure5_agreement_heatmap(evals)
    figure6_clustering(evals)
    figure8_sankey(evals)

    print("Advanced figures generated in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
