
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from xgboost import XGBClassifier


# ============================================================
# 1. CONFIGURATION
# ============================================================

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path("data/triagegeist/processed/cleaned")
REPORT_DIR = BASE_DIR / "reports" / "leave_one_site_out"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = BASE_DIR / "train_cleaned.csv"
FEATURE_FILE = BASE_DIR / "baseline_features.csv"

RANDOM_STATE = 42
ESI_LABELS = [1, 2, 3, 4, 5]

# Conservative feature exclusions.
EXCLUDED_FEATURES = [
    "site_id",
    "chief_complaint_raw"
]


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\n" + "=" * 70)
print("SMARTTRIAGE - LEAVE-ONE-SITE-OUT VALIDATION")
print("=" * 70)

print("\nLoading cleaned dataset...")
df = pd.read_csv(DATA_FILE)

print("Loading feature manifest...")
manifest = pd.read_csv(FEATURE_FILE)

if "feature" not in manifest.columns:
    raise ValueError("Feature manifest must contain 'feature' column.")

feature_columns = (
    manifest["feature"]
    .dropna()
    .astype(str)
    .tolist()
)

missing_columns = [
    col for col in feature_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing feature columns: {missing_columns}"
    )

if "site_id" not in df.columns:
    raise ValueError("site_id column not found.")

if "triage_acuity" not in df.columns:
    raise ValueError("triage_acuity target not found.")

# Exclude site identity and raw complaint text.
feature_columns = [
    col for col in feature_columns
    if col not in EXCLUDED_FEATURES
]

if not feature_columns:
    raise ValueError("No features available after exclusions.")

X = df[feature_columns].copy()

y = pd.to_numeric(
    df["triage_acuity"],
    errors="raise"
).astype(int)

sites = df["site_id"].astype(str)

if not set(y.unique()).issubset(set(ESI_LABELS)):
    raise ValueError(
        f"Unexpected ESI labels: {sorted(y.unique())}"
    )

if y.isna().any() or sites.isna().any():
    raise ValueError("Missing target or site values detected.")

assert len(X) == len(y) == len(sites)

site_names = sorted(sites.unique())

print("\n========== DATASET SUMMARY ==========")
print("Total records:", len(df))
print("Number of sites:", len(site_names))
print("Features used:", len(feature_columns))
print("Feature matrix shape:", X.shape)

print("\nExcluded features:", EXCLUDED_FEATURES)
print("\nFeatures used:")
print(feature_columns)

print("\nRecords per site:")
print(sites.value_counts())

print("\nOverall ESI distribution:")
print(y.value_counts().sort_index())


# ============================================================
# 3. BUILD MODEL PIPELINE
# ============================================================

def build_pipeline(X_train):

    numeric_features = X_train.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_features = X_train.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    numeric_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        )
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore")
        )
    ])

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_features
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        ],
        remainder="drop"
    )

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=5,
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_lambda=2,
        tree_method="hist",
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    return Pipeline([
        ("preprocessing", preprocessing),
        ("model", model)
    ])


# ============================================================
# 4. TRAIN AND TEST ON EACH HELD-OUT SITE
# ============================================================

site_results = []
all_predictions = []

