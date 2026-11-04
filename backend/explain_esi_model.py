
from pathlib import Path

import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split


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

MODEL_PATH = (
    PROJECT_DIR
    / "backend"
    / "artifacts"
    / "esi_xgboost_baseline.pkl"
)

REPORT_DIR = DATA_DIR / "reports"
SHAP_DIR = REPORT_DIR / "shap"

SHAP_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD MODEL AND DATA
# ==================================================

print("\nLoading trained ESI model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

pipeline = joblib.load(MODEL_PATH)

preprocessor = pipeline.named_steps["preprocessor"]
classifier = pipeline.named_steps["classifier"]

train = pd.read_csv(DATA_DIR / "train_cleaned.csv")

features = pd.read_csv(
    DATA_DIR / "baseline_features.csv"
)["feature"].tolist()

X = train[features].copy()
y = train["triage_acuity"].astype(int) - 1

print("Dataset loaded:", X.shape)


# ==================================================
# 3. RECREATE VALIDATION SPLIT
# ==================================================

print("\nRecreating validation split...")

_, X_val, _, y_val = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Validation records:", len(X_val))


# ==================================================
# 4. SELECT SHAP SAMPLE
# ==================================================

SAMPLE_SIZE = 100

X_sample = X_val.sample(
    n=min(SAMPLE_SIZE, len(X_val)),
    random_state=42
)

print("SHAP sample size:", len(X_sample))


# ==================================================
# 5. TRANSFORM FEATURES
# ==================================================

print("\nTransforming validation sample...")

X_transformed = preprocessor.transform(X_sample)

feature_names = preprocessor.get_feature_names_out()

print("Transformed feature count:", len(feature_names))

MAX_FEATURES = 6000

if len(feature_names) > MAX_FEATURES:
    raise ValueError(
        f"Feature count {len(feature_names)} exceeds "
        f"safety limit {MAX_FEATURES}."
    )

if hasattr(X_transformed, "toarray"):
    X_transformed = X_transformed.toarray()

X_explain = pd.DataFrame(
    X_transformed,
    columns=feature_names,
    index=X_sample.index
)

print("SHAP input shape:", X_explain.shape)


# ==================================================
# 6. INITIALIZE SHAP EXPLAINER
# ==================================================

print("\nInitializing SHAP TreeExplainer...")

explainer = shap.TreeExplainer(classifier)

print("Calculating SHAP values...")

shap_values = explainer.shap_values(X_explain)

print("SHAP calculation completed.")


# ==================================================
# 7. NORMALIZE MULTICLASS SHAP OUTPUT
# ==================================================

if isinstance(shap_values, list):

    class_shap_values = shap_values

elif isinstance(shap_values, np.ndarray):

    if shap_values.ndim == 3:

        if shap_values.shape == (
            len(X_explain),
            len(feature_names),
            5
        ):
            class_shap_values = [
                shap_values[:, :, i]
                for i in range(5)
            ]

        elif shap_values.shape == (
            5,
            len(X_explain),
            len(feature_names)
        ):
            class_shap_values = [
                shap_values[i, :, :]
                for i in range(5)
            ]

        else:
            raise ValueError(
                f"Unexpected SHAP output shape: {shap_values.shape}"
            )

    else:
        raise ValueError(
            f"Unexpected SHAP dimensions: {shap_values.shape}"
        )

else:
    raise TypeError("Unsupported SHAP output format.")

if len(class_shap_values) != 5:
    raise ValueError(
        f"Expected 5 class explanations, "
        f"received {len(class_shap_values)}."
    )

print("Number of explained classes:", len(class_shap_values))


# ==================================================
# 8. GLOBAL SHAP IMPORTANCE
# ==================================================

print("\nCalculating global SHAP importance...")

all_class_values = np.stack(
    class_shap_values,
    axis=0
)

global_importance = np.mean(
    np.abs(all_class_values),
    axis=(0, 1)
)

importance_df = pd.DataFrame({
    "feature": feature_names,
    "mean_absolute_shap": global_importance
})

importance_df = importance_df.sort_values(
    by="mean_absolute_shap",
    ascending=False
).reset_index(drop=True)

importance_df.to_csv(
    SHAP_DIR / "global_shap_importance.csv",
    index=False
)

print("\nTOP 20 GLOBAL SHAP FEATURES")

print(
    importance_df.head(20).to_string(index=False)
)


# ==================================================
# 9. GLOBAL SHAP BAR PLOT
# ==================================================

print("\nGenerating global SHAP bar plot...")

top_global = importance_df.head(20).sort_values(
    "mean_absolute_shap",
    ascending=True
)

plt.figure(figsize=(12, 9))

plt.barh(
    top_global["feature"],
    top_global["mean_absolute_shap"]
)

plt.xlabel("Mean Absolute SHAP Value")
plt.ylabel("Feature")
plt.title("Global SHAP Feature Importance - ESI Model")

plt.tight_layout()

plt.savefig(
    SHAP_DIR / "global_shap_importance.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# 10. CLASS-WISE SHAP SUMMARY PLOTS
# ==================================================

print("\nGenerating class-wise SHAP plots...")

for class_index in range(5):

    esi_level = class_index + 1

    print(f"Generating SHAP plot for ESI {esi_level}...")

    plt.figure(figsize=(12, 9))

    shap.summary_plot(
        class_shap_values[class_index],
        X_explain,
        max_display=20,
        show=False
    )

    plt.title(
        f"SHAP Summary - ESI {esi_level}",
        pad=15
    )

    plt.tight_layout()

    plt.savefig(
        SHAP_DIR / f"shap_summary_esi_{esi_level}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ==================================================
# 11. CLASS-WISE SHAP IMPORTANCE
# ==================================================

print("\nSaving class-wise SHAP importance...")

class_importance = pd.DataFrame({
    "feature": feature_names
})

for class_index in range(5):

    class_importance[f"ESI_{class_index + 1}"] = np.mean(
        np.abs(class_shap_values[class_index]),
        axis=0
    )

class_importance.to_csv(
    SHAP_DIR / "classwise_shap_importance.csv",
    index=False
)


# ==================================================
# 12. SAVE EXPLANATION SUMMARY
# ==================================================

summary = pd.DataFrame({
    "ESI_class": [1, 2, 3, 4, 5],
    "explained_records": [len(X_explain)] * 5
})

summary.to_csv(
    SHAP_DIR / "shap_execution_summary.csv",
    index=False
)


# ==================================================
# 13. FINAL SUMMARY
# ==================================================

print("\n" + "=" * 55)
print("SHAP ANALYSIS COMPLETED")
print("=" * 55)

print("Explained validation records:", len(X_explain))
print("ESI classes explained:", len(class_shap_values))
print("Transformed features:", len(feature_names))

print("\nSaved files:")

for file in SHAP_DIR.iterdir():
    if file.is_file():
        print("-", file.name)

print("\nSHAP analysis completed successfully.")
