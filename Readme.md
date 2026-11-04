# SmartTriage AI
### AI-Assisted Emergency Triage and Clinical Referral Support System

SmartTriage AI is an AI-assisted emergency triage prototype designed to support the preliminary assessment, prioritisation and referral of patients in emergency-care settings.

The system combines clinical text processing, vital-sign analysis, machine learning and explainable AI to generate a preliminary triage assessment. A human supervisor reviews the recommendation before the case proceeds to the doctor workflow.

> **Disclaimer:** SmartTriage AI is an educational and research prototype. It is not clinically validated and must not be used for real-world diagnosis, treatment or autonomous patient prioritisation.

---

## Problem Statement

Emergency departments often handle large numbers of patients with varying levels of urgency. Initial assessment requires healthcare professionals to interpret patient complaints, review vital signs and identify potential warning signs.

SmartTriage AI explores how natural language processing and machine learning can assist this workflow by:

- Extracting relevant clinical information from patient narratives.
- Identifying potential red-flag symptoms.
- Detecting missing information during intake.
- Analysing vital signs.
- Generating a preliminary triage category.
- Providing feature-level explanations for model predictions.
- Supporting human review and referral workflows.

## Key Features

### 1. Clinical Information Extraction
- Processes patient complaints using NLP.
- Extracts relevant clinical entities and symptoms.
- Identifies potential red flags.
- Detects missing information such as symptom duration, pain score and medical history.
- Matches narratives against five predefined syndromic archetypes.

### 2. Vital Sign Assessment
- Processes heart rate, respiratory rate, systolic blood pressure, oxygen saturation and temperature.
- Calculates a five-parameter NEWS2-inspired component score.
- Identifies incomplete vital-sign submissions.

*This is a simplified component score, not the official NEWS2 assessment.*

### 3. Machine Learning-Based Triage
- Uses an XGBoost classification model.
- Predicts one of three preliminary triage categories in the initial prototype: Routine, Urgent or Emergent.
- Combines vital-sign features, syndrome similarity, red-flag count and age-related risk features.

### 4. Explainable AI
- Uses SHAP (SHapley Additive exPlanations).
- Identifies features contributing to model predictions.
- Supports interpretation of model behaviour.

### 5. Human-in-the-Loop Workflow
- Supervisor reviews AI-generated assessments.
- Supports approval and override actions.
- Requires a supervisor comment.
- Routes approved cases to the doctor queue.

### 6. Audit Trail
- Records assessment generation.
- Records supervisor approval or override.
- Records doctor consultation completion.
- Maintains a history of case status changes.

---

## System Architecture

```text
              PATIENT INTAKE
                    |
                    v
          Clinical Narrative + Vitals
                    |
                    v
          NLP Processing Engine
          - Entity Extraction
          - Red Flag Detection
          - Missing Field Detection
          - Syndrome Matching
                    |
                    v
          Vital Sign Assessment
          - Five-Parameter Score
                    |
                    v
           Machine Learning Engine
                  XGBoost
                    |
                    v
             SHAP Explainability
                    |
                    v
           Preliminary Assessment
                    |
                    v
            SUPERVISOR REVIEW
              /          \
          Approve       Override
              \          /
                    |
                    v
              DOCTOR QUEUE
                    |
                    v
          Consultation and Referral
                    |
                    v
              AUDIT LOGGING
```

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| API Documentation | Swagger / OpenAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| NLP | spaCy, TF-IDF, Cosine Similarity |
| Machine Learning | XGBoost, Scikit-learn |
| Explainable AI | SHAP |
| Data Processing | Pandas, NumPy |
| Model Persistence | Joblib |

## Machine Learning and Dataset

The project currently uses the Triagegeist Kaggle competition dataset for its five-class ESI experimentation.

The dataset contains:
- 80,000 training records.
- 20,000 test records.
- Five ESI acuity categories (1–5).
- Supplementary chief-complaint and patient-history information.

**Dataset provenance:** The competition describes these records as synthetic emergency-department encounters. They are not real patient records.

The project also explores the MIMIC-IV-ED Demo dataset separately for real-world emergency-department data exploration.

