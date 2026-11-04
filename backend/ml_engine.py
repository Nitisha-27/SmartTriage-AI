
import numpy as np
import pandas as pd
import shap

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# Features used by the triage classifier
FEATURE_COLUMNS = [
    "news2_score",
    "syndrome_similarity",
    "red_flag_count",
    "age_risk"
]

# Triage class mapping
TRIAGE_CLASSES = {
    0: "Routine",
    1: "Urgent",
    2: "Emergent"
}




def generate_training_data():

    """
    Generate overlapping synthetic training data.

    All four input features contribute to a prototype risk score.
    Labels are assigned using score quantiles to maintain
    balanced classes.

    This is synthetic data, not clinically validated data.
    """

    np.random.seed(42)

    samples = 900

    # Generate overlapping feature distributions
    news2_score = np.random.randint(0, 16, samples)

    syndrome_similarity = np.random.uniform(
        0.10, 0.90, samples
    )

    red_flag_count = np.random.randint(
        0, 5, samples
    )

    age_risk = np.random.randint(
        0, 2, samples
    )

    data = pd.DataFrame({
        "news2_score": news2_score,
        "syndrome_similarity": syndrome_similarity,
        "red_flag_count": red_flag_count,
        "age_risk": age_risk
    })

    # Normalize features to comparable ranges
    normalized_news2 = data["news2_score"] / 15

    normalized_syndrome = data["syndrome_similarity"]

    normalized_red_flags = data["red_flag_count"] / 4

    normalized_age_risk = data["age_risk"]

    # Construct a synthetic prototype risk score
    risk_score = (
        0.35 * normalized_news2
        + 0.20 * normalized_syndrome
        + 0.30 * normalized_red_flags
        + 0.15 * normalized_age_risk
        + np.random.normal(0, 0.02, samples)
    )

    # Divide observations into three approximately
    # equally represented classes
    lower_threshold = risk_score.quantile(1 / 3)
    upper_threshold = risk_score.quantile(2 / 3)

    labels = np.where(
        risk_score <= lower_threshold,
        0,
        np.where(
            risk_score <= upper_threshold,
            1,
            2
        )
    )

    data["triage_class"] = labels.astype(int)

    # Shuffle the dataset
    data = data.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)

    return data



def train_triage_model():
    """
    Train the XGBoost triage classification model.
    """

    data = generate_training_data()

    print("\n--- DATASET CLASS DISTRIBUTION ---")
    print(data["triage_class"].value_counts().sort_index())

    print("\n--- CLASS DISTRIBUTION (%) ---")
    print(
    data["triage_class"]
    .value_counts(normalize=True)
    .sort_index()
    .mul(100)
)

    X = data[FEATURE_COLUMNS]
    y = data["triage_class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print("\n--- XGBOOST MODEL EVALUATION ---")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    print(f"Accuracy: {accuracy:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=[0, 1, 2],
            target_names=["Routine", "Urgent", "Emergent"],
            zero_division=0
        )
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions, labels=[0, 1, 2]))

    return model


def predict_triage(
    model,
    news2_score,
    syndrome_similarity,
    red_flag_count,
    age_risk
):
    """
    Predict the prototype triage class for a case.
    """

    input_data = pd.DataFrame([{
        "news2_score": news2_score,
        "syndrome_similarity": syndrome_similarity,
        "red_flag_count": red_flag_count,
        "age_risk": age_risk
    }], columns=FEATURE_COLUMNS)

    predicted_class = int(model.predict(input_data)[0])

    probabilities = model.predict_proba(input_data)[0]

    return {
        "triage_class": predicted_class,
        "triage_tier": TRIAGE_CLASSES[predicted_class],
        "confidence": float(probabilities[predicted_class]),
        "probabilities": {
            TRIAGE_CLASSES[i]: float(probabilities[i])
            for i in range(len(TRIAGE_CLASSES))
        }

    
    }

def explain_prediction(
    model,
    news2_score,
    syndrome_similarity,
    red_flag_count,
    age_risk
):
    input_data = pd.DataFrame([{
        "news2_score": news2_score,
        "syndrome_similarity": syndrome_similarity,
        "red_flag_count": red_flag_count,
        "age_risk": age_risk
    }], columns=FEATURE_COLUMNS)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_data)

    predicted_class = int(model.predict(input_data)[0])

    if isinstance(shap_values, list):
        contributions = shap_values[predicted_class][0]
    else:
        contributions = shap_values[0, :, predicted_class]

    explanation = []

    for feature, value, contribution in zip(
        FEATURE_COLUMNS,
        input_data.iloc[0].values,
        contributions
    ):
        explanation.append({
            "feature": feature,
            "input_value": float(value),
            "shap_value": float(contribution),
            "direction": (
                "Positive" if contribution > 0
                else "Negative" if contribution < 0
                else "Neutral"
            )
        })

    explanation.sort(
        key=lambda item: abs(item["shap_value"]),
        reverse=True
    )

    return {
        "predicted_class": predicted_class,
        "predicted_tier": TRIAGE_CLASSES[predicted_class],
        "explanation": explanation
    }



if __name__ == "__main__":

    triage_model = train_triage_model()

    print("\n--- SAMPLE PREDICTION ---")

    result = predict_triage(
        model=triage_model,
        news2_score=13,
        syndrome_similarity=0.48,
        red_flag_count=2,
        age_risk=0
    )

    print(result)

    shap_result = explain_prediction(
        model=triage_model,
        news2_score=13,
        syndrome_similarity=0.48,
        red_flag_count=2,
        age_risk=0
    )

    print(shap_result)

    
    # Test SHAP explanations for all three triage classes

    test_cases = [
        {
            "name": "Routine",
            "news2_score": 1,
            "syndrome_similarity": 0.2,
            "red_flag_count": 0,
            "age_risk": 0
        },
        {
           
    "name": "Urgent",
    "news2_score": 9,
    "syndrome_similarity": 0.8893,
    "red_flag_count": 0,
    "age_risk": 1

        },
        {
            "name": "Emergent",
            "news2_score": 13,
            "syndrome_similarity": 0.7,
            "red_flag_count": 3,
            "age_risk": 1
        }
    ]

    print("\n--- SHAP TEST FOR ALL TRIAGE CLASSES ---")

    for case in test_cases:

        explanation = explain_prediction(
            model=triage_model,
            news2_score=case["news2_score"],
            syndrome_similarity=case["syndrome_similarity"],
            red_flag_count=case["red_flag_count"],
            age_risk=case["age_risk"]
        )

        print(f"\nExpected: {case['name']}")
        print(f"Predicted: {explanation['predicted_tier']}")

        for item in explanation["explanation"]:
            print(
                item["feature"],
                ":",
                round(item["shap_value"], 4),
                "(" + item["direction"] + ")"
            )

            
    print("\n--- FINDING CORRECT URGENT TEST CASES ---")

    training_data = generate_training_data()

    urgent_cases = training_data[
        training_data["triage_class"] == 1
    ]

    for _, row in urgent_cases.iterrows():

        result = predict_triage(
            model=triage_model,
            news2_score=int(row["news2_score"]),
            syndrome_similarity=float(row["syndrome_similarity"]),
            red_flag_count=int(row["red_flag_count"]),
            age_risk=int(row["age_risk"])
        )

        if result["triage_class"] == 1:
            print("\nCorrect Urgent Example:")
            print(row[FEATURE_COLUMNS].to_dict())
            print("Prediction:", result["triage_tier"])
            break


