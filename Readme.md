# SmartTriage AI – Clinical Triage and Referral Support Platform

SmartTriage AI is an educational full-stack prototype designed to support structured patient intake, AI-assisted triage assessment, supervisor review, and doctor consultation workflows.

The platform combines clinical text processing, machine-learning-based triage prediction, explainability, and workflow analytics to demonstrate how AI can assist healthcare professionals in organizing patient information.

> **Disclaimer:** SmartTriage is an educational prototype. It is not clinically validated and must not be used to diagnose patients, determine real-world urgency, or make patient-care decisions.

## Project Status

**Current stage:** Core backend workflows implemented; frontend workflow pages and analytics integration in progress.

| Module | Status |
|---|---|
| Patient intake | Implemented |
| Clinical text processing | Implemented |
| Syndrome matching | Implemented |
| Vital-sign component scoring | Implemented |
| ML triage prediction | Implemented |
| SHAP-based explanations | Implemented |
| Supervisor review and override | Implemented |
| Doctor consultation workflow | Implemented |
| Case audit history | Implemented |
| Analytics backend APIs | Implemented and tested |
| Dashboard frontend | Implemented |
| Patient intake frontend | Implemented |
| Supervisor review frontend | Implemented |
| Doctor queue frontend | Implemented |
| Analytics frontend | Pending |
| Authentication and role-based access control | Pending |
| Docker-based deployment | Pending |

## Key Features

### 1. Patient Intake
- Capture patient demographics, clinical narrative, and vital signs.
- Extract relevant clinical entities and potential red flags.
- Identify missing clinical information.
- Generate a structured assessment for review.

### 2. Clinical NLP and Syndrome Matching
- Process patient narratives using spaCy and TF-IDF-based text similarity.
- Match narratives against five predefined syndrome categories:
  - Acute Coronary Syndrome
  - Acute Respiratory Failure
  - Systemic Sepsis
  - Acute Stroke
  - Acute Surgical Abdomen
- Identify potential red flags and missing information.

### 3. Vital-Sign Assessment
- Calculate a five-parameter component score using heart rate, respiratory rate, systolic blood pressure, oxygen saturation, and temperature.
- Handle incomplete vital-sign submissions.
- Prevent ML prediction when required vital information is missing.

**Note:** This is a prototype five-parameter score, not the complete or officially validated NEWS2 scoring system.

### 4. Machine Learning and Explainability
- XGBoost-based triage classification.
- Three prototype output categories: Routine, Urgent, and Emergent.
- Confidence estimates and SHAP-based feature explanations.
- Model training and evaluation using a synthetic development dataset.

The synthetic model achieved approximately 86% accuracy on its held-out synthetic test split. This result does not represent clinical performance or real-world generalization.

### 5. Supervisor Review
- Retrieve cases awaiting review.
- Approve AI-generated recommendations.
- Override the AI-suggested triage tier.
- Require a supervisor comment for each decision.
- Record review decisions in the audit history.

### 6. Doctor Consultation
- Display supervisor-approved cases.
- Prioritize cases using supervisor-verified triage tiers.
- Retrieve patient assessment details.
- Record consultation notes and referral information.
- Mark consultations as completed.

### 7. Audit Trail
- Record AI assessment generation.
- Record supervisor approvals and overrides.
- Record doctor consultation completion.
- Retrieve chronological audit history for individual cases.

### 8. Analytics Backend
Implemented and tested API endpoints for:
- Overall case and workflow statistics.
- AI–supervisor disagreement rate.
- AI and supervisor triage distributions.

The analytics frontend is not yet implemented.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS |
| UI and charts | Lucide React, Recharts |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| NLP | spaCy, TF-IDF, cosine similarity |
| Machine Learning | XGBoost, scikit-learn |
| Explainability | SHAP |
| Development tools | VS Code, Git, GitHub |

## Backend API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/cases/intake` | Submit patient assessment |
| GET | `/cases/pending` | Retrieve pending reviews |
| POST | `/cases/supervisor/review` | Approve or override assessment |
| GET | `/cases/queue` | Retrieve doctor queue |
| POST | `/cases/doctor/complete` | Record consultation completion |
| GET | `/cases/{case_id}` | Retrieve case details |
| GET | `/cases/{case_id}/audit` | Retrieve audit history |
| GET | `/analytics/summary` | Retrieve workflow statistics |
| GET | `/analytics/discordance` | Retrieve disagreement statistics |
| GET | `/analytics/triage-distribution` | Retrieve triage distributions |

Interactive API documentation is available through FastAPI Swagger UI at `/docs` when the backend is running.

## Dataset and Model Development

The project includes two separate model-development efforts:

**1. Prototype three-tier triage model**
- Developed using a synthetic dataset.
- Predicts Routine, Urgent, and Emergent categories.
- Uses a five-feature input representation.
- Evaluated on a held-out synthetic test split.
- SHAP explanations are generated for predictions.

**2. Five-class ESI classification experiment**
- Explored a downloaded dataset containing 80,000 training records and 20,000 test records, alongside supplementary patient-history and chief-complaint files.
- Developed a preprocessing and data-quality investigation pipeline.
- Trained an XGBoost model to classify ESI levels 1–5.
- Evaluated performance using random validation, grouped complaint validation, and leave-one-site-out experiments.
- Achieved approximately 84.97% pooled accuracy and 86.56% macro F1 in leave-one-site-out evaluation.

**Dataset provenance limitation:** The source, collection methodology, label-generation process, and licence of the downloaded ESI dataset have not yet been independently verified. It should not be represented as official Triagegeist competition data. Its experimental results are dataset-specific and do not establish clinical validity.

## Project Structure

```text
Smarttriage/
│
├── backend/
│   ├── routers/
│   │   ├── cases.py
│   │   ├── supervisor.py
│   │   └── doctor.py
│   ├── artifacts/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── nlp_engine.py
│   ├── ml_engine.py
│   ├── assessment_engine.py
│   ├── model_loader.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── intake/
│   │   ├── supervisor/
│   │   ├── doctor/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   └── src/
│       ├── app/
│       └── components/
│
├── data/
├── .gitignore
└── README.md
```

## Running the Project Locally

### Backend

From the project root, activate the Python virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

Configure the PostgreSQL connection in the root `.env` file:

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/smarttriage
```

Start the FastAPI server:

```powershell
uvicorn main:app --reload --app-dir backend
```

Backend API:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## Current Development Priorities

- Complete the Analytics frontend and connect it to the existing backend endpoints.
- Improve incomplete-vitals handling and clinical workflow validation.
- Implement authentication and proper role-based access control.
- Strengthen dataset provenance documentation and external validation.
- Add automated backend and frontend tests.
- Containerize the application using Docker Compose.
- Improve deployment readiness, monitoring, and documentation.

## Future Scope

- More robust clinical entity extraction.
- Improved clinical decision-support explainability.
- Better handling of incomplete and conflicting patient information.
- Secure role-based access and audit controls.
- Expanded validation using appropriately sourced and documented datasets.
- Deployment as a complete, containerized application.

---

**SmartTriage AI**  
*An educational prototype exploring AI-assisted clinical triage, explainability, and healthcare workflow management.*