### Data Preparation
- Merged supplementary records using patient identifiers.
- Examined missing values and inconsistent measurements.
- Flagged inconsistent blood pressure readings.
- Converted unknown pain-score values into missing values while retaining an indicator.
- Excluded potential target leakage variables from the baseline feature set.

### ESI Model Validation

The XGBoost model was evaluated using a stratified validation split and leave-one-site-out validation.

| Metric | Leave-one-site-out result |
|---|---:|
| Accuracy | 84.97% |
| Balanced Accuracy | 86.16% |
| Macro F1-score | 86.56% |
| Weighted F1-score | 85.02% |

The model was also evaluated using confusion matrices, class-wise precision and recall, SHAP feature importance and error analysis.

The leave-one-site-out experiments produced a mean macro F1-score of 86.56% across five held-out sites.

**Important limitations:**
- These metrics measure performance on the synthetic Triagegeist dataset only.
- They do not establish generalisation to real patients or hospitals.
- Under-triage and over-triage counts are ordinal classification error analyses, not validated clinical safety measures.
- The dataset's non-commercial research licence must be respected. The restricted dataset files are not included in this repository.

---

## Backend API

The current backend provides the following endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/cases/intake` | Submit a patient assessment |
| GET | `/cases/pending` | Retrieve cases awaiting review |
| GET | `/cases/queue` | Retrieve approved doctor queue |
| GET | `/cases/{case_id}` | Retrieve case details |
| POST | `/cases/supervisor/review` | Approve or override assessment |
| POST | `/cases/doctor/complete` | Complete consultation |
| GET | `/cases/{case_id}/audit` | Planned audit retrieval |
| GET | `/analytics/summary` | Planned analytics |
| GET | `/analytics/discordance` | Planned override analysis |
| GET | `/analytics/triage-distribution` | Planned triage distribution |

The audit retrieval and analytics endpoints are planned and are not yet implemented.

Interactive API documentation is available through Swagger UI.

## Project Structure

```text
Smarttriage/
│
├── backend/
│   ├── routers/
│   │   ├── cases.py
│   │   ├── doctor.py
│   │   └── supervisor.py
│   │
│   ├── artifacts/                 # Local model files
│   ├── assessment_engine.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── ml_engine.py
│   ├── model_loader.py
│   ├── models.py
│   ├── nlp_engine.py
│   ├── schemas.py
│   ├── train_model.py
│   ├── train_esi_model.py
│   └── requirements.txt
│
├── data/                          # Local datasets; excluded from Git
│
├── .env                            # Local credentials; excluded from Git
├── .gitignore
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Nitisha-27/SmartTriage-AI.git
cd SmartTriage-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://admin:YOUR_PASSWORD@localhost:5432/smarttriage
```

Replace the placeholder with your local PostgreSQL credentials.

### 5. Create database tables

```bash
python backend/create_tables.py
```

### 6. Start the backend

```bash
uvicorn main:app --reload --app-dir backend
```

### 7. Access the API

- Backend: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

A local trained model artifact is required for the initial ML prediction workflow. Model files are excluded from Git and must be generated locally using the appropriate training scripts and permitted data.

---

## Future Enhancements

- Complete audit retrieval and analytics APIs.
- Develop a Next.js frontend dashboard.
- Add role-based authentication and authorisation.
- Improve handling of incomplete clinical information.
- Integrate additional validated clinical datasets where permitted.
- Evaluate generalisation using appropriately sourced real-world data.
- Improve model calibration and uncertainty estimation.
- Add Docker-based deployment.
- Conduct further safety, fairness and clinical validation research.

## Research and Data Sources

- **Triagegeist:** [Kaggle Competition](https://www.kaggle.com/competitions/triagegeist/data)
- **MIMIC-IV-ED Demo:** [PhysioNet](https://physionet.org/content/mimic-iv-ed-demo/)

Refer to the original dataset pages for their terms, licence and access requirements. Do not redistribute restricted dataset files.

---

## Author

**Nitisha Mishra**

B.Tech – Electronics and Communication Engineering (Biomedical Specialization)

VIT Vellore

GitHub: [Nitisha-27](https://github.com/Nitisha-27)

---

*SmartTriage AI is an academic project exploring the application of artificial intelligence, machine learning and explainable AI in emergency-care workflow support.*
