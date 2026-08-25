from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.payments import router as payments_router
from app.api.customers import router as customers_router
from app.api.recovery_cases import router as recovery_cases_router
from app.api.analytics import router as analytics_router
from app.api.ml_prediction import router as ml_prediction_router
from app.api.ai_agent import router as ai_agent_router
from app.api.simulator import router as simulator_router
from app.api.memory import router as memory_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(payments_router)
api_router.include_router(customers_router)
api_router.include_router(recovery_cases_router)
api_router.include_router(analytics_router)
api_router.include_router(ml_prediction_router)
api_router.include_router(ai_agent_router)
api_router.include_router(simulator_router)
api_router.include_router(memory_router)
