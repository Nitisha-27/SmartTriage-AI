
from assessment_engine import assess_patient

result = assess_patient(
    patient_name="Incomplete Test",
    age=45,
    gender="Female",
    narrative="Patient reports chest pain for two hours.",
    vitals={
        "heart_rate": 110,
        "resp_rate": 24,
        "systolic_bp": None,
        "spo2": 94,
        "temperature": 38.0
    }
)

print("\n========== INCOMPLETE VITALS TEST ==========")

print("\nVital Assessment:")
print(result["vital_assessment"])

print("\nML Assessment:")
print(result["ml_assessment"])

print("\nSHAP Explanation:")
print(result["shap_explanation"])

print("\nWorkflow Status:")
print(result["review_status"])
