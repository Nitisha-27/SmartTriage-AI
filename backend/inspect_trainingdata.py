
from ml_engine import generate_training_data, FEATURE_COLUMNS

data = generate_training_data()

print("\n========== TRAINING DATA DISTRIBUTION ==========")

for class_id, class_name in {
    0: "Routine",
    1: "Urgent",
    2: "Emergent"
}.items():

    subset = data[data["triage_class"] == class_id]

    print(f"\n{class_name}: {len(subset)} samples")

    print(
        subset[FEATURE_COLUMNS]
        .describe()
        .round(3)
    )

print("\n========== CASE 5 COMPARISON ==========")

case = {
    "news2_score": 12,
    "syndrome_similarity": 0.2745,
    "red_flag_count": 1,
    "age_risk": 0
}

for class_id, class_name in {
    0: "Routine",
    1: "Urgent",
    2: "Emergent"
}.items():

    subset = data[data["triage_class"] == class_id]

    print(f"\n{class_name}:")

    for feature, value in case.items():
        print(
            f"{feature}: Case 5 = {value}, "
            f"class mean = {subset[feature].mean():.3f}"
        )
