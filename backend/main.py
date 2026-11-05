
from fastapi import FastAPI

from routers.cases import router as cases_router
from routers.supervisor import router as supervisor_router
from routers.doctor import router as doctor_router
from routers.analytics import router as analytics_router


app = FastAPI(
    title="SmartTriage AI",
    description=(
        "AI-assisted clinical triage and referral "
        "management prototype."
    ),
    version="1.0.0"
)


# Register API routers
app.include_router(cases_router)
app.include_router(supervisor_router)
app.include_router(doctor_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "message": "SmartTriage AI API is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
