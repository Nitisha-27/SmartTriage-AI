
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Case, AuditLog
from schemas import SupervisorReview


router = APIRouter(
    prefix="/cases",
    tags=["Supervisor"]
)


VALID_TIERS = ["Routine", "Urgent", "Emergent"]


# -----------------------------------------
# 1. Retrieve pending cases
# -----------------------------------------

@router.get("/pending")
def get_pending_cases(
    db: Session = Depends(get_db)
):
    cases = (
        db.query(Case)
        .filter(Case.status == "PENDING_REVIEW")
        .order_by(Case.created_at.asc())
        .all()
    )

    return {
        "total_pending": len(cases),
        "cases": [
            {
                "case_id": case.id,
                "patient_name": case.patient_name,
                "age": case.age,
                "gender": case.gender,
                "raw_narrative": case.raw_narrative,
                "ai_triage_tier": case.ai_triage_tier,
                "ai_confidence": case.ai_confidence,
                "syndrome_match": case.syndrome_match,
                "syndrome_similarity": case.syndrome_similarity,
                "news2_score": case.news2_score,
                "detected_red_flags": case.detected_red_flags,
                "missing_fields": case.missing_fields,
                "shap_explanation": case.shap_explanation,
                "status": case.status,
                "created_at": case.created_at
            }
            for case in cases
        ]
    }


# -----------------------------------------
# 2. Supervisor approval / override
# -----------------------------------------

@router.post("/supervisor/review")
def review_case(
    review: SupervisorReview,
    db: Session = Depends(get_db)
):

    # Find patient case

    case = db.query(Case).filter(
        Case.id == review.case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Patient case not found."
        )

    # Ensure case is awaiting review

    if case.status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="This case has already been reviewed."
        )

    # Validate action

    action = review.action.strip().upper()

    if action not in ["APPROVE", "OVERRIDE"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be APPROVE or OVERRIDE."
        )

    # Validate supervisor-selected tier

    verified_tier = review.verified_tier.strip().capitalize()

    if verified_tier not in VALID_TIERS:
        raise HTTPException(
            status_code=400,
            detail="Tier must be Routine, Urgent, or Emergent."
        )

    comment = review.comment.strip()

    if not comment:
        raise HTTPException(
            status_code=400,
            detail="Supervisor comment is mandatory."
        )

    # Approval must retain the AI tier

    if action == "APPROVE":

        if not case.ai_triage_tier:
            raise HTTPException(
                status_code=400,
                detail="Cannot approve: AI triage prediction is unavailable."
            )

        if verified_tier != case.ai_triage_tier:
            raise HTTPException(
                status_code=400,
                detail="Approved tier must match the AI-suggested tier. Use OVERRIDE to change it."
            )

    # Override must change the suggested tier

    if action == "OVERRIDE":

        if verified_tier == case.ai_triage_tier:
            raise HTTPException(
                status_code=400,
                detail="Override tier must differ from the AI-suggested tier."
            )

    previous_tier = case.ai_triage_tier or "NO_AI_PREDICTION"

    # Save supervisor decision

    case.human_verified_tier = verified_tier
    case.supervisor_comment = comment
    case.supervisor_action = action
    case.status = "APPROVED_FOR_DOCTOR"

    # Create audit record

    audit_entry = AuditLog(
        case_id=case.id,
        actor_role="SUPERVISOR",
        action=(
            "SUPERVISOR_APPROVED"
            if action == "APPROVE"
            else "SUPERVISOR_OVERRIDDEN"
        ),
        previous_value=previous_tier,
        new_value=verified_tier,
        comment=comment
    )

    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(case)

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save supervisor review: {str(error)}"
        )

    return {
        "message": "Supervisor review completed successfully.",
        "case_id": case.id,
        "ai_triage_tier": case.ai_triage_tier,
        "human_verified_tier": case.human_verified_tier,
        "supervisor_action": case.supervisor_action,
        "supervisor_comment": case.supervisor_comment,
        "status": case.status
    }
