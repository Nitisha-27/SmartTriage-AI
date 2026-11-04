
from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# 1. Load processed training dataset
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "triagegeist"
    / "processed"
    / "train_merged.csv"
)

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

df = pd.read_csv(DATA_FILE)

print("\nDataset shape:", df.shape)


# --------------------------------------------------
# 2. Investigate negative pulse pressure
# --------------------------------------------------

print("\n" + "=" * 60)
print("1. NEGATIVE PULSE PRESSURE RECORDS")
print("=" * 60)

negative_pp = df[df["pulse_pressure"] < 0]

print("Count:", len(negative_pp))

columns = [
    "patient_id",
    "triage_acuity",
    "systolic_bp",
    "diastolic_bp",
    "pulse_pressure",
    "heart_rate"
]

print(negative_pp[columns].head(20).to_string(index=False))


# --------------------------------------------------
# 3. Pain score distribution
# --------------------------------------------------

print("\n" + "=" * 60)
print("2. PAIN SCORE DISTRIBUTION")
print("=" * 60)

print(
    df["pain_score"]
    .value_counts(dropna=False)
    .sort_index()
)


# --------------------------------------------------
# 4. Investigate BMI mismatches
# --------------------------------------------------

print("\n" + "=" * 60)
print("3. BMI MISMATCH RECORDS")
print("=" * 60)

calculated_bmi = (
    df["weight_kg"] /
    (df["height_cm"] / 100) ** 2
)

bmi_difference = (
    df["bmi"] - calculated_bmi
).abs()

bmi_mismatch = df[bmi_difference > 1]

print("Mismatch count:", len(bmi_mismatch))

bmi_details = bmi_mismatch[
    [
        "patient_id",
        "height_cm",
        "weight_kg",
        "bmi"
    ]
].copy()

bmi_details["calculated_bmi"] = calculated_bmi.loc[
    bmi_mismatch.index
]

bmi_details["difference"] = bmi_difference.loc[
    bmi_mismatch.index
]

print(bmi_details.head(20).to_string(index=False))


# --------------------------------------------------
# 5. BMI difference summary
# --------------------------------------------------

print("\n" + "=" * 60)
print("4. BMI DIFFERENCE SUMMARY")
print("=" * 60)

print(bmi_difference.describe())


# --------------------------------------------------
# 6. Temperature distribution
# --------------------------------------------------

print("\n" + "=" * 60)
print("5. TEMPERATURE DISTRIBUTION")
print("=" * 60)

print(df["temperature_c"].describe())


# --------------------------------------------------
# 7. Check pain score -1 against ESI
# --------------------------------------------------

print("\n" + "=" * 60)
print("6. ESI VS UNKNOWN PAIN SCORE")
print("=" * 60)

pain_unknown = df["pain_score"] == -1

print(
    pd.crosstab(
        df["triage_acuity"],
        pain_unknown,
        normalize="index"
    ).round(3)
)


# --------------------------------------------------
# 8. Inspect important feature columns
# --------------------------------------------------

print("\n" + "=" * 60)
print("7. DATASET COLUMNS")
print("=" * 60)

for column in df.columns:
    print(column)


# --------------------------------------------------
# 9. Summary
# --------------------------------------------------

print("\n" + "=" * 60)
print("INVESTIGATION COMPLETED")
print("=" * 60)

print("Negative pulse pressure:", len(negative_pp))
print("Pain score -1:", int(pain_unknown.sum()))
print("BMI mismatches:", len(bmi_mismatch))

print("\nNo original dataset values were modified.")
