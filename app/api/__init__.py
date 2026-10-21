from fastapi import APIRouter
from app.api.v1 import knowledge_base
from app.api.v1 import user
from app.api.v1 import login
from app.api.v1 import particule
from app.api.v1 import tag
from app.api.v1 import link
from app.api.v1 import source

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(knowledge_base.router)
api_router.include_router(particule.router)
api_router.include_router(tag.router)
api_router.include_router(link.router)
api_router.include_router(source.router)
api_router.include_router(user.router)
api_router.include_router(login.router)