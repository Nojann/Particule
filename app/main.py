from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.models import *

from app.config import settings
from app.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    #create_db_and_tables()
    yield
    #shutdown

app = FastAPI(
    title=settings.project_name,
    #lifespan=lifespan
    #openapi_url
)

app.include_router(api_router)