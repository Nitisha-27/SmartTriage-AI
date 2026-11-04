import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/mimic-iv-ed-demo-2.2")

files = [
    "diagnosis.csv",
    "edstays.csv",
    "medrecon.csv",
    "pyxis.csv",
    "triage.csv",
    "vitalsign.csv"
]

for file in files:
    path = DATA_DIR / file

    df = pd.read_csv(path)

    print("\n" + "=" * 60)
    print(f"FILE: {file}")
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))