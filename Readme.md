# SmartTriage AI
### AI-Assisted Clinical Triage, Explainability & Healthcare Workflow Management

SmartTriage AI is a full-stack educational prototype that demonstrates how Artificial Intelligence can support structured patient intake, clinical information processing, triage assessment, supervisor review, and doctor consultation workflows.

The platform integrates **Natural Language Processing (NLP), XGBoost classification, SHAP explainability, independent rule-based safety alerts, and role-based workflow management** into a unified healthcare workflow application.

It is designed to explore the intersection of AI-assisted clinical assessment, interpretable machine learning, and human-supervised decision workflows.

> **Disclaimer:** SmartTriage AI is an educational prototype, not a clinically validated medical device. It must not be used to diagnose patients, determine real-world clinical urgency, or make patient-care decisions.

---

## Project Overview

SmartTriage AI follows a structured patient-management workflow:

1. **Patient Intake:** A health worker submits patient demographics, clinical symptoms, and vital signs.
2. **Clinical Processing:** The system extracts clinical entities, identifies potential red flags, detects missing information, and matches the narrative against predefined syndrome categories.
3. **AI Assessment:** An XGBoost model generates a prototype triage prediction with probability estimates and SHAP explanations.
4. **Independent Safety Assessment:** A separate rule-based engine evaluates predefined warning conditions independently of the ML prediction.
5. **Supervisor Review:** A supervisor reviews the complete assessment, safety alerts, and model explanation before approving or overriding the AI recommendation.
6. **Doctor Consultation:** Approved cases enter the doctor queue for consultation and referral documentation.
7. **Analytics:** Supervisors and administrators monitor workflow statistics, triage distributions, and AI–supervisor disagreement.

---

## Application Features

### 1. Role-Based Authentication

JWT-based authentication and role-based authorization protect the application workflows.

Four user roles are supported:

| Role | Access |
|---|---|
| Admin | Administrative access to supported workflows |
| Health Worker | Patient intake |
| Supervisor | Pending-case review, approval, override, and analytics |
| Doctor | Approved-case queue, consultation, and case audit access |

Authentication includes password hashing, access-token generation, protected API endpoints, and role-based permission checks.

### 2. Patient Intake and Clinical NLP

The patient intake module captures:

- Patient demographics
- Clinical narrative
- Vital signs
- Relevant medical information

The NLP pipeline uses spaCy and TF-IDF-based text similarity to:

- Extract relevant clinical entities.
- Identify potential red-flag symptoms.
- Handle selected symptom-negation patterns.
- Detect missing clinical information.
- Match narratives against predefined syndrome categories.

**Supported syndrome categories:**

1. Acute Coronary Syndrome
2. Acute Respiratory Failure
3. Systemic Sepsis
4. Acute Stroke
5. Acute Surgical Abdomen

### 3. Vital-Sign Assessment

A prototype five-parameter component score evaluates:

- Heart rate
- Respiratory rate
- Systolic blood pressure
- Oxygen saturation
- Body temperature

Additional handling includes incomplete vital-sign submissions and prevention of ML prediction when required vital information is unavailable.

> This is a prototype five-parameter score, not the complete or officially validated NEWS2 scoring system.

### 4. XGBoost-Based Triage Prediction

The machine-learning component uses XGBoost to classify assessments into three prototype categories:

- Routine
- Urgent
- Emergent

The prediction pipeline includes:

- Structured feature extraction.
- Three-class classification.
- Class probability estimates.
- Prediction confidence display.
- SHAP-based feature contribution explanations.

The current prototype model uses a synthetic development dataset and achieved approximately **86% accuracy on its held-out synthetic test split**.

This result is limited to the synthetic evaluation setting and does not demonstrate clinical accuracy or real-world generalization.

### 5. Independent Rule-Based Safety Engine

A separate safety engine evaluates patient information independently of the XGBoost model.

Current prototype warning rules cover:

- Cardiac symptom combinations.
- Elevated respiratory rate.
- Low oxygen saturation.
- Low systolic blood pressure.
- Elevated five-parameter component scores.

Each generated warning contains:

- Alert code
- Alert category
- Explanatory message
- Severity
- Alert source

