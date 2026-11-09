
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case

from dependencies import get_db, require_roles
from models import Case, AuditLog
from schemas import DoctorComplete


router = APIRouter(
    prefix="/cases",
    tags=["Doctor"]
)


# -----------------------------------------
# 1. Doctor queue
# -----------------------------------------

@router.get("/queue")
def get_doctor_queue(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("doctor", "admin")
    )
):
    """
    Retrieve supervisor-approved cases.
    Emergent cases appear first.
    """

    priority_order = case(
        (Case.human_verified_tier == "Emergent", 1),
        (Case.human_verified_tier == "Urgent", 2),
        (Case.human_verified_tier == "Routine", 3),
        else_=4
    )

    cases = (
        db.query(Case)
        .filter(Case.status == "APPROVED_FOR_DOCTOR")
        .order_by(priority_order, Case.created_at.asc())
        .all()
    )

    return {
        "total_cases": len(cases),
        "cases": [
            {
                "case_id": item.id,
                "patient_name": item.patient_name,
                "age": item.age,
                "gender": item.gender,
                "ai_triage_tier": item.ai_triage_tier,
                "human_verified_tier": item.human_verified_tier,
                "news2_score": item.news2_score,
                "syndrome_match": item.syndrome_match,
                "status": item.status,
                "created_at": item.created_at
            }
            for item in cases
        ]
    }


# -----------------------------------------
# 2. Doctor consultation completion
# -----------------------------------------

@router.post("/doctor/complete")
def complete_consultation(
    consultation: DoctorComplete,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("doctor", "admin")
    )
):

    patient_case = (
        db.query(Case)
        .filter(Case.id == consultation.case_id)
        .first()
    )

    if not patient_case:
        raise HTTPException(
            status_code=404,
            detail="Patient case not found."
        )

    if patient_case.status != "APPROVED_FOR_DOCTOR":
        raise HTTPException(
            status_code=409,
            detail="Case is not available for doctor consultation."
        )

    notes = consultation.doctor_notes.strip()

    if not notes:
        raise HTTPException(
            status_code=400,
            detail="Doctor consultation notes cannot be empty."
        )

    previous_status = patient_case.status

    patient_case.doctor_notes = notes
    patient_case.referral_facility = consultation.referral_facility
    patient_case.status = "COMPLETED"

    audit_entry = AuditLog(
        case_id=patient_case.id,
        actor_role=current_user.role.upper(),
        action="CONSULTATION_COMPLETED",
        previous_value=previous_status,
        new_value="COMPLETED",
        comment=notes
    )

    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(patient_case)

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to complete consultation: {str(error)}"
        )

    return {
        "message": "Doctor consultation completed successfully.",
        "case_id": patient_case.id,
        "doctor_notes": patient_case.doctor_notes,
        "referral_facility": patient_case.referral_facility,
        "completed_by": current_user.full_name,
        "completed_by_role": current_user.role,
        "status": patient_case.status
    }


# -----------------------------------------
# 3. Retrieve audit history
# -----------------------------------------

@router.get("/{case_id}/audit")
def get_case_audit_history(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("supervisor", "doctor", "admin")
    )
):
    """
    Retrieve the audit history of a patient case.
    Records are returned in chronological order.
    """

    patient_case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if not patient_case:
        raise HTTPException(
            status_code=404,
            detail="Patient case not found."
        )

    audit_records = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(
            AuditLog.timestamp.asc(),
            AuditLog.id.asc()
        )
        .all()
    )

    return {
        "case_id": patient_case.id,
        "patient_name": patient_case.patient_name,
        "current_status": patient_case.status,
        "total_audit_records": len(audit_records),
        "audit_history": [
            {
                "audit_id": record.id,
                "timestamp": record.timestamp,
                "actor_role": record.actor_role,
                "action": record.action,
                "previous_value": record.previous_value,
                "new_value": record.new_value,
                "comment": record.comment
            }
            for record in audit_records
        ]
    }


# -----------------------------------------
# 4. Retrieve individual case details
# -----------------------------------------

@router.get("/{case_id}")
def get_case_details(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("supervisor", "doctor", "admin")
    )
):

    patient_case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if not patient_case:
        raise HTTPException(
            status_code=404,
            detail="Patient case not found."
        )

    return {
        "case_id": patient_case.id,
        "patient_name": patient_case.patient_name,
        "age": patient_case.age,
        "gender": patient_case.gender,
        "raw_narrative": patient_case.raw_narrative,

        "vitals": {
            "heart_rate": patient_case.heart_rate,
            "resp_rate": patient_case.resp_rate,
            "systolic_bp": patient_case.systolic_bp,
            "spo2": patient_case.spo2,
            "temperature": patient_case.temperature
        },

        "clinical_analysis": {
            "entities": patient_case.extracted_entities,
            "red_flags": patient_case.detected_red_flags,
            "missing_fields": patient_case.missing_fields,
            "syndrome": patient_case.syndrome_match,
            "syndrome_similarity": patient_case.syndrome_similarity
        },

        "vital_assessment": {
            "five_parameter_score": patient_case.news2_score
        },

        "ai_triage_tier": patient_case.ai_triage_tier,
        "ai_confidence": patient_case.ai_confidence,
        "shap_explanation": patient_case.shap_explanation,

        "human_verified_tier": patient_case.human_verified_tier,
        "supervisor_comment": patient_case.supervisor_comment,

        "soap": {
            "subjective": patient_case.soap_subjective,
            "objective": patient_case.soap_objective,
            "assessment": patient_case.soap_assessment
        },

        "doctor_notes": patient_case.doctor_notes,
        "referral_facility": patient_case.referral_facility,
        "status": patient_case.status,
        "created_at": patient_case.created_at
    }
