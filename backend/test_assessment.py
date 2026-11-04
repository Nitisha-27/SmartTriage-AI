
from assessment_engine import assess_patient


patient = {
    "patient_name": "Test Patient",
    "age": 45,
    "gender": "Female",

    "narrative": (
        "Patient reports severe crushing chest pain "
        "radiating to left arm for 2 hours. "
        "Pain score is 8/10. "
        "Patient has a previous medical history of hypertension. "
        "No known allergies. "
        "Current medications include aspirin. "
        "Symptoms started suddenly."
    ),

    "vitals": {
        "heart_rate": 125,
        "resp_rate": 28,
        "systolic_bp": 85,
        "spo2": 89,
        "temperature": 39.5
    }
}


if __name__ == "__main__":

    result = assess_patient(
        patient_name=patient["patient_name"],
        age=patient["age"],
        gender=patient["gender"],
        narrative=patient["narrative"],
        vitals=patient["vitals"]
    )

    print("\n========== SMARTTRIAGE ASSESSMENT ==========")

    print("\n--- CLINICAL ANALYSIS ---")
    print(result["clinical_analysis"])

    print("\n--- VITAL ASSESSMENT ---")
    print(result["vital_assessment"])

    print("\n--- ML PREDICTION ---")
    print(result["ml_assessment"])

    print("\n--- SHAP EXPLANATION ---")
    for item in result["shap_explanation"]:
        print(item)

    print("\n--- SOAP REPORT ---")
    for section, content in result["soap"].items():
        print(f"\n{section.upper()}:")
        print(content)

    print("\n--- WORKFLOW STATUS ---")
    print(result["review_status"])

    print("\n========== ASSESSMENT COMPLETED ==========")
