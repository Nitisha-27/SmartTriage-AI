
import pandas as pd
from pathlib import Path
import sys

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

POSSIBLE_DATA_DIRS = [
    PROJECT_ROOT / "data" / "mimic-iv-ed-demo-2.2",
    PROJECT_ROOT / "data" / "mimic-iv-ed-demo-2.2" / "ed"
]

REQUIRED_FILES = [
    "triage.csv",
    "edstays.csv",
    "vitalsign.csv",
    "diagnosis.csv"
]

# --------------------------------------------------
# 2. LOCATE DATASET AUTOMATICALLY
# --------------------------------------------------

DATA_DIR = None

for folder in POSSIBLE_DATA_DIRS:
    if all((folder / file).exists() for file in REQUIRED_FILES):
        DATA_DIR = folder
        break

if DATA_DIR is None:
    print("ERROR: Dataset folder could not be located.")
    print("\nChecked these locations:")

    for folder in POSSIBLE_DATA_DIRS:
        print(folder)

    print("\nPlease verify your dataset folder structure.")
    sys.exit(1)

print("=" * 70)
print("MIMIC-IV-ED DEMO DATASET ANALYSIS")
print("=" * 70)
print(f"\nDataset location: {DATA_DIR}")

# --------------------------------------------------
# 3. LOAD AND ANALYSE EACH DATASET
# --------------------------------------------------

dataframes = {}

for filename in REQUIRED_FILES:

    path = DATA_DIR / filename

    try:
        df = pd.read_csv(path)
        dataframes[filename] = df

    except Exception as error:
        print(f"\nERROR loading {filename}: {error}")
        continue

    print("\n" + "=" * 70)
    print(f"FILE: {filename}")
    print("=" * 70)

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn names:")
    print(list(df.columns))

    # Missing-value analysis
    missing_report = pd.DataFrame({
        "Missing Count": df.isnull().sum(),
        "Missing Percentage": (
            df.isnull().mean() * 100
        ).round(2)
    })

    print("\nMissing Value Report:")
    print(missing_report.to_string())

    # Duplicate analysis
    print("\nExact duplicate rows:", df.duplicated().sum())

    if "stay_id" in df.columns:
        print("Unique ED stays:", df["stay_id"].nunique())

    # ESI distribution
    if "acuity" in df.columns:

        print("\nESI Acuity Distribution:")

        print(
            df["acuity"]
            .value_counts(dropna=False)
            .sort_index()
            .to_string()
        )

        print(
            "\nRecords with valid acuity:",
            df["acuity"].notna().sum()
        )

        print(
            "Records without acuity:",
            df["acuity"].isna().sum()
        )

    # Vital-sign summary
    vital_columns = [
        "temperature",
        "heartrate",
        "resprate",
        "o2sat",
        "sbp",
        "dbp",
        "pain"
    ]

    available_vitals = [
        col for col in vital_columns if col in df.columns
    ]

    if available_vitals:

        print("\nVital Sign Statistical Summary:")

        print(
            df[available_vitals]
            .describe()
            .round(2)
            .to_string()
        )

# --------------------------------------------------
# 4. TRIAGE DATASET SUMMARY
# --------------------------------------------------

triage = dataframes.get("triage.csv")

if triage is not None:

    print("\n" + "=" * 70)
    print("FINAL TRIAGE DATASET SUMMARY")
    print("=" * 70)

    print("Total triage records:", len(triage))

    if "stay_id" in triage.columns:
        print("Unique stays:", triage["stay_id"].nunique())

    if "acuity" in triage.columns:

        valid_labels = triage["acuity"].notna()

        print("Valid ESI labels:", valid_labels.sum())
        print("Missing ESI labels:", (~valid_labels).sum())

        print("\nFinal ESI Class Distribution:")

        print(
            triage.loc[valid_labels, "acuity"]
            .value_counts()
            .sort_index()
            .to_string()
        )

    print("\nMissing Triage Vital Values:")

    vital_columns = [
        "temperature",
        "heartrate",
        "resprate",
        "o2sat",
        "sbp",
        "dbp",
        "pain"
    ]

    for column in vital_columns:

        if column in triage.columns:

            missing = triage[column].isna().sum()

            percentage = (
                missing / len(triage) * 100
            )

            print(
                f"{column}: {missing} "
                f"({percentage:.2f}%)"
            )

# --------------------------------------------------
# 5. SAVE REPORT
# --------------------------------------------------

OUTPUT_DIR = PROJECT_ROOT / "data" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

report_path = OUTPUT_DIR / "dataset_analysis.txt"

print("\nAnalysis completed.")
print(f"Dataset folder: {DATA_DIR}")
print(f"Report folder: {OUTPUT_DIR}")

