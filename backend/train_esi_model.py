
from pathlib import Path

import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from xgboost import XGBClassifier


# ==================================================
# 1. PATH CONFIGURATION
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_DIR
    / "data"
    / "triagegeist"
    / "processed"
    / "cleaned"
)

ARTIFACT_DIR = PROJECT_DIR / "backend" / "artifacts"
REPORT_DIR = DATA_DIR / "reports"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = DATA_DIR / "train_cleaned.csv"
FEATURE_FILE = DATA_DIR / "baseline_features.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

print("\nLoading cleaned dataset...")

if not TRAIN_FILE.exists():
    raise FileNotFoundError(f"Training file not found: {TRAIN_FILE}")

if not FEATURE_FILE.exists():
    raise FileNotFoundError(f"Feature file not found: {FEATURE_FILE}")

train = pd.read_csv(TRAIN_FILE)

feature_table = pd.read_csv(FEATURE_FILE)

features = feature_table["feature"].tolist()
target = "triage_acuity"

print("Dataset shape:", train.shape)
print("Candidate feature count:", len(features))


# ==================================================
# 3. VALIDATE TARGET AND FEATURES
# ==================================================

if target not in train.columns:
    raise ValueError("Target column not found.")

missing_features = [
    col for col in features
    if col not in train.columns
]

if missing_features:
    raise ValueError(f"Missing features: {missing_features}")

if train[target].isna().any():
    raise ValueError("Missing ESI target labels detected.")

# Preserve original ESI labels
y_original = train[target].astype(int).copy()

# Validate original labels
expected_classes = {1, 2, 3, 4, 5}

if set(y_original.unique()) != expected_classes:
    raise ValueError(
        f"Expected ESI labels {expected_classes}, "
        f"but found {set(y_original.unique())}"
    )

# Select features
X = train[features].copy()

# XGBoost requires classes starting at zero
# ESI 1 -> 0
# ESI 2 -> 1
# ESI 3 -> 2
# ESI 4 -> 3
# ESI 5 -> 4

y = y_original - 1

print("\nOriginal ESI distribution:")
print(y_original.value_counts().sort_index())

print("\nEncoded target distribution:")
print(y.value_counts().sort_index())


# ==================================================
# 4. IDENTIFY FEATURE TYPES
# ==================================================

numeric_features = X.select_dtypes(
    include=["number", "bool"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()

print("\nNumeric features:", len(numeric_features))
print("Categorical features:", len(categorical_features))


# ==================================================
# 5. PREPROCESSING PIPELINES
# ==================================================

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

preprocessor = ColumnTransformer([
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
])


# ==================================================
# 6. TRAIN-VALIDATION SPLIT
# ==================================================

X_train, X_val, y_train, y_val = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Validation samples:", len(X_val))


# ==================================================
# 7. XGBOOST CLASSIFIER
# ==================================================

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

    eval_metric="mlogloss",
    tree_method="hist",

    random_state=42,
    n_jobs=-1
)


# ==================================================
# 8. COMPLETE ML PIPELINE
# ==================================================

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", model)
])


# ==================================================
# 9. MODEL TRAINING
# ==================================================

print("\n" + "=" * 55)
print("TRAINING FIVE-CLASS ESI MODEL")
print("=" * 55)

pipeline.fit(X_train, y_train)

print("\nModel training completed successfully.")


# ==================================================
# 10. VALIDATION PREDICTIONS
# ==================================================

print("\nGenerating validation predictions...")

predictions_encoded = pipeline.predict(X_val)

# Convert predictions from 0-4 back to ESI 1-5
predictions = predictions_encoded.astype(int) + 1

# Convert validation labels back to ESI 1-5
y_val_original = y_val.astype(int) + 1


# ==================================================
# 11. EVALUATION METRICS
# ==================================================

accuracy = accuracy_score(
    y_val_original,
    predictions
)

balanced_accuracy = balanced_accuracy_score(
    y_val_original,
    predictions
)

macro_f1 = f1_score(
    y_val_original,
    predictions,
    average="macro"
)

weighted_f1 = f1_score(
    y_val_original,
    predictions,
    average="weighted"
)


# ==================================================
# 12. CLASSIFICATION REPORT
# ==================================================

print("\n" + "=" * 55)
print("ESI MODEL VALIDATION RESULTS")
print("=" * 55)

print(f"Accuracy:          {accuracy:.4f}")
print(f"Balanced Accuracy: {balanced_accuracy:.4f}")
print(f"Macro F1:          {macro_f1:.4f}")
print(f"Weighted F1:       {weighted_f1:.4f}")

class_names = [
    "ESI 1",
    "ESI 2",
    "ESI 3",
    "ESI 4",
    "ESI 5"
]

report_text = classification_report(
    y_val_original,
    predictions,
    labels=[1, 2, 3, 4, 5],
    target_names=class_names,
    zero_division=0
)

print("\nCLASSIFICATION REPORT")
print(report_text)

report_dict = classification_report(
    y_val_original,
    predictions,
    labels=[1, 2, 3, 4, 5],
    target_names=class_names,
    output_dict=True,
    zero_division=0
)


# ==================================================
# 13. CONFUSION MATRIX
# ==================================================

cm = confusion_matrix(
    y_val_original,
    predictions,
    labels=[1, 2, 3, 4, 5]
)

cm_df = pd.DataFrame(
    cm,
    index=[f"Actual ESI {i}" for i in range(1, 6)],
    columns=[f"Predicted ESI {i}" for i in range(1, 6)]
)

print("\nCONFUSION MATRIX")
print(cm_df)


# ==================================================
# 14. SAVE MODEL
# ==================================================

model_path = ARTIFACT_DIR / "esi_xgboost_baseline.pkl"

joblib.dump(pipeline, model_path)

print("\nModel saved:", model_path)


# ==================================================
# 15. SAVE EVALUATION REPORTS
# ==================================================

metrics_df = pd.DataFrame([{
    "accuracy": accuracy,
    "balanced_accuracy": balanced_accuracy,
    "macro_f1": macro_f1,
    "weighted_f1": weighted_f1
}])

metrics_df.to_csv(
    REPORT_DIR / "model_metrics.csv",
    index=False
)

pd.DataFrame(report_dict).transpose().to_csv(
    REPORT_DIR / "classification_report.csv"
)

cm_df.to_csv(
    REPORT_DIR / "confusion_matrix.csv"
)

# Save predictions for later error analysis
prediction_df = pd.DataFrame({
    "actual_esi": y_val_original,
    "predicted_esi": predictions
})

prediction_df.to_csv(
    REPORT_DIR / "validation_predictions.csv",
    index=False
)


# ==================================================
# 16. FINAL SUMMARY
# ==================================================

print("\n" + "=" * 55)
print("BASELINE TRAINING COMPLETED")
print("=" * 55)

print("Training records:", len(X_train))
print("Validation records:", len(X_val))
print("Number of ESI classes:", 5)
print("Number of features:", len(features))

print("\nSaved artifacts:")
print("1.", model_path)

print("\nSaved reports:")
for file in REPORT_DIR.iterdir():
    if file.is_file():
        print("-", file.name)

print("\nOriginal ESI labels preserved: 1, 2, 3, 4, 5")
