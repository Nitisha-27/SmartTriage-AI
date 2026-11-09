
import pandas as pd

from model_loader import triage_model
from ml_engine import FEATURE_COLUMNS, TRIAGE_CLASSES

print("\n========== MODEL DIAGNOSTICS ==========")

print("\n1. MODEL CLASSES")
print("Classes:", triage_model.classes_)
print("Class mapping:", TRIAGE_CLASSES)

print("\n2. FEATURE ORDER")
print("Expected:", FEATURE_COLUMNS)
print("Model features:", getattr(triage_model, "feature_names_in_", "Not stored"))

print("\n3. FEATURE IMPORTANCE")
for feature, importance in sorted(
    zip(FEATURE_COLUMNS, triage_model.feature_importances_),
    key=lambda item: item[1],
    reverse=True
):
    print(f"{feature}: {importance:.4f}")

print("\n4. CASE 5 PREDICTION")

case = {
    "news2_score": 12,
    "syndrome_similarity": 0.2745,
    "red_flag_count": 1,
    "age_risk": 0
}

def predict_case(values):
    X = pd.DataFrame([values], columns=FEATURE_COLUMNS)
    probabilities = triage_model.predict_proba(X)[0]

    return {
        TRIAGE_CLASSES[int(cls)]: round(float(prob), 4)
        for cls, prob in zip(triage_model.classes_, probabilities)
    }

print("Original:", predict_case(case))

print("\n5. FEATURE SENSITIVITY TEST")

tests = [
    ("Original", case),
    ("Higher NEWS-like score", {**case, "news2_score": 15}),
    ("Higher red-flag count", {**case, "red_flag_count": 4}),
    ("Higher syndrome similarity", {**case, "syndrome_similarity": 0.90}),
    ("Higher age risk", {**case, "age_risk": 1}),
]

for name, values in tests:
    print(f"\n{name}:")
    print(predict_case(values))
