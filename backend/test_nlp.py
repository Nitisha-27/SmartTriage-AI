
from nlp_engine import (
    extract_clinical_entities,
    detect_missing_fields,
    compute_syndrome_match,
    calculate_news2,
    build_soap
)


narrative = """
Patient reports severe crushing chest pain radiating to left arm
for 2 hours. Pain score is 8/10.
Patient has a previous medical history of hypertension.
No known allergies. Current medications include aspirin.
Symptoms started suddenly.
"""

vitals = {
    "heart_rate": 125,
    "resp_rate": 28,
    "systolic_bp": 85,
    "spo2": 89,
    "temperature": 39.5
}


print("\n--- ENTITY EXTRACTION ---")
entities, red_flags = extract_clinical_entities(narrative)
print("Entities:", entities)
print("Red Flags:", red_flags)


print("\n--- MISSING FIELDS ---")
missing = detect_missing_fields(narrative)
print("Missing:", missing)


print("\n--- SYNDROME MATCHING ---")
syndrome, similarity = compute_syndrome_match(narrative)
print("Syndrome:", syndrome)
print("Similarity:", similarity)


print("\n--- FIVE-PARAMETER SCORE ---")
score = calculate_news2(
    hr=vitals["heart_rate"],
    rr=vitals["resp_rate"],
    sbp=vitals["systolic_bp"],
    spo2=vitals["spo2"],
    temp=vitals["temperature"]
)
print("Score:", score)


print("\n--- SOAP GENERATION ---")
soap = build_soap(
    narrative,
    entities,
    red_flags,
    syndrome,
    similarity,
    score,
    "Prototype assessment pending human review",
    vitals
)

for section, content in soap.items():
    print(f"\n{section.upper()}:")
    print(content)
