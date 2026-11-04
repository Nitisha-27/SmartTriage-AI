
from nlp_engine import (
    extract_clinical_entities,
    detect_missing_fields,
    compute_syndrome_match,
    calculate_news2,
    build_soap
)

from model_loader import (
    get_triage_prediction,
    get_shap_explanation
)


REQUIRED_VITALS = [
    "heart_rate",
    "resp_rate",
    "systolic_bp",
    "spo2",
    "temperature"
]


def assess_patient(
    patient_name,
    age,
    gender,
    narrative,
    vitals
):
    """
    Integrated SmartTriage prototype assessment.

    The ML output is experimental and based on synthetic data.
    It must not be used as a standalone clinical decision.
    """

    # 1. Input validation

    if not narrative or not narrative.strip():
        raise ValueError("Patient narrative cannot be empty.")

    if not isinstance(age, int) or not 0 <= age <= 120:
        raise ValueError("Age must be an integer between 0 and 120.")

    if not isinstance(vitals, dict):
        raise ValueError("Vitals must be provided as a dictionary.")

    # 2. Clinical NLP analysis

    entities, red_flags = extract_clinical_entities(narrative)

    missing_fields = detect_missing_fields(narrative)

    syndrome, similarity = compute_syndrome_match(narrative)

    red_flag_count = len(red_flags)

    # 3. Check vital completeness

    missing_vitals = [
        vital for vital in REQUIRED_VITALS
        if vitals.get(vital) is None
    ]

    vital_assessment = {
        "five_parameter_score": None,
        "missing_vitals": missing_vitals,
        "score_status": (
            "INCOMPLETE"
            if missing_vitals
            else "CALCULATED"
        ),
        "score_description": (
            "Five-parameter component score; "
            "not a complete official NEWS2 assessment."
        )
    }

    prediction = None
    shap_result = None
    soap_tier = "Not generated"

    # 4. Calculate score and run ML only when all
    # required vital measurements are available.

    if not missing_vitals:

        news2_score = calculate_news2(
            hr=vitals["heart_rate"],
            rr=vitals["resp_rate"],
            sbp=vitals["systolic_bp"],
            spo2=vitals["spo2"],
            temp=vitals["temperature"]
        )

        vital_assessment["five_parameter_score"] = news2_score

        # Prototype age feature; not a clinical risk rule.
        age_risk = 1 if age >= 65 else 0

        # 5. XGBoost prediction

        prediction = get_triage_prediction(
            news2_score=news2_score,
            syndrome_similarity=similarity,
            red_flag_count=red_flag_count,
            age_risk=age_risk
        )

        # 6. SHAP explanation

        shap_result = get_shap_explanation(
            news2_score=news2_score,
            syndrome_similarity=similarity,
            red_flag_count=red_flag_count,
            age_risk=age_risk
        )

        soap_tier = prediction["triage_tier"]

    # 7. Generate SOAP report

    soap = build_soap(
        narrative=narrative,
        entities=entities,
        red_flags=red_flags,
        syndrome=syndrome,
        similarity=similarity,
        news2=vital_assessment["five_parameter_score"],
        tier=soap_tier,
        vitals=vitals
    )

    # 8. Final assessment

    return {
        "patient": {
            "name": patient_name,
            "age": age,
            "gender": gender
        },

        "clinical_analysis": {
            "entities": entities,
            "red_flags": red_flags,
            "red_flag_count": red_flag_count,
            "missing_fields": missing_fields,
            "syndrome": syndrome,
            "syndrome_similarity": similarity
        },

        "vital_assessment": vital_assessment,

        "ml_assessment": prediction,

        "shap_explanation": (
            shap_result["explanation"]
            if shap_result is not None
            else []
        ),

        "soap": soap,

        "review_status": "PENDING_SUPERVISOR_REVIEW",

        "prototype_notice": (
            "Experimental educational prototype trained on "
            "synthetic data. Its predictions are not clinically "
            "validated and must not guide real patient care. "
            "Human review is required."
        )
    }
