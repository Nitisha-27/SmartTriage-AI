
from model_loader import (
    get_triage_prediction,
    get_shap_explanation
)


def test_loaded_model():

    print("\n========== SMARTTRIAGE MODEL LOADER TEST ==========")

    # Sample patient assessment features
    test_input = {
        "news2_score": 9,
        "syndrome_similarity": 0.8893,
        "red_flag_count": 0,
        "age_risk": 1
    }

    print("\n--- INPUT FEATURES ---")

    for feature, value in test_input.items():
        print(f"{feature}: {value}")

    # ----------------------------------------
    # 1. XGBoost Prediction
    # ----------------------------------------

    print("\n--- LOADED MODEL PREDICTION ---")

    result = get_triage_prediction(
        news2_score=test_input["news2_score"],
        syndrome_similarity=test_input["syndrome_similarity"],
        red_flag_count=test_input["red_flag_count"],
        age_risk=test_input["age_risk"]
    )

    print(f"Predicted Class: {result['triage_class']}")
    print(f"Predicted Tier: {result['triage_tier']}")
    print(f"Confidence: {result['confidence']:.4f}")

    print("\nClass Probabilities:")

    for tier, probability in result["probabilities"].items():
        print(f"{tier}: {probability:.4f}")

    # ----------------------------------------
    # 2. SHAP Explainability
    # ----------------------------------------

    print("\n--- LOADED MODEL SHAP EXPLANATION ---")

    explanation = get_shap_explanation(
        news2_score=test_input["news2_score"],
        syndrome_similarity=test_input["syndrome_similarity"],
        red_flag_count=test_input["red_flag_count"],
        age_risk=test_input["age_risk"]
    )

    print(f"Predicted Tier: {explanation['predicted_tier']}")

    print("\nFeature Contributions:")

    for item in explanation["explanation"]:

        print(
            f"Feature: {item['feature']} | "
            f"Input: {item['input_value']} | "
            f"SHAP: {item['shap_value']:.4f} | "
            f"Direction: {item['direction']}"
        )

    print("\n========== TEST COMPLETED ==========")


if __name__ == "__main__":
    test_loaded_model()
