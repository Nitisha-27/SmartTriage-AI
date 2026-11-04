from nlp_engine import compute_syndrome_match

test_cases = {
    "Acute Coronary Syndrome":
        "Patient has crushing chest pain radiating to left arm with sweating and nausea.",

    "Acute Respiratory Failure":
        "Patient has severe breathlessness, respiratory distress, low oxygen saturation and rapid breathing.",

    "Systemic Sepsis":
        "Patient has fever, chills, elevated heart rate, rapid breathing and low blood pressure.",

    "Acute Stroke":
        "Patient suddenly develops facial droop, arm weakness and difficulty speaking.",

    "Acute Surgical Abdomen":
        "Patient has severe abdominal pain, abdominal tenderness, vomiting and abdominal distension."
}

for expected, narrative in test_cases.items():
    syndrome, similarity = compute_syndrome_match(narrative)

    print(f"\nExpected: {expected}")
    print(f"Predicted: {syndrome}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Correct: {expected == syndrome}")