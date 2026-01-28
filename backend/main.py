"""
Pixll - AI-Powered Data Analysis Platform
Main FastAPI Application Entry Point
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from routers import upload, clean, visualize
from models.schemas import HealthResponse

# Load environment variables
load_dotenv()

# In-memory session storage for uploaded data
# In production, use Redis or database
DATA_STORE = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("[Pixll] Backend Starting...")
    print(f"[AI] Gemini Model: {os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')}")
    
    # Create uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    yield
    
    # Shutdown
    print("[Pixll] Backend Shutting Down...")
    DATA_STORE.clear()

# Initialize FastAPI app
app = FastAPI(
    title="Pixll API",
    description="AI-Powered Data Analysis Platform - Upload, Clean, Visualize",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(clean.router, prefix="/api", tags=["Cleaning"])
app.include_router(visualize.router, prefix="/api", tags=["Visualization"])

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Welcome to Pixll - AI-Powered Data Analysis Platform",
        version="1.0.0"
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check"""
    api_key_set = bool(os.getenv("GOOGLE_API_KEY"))
    return HealthResponse(
        status="healthy" if api_key_set else "degraded",
        message="All systems operational" if api_key_set else "Google Gemini API key not configured",
        version="1.0.0"
    )

def get_data_store():
    """Get the shared data store - used by routers"""
    return DATA_STORE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true"
    )
