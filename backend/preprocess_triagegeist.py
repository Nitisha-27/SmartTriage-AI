from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data" / "triagegeist"
OUTPUT_DIR = DATA_DIR / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = DATA_DIR / "train.csv"
TEST_FILE = DATA_DIR / "test.csv"
COMPLAINT_FILE = DATA_DIR / "chief_complaints.csv"
HISTORY_FILE = DATA_DIR / "patient_history.csv"
SUBMISSION_FILE = DATA_DIR / "sample_submission.csv"


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return pd.read_csv(path)


# --------------------------------------------------
# 2. Load datasets
# --------------------------------------------------

print("\nLoading datasets...")

train = load_csv(TRAIN_FILE)
test = load_csv(TEST_FILE)
complaints = load_csv(COMPLAINT_FILE)
history = load_csv(HISTORY_FILE)
submission = load_csv(SUBMISSION_FILE)

print("Training:", train.shape)
print("Testing:", test.shape)
print("Chief complaints:", complaints.shape)
print("Patient history:", history.shape)
print("Sample submission:", submission.shape)


# --------------------------------------------------
# 3. Check patient IDs
# --------------------------------------------------

print("\nChecking patient IDs...")

for name, df in {
    "train": train,
    "test": test,
    "complaints": complaints,
    "history": history,
    "submission": submission
}.items():

    print(
        f"{name}:",
        "rows =", len(df),
        "| unique IDs =", df["patient_id"].nunique(),
        "| missing IDs =", df["patient_id"].isna().sum(),
        "| duplicate IDs =", df["patient_id"].duplicated().sum()
    )

train_ids = set(train["patient_id"].dropna())
test_ids = set(test["patient_id"].dropna())

print("Train-test ID overlap:", len(train_ids.intersection(test_ids)))


# --------------------------------------------------
# 4. Check supplementary file coverage
# --------------------------------------------------

print("\nChecking supplementary file coverage...")

for name, df in {
    "complaints": complaints,
    "history": history
}.items():

    ids = set(df["patient_id"].dropna())

    print(
        f"{name}:",
        "missing train matches =", len(train_ids - ids),
        "| missing test matches =", len(test_ids - ids)
    )


# --------------------------------------------------
# 5. Check duplicate keys before joining
# --------------------------------------------------

if train["patient_id"].duplicated().any():
    raise ValueError("Duplicate patient IDs found in train.csv")

if test["patient_id"].duplicated().any():
    raise ValueError("Duplicate patient IDs found in test.csv")

if complaints["patient_id"].duplicated().any():
    raise ValueError("Duplicate patient IDs found in chief_complaints.csv")

if history["patient_id"].duplicated().any():
    raise ValueError("Duplicate patient IDs found in patient_history.csv")


# --------------------------------------------------
# 6. Merge supplementary data
# --------------------------------------------------

print("\nMerging training data...")

train_merged = train.merge(
    complaints[["patient_id", "chief_complaint_raw"]],
    on="patient_id",
    how="left",
    validate="one_to_one"
)

train_merged = train_merged.merge(
    history,
    on="patient_id",
    how="left",
    validate="one_to_one"
)

print("Merged training shape:", train_merged.shape)


print("\nMerging test data...")

test_merged = test.merge(
    complaints[["patient_id", "chief_complaint_raw"]],
    on="patient_id",
    how="left",
    validate="one_to_one"
)

test_merged = test_merged.merge(
    history,
    on="patient_id",
    how="left",
    validate="one_to_one"
)

print("Merged test shape:", test_merged.shape)


# --------------------------------------------------
# 7. ESI label distribution
# --------------------------------------------------

print("\nESI distribution:")

