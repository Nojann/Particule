from fastapi import APIRouter
from app.api.v1 import knowledge_base

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(knowledge_base.router)
#api_router.include_router(user.router)