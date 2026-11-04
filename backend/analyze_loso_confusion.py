
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    balanced_accuracy_score,
    f1_score
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path("data/triagegeist/processed/cleaned")
INPUT_DIR = BASE_DIR / "reports" / "leave_one_site_out"

OUTPUT_DIR = INPUT_DIR / "confusion_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PREDICTIONS_FILE = INPUT_DIR / "all_site_predictions.csv"

ESI_LABELS = [1, 2, 3, 4, 5]


# ============================================================
# 2. LOAD PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print("SMARTTRIAGE - LOSO CONFUSION MATRIX ANALYSIS")
print("=" * 70)

df = pd.read_csv(PREDICTIONS_FILE)

required_columns = {
    "site_id",
    "actual_esi",
    "predicted_esi"
}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

df["actual_esi"] = df["actual_esi"].astype(int)
df["predicted_esi"] = df["predicted_esi"].astype(int)

if not set(df["actual_esi"].unique()).issubset(ESI_LABELS):
    raise ValueError("Unexpected actual ESI labels.")

if not set(df["predicted_esi"].unique()).issubset(ESI_LABELS):
    raise ValueError("Unexpected predicted ESI labels.")

print("\nTotal predictions:", len(df))
print("Hospitals:", df["site_id"].nunique())


# ============================================================
# 3. OVERALL CONFUSION MATRIX
# ============================================================

actual = df["actual_esi"]
predicted = df["predicted_esi"]

cm = confusion_matrix(
    actual,
    predicted,
    labels=ESI_LABELS
)

cm_df = pd.DataFrame(
    cm,
    index=[f"Actual ESI {i}" for i in ESI_LABELS],
    columns=[f"Predicted ESI {i}" for i in ESI_LABELS]
)

cm_df.to_csv(OUTPUT_DIR / "overall_confusion_matrix.csv")

print("\n========== OVERALL CONFUSION MATRIX ==========")
print(cm_df)


# ============================================================
# 4. NORMALIZED CONFUSION MATRIX
# ============================================================

row_totals = cm.sum(axis=1, keepdims=True)

normalized_cm = np.divide(
    cm,
    row_totals,
    out=np.zeros_like(cm, dtype=float),
    where=row_totals != 0
)

normalized_df = pd.DataFrame(
    normalized_cm,
    index=[f"Actual ESI {i}" for i in ESI_LABELS],
    columns=[f"Predicted ESI {i}" for i in ESI_LABELS]
)

normalized_df.to_csv(
    OUTPUT_DIR / "normalized_confusion_matrix.csv"
)

print("\n========== NORMALIZED CONFUSION MATRIX ==========")
print(normalized_df.round(3))


# ============================================================
# 5. CONFUSION MATRIX VISUALIZATION
# ============================================================

fig, ax = plt.subplots(figsize=(9, 7))

image = ax.imshow(cm, interpolation="nearest", cmap="Blues")

ax.set_title(
    "LOSO Validation - Confusion Matrix",
    fontsize=14,
    pad=15
)

ax.set_xlabel("Predicted ESI", fontsize=11)
ax.set_ylabel("Actual ESI", fontsize=11)

ax.set_xticks(range(5))
ax.set_yticks(range(5))

ax.set_xticklabels(ESI_LABELS)
ax.set_yticklabels(ESI_LABELS)

threshold = cm.max() / 2

for i in range(5):
    for j in range(5):
        ax.text(
            j,
            i,
            f"{cm[i, j]:,}",
            ha="center",
            va="center",
            color="white" if cm[i, j] > threshold else "black"
        )

fig.colorbar(image, ax=ax, label="Number of records")

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "overall_confusion_matrix.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 6. NORMALIZED CONFUSION MATRIX VISUALIZATION
# ============================================================

fig, ax = plt.subplots(figsize=(9, 7))

image = ax.imshow(
    normalized_cm,
    interpolation="nearest",
    cmap="Blues",
    vmin=0,
    vmax=1
)

ax.set_title(
    "LOSO Validation - Normalized Confusion Matrix",
    fontsize=14,
    pad=15
)

ax.set_xlabel("Predicted ESI", fontsize=11)
ax.set_ylabel("Actual ESI", fontsize=11)

ax.set_xticks(range(5))
ax.set_yticks(range(5))

ax.set_xticklabels(ESI_LABELS)
ax.set_yticklabels(ESI_LABELS)

for i in range(5):
    for j in range(5):
        ax.text(
            j,
            i,
            f"{normalized_cm[i, j]:.1%}",
            ha="center",
            va="center",
            color="white" if normalized_cm[i, j] > 0.5 else "black"
        )

fig.colorbar(image, ax=ax, label="Proportion of actual class")

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "normalized_confusion_matrix.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 7. CLASS-WISE PERFORMANCE
# ============================================================

report = classification_report(
    actual,
    predicted,
    labels=ESI_LABELS,
    output_dict=True,
    zero_division=0
)

class_rows = []

for label in ESI_LABELS:
    metrics = report[str(label)]

    class_rows.append({
        "esi_class": label,
        "support": int(metrics["support"]),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1-score"],
        "correct_predictions": int(cm[label - 1, label - 1]),
        "incorrect_predictions": int(
            cm[label - 1].sum() - cm[label - 1, label - 1]
        )
    })

class_df = pd.DataFrame(class_rows)

class_df.to_csv(
    OUTPUT_DIR / "class_wise_performance.csv",
    index=False
)

print("\n========== CLASS-WISE PERFORMANCE ==========")
print(class_df.round(4).to_string(index=False))


