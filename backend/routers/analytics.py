
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from dependencies import get_db
from models import Case


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

VALID_TIERS = ["Routine", "Urgent", "Emergent"]

REVIEWED_STATUSES = [
    "APPROVED_FOR_DOCTOR",
    "COMPLETED"
]


# -----------------------------------------
# 1. Overall analytics summary
# -----------------------------------------

@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db)
):
    """
    Retrieve overall case and workflow statistics.
    """

    total_cases = db.query(func.count(Case.id)).scalar() or 0

    pending_reviews = (
        db.query(func.count(Case.id))
        .filter(Case.status == "PENDING_REVIEW")
        .scalar() or 0
    )

    approved_cases = (
        db.query(func.count(Case.id))
        .filter(Case.status == "APPROVED_FOR_DOCTOR")
        .scalar() or 0
    )

    completed_cases = (
        db.query(func.count(Case.id))
        .filter(Case.status == "COMPLETED")
        .scalar() or 0
    )

    reviewed_cases = approved_cases + completed_cases

    return {
        "total_cases": total_cases,
        "pending_reviews": pending_reviews,
        "approved_for_doctor": approved_cases,
        "completed_cases": completed_cases,
        "total_reviewed_cases": reviewed_cases
    }


# -----------------------------------------
# 2. AI-supervisor discordance analysis
# -----------------------------------------

@router.get("/discordance")
def get_discordance_analytics(
    db: Session = Depends(get_db)
):
    """
    Calculate the percentage of reviewed cases
    where the supervisor changed the AI prediction.

    Cases without an AI prediction are excluded.
    """

    reviewed_cases = (
        db.query(Case)
        .filter(
            Case.status.in_(REVIEWED_STATUSES),
            Case.ai_triage_tier.isnot(None),
            Case.human_verified_tier.isnot(None)
        )
        .all()
    )

    total_reviewed = len(reviewed_cases)

    discordant_cases = [
        item for item in reviewed_cases
        if item.ai_triage_tier != item.human_verified_tier
    ]

    total_discordant = len(discordant_cases)

    discordance_rate = (
        (total_discordant / total_reviewed) * 100
        if total_reviewed > 0
        else 0.0
    )

    return {
        "total_reviewed_cases_with_ai_prediction": total_reviewed,
        "total_discordant_cases": total_discordant,
        "total_agreement_cases": total_reviewed - total_discordant,
        "discordance_rate_percent": round(discordance_rate, 2),
        "agreement_rate_percent": round(
            100 - discordance_rate if total_reviewed > 0 else 0.0,
            2
        ),
        "discordant_case_ids": [
            item.id for item in discordant_cases
        ],
        "interpretation": (
            "Percentage of reviewed cases where the "
            "supervisor-verified tier differs from the AI tier."
        )
    }


# -----------------------------------------
# 3. AI and supervisor triage distribution
# -----------------------------------------

@router.get("/triage-distribution")
def get_triage_distribution(
    db: Session = Depends(get_db)
):
    """
    Compare AI-generated and supervisor-verified
    triage tier distributions.
    """

    all_cases = db.query(Case).all()

    ai_distribution = {
        tier: 0 for tier in VALID_TIERS
    }

    supervisor_distribution = {
        tier: 0 for tier in VALID_TIERS
    }

    for item in all_cases:

        if item.ai_triage_tier in ai_distribution:
            ai_distribution[item.ai_triage_tier] += 1

        if item.human_verified_tier in supervisor_distribution:
            supervisor_distribution[item.human_verified_tier] += 1

    total_ai_predictions = sum(ai_distribution.values())

    total_supervisor_reviews = sum(
        supervisor_distribution.values()
    )

    def calculate_percentages(distribution, total):
        return {
            tier: round(
                (count / total) * 100, 2
            ) if total > 0 else 0.0
            for tier, count in distribution.items()
        }

    return {
        "ai_distribution": {
            "total_predictions": total_ai_predictions,
            "counts": ai_distribution,
            "percentages": calculate_percentages(
                ai_distribution,
                total_ai_predictions
            )
        },

        "supervisor_distribution": {
            "total_verified_cases": total_supervisor_reviews,
            "counts": supervisor_distribution,
            "percentages": calculate_percentages(
                supervisor_distribution,
                total_supervisor_reviews
            )
        }
    }
