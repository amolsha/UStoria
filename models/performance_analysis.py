import sqlite3
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix
import pandas as pd

from models.storage import get_data_for_performance_analysis


def confusion_for_criterion(y_true, y_pred, criterion_name):
    print(y_true)
    print(y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=[1, 0])
    # cm = [[TP, FP], [FN, TN]] if we order labels=[1,0]
    TP, FP = cm[0, 0], cm[1, 0]
    FN, TN = cm[0, 1], cm[1, 1]

    print(f"Confusion Matrix for {criterion_name}:")
    print(f"TP: {TP}, FP: {FP}, FN: {FN}, TN: {TN}")
    return cm

def compute_metrics(run_id):
    print("Run: ",run_id)
    rows = get_data_for_performance_analysis(run_id)

    if not rows:
        print("No matching data found for this run.")
        return None

    df = pd.DataFrame(rows, columns=["criterion", "model_passed", "gold_passed"])

    metrics = {}
    # Calculate per-criterion metrics
    for criterion, group in df.groupby("criterion"):
        y_true = group["gold_passed"].astype(int)
        y_pred = group["model_passed"].astype(int)

        cm = confusion_for_criterion(y_true,y_pred,criterion)
        print(f"Confustion matrix for the criterion: {criterion} ")
        print(cm)

        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )
        acc = accuracy_score(y_true, y_pred)

        metrics[criterion] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "accuracy": round(acc, 3),
            "n_samples": len(group),
        }

    # Overall macro-averaged metrics
    y_true_all = df["gold_passed"].astype(int)
    y_pred_all = df["model_passed"].astype(int)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_all, y_pred_all, average="binary", zero_division=0
    )
    acc = accuracy_score(y_true_all, y_pred_all)

    metrics["overall"] = {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(acc, 3),
        "n_samples": len(df),
    }

    return metrics

if __name__ == "__main__":
    db_path = "../data/evaluations.db"
    run_id = 37

    results = compute_metrics(db_path, run_id)
    if results:
        for crit, vals in results.items():
            print(f"\nCriterion: {crit}")
            for k, v in vals.items():
                print(f"  {k}: {v}")