# ============================================================
# 8. UNDER-TRIAGE AND OVER-TRIAGE ANALYSIS
# ============================================================

# ESI 1 = most urgent.
# A numerically higher prediction means a less urgent category.
#
# Under-triage: predicted ESI > actual ESI.
# Over-triage: predicted ESI < actual ESI.

df["prediction_difference"] = (
    df["predicted_esi"] - df["actual_esi"]
)

df["error_type"] = np.select(
    [
        df["prediction_difference"] == 0,
        df["prediction_difference"] > 0,
        df["prediction_difference"] < 0
    ],
    [
        "Correct",
        "Under-triage",
        "Over-triage"
    ],
    default="Unknown"
)

error_summary = (
    df["error_type"]
    .value_counts()
    .reindex(
        ["Correct", "Under-triage", "Over-triage"],
        fill_value=0
    )
    .rename_axis("error_type")
    .reset_index(name="records")
)

error_summary["percentage"] = (
    error_summary["records"] / len(df) * 100
)

error_summary.to_csv(
    OUTPUT_DIR / "triage_error_summary.csv",
    index=False
)

print("\n========== TRIAGE ERROR SUMMARY ==========")
print(error_summary.round(3).to_string(index=False))


# ============================================================
# 9. SEVERITY OF MISCLASSIFICATION
# ============================================================

df["absolute_esi_error"] = (
    df["predicted_esi"] - df["actual_esi"]
).abs()

severity_summary = (
    df.groupby("absolute_esi_error")
    .size()
    .reindex(range(5), fill_value=0)
    .rename("records")
    .reset_index()
)

severity_summary["percentage"] = (
    severity_summary["records"] / len(df) * 100
)

severity_summary.to_csv(
    OUTPUT_DIR / "misclassification_severity.csv",
    index=False
)

print("\n========== MISCLASSIFICATION DISTANCE ==========")
print(severity_summary.round(3).to_string(index=False))


# ============================================================
# 10. MOST FREQUENT MISCLASSIFICATION PAIRS
# ============================================================

misclassified = df[df["actual_esi"] != df["predicted_esi"]]

pairs = (
    misclassified.groupby(
        ["actual_esi", "predicted_esi"]
    )
    .size()
    .reset_index(name="records")
    .sort_values("records", ascending=False)
)

pairs["error_type"] = np.where(
    pairs["predicted_esi"] > pairs["actual_esi"],
    "Under-triage",
    "Over-triage"
)

pairs["percentage_of_all_predictions"] = (
    pairs["records"] / len(df) * 100
)

pairs.to_csv(
    OUTPUT_DIR / "misclassification_pairs.csv",
    index=False
)

print("\n========== TOP 15 MISCLASSIFICATION PAIRS ==========")
print(pairs.head(15).round(3).to_string(index=False))


# ============================================================
# 11. SITE-WISE ERROR ANALYSIS
# ============================================================

site_rows = []

for site, group in df.groupby("site_id"):

    site_accuracy = accuracy_score(
        group["actual_esi"],
        group["predicted_esi"]
    )

    site_macro_f1 = f1_score(
        group["actual_esi"],
        group["predicted_esi"],
        labels=ESI_LABELS,
        average="macro",
        zero_division=0
    )

    site_under = (
        group["predicted_esi"] > group["actual_esi"]
    ).sum()

    site_over = (
        group["predicted_esi"] < group["actual_esi"]
    ).sum()

    site_rows.append({
        "site_id": site,
        "records": len(group),
        "accuracy": site_accuracy,
        "macro_f1": site_macro_f1,
        "under_triage_records": int(site_under),
        "over_triage_records": int(site_over),
        "under_triage_percentage": site_under / len(group) * 100,
        "over_triage_percentage": site_over / len(group) * 100
    })

site_df = pd.DataFrame(site_rows)

site_df.to_csv(
    OUTPUT_DIR / "site_wise_error_analysis.csv",
    index=False
)

print("\n========== SITE-WISE ERROR ANALYSIS ==========")
print(site_df.round(4).to_string(index=False))


# ============================================================
# 12. OVERALL METRICS
# ============================================================

overall_metrics = pd.DataFrame([{
    "total_records": len(df),
    "accuracy": accuracy_score(actual, predicted),
    "balanced_accuracy": balanced_accuracy_score(actual, predicted),
    "macro_f1": f1_score(
        actual,
        predicted,
        labels=ESI_LABELS,
        average="macro",
        zero_division=0
    ),
    "weighted_f1": f1_score(
        actual,
        predicted,
        labels=ESI_LABELS,
        average="weighted",
        zero_division=0
    ),
    "under_triage_percentage": (
        df["error_type"].eq("Under-triage").mean() * 100
    ),
    "over_triage_percentage": (
        df["error_type"].eq("Over-triage").mean() * 100
    ),
    "exact_accuracy": (
        df["prediction_difference"].eq(0).mean() * 100
    )
}])

overall_metrics.to_csv(
    OUTPUT_DIR / "overall_metrics.csv",
    index=False
)

print("\n========== OVERALL METRICS ==========")
print(overall_metrics.round(4).to_string(index=False))


# ============================================================
# 13. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("CONFUSION MATRIX ANALYSIS COMPLETED")
print("=" * 70)

print("\nOutput directory:")
print(OUTPUT_DIR.resolve())

print("\nGenerated files:")
for file in sorted(OUTPUT_DIR.iterdir()):
    if file.is_file():
        print("-", file.name)

print("\nAnalysis completed successfully.")
