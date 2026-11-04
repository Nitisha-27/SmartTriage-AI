
from nlp_engine import (
    extract_clinical_entities,
    detect_missing_fields
)

test_cases = [
    "Patient has severe chest pain.",
    "Patient denies chest pain.",
    "No facial droop observed.",
    "Patient has crushing chest pain radiating to left arm.",
    "Patient denies breathlessness.",
    "Patient denies chest pain but later develops chest pain.",
    "No crushing chest pain reported.",
    "Patient has facial droop and arm weakness.",
    "Patient denies fever but reports severe headache.",
    "Patient has no history of diabetes."
]


for case in test_cases:

    entities, flags = extract_clinical_entities(case)

    print("\nNarrative:", case)
    print("Entities:", entities)
    print("Red flags:", flags)


print("\n--- MISSING FIELD TEST ---")

narrative = "Patient reports fever and weakness."

print(detect_missing_fields(narrative))
