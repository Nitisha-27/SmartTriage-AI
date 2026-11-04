from pathlib import Path
import re
import pandas as pd

DATA_DIR = Path("data/triagegeist/processed/cleaned")
REPORT_DIR = DATA_DIR / "reports" / "leakage_audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "train_cleaned.csv")

# Normalize text to detect minor punctuation and spacing variations.
def normalize(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text)

df["normalized_complaint"] = df["chief_complaint_raw"].apply(normalize)

# Examine how consistently each complaint maps to an ESI label.
summary = (
    df.groupby("normalized_complaint")
    .agg(
        records=("triage_acuity", "size"),
        unique_esi=("triage_acuity", "nunique"),
        dominant_esi=("triage_acuity", lambda x: x.mode().iloc[0]),
        dominant_label_count=("triage_acuity", lambda x: x.value_counts().max())
    )
    .reset_index()
)

summary["label_purity"] = (
    summary["dominant_label_count"] / summary["records"]
)

# Overall repetition and label consistency.
repeated = summary[summary["records"] >= 2]
frequent = summary[summary["records"] >= 10]

print("\n========== COMPLAINT REPETITION ==========")
print("Total unique normalized complaints:", len(summary))
print("Complaints repeated at least twice:", len(repeated))
print("Complaints repeated at least 10 times:", len(frequent))

print("\n========== LABEL CONSISTENCY ==========")
print(
    "Repeated complaints with only one ESI label:",
    (repeated["unique_esi"] == 1).sum()
)
print(
    "Percentage of repeated complaints with one ESI label:",
    round((repeated["unique_esi"] == 1).mean() * 100, 2)
    if len(repeated) else 0
)

print("\n========== FREQUENT COMPLAINTS ==========")
print(
    frequent.sort_values("records", ascending=False)
    .head(30)
    .to_string(index=False)
)

print("\n========== HIGHLY INCONSISTENT COMPLAINTS ==========")
print(
    summary[summary["records"] >= 5]
    .sort_values("label_purity")
    .head(20)
    .to_string(index=False)
)

summary.to_csv(
    REPORT_DIR / "complaint_repetition_summary.csv",
    index=False
)

print("\nReport saved:", REPORT_DIR / "complaint_repetition_summary.csv")