Safety assessments are persisted in PostgreSQL and exposed through the backend API.

The supervisor interface displays these warnings separately from the ML prediction. This allows human reviewers to inspect potential warning conditions even when the model produces a lower triage category.

The safety engine uses experimental rules and thresholds. It is not clinically validated and does not replace professional assessment.

### 6. Supervisor Review and Override

The supervisor module provides:

- Pending-case retrieval.
- Patient assessment review.
- AI triage recommendation and confidence.
- Clinical red-flag display.
- Missing-information display.
- Independent safety-alert review.
- SHAP explanation inspection.
- AI recommendation approval.
- Manual triage-tier override.
- Mandatory supervisor comments.

All supervisor decisions are recorded in the case audit history.

### 7. Doctor Consultation

The doctor module supports:

- Retrieval of supervisor-approved cases.
- Display of supervisor-verified triage categories.
- Patient assessment review.
- Consultation documentation.
- Referral information.
- Consultation completion.

### 8. Audit Trail

The audit system records important events across the patient workflow, including:

- AI assessment generation.
- Supervisor approvals.
- Supervisor overrides.
- Doctor consultation completion.

Individual case audit histories can be retrieved through the API.

### 9. Analytics Dashboard

The Analytics Dashboard provides an overview of application activity and workflow performance.

**Workflow statistics:**
- Total cases.
- Pending supervisor reviews.
- Cases approved for doctor consultation.
- Completed consultations.

**Visual analytics:**
- AI-predicted versus supervisor-verified triage distribution.
- Workflow status distribution.
- AI prediction breakdown.
- Supervisor-verified triage breakdown.

**AI–Supervisor disagreement analysis:**
- Total reviewed cases with AI predictions.
- Discordant cases.
- Agreement cases.
- Discordance percentage.
- Agreement percentage.
- Discordant case IDs.

The discordance metric measures differences between AI predictions and supervisor-verified tiers. It does not establish which decision was clinically correct.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 14, React, TypeScript |
| Styling | Tailwind CSS |
| UI Components | Lucide React |
| Data Visualization | Recharts |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Authentication | JWT, PyJWT, Argon2 |
| NLP | spaCy, TF-IDF, Cosine Similarity |
| Machine Learning | XGBoost, scikit-learn |
| Explainability | SHAP |
| Data Processing | NumPy, Pandas, SciPy |
| Development Tools | VS Code, Git, GitHub |

---

## System Architecture

```text
                 SMARTTRIAGE AI
                        |
                        v
                Next.js Frontend
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Patient       Supervisor      Doctor
       Intake         Review       Consultation
          |             |             |
          +-------------+-------------+
                        |
                        v
                  FastAPI Backend
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       Clinical       ML Engine     Safety Engine
        NLP           XGBoost       Rule-Based
          |             |             |
          v             v             v
       Syndrome       SHAP          Safety Alerts
       Matching    Explanation
          |             |             |
          +-------------+-------------+
                        |
                        v
                   PostgreSQL
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
        Cases       Audit Logs      Users
                        |
                        v
                Analytics Dashboard
```

---

## Backend API Reference

Interactive API documentation is available through FastAPI Swagger UI at `/docs`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate a user |
| GET | `/auth/me` | Retrieve the current user profile |
| POST | `/auth/users` | Create a user (admin only) |

