import pandas as pd
import numpy as np

# ================= CONFIG =================
RATER_FILES = {
    "R1": "meta_eval_results_2.xlsx",
    "R2": "meta_eval_results_3.xlsx",
    "R3": "meta_eval_results_4.xlsx",
}

ID_COLS = ["story_id", "model", "context", "criterion"]
# =========================================


# ---------- LOAD & NORMALIZE ----------

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

        # Reason: ordinal → binary (≥2 adequate)
        df["reason_rating"] = pd.to_numeric(df["reason_rating"], errors="coerce")
        df["reason_binary"] = (df["reason_rating"] >= 2).astype(int)

        df["rater"] = rater
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    return df_all.dropna(
        subset=["repair_binary", "reason_binary"]
    )


# ---------- MAJORITY VOTING ----------

def majority_vote(df):
    # ---- Repair ----
    repair_pivot = (
        df.pivot_table(
            index=ID_COLS,
            columns="rater",
            values="repair_binary",
        )
        .dropna()
        .add_prefix("repair_")
    )

    # ---- Reason ----
    reason_pivot = (
        df.pivot_table(
            index=ID_COLS,
            columns="rater",
            values="reason_binary",
        )
        .dropna()
        .add_prefix("reason_")
    )

    # Align indices
    common_idx = repair_pivot.index.intersection(reason_pivot.index)
    repair_pivot = repair_pivot.loc[common_idx]
    reason_pivot = reason_pivot.loc[common_idx]

    # Majority rules (2 out of 3)
    repair_majority = (repair_pivot.sum(axis=1) >= 2).astype(int)
    reason_majority = (reason_pivot.sum(axis=1) >= 2).astype(int)

    # Combine all
    final = (
        pd.concat(
            [repair_pivot, reason_pivot],
            axis=1,
        )
        .reset_index()
    )

    final["repair_majority"] = repair_majority.values
    final["reason_majority"] = reason_majority.values

    return final


# ---------- PER-MODEL STATISTICS ----------

def per_model_statistics(df_all, majority_df):
    # Majority-based rates
    majority_stats = (
        majority_df
        .groupby("model")
        .agg(
            Repair_Conformance_Rate=("repair_majority", "mean"),
            Reason_Adequacy_Rate=("reason_majority", "mean"),
            Total_Items=("repair_majority", "count"),
        )
        .reset_index()
    )

    # Mean rater repair rate
    mean_repair = (
        df_all
        .groupby(["model", "rater"])["repair_binary"]
        .mean()
        .groupby("model")
        .mean()
        .reset_index(name="Mean_Rater_Repair_Rate")
    )

    # Mean rater reason adequacy
    mean_reason = (
        df_all
        .groupby(["model", "rater"])["reason_binary"]
        .mean()
        .groupby("model")
        .mean()
        .reset_index(name="Mean_Rater_Reason_Adequacy")
    )

    return (
        majority_stats
        .merge(mean_repair, on="model")
        .merge(mean_reason, on="model")
        .sort_values("Repair_Conformance_Rate", ascending=False)
    )


# ---------- MAIN ----------

def main():
    df_all = load_all_raters()

    majority_df = majority_vote(df_all)

    model_stats = per_model_statistics(df_all, majority_df)

    with pd.ExcelWriter(
        "Majority_Vote_Repair_and_Reason.xlsx",
        engine="openpyxl",
    ) as writer:
        majority_df.to_excel(
            writer,
            sheet_name="Item_Level_Majority",
            index=False,
        )
        model_stats.to_excel(
            writer,
            sheet_name="Per_Model_Statistics",
            index=False,
        )

    print("✅ Majority voting completed (repair + reason).")
    print("📁 Output written to: Majority_Vote_Repair_and_Reason.xlsx")


if __name__ == "__main__":
    main()

