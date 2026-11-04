
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# -----------------------------
# Patient vital signs
# -----------------------------

class Vitals(BaseModel):
    heart_rate: Optional[int] = Field(default=None, ge=0)
    resp_rate: Optional[int] = Field(default=None, ge=0)
    systolic_bp: Optional[int] = Field(default=None, ge=0)
    spo2: Optional[float] = Field(default=None, ge=0, le=100)
    temperature: Optional[float] = Field(default=None, ge=0)


# -----------------------------
# Patient intake
# -----------------------------

class CaseIntake(BaseModel):
    patient_name: str = Field(min_length=1, max_length=150)
    age: int = Field(ge=0, le=120)
    gender: str
    raw_narrative: str = Field(min_length=1)
    vitals: Vitals


# -----------------------------
# Supervisor review
# -----------------------------

class SupervisorReview(BaseModel):
    case_id: int
    verified_tier: str
    comment: str = Field(min_length=1)
    action: str


# -----------------------------
# Doctor consultation
# -----------------------------

class DoctorComplete(BaseModel):
    case_id: int
    doctor_notes: str = Field(min_length=1)
    referral_facility: Optional[str] = None


# -----------------------------
# Audit log response
# -----------------------------

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    timestamp: Optional[datetime] = None
    actor_role: str
    action: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None


# -----------------------------
# Case summary response
# -----------------------------

class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: str
    age: int
    gender: str
    news2_score: Optional[int] = None
    ai_triage_tier: Optional[str] = None
    human_verified_tier: Optional[str] = None
    status: str


# -----------------------------
# Analytics response
# -----------------------------

class AnalyticsSummary(BaseModel):
    total_cases: int
    emergent_count: int
    urgent_count: int
    routine_count: int
    override_count: int
    discordance_rate: float
    avg_news2: float
    pending_review: int
