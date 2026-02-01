from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
# from app.core.database import create_db_and_tables  # Not needed with Alembic
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Database tables are managed by Alembic migrations
    # Run: alembic upgrade head
    # No need to call create_db_and_tables() when using Alembic
    
    yield
    
    # Shutdown: Add cleanup logic here if needed


app = FastAPI(
    title=settings.app_name,
    description="API for managing employee data and efficiency metrics",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
# Configured for development - allows frontend on localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "version": settings.app_version,
    }
