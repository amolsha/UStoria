import pandas as pd

# ---------------- CONFIG ----------------
INPUT_EXCEL_FILE = "meta_eval_results_1.xlsx"
OUTPUT_EXCEL_FILE = "RSR_RAS_results.xlsx"
# ---------------------------------------


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize input data"""

    # Map Yes/No to 1/0
    df["repair_conforms"] = (
        df["repair_conforms"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
    )

    # Convert reason_rating to numeric
    df["reason_rating"] = pd.to_numeric(df["reason_rating"], errors="coerce")

    # Drop invalid rows explicitly
    df = df.dropna(subset=["repair_conforms", "reason_rating"])

    return df


def compute_base_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Base aggregates per (model, context, criterion)"""

    base = (
        df
        .groupby(["model", "context", "criterion"])
        .agg(
            N=("story_id", "count"),
            N_repaired_conforming=("repair_conforms", "sum"),
            sum_reason_rating=("reason_rating", "sum"),
        )
        .reset_index()
    )

    base["RSR"] = base["N_repaired_conforming"] / base["N"]
    base["RAS"] = base["sum_reason_rating"] / (3 * base["N"])

    return base


def aggregate_model_context(base: pd.DataFrame) -> pd.DataFrame:
    """Overall RSR/RAS per (model, context)"""

    mc = (
        base
        .groupby(["model", "context"])
        .agg(
            N=("N", "sum"),
            N_repaired_conforming=("N_repaired_conforming", "sum"),
            sum_reason_rating=("sum_reason_rating", "sum"),
        )
        .reset_index()
    )

    mc["RSR"] = mc["N_repaired_conforming"] / mc["N"]
    mc["RAS"] = mc["sum_reason_rating"] / (3 * mc["N"])

    return mc


def aggregate_model(base: pd.DataFrame) -> pd.DataFrame:
    """Overall RSR/RAS per model"""

    m = (
        base
        .groupby("model")
        .agg(
            N=("N", "sum"),
            N_repaired_conforming=("N_repaired_conforming", "sum"),
            sum_reason_rating=("sum_reason_rating", "sum"),
        )
        .reset_index()
    )

    m["RSR"] = m["N_repaired_conforming"] / m["N"]
    m["RAS"] = m["sum_reason_rating"] / (3 * m["N"])

    return m


def main():
    df = pd.read_excel(INPUT_EXCEL_FILE)

    required_columns = {
        "story_id",
        "model",
        "context",
        "criterion",
        "repair_conforms",
        "reason_rating",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = preprocess(df)

    base_results = compute_base_aggregates(df)
    model_context_results = aggregate_model_context(base_results)
    model_results = aggregate_model(base_results)

    # Write all results to Excel (separate sheets)
    with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine="openpyxl") as writer:
        base_results.to_excel(
            writer,
            sheet_name="Per_Model_Context_Criterion",
            index=False
        )
        model_context_results.to_excel(
            writer,
            sheet_name="Per_Model_Context",
            index=False
        )
        model_results.to_excel(
            writer,
            sheet_name="Per_Model_Overall",
            index=False
        )

    print("✅ RSR and RAS computed at all aggregation levels.")
    print(f"📁 Output written to: {OUTPUT_EXCEL_FILE}")


if __name__ == "__main__":
    main()


