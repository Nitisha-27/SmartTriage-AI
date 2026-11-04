
from pathlib import Path
import re
import warnings

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, GroupShuffleSplit
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
REPORT_DIR = BASE_DIR / "reports" / "generalization"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = BASE_DIR / "train_cleaned.csv"
FEATURE_FILE = BASE_DIR / "baseline_features.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20

ESI_LABELS = [1, 2, 3, 4, 5]


# ============================================================
# 2. LOAD DATA AND FEATURE MANIFEST
# ============================================================

print("\n" + "=" * 70)
print("SMARTTRIAGE - MODEL GENERALIZATION COMPARISON")
print("=" * 70)

print("\nLoading cleaned dataset...")
df = pd.read_csv(DATA_FILE)

print("Loading feature manifest...")
feature_manifest = pd.read_csv(FEATURE_FILE)

if "feature" not in feature_manifest.columns:
    raise ValueError(
        "Feature manifest must contain a column named 'feature'."
    )

feature_columns = (
    feature_manifest["feature"]
    .dropna()
    .astype(str)
    .tolist()
)

if not feature_columns:
    raise ValueError("No feature names found in the feature manifest.")

if len(feature_columns) != len(set(feature_columns)):
    raise ValueError("Duplicate feature names found in the manifest.")

missing_columns = [
    col for col in feature_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Features missing from cleaned dataset: {missing_columns}"
    )

if "triage_acuity" not in df.columns:
    raise ValueError("Target column 'triage_acuity' not found.")

# Construct the actual feature matrix from the manifest.
X_all = df[feature_columns].copy()

# Preserve the original ESI labels (1 to 5).
y = pd.to_numeric(
    df["triage_acuity"],
    errors="raise"
).astype(int)

if y.isna().any():
    raise ValueError("Target contains missing values.")

if not set(y.unique()).issubset(set(ESI_LABELS)):
    raise ValueError(
        f"Unexpected ESI labels found: {sorted(y.unique())}"
    )

# Verify row alignment.
assert len(df) == len(X_all) == len(y)

print("\n========== DATASET INFORMATION ==========")
print("Dataset records:", len(df))
print("Selected features:", len(feature_columns))
print("Feature matrix shape:", X_all.shape)
print("Target shape:", y.shape)

print("\nESI distribution:")
print(y.value_counts().sort_index())

print("\nFeature names:")
print(feature_columns)


# ============================================================
# 3. NORMALIZE CHIEF COMPLAINTS FOR GROUPED VALIDATION
# ============================================================

if "chief_complaint_raw" not in df.columns:
    raise ValueError(
        "chief_complaint_raw is required for complaint-grouped validation."
    )


def normalize_complaint(value):
    """Normalize complaint text for exact-duplicate grouping."""

    if pd.isna(value):
        return "__missing_complaint__"

    value = str(value).lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value if value else "__missing_complaint__"


groups = df["chief_complaint_raw"].apply(normalize_complaint)

print("\nUnique normalized complaints:", groups.nunique())


# ============================================================
# 4. DEFINE FEATURE SETS
# ============================================================

# Experiment A and C use all original baseline features.
X_without_shortcuts = X_all.drop(
    columns=["site_id", "chief_complaint_raw"],
    errors="ignore"
)

experiments = [
    ("A_random_all_features", X_all, "random"),
    ("B_random_without_shortcuts", X_without_shortcuts, "random"),
    ("C_grouped_all_features", X_all, "grouped"),
    ("D_grouped_without_shortcuts", X_without_shortcuts, "grouped")
]


# ============================================================
# 5. BUILD PREPROCESSING AND MODEL PIPELINE
# ============================================================

