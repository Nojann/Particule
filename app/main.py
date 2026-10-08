from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.models import *

#from app.api import api_router
from app.config import get_settings
from app.database import engine, create_db_and_tables

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    create_db_and_tables()
    yield
    #shutdown

app = FastAPI(
    title=settings.project_name,
    #lifespan=lifespan
    #openapi_url
)