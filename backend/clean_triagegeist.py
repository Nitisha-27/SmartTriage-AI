
from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_DIR / "data" / "triagegeist" / "processed"
OUTPUT_DIR = INPUT_DIR / "cleaned"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load datasets
# --------------------------------------------------

train = pd.read_csv(INPUT_DIR / "train_merged.csv")
test = pd.read_csv(INPUT_DIR / "test_merged.csv")

print("Original training shape:", train.shape)
print("Original testing shape:", test.shape)


# --------------------------------------------------
# 3. Cleaning function
# --------------------------------------------------

def clean_dataset(df, dataset_name):

    df = df.copy()

    # Track records affected by cleaning
    df["bp_inconsistent_flag"] = 0
    df["pain_unknown_flag"] = 0

    # ----------------------------------------------
    # A. Handle inconsistent blood pressure
    # ----------------------------------------------

    bp_columns = [
        "systolic_bp",
        "diastolic_bp",
        "mean_arterial_pressure",
        "pulse_pressure",
        "shock_index"
    ]

    if all(col in df.columns for col in bp_columns):

        invalid_bp = (
            df["systolic_bp"].notna()
            & df["diastolic_bp"].notna()
            & (df["diastolic_bp"] >= df["systolic_bp"])
        )

        df.loc[invalid_bp, "bp_inconsistent_flag"] = 1

        print(
            f"{dataset_name} - Inconsistent BP records:",
            int(invalid_bp.sum())
        )

        # Preserve patient records but mark the
        # inconsistent BP measurements as missing.
        df.loc[invalid_bp, bp_columns] = np.nan

    # ----------------------------------------------
    # B. Handle unknown pain score
    # ----------------------------------------------

    if "pain_score" in df.columns:

        pain_unknown = df["pain_score"] == -1

        df.loc[pain_unknown, "pain_unknown_flag"] = 1
        df.loc[pain_unknown, "pain_score"] = np.nan

        print(
            f"{dataset_name} - Unknown pain scores:",
            int(pain_unknown.sum())
        )

    # ----------------------------------------------
    # C. Keep questionable anthropometric fields
    #    unchanged for now.
    #    They will be excluded from baseline features.
    # ----------------------------------------------

    # Do not overwrite original BMI, height or weight.
    # Their reliability needs further investigation.

    return df


# --------------------------------------------------
# 4. Clean train and test
# --------------------------------------------------

print("\nCleaning training data...")

train_clean = clean_dataset(train, "TRAIN")

print("\nCleaning testing data...")

test_clean = clean_dataset(test, "TEST")


# --------------------------------------------------
# 5. Save cleaned datasets
# --------------------------------------------------

train_path = OUTPUT_DIR / "train_cleaned.csv"
test_path = OUTPUT_DIR / "test_cleaned.csv"

train_clean.to_csv(train_path, index=False)
test_clean.to_csv(test_path, index=False)


# --------------------------------------------------
# 6. Create baseline feature exclusion list
# --------------------------------------------------

excluded_features = [
    "patient_id",
    "triage_nurse_id",
    "triage_acuity",
    "disposition",
    "ed_los_hours",
    "height_cm",
    "weight_kg",
    "bmi",
    "news2_score",
    "mean_arterial_pressure",
    "pulse_pressure",
    "shock_index",
    "age_group",
    "arrival_season",
    "shift"
]

# The exclusion list is a starting baseline policy.
# Derived features and proxies can be evaluated later.

feature_list = [
    col for col in train_clean.columns
    if col not in excluded_features
    and col not in [
        "bp_inconsistent_flag",
        "pain_unknown_flag"
    ]
]

feature_list = [
    col for col in feature_list
    if col in test_clean.columns
]

pd.DataFrame({
    "feature": feature_list
}).to_csv(
    OUTPUT_DIR / "baseline_features.csv",
    index=False
)


# --------------------------------------------------
# 7. Save cleaning summary
# --------------------------------------------------

summary = pd.DataFrame([
    {
        "dataset": "train",
        "records": len(train_clean),
        "inconsistent_bp": int(
            train_clean["bp_inconsistent_flag"].sum()
        ),
        "unknown_pain": int(
            train_clean["pain_unknown_flag"].sum()
        )
    },
    {
        "dataset": "test",
        "records": len(test_clean),
        "inconsistent_bp": int(
            test_clean["bp_inconsistent_flag"].sum()
        ),
        "unknown_pain": int(
            test_clean["pain_unknown_flag"].sum()
        )
    }
])

summary.to_csv(
    OUTPUT_DIR / "cleaning_summary.csv",
    index=False
)


# --------------------------------------------------
# 8. Final report
# --------------------------------------------------

print("\n" + "=" * 55)
print("CLEANING COMPLETED")
print("=" * 55)

print("Training records:", len(train_clean))
print("Testing records:", len(test_clean))
print("Baseline feature count:", len(feature_list))

print("\nSaved files:")

for file in OUTPUT_DIR.iterdir():
    print(file.name)

print("\nOriginal merged datasets remain unchanged.")
