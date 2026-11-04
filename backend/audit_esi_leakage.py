
from pathlib import Path
import pandas as pd
import numpy as np

from scipy.stats import spearmanr


# ==================================================
# 1. PATHS
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_DIR
    / "data"
    / "triagegeist"
    / "processed"
    / "cleaned"
)

REPORT_DIR = DATA_DIR / "reports" / "leakage_audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "train_cleaned.csv"
FEATURE_FILE = DATA_DIR / "baseline_features.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

features = pd.read_csv(
    FEATURE_FILE
)["feature"].tolist()

target = "triage_acuity"

X = df[features].copy()
y = df[target].astype(int)

print("Dataset shape:", df.shape)
print("Candidate features:", len(features))


# ==================================================
# 3. KNOWN POST-OUTCOME / RISKY FEATURES
# ==================================================

post_outcome_keywords = [
    "disposition",
    "ed_los",
    "length_of_stay",
    "admission",
    "discharge",
    "outcome",
    "treatment",
    "intervention",
    "final_diagnosis",
    "final_acuity",
    "final_triage",
    "hospital_course"
]

identifier_keywords = [
    "patient_id",
    "encounter_id",
    "visit_id",
    "record_id",
    "nurse_id",
    "doctor_id",
    "clinician_id"
]

derived_feature_keywords = [
    "news2",
    "shock_index",
    "mean_arterial_pressure",
    "pulse_pressure"
]


# ==================================================
# 4. FEATURE-LEVEL AUDIT
# ==================================================

print("\nAuditing individual features...")

audit_rows = []

for col in features:

    series = X[col]

    unique_count = series.nunique(dropna=True)
    missing_count = series.isna().sum()
    missing_pct = missing_count / len(df) * 100

    col_lower = col.lower()

    if any(word in col_lower for word in post_outcome_keywords):
        risk = "HIGH - possible post-outcome information"

    elif any(word in col_lower for word in identifier_keywords):
        risk = "HIGH - possible identifier leakage"

    elif any(word in col_lower for word in derived_feature_keywords):
        risk = "REVIEW - derived clinical feature"

    elif unique_count > 1000 and series.dtype == "object":
        risk = "REVIEW - high-cardinality categorical feature"

    else:
        risk = "REVIEW - verify availability at initial triage"

    if pd.api.types.is_numeric_dtype(series):

        correlation = spearmanr(
            series,
            y,
            nan_policy="omit"
        ).statistic

    else:
        correlation = np.nan

    audit_rows.append({
        "feature": col,
        "data_type": str(series.dtype),
        "unique_values": unique_count,
        "missing_count": missing_count,
        "missing_percentage": round(missing_pct, 2),
        "spearman_correlation_with_esi": correlation,
        "initial_risk_flag": risk
    })


audit_df = pd.DataFrame(audit_rows)

audit_df.to_csv(
    REPORT_DIR / "feature_level_audit.csv",
    index=False
)


# ==================================================
# 5. CHECK KNOWN LEAKAGE CANDIDATES
# ==================================================

print("\nChecking known leakage candidates...")

all_columns = set(df.columns)

candidate_columns = [
    "disposition",
    "ed_los_hours",
    "news2_score",
    "shock_index",
    "mean_arterial_pressure",
    "pulse_pressure",
    "triage_nurse_id",
    "site_id",
    "triage_acuity"
]

candidate_report = []

for col in candidate_columns:

    candidate_report.append({
        "feature": col,
        "present_in_dataset": col in all_columns,
        "included_in_model": col in features
    })

candidate_df = pd.DataFrame(candidate_report)

print(candidate_df.to_string(index=False))

candidate_df.to_csv(
    REPORT_DIR / "known_leakage_candidates.csv",
    index=False
)


# ==================================================
# 6. NUMERIC FEATURE ASSOCIATION
# ==================================================

print("\nCalculating numeric feature associations...")

numeric_features = X.select_dtypes(
    include=["number", "bool"]
).columns.tolist()

numeric_rows = []

for col in numeric_features:

    values = X[col]

    valid = values.notna() & y.notna()

    if valid.sum() < 10 or values[valid].nunique() < 2:
        continue

    corr, p_value = spearmanr(
        values[valid],
        y[valid]
    )

    numeric_rows.append({
        "feature": col,
        "spearman_correlation": corr,
        "absolute_correlation": abs(corr),
        "p_value": p_value,
        "valid_records": int(valid.sum())
    })


numeric_df = pd.DataFrame(numeric_rows)

if not numeric_df.empty:

    numeric_df = numeric_df.sort_values(
        "absolute_correlation",
        ascending=False
    )

    print("\nTop numeric associations:")

    print(numeric_df.head(20).to_string(index=False))

numeric_df.to_csv(
    REPORT_DIR / "numeric_target_association.csv",
    index=False
)


# ==================================================
# 7. CATEGORICAL FEATURE ASSOCIATION
# ==================================================

print("\nInspecting categorical features...")

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()

categorical_rows = []

for col in categorical_features:

    temp = pd.DataFrame({
        "value": X[col].fillna("__MISSING__"),
        "esi": y
    })

    distribution = (
        temp.groupby("value")["esi"]
        .agg(["count", "nunique"])
        .reset_index()
    )

    distribution["feature"] = col

    distribution = distribution.sort_values(
        "count",
        ascending=False
    )

    # Save the most frequent categories for inspection
    for _, row in distribution.head(15).iterrows():

        category_data = temp[
            temp["value"] == row["value"]
        ]

        categorical_rows.append({
            "feature": col,
            "category": row["value"],
            "count": int(row["count"]),
            "esi_distribution": str(
                category_data["esi"]
                .value_counts(normalize=True)
                .sort_index()
                .round(3)
                .to_dict()
            )
        })


categorical_df = pd.DataFrame(categorical_rows)

categorical_df.to_csv(
    REPORT_DIR / "categorical_target_association.csv",
    index=False
)


# ==================================================
# 8. HIGH-CARDINALITY FEATURES
# ==================================================

print("\nChecking high-cardinality features...")

high_cardinality = audit_df[
    audit_df["unique_values"] > 100
].copy()

print(
    high_cardinality[
        ["feature", "unique_values", "initial_risk_flag"]
    ].to_string(index=False)
)

high_cardinality.to_csv(
    REPORT_DIR / "high_cardinality_features.csv",
    index=False
)


# ==================================================
# 9. CHECK TARGET-LIKE FEATURE NAMES
# ==================================================

print("\nChecking target-like feature names...")

target_keywords = [
    "esi",
    "acuity",
    "triage_level",
    "priority",
    "severity",
    "risk_class"
]

target_like_features = [
    col for col in features
    if any(word in col.lower() for word in target_keywords)
]

print("Target-like features:", target_like_features)

pd.DataFrame({
    "target_like_feature": target_like_features
}).to_csv(
    REPORT_DIR / "target_like_features.csv",
    index=False
)


# ==================================================
# 10. FINAL SUMMARY
# ==================================================

print("\n" + "=" * 60)
print("LEAKAGE AUDIT COMPLETED")
print("=" * 60)

print("Total candidate features:", len(features))
print("Numeric features:", len(numeric_features))
print("Categorical features:", len(categorical_features))
print("High-cardinality features:", len(high_cardinality))
print("Target-like feature names:", len(target_like_features))

print("\nReports saved in:")

print(REPORT_DIR)

print("\nGenerated reports:")

for file in REPORT_DIR.iterdir():

    if file.is_file():
        print("-", file.name)

print("\nNo model features or original datasets were modified.")