### Patient and Workflow Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/cases/intake` | Submit patient information and generate an assessment |
| GET | `/cases/pending` | Retrieve pending supervisor reviews |
| POST | `/cases/supervisor/review` | Approve or override an assessment |
| GET | `/cases/queue` | Retrieve the doctor queue |
| POST | `/cases/doctor/complete` | Record consultation completion |
| GET | `/cases/{case_id}` | Retrieve individual case details |
| GET | `/cases/{case_id}/audit` | Retrieve case audit history |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/summary` | Retrieve workflow statistics |
| GET | `/analytics/discordance` | Calculate AI–supervisor disagreement |
| GET | `/analytics/triage-distribution` | Compare AI and supervisor triage distributions |

---

## Model Development and Dataset Experiments

### 1. Synthetic Three-Class Triage Model

The prototype XGBoost model was developed using a synthetic dataset.

It uses a five-feature representation:

- Five-parameter component score.
- Syndrome similarity.
- Red-flag count.
- Age-risk indicator.
- Associated model inputs as defined in the training pipeline.

The model produces Routine, Urgent, and Emergent predictions, with SHAP explanations.

Its reported accuracy of approximately 86% is specific to the held-out synthetic test split.

### 2. Experimental Five-Class ESI Classification

A separate model-development experiment explored a downloaded dataset containing:

- 80,000 training records.
- 20,000 test records.
- Supplementary patient-history and chief-complaint files.

The experiment included:

- Data preprocessing and quality investigation.
- XGBoost classification of ESI levels 1–5.
- Random validation.
- Grouped complaint validation.
- Leave-one-site-out evaluation.

Reported leave-one-site-out results:

| Metric | Result |
|---|---:|
| Pooled Accuracy | 84.97% |
| Macro F1 | 86.56% |

**Dataset provenance limitation:** The source, collection methodology, label-generation process, and licence of the downloaded ESI dataset have not been independently verified. It must not be represented as official Triagegeist competition data. These results are dataset-specific and do not establish clinical validity.

---

## Project Structure

```text
Smarttriage/
│
├── backend/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── cases.py
│   │   ├── supervisor.py
│   │   ├── doctor.py
│   │   └── analytics.py
│   │
│   ├── artifacts/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── auth.py
│   ├── dependencies.py
│   ├── nlp_engine.py
│   ├── ml_engine.py
│   ├── model_loader.py
│   ├── assessment_engine.py
│   ├── safety_engine.py
│   ├── create_tables.py
│   ├── create_admin.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── intake/
│   │   ├── supervisor/
│   │   ├── doctor/
│   │   ├── analytics/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   └── src/
│       ├── components/
│       └── lib/
│
├── .gitignore
├── README.md
└── .env                 # Local only; not committed
```

---

## Running the Project Locally

### Prerequisites

- Python 3.11
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the Repository

```powershell
git clone https://github.com/Nitisha-27/SmartTriage-AI.git
cd SmartTriage-AI
```

### 2. Configure the Backend Environment

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/smarttriage
JWT_SECRET_KEY=YOUR_SECRET_KEY
```

Replace the placeholders with your local PostgreSQL credentials and a securely generated JWT secret.

Never commit `.env` or other secret credentials to GitHub.

### 4. Initialize the Database

Create a PostgreSQL database named `smarttriage`.

Run the table initialization script:

```powershell
python backend\create_tables.py
```

Create the initial administrator account:

```powershell
python backend\create_admin.py
```

### 5. Start the Backend

From the project root:

```powershell
uvicorn main:app --reload --app-dir backend
```

Backend:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 6. Start the Frontend

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

`http://localhost:3000`

---

## Current Development Status

| Area | Status |
|---|---|
| Backend APIs | Implemented |
| PostgreSQL integration | Implemented |
| Authentication | Implemented |
| Role-based authorization | Implemented and tested |
| Clinical NLP | Implemented |
| Syndrome matching | Implemented |
| XGBoost prediction | Implemented |
| SHAP explanations | Implemented |
| Independent safety engine | Implemented |
| Safety-alert persistence | Implemented |
| Patient intake interface | Implemented |
| Supervisor review interface | Implemented |
| Doctor queue interface | Implemented |
| Analytics dashboard | Implemented |
| Core workflow integration | Under end-to-end verification |
| Automated test suite | Future work |
| Docker Compose deployment | Future work |

---

## Future Enhancements

- Automated backend and frontend testing.
- Improved clinical entity extraction and negation handling.
- More robust handling of incomplete and conflicting patient information.
- Stronger dataset provenance and external model validation.
- Improved monitoring and error handling.
- Database migration management.
- Docker Compose-based deployment.
- Enhanced security and deployment readiness.

---

## Project Objective

SmartTriage AI explores how machine learning, explainability, independent rule-based checks, and human review can be combined in a structured healthcare workflow.

The project emphasizes not only AI-generated predictions, but also transparency, independent warning mechanisms, human oversight, and traceable workflow decisions.

---

**SmartTriage AI**  
*Exploring AI-assisted clinical workflows through explainable machine learning and human-supervised decision support.*