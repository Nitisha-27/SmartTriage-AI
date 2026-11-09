
"""
Independent safety-alert engine for SmartTriage AI.

This module generates prototype warning alerts independently
of the XGBoost prediction.

Educational prototype only. These rules are not clinically
validated and must not be used for real patient triage.
"""

def generate_safety_alerts(
    narrative,
    vitals,
    red_flags,
    five_parameter_score
):
    alerts = []

    narrative = (narrative or "").lower()

    # -------------------------------------------------
    # 1. Concerning symptom combinations
    # -------------------------------------------------

    cardiac_symptoms = [
        "chest pain",
        "central chest pain",
        "crushing chest",
        "radiating to the left arm",
        "radiating to left arm"
    ]

    cardiac_associated_symptoms = [
        "sweating",
        "diaphoresis",
        "nausea",
        "shortness of breath"
    ]

    has_cardiac_symptom = any(
        phrase in narrative
        for phrase in cardiac_symptoms
    )

    has_associated_symptom = any(
        phrase in narrative
        for phrase in cardiac_associated_symptoms
    )

    if has_cardiac_symptom and has_associated_symptom:
        alerts.append({
            "code": "CARDIAC_SYMPTOM_COMBINATION",
            "category": "Symptom warning",
            "message": (
                "Chest discomfort with associated symptoms "
                "detected. Requires human review."
            ),
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    # -------------------------------------------------
    # 2. Vital-sign warnings
    # -------------------------------------------------

    hr = vitals.get("heart_rate")
    rr = vitals.get("resp_rate")
    spo2 = vitals.get("spo2")
    sbp = vitals.get("systolic_bp")
    temp = vitals.get("temperature")

    if hr is not None and hr > 130:
        alerts.append({
            "code": "HIGH_HEART_RATE",
            "category": "Vital-sign warning",
            "message": "Heart rate exceeds the prototype alert threshold.",
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    if rr is not None and rr > 24:
        alerts.append({
            "code": "HIGH_RESPIRATORY_RATE",
            "category": "Vital-sign warning",
            "message": "Respiratory rate exceeds the prototype alert threshold.",
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    if spo2 is not None and spo2 <= 91:
        alerts.append({
            "code": "LOW_OXYGEN_SATURATION",
            "category": "Vital-sign warning",
            "message": "Oxygen saturation is at or below the prototype alert threshold.",
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    if sbp is not None and sbp <= 90:
        alerts.append({
            "code": "LOW_SYSTOLIC_BP",
            "category": "Vital-sign warning",
            "message": "Systolic blood pressure is at or below the prototype alert threshold.",
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    if temp is not None and temp > 39:
        alerts.append({
            "code": "HIGH_TEMPERATURE",
            "category": "Vital-sign warning",
            "message": "Temperature exceeds the prototype alert threshold.",
            "severity": "MODERATE",
            "source": "Rule-based safety engine"
        })

    # -------------------------------------------------
    # 3. Multiple red flags
    # -------------------------------------------------

    if len(red_flags or {}) >= 2:
        alerts.append({
            "code": "MULTIPLE_RED_FLAGS",
            "category": "Symptom warning",
            "message": "Multiple NLP-detected warning features require review.",
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    # -------------------------------------------------
    # 4. Five-parameter score warning
    # -------------------------------------------------

    if five_parameter_score is not None and five_parameter_score >= 7:
        alerts.append({
            "code": "ELEVATED_COMPONENT_SCORE",
            "category": "Composite score warning",
            "message": (
                "The five-parameter component score is elevated. "
                "This is not a complete official NEWS2 assessment."
            ),
            "severity": "HIGH",
            "source": "Rule-based safety engine"
        })

    return {
        "alerts": alerts,
        "alert_count": len(alerts),
        "has_safety_alert": len(alerts) > 0,
        "engine": "Independent rule-based safety engine",
        "notice": (
            "Prototype alerts only. Not clinically validated "
            "and not a substitute for professional assessment."
        )
    }
