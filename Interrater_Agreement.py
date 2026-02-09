import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa
import pingouin as pg
import krippendorff
import numpy as np

# ================= CONFIG =================
RATER_FILES = {
    "R1": "meta_eval_results_2.xlsx",
    "R2": "meta_eval_results_3.xlsx",
    "R3": "meta_eval_results_4.xlsx",
}

ID_COLS = ["story_id", "model", "context", "criterion"]
# =========================================


# ---------- DATA LOADING & PREPROCESSING ----------
def load_all_raters():
    dfs = []

    for rater, file in RATER_FILES.items():
        df = pd.read_excel(file)
        df = df[ID_COLS + ["repair_conforms", "reason_rating"]].copy()

        # Map Yes/No → 1/0
        df["repair_conforms"] = df["repair_conforms"].astype(str).str.strip().str.lower().map({"yes": 1, "no": 0})

        # Ensure numeric ratings
        df["reason_rating"] = pd.to_numeric(df["reason_rating"], errors="coerce")

        # Collapse 1–3 ratings into binary adequacy
        df["reason_binary"] = df["reason_rating"].apply(lambda x: 1 if x >= 2 else 0)

        df["rater"] = rater
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)
    df_all = df_all.dropna(subset=["repair_conforms", "reason_rating", "reason_binary"])
    return df_all


# ---------- AGREEMENT METRICS ----------
def fleiss_kappa_from_df(df, column):
    """
    Fleiss' kappa for a binary column (0/1) per group.
    Returns NaN if undefined (zero variance).
    """
    pivot = df.pivot_table(
        index=ID_COLS,
        columns="rater",
        values=column
    ).dropna()

    if pivot.empty:
        return np.nan

    counts = pivot.apply(lambda r: [(r == 0).sum(), (r == 1).sum()],
                         axis=1, result_type="expand")
    try:
        return fleiss_kappa(counts.values)
    except Exception:
        return np.nan


def icc_from_df(df):
    """
    ICC(2,1): two-way random, absolute agreement
    """
    melted = df.pivot_table(
        index=ID_COLS,
        columns="rater",
        values="reason_rating"
    ).dropna().reset_index().melt(id_vars=ID_COLS, var_name="rater", value_name="score")

    if melted.empty:
        return np.nan, np.nan

    icc = pg.intraclass_corr(data=melted, targets="story_id", raters="rater", ratings="score")
    icc_2_1 = icc.loc[icc["Type"] == "ICC2"]
    return icc_2_1["ICC"].values[0], icc_2_1["CI95%"].values[0]


def krippendorff_alpha_from_df(df):
    """
    Krippendorff's alpha (ordinal)
    """
    pivot = df.pivot_table(
        index=ID_COLS,
        columns="rater",
        values="reason_rating"
    ).dropna()

    if pivot.empty:
        return np.nan

    print("Data shape:", pivot.shape)

    try:
        return krippendorff.alpha(
            reliability_data=pivot.values.T,
            level_of_measurement="ordinal"
        )

    except Exception:
        return np.nan


# ---------- GENERIC AGREEMENT COMPUTATION ----------
def compute_agreement(df, group_by=None):
    """
    Compute agreement metrics.
    If group_by is None → overall agreement.
    """
    results = []

    if not group_by:
        groups = [("Overall", df)]
        group_by = ["Scope"]
    else:
        groups = df.groupby(group_by)

    for key, subset in groups:
        row = {}

        if group_by == ["Scope"]:
            row["Scope"] = "Overall"
        else:
            if isinstance(key, tuple):
                for col, val in zip(group_by, key):
                    row[col] = val
            else:
                row[group_by[0]] = key

        # Fleiss' Kappa
        row["Fleiss_RepairConforms"] = fleiss_kappa_from_df(subset, "repair_conforms")
        row["Fleiss_ReasonBinary"] = fleiss_kappa_from_df(subset, "reason_binary")

        # ICC and Krippendorff
        icc_val, icc_ci = icc_from_df(subset)
        row["ICC_2_1"] = icc_val
        row["ICC_95CI"] = icc_ci
        row["Krippendorff_Alpha"] = krippendorff_alpha_from_df(subset)

        results.append(row)

    return pd.DataFrame(results)


# ---------- MAIN PIPELINE ----------
def main():
    df = load_all_raters()

    per_criterion = compute_agreement(df, ["criterion"])
    per_model = compute_agreement(df, ["model"])
    overall = compute_agreement(df)

    with pd.ExcelWriter("Interrater_Agreement_BinaryReason.xlsx", engine="openpyxl") as writer:
        per_criterion.to_excel(writer, sheet_name="Per_Criterion", index=False)
        per_model.to_excel(writer, sheet_name="Per_Model", index=False)
        overall.to_excel(writer, sheet_name="Overall", index=False)

    print("✅ Interrater agreement (including binary reason rating) computed successfully.")
    print("📁 Output written to: Interrater_Agreement_BinaryReason.xlsx")


if __name__ == "__main__":
    main()

