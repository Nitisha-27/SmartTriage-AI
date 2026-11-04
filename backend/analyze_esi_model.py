
from pathlib import Path

import joblib
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_DIR
    / "backend"
    / "artifacts"
    / "esi_xgboost_baseline.pkl"
)

DATA_DIR = (
    PROJECT_DIR
    / "data"
    / "triagegeist"
    / "processed"
    / "cleaned"
)

REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load trained pipeline
# --------------------------------------------------

print("\nLoading trained ESI model...")

pipeline = joblib.load(MODEL_PATH)

preprocessor = pipeline.named_steps["preprocessor"]
classifier = pipeline.named_steps["classifier"]


# --------------------------------------------------
# 3. Retrieve transformed feature names
# --------------------------------------------------

feature_names = preprocessor.get_feature_names_out()

importances = classifier.feature_importances_

if len(feature_names) != len(importances):
    raise ValueError("Feature names and importance count differ.")

importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
})

importance_df = importance_df.sort_values(
    by="importance",
    ascending=False
).reset_index(drop=True)


# --------------------------------------------------
# 4. Display top features
# --------------------------------------------------

print("\n" + "=" * 55)
print("TOP 25 FEATURE IMPORTANCES")
print("=" * 55)

print(
    importance_df.head(25).to_string(index=False)
)


# --------------------------------------------------
# 5. Save complete feature importance
# --------------------------------------------------

importance_path = REPORT_DIR / "feature_importance.csv"

importance_df.to_csv(
    importance_path,
    index=False
)


# --------------------------------------------------
# 6. Plot top 20 features
# --------------------------------------------------

top_features = importance_df.head(20).sort_values(
    "importance",
    ascending=True
)

plt.figure(figsize=(11, 8))

plt.barh(
    top_features["feature"],
    top_features["importance"]
)

plt.xlabel("XGBoost Feature Importance")
plt.ylabel("Feature")
plt.title("Top 20 Features - ESI Prediction Model")

plt.tight_layout()

plot_path = REPORT_DIR / "feature_importance.png"

plt.savefig(plot_path, dpi=300)
plt.show()


# --------------------------------------------------
# 7. Summary
# --------------------------------------------------

print("\nFeature importance analysis completed.")

print("Saved CSV:", importance_path)
print("Saved chart:", plot_path)