for fold_number, held_out_site in enumerate(site_names, start=1):

    print("\n\n" + "=" * 70)
    print(f"FOLD {fold_number}/{len(site_names)}")
    print("HELD-OUT SITE:", held_out_site)
    print("=" * 70)

    # Test contains only the held-out hospital.
    test_mask = sites == held_out_site

    train_mask = ~test_mask

    X_train = X.loc[train_mask].copy()
    X_test = X.loc[test_mask].copy()

    y_train = y.loc[train_mask].copy()
    y_test = y.loc[test_mask].copy()

    print("\nTraining sites:")
    print(sorted(sites.loc[train_mask].unique()))

    print("\nTraining records:", len(X_train))
    print("Testing records:", len(X_test))

    # Verify that the held-out site is not in training.
    if held_out_site in sites.loc[train_mask].unique():
        raise ValueError("Held-out site found in training data.")

    print("\nTest ESI distribution:")
    print(y_test.value_counts().sort_index())

    # XGBoost expects class labels 0 to 4.
    y_train_encoded = y_train - 1

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print("\nTraining model...")

    pipeline = build_pipeline(X_train)

    pipeline.fit(
        X_train,
        y_train_encoded
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    predictions_encoded = pipeline.predict(X_test)

    # Convert predictions back to ESI 1 to 5.
    predictions = predictions_encoded.astype(int) + 1

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    balanced_accuracy = balanced_accuracy_score(
        y_test,
        predictions
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        labels=ESI_LABELS,
        average="macro",
        zero_division=0
    )

    weighted_f1 = f1_score(
        y_test,
        predictions,
        labels=ESI_LABELS,
        average="weighted",
        zero_division=0
    )

    print("\n========== SITE PERFORMANCE ==========")
    print("Site:", held_out_site)
    print("Accuracy:", round(accuracy, 4))
    print("Balanced accuracy:", round(balanced_accuracy, 4))
    print("Macro F1:", round(macro_f1, 4))
    print("Weighted F1:", round(weighted_f1, 4))

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    report = classification_report(
        y_test,
        predictions,
        labels=ESI_LABELS,
        output_dict=True,
        zero_division=0
    )

    report_df = pd.DataFrame(report).T

    report_df.to_csv(
        REPORT_DIR / f"{held_out_site}_classification_report.csv"
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=ESI_LABELS,
            zero_division=0
        )
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=ESI_LABELS
    )

    matrix_df = pd.DataFrame(
        matrix,
        index=[f"Actual_ESI_{i}" for i in ESI_LABELS],
        columns=[f"Predicted_ESI_{i}" for i in ESI_LABELS]
    )

    matrix_df.to_csv(
        REPORT_DIR / f"{held_out_site}_confusion_matrix.csv"
    )

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    prediction_df = pd.DataFrame({
        "original_index": X_test.index,
        "site_id": held_out_site,
        "actual_esi": y_test.to_numpy(),
        "predicted_esi": predictions
    })

    prediction_df.to_csv(
        REPORT_DIR / f"{held_out_site}_predictions.csv",
        index=False
    )

    all_predictions.append(prediction_df)

    # --------------------------------------------------------
    # Store metrics
    # --------------------------------------------------------

    site_results.append({
        "held_out_site": held_out_site,
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1
    })


# ============================================================
# 5. AGGREGATE RESULTS
# ============================================================

results_df = pd.DataFrame(site_results)

results_df.to_csv(
    REPORT_DIR / "site_level_metrics.csv",
    index=False
)

predictions_df = pd.concat(
    all_predictions,
    ignore_index=True
)

predictions_df.to_csv(
    REPORT_DIR / "all_site_predictions.csv",
    index=False
)

# Pooled evaluation across all held-out predictions.
overall_accuracy = accuracy_score(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"]
)

overall_balanced_accuracy = balanced_accuracy_score(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"]
)

overall_macro_f1 = f1_score(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"],
    labels=ESI_LABELS,
    average="macro",
    zero_division=0
)

overall_weighted_f1 = f1_score(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"],
    labels=ESI_LABELS,
    average="weighted",
    zero_division=0
)

overall_report = classification_report(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"],
    labels=ESI_LABELS,
    output_dict=True,
    zero_division=0
)

pd.DataFrame(overall_report).T.to_csv(
    REPORT_DIR / "overall_classification_report.csv"
)

overall_matrix = confusion_matrix(
    predictions_df["actual_esi"],
    predictions_df["predicted_esi"],
    labels=ESI_LABELS
)

pd.DataFrame(
    overall_matrix,
    index=[f"Actual_ESI_{i}" for i in ESI_LABELS],
    columns=[f"Predicted_ESI_{i}" for i in ESI_LABELS]
).to_csv(
    REPORT_DIR / "overall_confusion_matrix.csv"
)


# ============================================================
# 6. FINAL SUMMARY
# ============================================================

print("\n\n" + "=" * 70)
print("LEAVE-ONE-SITE-OUT VALIDATION RESULTS")
print("=" * 70)

print("\nSite-level results:")
print(
    results_df.round(4).to_string(index=False)
)

print("\n========== SITE METRIC SUMMARY ==========")

for metric in [
    "accuracy",
    "balanced_accuracy",
    "macro_f1",
    "weighted_f1"
]:
    print(
        f"{metric}: "
        f"mean={results_df[metric].mean():.4f}, "
        f"std={results_df[metric].std():.4f}, "
        f"min={results_df[metric].min():.4f}, "
        f"max={results_df[metric].max():.4f}"
    )

print("\n========== POOLED HELD-OUT PERFORMANCE ==========")
print("Accuracy:", round(overall_accuracy, 4))
print("Balanced accuracy:", round(overall_balanced_accuracy, 4))
print("Macro F1:", round(overall_macro_f1, 4))
print("Weighted F1:", round(overall_weighted_f1, 4))

print("\nPooled classification report:")
print(
    classification_report(
        predictions_df["actual_esi"],
        predictions_df["predicted_esi"],
        labels=ESI_LABELS,
        zero_division=0
    )
)

print("\nReports saved to:")
print(REPORT_DIR.resolve())

print("\nAll five site-held-out experiments completed.")
