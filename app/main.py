from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging_config import setup_logging

# Set up logging
logger = setup_logging()

app = FastAPI(
    title="iGenius RAG API",
    description="RAG Pipeline for Contextual Query Handling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RAG API")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Model: {settings.GROQ_MODEL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down RAG API")
