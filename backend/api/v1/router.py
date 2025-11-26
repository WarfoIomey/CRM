from fastapi import APIRouter
from .routes import (
    auth,
    analytics,
    deals,
    organizations,
    contacts,
    tasks
)


api_router = APIRouter(prefix="/v1")

api_router.include_router(auth.router)
api_router.include_router(analytics.router)
api_router.include_router(organizations.router)
api_router.include_router(contacts.router)
api_router.include_router(deals.router)
api_router.include_router(tasks.router)
