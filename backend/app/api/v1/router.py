"""Aggregate router for API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    chat,
    counseling,
    health,
    ml,
    predictions,
    recommendations,
    reports,
    students,
    uploads,
    users,
)


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(students.router)
api_router.include_router(uploads.router)
api_router.include_router(predictions.router)
api_router.include_router(ml.router)
api_router.include_router(recommendations.router)
api_router.include_router(counseling.router)
api_router.include_router(analytics.router)
api_router.include_router(reports.router)
api_router.include_router(chat.router)
