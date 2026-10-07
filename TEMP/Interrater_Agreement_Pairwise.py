import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr, kendalltau

# ================= CONFIG =================
RATER_FILES = {
    "R1": "meta_eval_results_2.xlsx",
    "R2": "meta_eval_results_3.xlsx",
    "R3": "meta_eval_results_4.xlsx",
}

ID_COLS = ["story_id", "model", "context", "criterion"]
RATER_PAIRS = [("R1", "R2"), ("R1", "R3"), ("R2", "R3")]
# =========================================


# ---------- LOAD DATA ----------

def load_all_raters():
    dfs = []

    for rater, file in RATER_FILES.items():
        df = pd.read_excel(file)

        df = df[ID_COLS + ["repair_conforms", "reason_rating"]].copy()

        # Repair: Yes/No → 1/0
        df["repair_binary"] = (
            df["repair_conforms"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"yes": 1, "no": 0})
        )

        # Reason: ordinal → binary
        df["reason_rating"] = pd.to_numeric(df["reason_rating"], errors="coerce")
        df["reason_binary"] = (df["reason_rating"] >= 2).astype(int)

        df["rater"] = rater
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True).dropna(
        subset=["repair_binary", "reason_binary", "reason_rating"]
    )


# ---------- PAIRWISE AGREEMENT ----------

def pairwise_agreement(df):
    results = []

    for r1, r2 in RATER_PAIRS:
        d1 = df[df["rater"] == r1]
        d2 = df[df["rater"] == r2]

        merged = d1.merge(
            d2,
            on=ID_COLS,
            suffixes=(f"_{r1}", f"_{r2}"),
        )

        if merged.empty:
            continue

        # --- Repair conformance (binary) ---
        repair_kappa = cohen_kappa_score(
            merged[f"repair_binary_{r1}"],
            merged[f"repair_binary_{r2}"],
        )

        # --- Reason adequacy (binary) ---
        reason_kappa = cohen_kappa_score(
            merged[f"reason_binary_{r1}"],
            merged[f"reason_binary_{r2}"],
        )

        # --- Optional: ordinal correlations ---
        spearman_r, _ = spearmanr(
            merged[f"reason_rating_{r1}"],
            merged[f"reason_rating_{r2}"],
        )

        kendall_tau, _ = kendalltau(
            merged[f"reason_rating_{r1}"],
            merged[f"reason_rating_{r2}"],
        )

        results.append({
            "Rater_Pair": f"{r1}-{r2}",
            "Repair_Cohens_Kappa": repair_kappa,
            "Reason_Cohens_Kappa": reason_kappa,
            "Spearman_rho_Reason": spearman_r,
            "Kendall_tau_Reason": kendall_tau,
            "N_Items": len(merged),
        })

    return pd.DataFrame(results)


# ---------- MAIN ----------

def main():
    df_all = load_all_raters()

    pairwise_df = pairwise_agreement(df_all)

    pairwise_df.to_excel(
        "Pairwise_Interrater_Agreement.xlsx",
        index=False,
    )

    print("✅ Pairwise interrater agreement computed.")
    print("📁 Output written to: Pairwise_Interrater_Agreement.xlsx")


if __name__ == "__main__":
    main()
