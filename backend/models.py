
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Patient information
    patient_name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(30), nullable=False)

    # Original patient complaint
    raw_narrative = Column(Text, nullable=False)

    # Vital signs
    heart_rate = Column(Integer, nullable=True)
    resp_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)

    # NLP results
    extracted_entities = Column(JSON, default=list)
    detected_red_flags = Column(JSON, default=dict)
    missing_fields = Column(JSON, default=list)

    syndrome_match = Column(String(150), nullable=True)
    syndrome_similarity = Column(Float, nullable=True)

    # NEWS2 and ML results
    news2_score = Column(Integer, nullable=True)
    shap_explanation = Column(JSON, default=list)

    ai_triage_tier = Column(String(50), nullable=True)
    ai_confidence = Column(Float, nullable=True)

    # SOAP notes
    soap_subjective = Column(Text, nullable=True)
    soap_objective = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)

    # Supervisor review
    human_verified_tier = Column(String(50), nullable=True)
    supervisor_comment = Column(Text, nullable=True)
    supervisor_action = Column(String(30), nullable=True)

    # Doctor consultation
    doctor_notes = Column(Text, nullable=True)
    referral_facility = Column(String(200), nullable=True)

    # Case workflow
    status = Column(
        String(50),
        nullable=False,
        default="PENDING_REVIEW"
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="case",
        cascade="all, delete-orphan"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    actor_role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False)

    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)

    case = relationship(
        "Case",
        back_populates="audit_logs"
    )
