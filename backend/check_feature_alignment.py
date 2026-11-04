from pathlib import Path
import pandas as pd

BASE = Path("data/triagegeist/processed/cleaned")

df = pd.read_csv(BASE / "train_cleaned.csv")
X = pd.read_csv(BASE / "baseline_features.csv")

print("\n========== FILE SHAPES ==========")
print("Cleaned dataset:", df.shape)
print("Baseline features:", X.shape)

print("\n========== INDEX CHECK ==========")
print("Cleaned index:", df.index[:5].tolist())
print("Feature index:", X.index[:5].tolist())

print("\n========== TARGET CHECK ==========")
print("Target column exists:", "triage_acuity" in df.columns)
print("Target records:", len(df["triage_acuity"]))
print("Target missing:", df["triage_acuity"].isna().sum())

print("\n========== PATIENT ID CHECK ==========")
if "patient_id" in df.columns:
    print("Cleaned unique IDs:", df["patient_id"].nunique())

print("\n========== FEATURE FILE ==========")
print("Feature columns:", len(X.columns))
print("Feature missing values:", X.isna().sum().sum())

print("\n========== RESULT ==========")
print("Row difference:", len(df) - len(X))