
from pathlib import Path
import joblib

from ml_engine import train_triage_model

# Define the model storage location
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACTS_DIR / "triage_model.pkl"


def save_trained_model():

    print("\n--- TRAINING FINAL TRIAGE MODEL ---")

    # Train the XGBoost model
    model = train_triage_model()

    # Create artifacts folder if it does not exist
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save trained model
    joblib.dump(model, MODEL_PATH)

    print("\n--- MODEL SAVED SUCCESSFULLY ---")
    print(f"Model location: {MODEL_PATH}")


if __name__ == "__main__":
    save_trained_model()