def build_pipeline(X):
    """Build preprocessing and XGBoost classification pipeline."""

    numeric_features = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_features = X.select_dtypes(
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
# 6. RUN EXPERIMENTS
# ============================================================

results = []

for experiment_name, X, split_type in experiments:

    print("\n\n" + "=" * 70)
    print("EXPERIMENT:", experiment_name)
    print("=" * 70)

    # --------------------------------------------------------
    # Create train-validation split.
    # --------------------------------------------------------

    if split_type == "random":

        train_idx, val_idx = train_test_split(
            np.arange(len(X)),
            test_size=TEST_SIZE,
            stratify=y,
            random_state=RANDOM_STATE
        )

    elif split_type == "grouped":

        splitter = GroupShuffleSplit(
            n_splits=1,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE
        )

        train_idx, val_idx = next(
            splitter.split(X, y, groups=groups)
        )

    else:
        raise ValueError(f"Unknown split type: {split_type}")

    X_train = X.iloc[train_idx].copy()
    X_val = X.iloc[val_idx].copy()

    y_train = y.iloc[train_idx].copy()
    y_val = y.iloc[val_idx].copy()

    # --------------------------------------------------------
    # Check complaint overlap.
    # --------------------------------------------------------

    train_groups = set(groups.iloc[train_idx])
    val_groups = set(groups.iloc[val_idx])

    overlap = train_groups.intersection(val_groups)

    if split_type == "grouped" and overlap:
        raise ValueError(
            "Complaint overlap detected in grouped validation."
        )

    print("\nSplit information:")
    print("Training records:", len(train_idx))
    print("Validation records:", len(val_idx))
    print("Training features:", X.shape[1])
    print("Unique complaint overlap:", len(overlap))

    print("\nValidation ESI distribution:")
    print(
        y_val.value_counts(normalize=True)
        .sort_index()
        .round(3)
    )

    # --------------------------------------------------------
    # Encode ESI labels 1-5 into 0-4 for XGBoost.
    # --------------------------------------------------------

    y_train_encoded = y_train - 1

    # --------------------------------------------------------
    # Train model.
    # --------------------------------------------------------

    print("\nTraining XGBoost model...")

    pipeline = build_pipeline(X_train)

    pipeline.fit(
        X_train,
        y_train_encoded
    )

    # Convert predictions back from 0-4 to ESI 1-5.
    predictions_encoded = pipeline.predict(X_val)
    predictions = predictions_encoded.astype(int) + 1

    # --------------------------------------------------------
    # Evaluate model.
    # --------------------------------------------------------

    accuracy = accuracy_score(y_val, predictions)

    balanced_accuracy = balanced_accuracy_score(
        y_val,
        predictions
    )

    macro_f1 = f1_score(
        y_val,
        predictions,
        labels=ESI_LABELS,
        average="macro",
        zero_division=0
    )

    weighted_f1 = f1_score(
        y_val,
        predictions,
        labels=ESI_LABELS,
        average="weighted",
        zero_division=0
    )

    print("\n========== PERFORMANCE ==========")
    print("Accuracy:", round(accuracy, 4))
    print("Balanced accuracy:", round(balanced_accuracy, 4))
    print("Macro F1:", round(macro_f1, 4))
    print("Weighted F1:", round(weighted_f1, 4))

    # --------------------------------------------------------
    # Classification report.
    # --------------------------------------------------------

    report = classification_report(
        y_val,
        predictions,
        labels=ESI_LABELS,
        output_dict=True,
        zero_division=0
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_val,
            predictions,
            labels=ESI_LABELS,
            zero_division=0
        )
    )

    report_df = pd.DataFrame(report).T

    report_df.to_csv(
        REPORT_DIR / f"{experiment_name}_classification_report.csv"
    )

    # --------------------------------------------------------
    # Confusion matrix.
    # --------------------------------------------------------

    matrix = confusion_matrix(
        y_val,
        predictions,
        labels=ESI_LABELS
    )

    matrix_df = pd.DataFrame(
        matrix,
        index=[f"Actual_ESI_{i}" for i in ESI_LABELS],
        columns=[f"Predicted_ESI_{i}" for i in ESI_LABELS]
    )

    matrix_df.to_csv(
        REPORT_DIR / f"{experiment_name}_confusion_matrix.csv"
    )

    # --------------------------------------------------------
    # Save validation predictions.
    # --------------------------------------------------------

    predictions_df = pd.DataFrame({
        "original_index": val_idx,
        "actual_esi": y_val.to_numpy(),
        "predicted_esi": predictions
    })

    predictions_df.to_csv(
        REPORT_DIR / f"{experiment_name}_predictions.csv",
        index=False
    )

    # --------------------------------------------------------
    # Store experiment metrics.
    # --------------------------------------------------------

    results.append({
        "experiment": experiment_name,
        "split_type": split_type,
        "feature_count": X.shape[1],
        "training_records": len(train_idx),
        "validation_records": len(val_idx),
        "complaint_group_overlap": len(overlap),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1
    })


# ============================================================
# 7. FINAL COMPARISON
# ============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    REPORT_DIR / "comparison_metrics.csv",
    index=False
)

print("\n\n" + "=" * 70)
print("FINAL MODEL GENERALIZATION COMPARISON")
print("=" * 70)

print(
    results_df.round(4).to_string(index=False)
)

print("\n========== INTERPRETATION ==========")

random_macro = results_df.loc[
    results_df["experiment"] == "A_random_all_features",
    "macro_f1"
].iloc[0]

grouped_macro = results_df.loc[
    results_df["experiment"] == "C_grouped_all_features",
    "macro_f1"
].iloc[0]

print(
    "Random split macro F1:",
    round(random_macro, 4)
)

print(
    "Grouped split macro F1:",
    round(grouped_macro, 4)
)

print(
    "Macro F1 difference:",
    round(random_macro - grouped_macro, 4)
)

print("\nReports saved to:")
print(REPORT_DIR.resolve())

print("\nAll four experiments completed successfully.")
