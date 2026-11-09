
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db, require_roles
from models import Case, AuditLog
from schemas import CaseIntake
from assessment_engine import assess_patient


router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


@router.post("/intake")
def create_case(
    patient: CaseIntake,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("health_worker", "admin")
    )
):
    try:
        # 1. Extract patient vitals

        vitals = patient.vitals.model_dump()

        # 2. Generate complete assessment

        assessment = assess_patient(
            patient_name=patient.patient_name,
            age=patient.age,
            gender=patient.gender,
            narrative=patient.raw_narrative,
            vitals=vitals
        )

        clinical = assessment["clinical_analysis"]
        vital_assessment = assessment["vital_assessment"]
        ml_assessment = assessment["ml_assessment"]
        safety_assessment = assessment["safety_assessment"]

        # 3. Create database record

        new_case = Case(
            patient_name=patient.patient_name,
            age=patient.age,
            gender=patient.gender,
            raw_narrative=patient.raw_narrative,

            # Vital signs
            heart_rate=vitals["heart_rate"],
            resp_rate=vitals["resp_rate"],
            systolic_bp=vitals["systolic_bp"],
            spo2=vitals["spo2"],
            temperature=vitals["temperature"],

            # NLP results
            extracted_entities=clinical["entities"],
            detected_red_flags=clinical["red_flags"],
            missing_fields=clinical["missing_fields"],

            syndrome_match=clinical["syndrome"],
            syndrome_similarity=clinical["syndrome_similarity"],

            # Five-parameter component score
            news2_score=vital_assessment["five_parameter_score"],

            # ML and SHAP
            shap_explanation=assessment["shap_explanation"],

            ai_triage_tier=(
                ml_assessment["triage_tier"]
                if ml_assessment else None
            ),

            ai_confidence=(
                ml_assessment["confidence"]
                if ml_assessment else None
            ),

            # Independent safety assessment
            safety_assessment=safety_assessment,

            # SOAP notes
            soap_subjective=assessment["soap"]["subjective"],
            soap_objective=assessment["soap"]["objective"],
            soap_assessment=assessment["soap"]["assessment"],

            # Workflow
            status="PENDING_REVIEW"
        )

        db.add(new_case)
        db.flush()

        # 4. Record assessment generation in audit log

        audit_entry = AuditLog(
            case_id=new_case.id,
            actor_role="AI_ENGINE",
            action="ASSESSMENT_GENERATED",
            previous_value=None,
            new_value=(
                ml_assessment["triage_tier"]
                if ml_assessment
                else "ASSESSMENT_INCOMPLETE"
            ),
            comment=(
                f"Experimental ML assessment generated. "
                f"Independent safety alerts: "
                f"{safety_assessment['alert_count']}. "
                f"Human supervisor review required."
            )
        )

        db.add(audit_entry)

        # 5. Commit database transaction

        db.commit()
        db.refresh(new_case)

        # 6. Return assessment

        return {
            "message": "Patient case created successfully.",
            "case_id": new_case.id,
            "status": new_case.status,
            "assessment": assessment
        }

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to create patient case: {str(error)}"
        )