print(
    train_merged["triage_acuity"]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nESI percentages:")

print(
    train_merged["triage_acuity"]
    .value_counts(normalize=True)
    .sort_index()
    .mul(100)
    .round(2)
)


# --------------------------------------------------
# 8. Missing value analysis
# --------------------------------------------------

print("\nTop missing values in training data:")

missing = train_merged.isna().sum()

missing_report = pd.DataFrame({
    "missing_count": missing,
    "missing_percentage": (
        missing / len(train_merged) * 100
    ).round(2)
}).sort_values(
    "missing_percentage",
    ascending=False
)

print(missing_report.head(25))


# --------------------------------------------------
# 9. Suspicious value checks
# --------------------------------------------------

print("\nChecking suspicious values...")

checks = {
    "negative_systolic_bp": train_merged["systolic_bp"] <= 0,
    "negative_diastolic_bp": train_merged["diastolic_bp"] <= 0,
    "negative_pulse_pressure": train_merged["pulse_pressure"] < 0,
    "negative_heart_rate": train_merged["heart_rate"] <= 0,
    "invalid_spo2": (
        (train_merged["spo2"] < 0) |
        (train_merged["spo2"] > 100)
    ),
    "invalid_gcs": (
        (train_merged["gcs_total"] < 3) |
        (train_merged["gcs_total"] > 15)
    ),
    "pain_score_minus_one": train_merged["pain_score"] == -1,
    "invalid_temperature": (
        (train_merged["temperature_c"] < 25) |
        (train_merged["temperature_c"] > 45)
    )
}

anomaly_report = []

for name, condition in checks.items():

    count = int(condition.fillna(False).sum())

    anomaly_report.append({
        "check": name,
        "count": count
    })

    print(f"{name}: {count}")


anomaly_report = pd.DataFrame(anomaly_report)


# --------------------------------------------------
# 10. Check derived feature consistency
# --------------------------------------------------

print("\nChecking derived features...")

def compare_derived(name, actual, expected, tolerance=2.0):

    valid = actual.notna() & expected.notna()

    differences = (
        actual[valid] - expected[valid]
    ).abs()

    mismatches = int(
        (differences > tolerance).sum()
    )

    print(
        f"{name}:",
        "checked =", int(valid.sum()),
        "| mismatches =", mismatches
    )

    return mismatches


expected_pulse_pressure = (
    train_merged["systolic_bp"] -
    train_merged["diastolic_bp"]
)

expected_map = (
    train_merged["systolic_bp"] +
    2 * train_merged["diastolic_bp"]
) / 3

expected_shock_index = (
    train_merged["heart_rate"] /
    train_merged["systolic_bp"].replace(0, np.nan)
)

expected_bmi = (
    train_merged["weight_kg"] /
    (train_merged["height_cm"] / 100) ** 2
)

derived_report = {
    "pulse_pressure": compare_derived(
        "pulse_pressure",
        train_merged["pulse_pressure"],
        expected_pulse_pressure
    ),
    "mean_arterial_pressure": compare_derived(
        "mean_arterial_pressure",
        train_merged["mean_arterial_pressure"],
        expected_map
    ),
    "shock_index": compare_derived(
        "shock_index",
        train_merged["shock_index"],
        expected_shock_index,
        tolerance=0.05
    ),
    "bmi": compare_derived(
        "bmi",
        train_merged["bmi"],
        expected_bmi,
        tolerance=1.0
    )
}


# --------------------------------------------------
# 11. Save merged datasets
# --------------------------------------------------

train_output = OUTPUT_DIR / "train_merged.csv"
test_output = OUTPUT_DIR / "test_merged.csv"

train_merged.to_csv(train_output, index=False)
test_merged.to_csv(test_output, index=False)


# --------------------------------------------------
# 12. Save audit reports
# --------------------------------------------------

missing_report.to_csv(
    OUTPUT_DIR / "missing_values_report.csv"
)

anomaly_report.to_csv(
    OUTPUT_DIR / "anomaly_report.csv",
    index=False
)

pd.DataFrame(
    list(derived_report.items()),
    columns=["feature", "mismatch_count"]
).to_csv(
    OUTPUT_DIR / "derived_feature_report.csv",
    index=False
)


# --------------------------------------------------
# 13. Final summary
# --------------------------------------------------

print("\n" + "=" * 50)
print("DATA PREPARATION COMPLETED")
print("=" * 50)

print("Training records:", len(train_merged))
print("Testing records:", len(test_merged))
print("Training features:", train_merged.shape[1] - 1)
print("Target column: triage_acuity")

print("\nSaved files:")

for file in OUTPUT_DIR.iterdir():
    if file.is_file():
        print(file.name)

print("\nOriginal CSV files were not modified.")