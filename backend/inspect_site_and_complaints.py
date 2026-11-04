from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/triagegeist/processed/cleaned")

df = pd.read_csv(DATA_DIR / "train_cleaned.csv")

print("\n========== SITE ANALYSIS ==========")

print("\nNumber of unique sites:", df["site_id"].nunique())

print("\nRecords per site:")
print(df["site_id"].value_counts().sort_index())

print("\nESI distribution by site:")
site_esi = pd.crosstab(
    df["site_id"],
    df["triage_acuity"],
    normalize="index"
).round(3)

print(site_esi)

print("\n========== CHIEF COMPLAINT ANALYSIS ==========")

complaints = (
    df.groupby("chief_complaint_raw")
    .agg(
        records=("triage_acuity", "size"),
        unique_esi=("triage_acuity", "nunique"),
        average_esi=("triage_acuity", "mean")
    )
    .sort_values("records", ascending=False)
)

print("\nTop 25 most frequent complaints:")
print(complaints.head(25))

print("\nRare complaints (5 or fewer records):")
print(complaints[complaints["records"] <= 5].shape[0])

print("\n========== ESI DISTRIBUTION ==========")
print(df["triage_acuity"].value_counts().sort_index())

print("\nAnalysis completed.")