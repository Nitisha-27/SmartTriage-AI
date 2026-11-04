
from pathlib import Path
import joblib

from ml_engine import predict_triage, explain_prediction

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "artifacts" / "triage_model.pkl"


def load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}. "
            "Run train_model.py first."
        )

    model = joblib.load(MODEL_PATH)

    print("XGBoost model loaded successfully.")

    return model


# Load model once when this module is imported
triage_model = load_model()


def get_triage_prediction(
    news2_score,
    syndrome_similarity,
    red_flag_count,
    age_risk
):

    return predict_triage(
        model=triage_model,
        news2_score=news2_score,
        syndrome_similarity=syndrome_similarity,
        red_flag_count=red_flag_count,
        age_risk=age_risk
    )


def get_shap_explanation(
    news2_score,
    syndrome_similarity,
    red_flag_count,
    age_risk
):

    return explain_prediction(
        model=triage_model,
        news2_score=news2_score,
        syndrome_similarity=syndrome_similarity,
        red_flag_count=red_flag_count,
        age_risk=age_risk
    )
