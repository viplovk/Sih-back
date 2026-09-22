"""ALGORIOT Backend - Hybrid AI-NWP Multi-Model Forecast Blending System.

SIH Problem Statement: SIH26081
Theme: Disaster Management
Repository: viplovk/Sih-back
Frontend: https://github.com/viplovk/SIH-Frontend
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AlgoriotException
from app.providers.open_meteo import open_meteo_client

# Route imports
from app.api.health import router as health_router
from app.api.weather import router as weather_router
from app.api.forecast import router as forecast_router
from app.api.models import router as models_router
from app.api.extremes import router as extremes_router
from app.api.uncertainty import router as uncertainty_router
from app.api.map import router as map_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application startup and clean resource shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    yield
    logger.info("Shutting down ALGORIOT backend resources...")
    await open_meteo_client.close()


app = FastAPI(
    title="ALGORIOT - Hybrid AI-NWP Multi-Model Forecast Blending System",
    description=(
        "Production-ready backend for SIH26081 (Disaster Management). "
        "Integrates operational NWP, physics-based simulations, and foundation AI weather models "
        "using atmospheric regime detection, dynamic meta-learner weighting, and ensemble uncertainty calibration."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Structured Request Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()

    # Process request
    try:
        response = await call_next(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} completed with status {response.status_code} in {latency_ms}ms [req_id={request_id}]"
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"{request.method} {request.url.path} unhandled error after {latency_ms}ms: {exc} [req_id={request_id}]"
        )
        raise exc


# Exception Handlers
@app.exception_handler(AlgoriotException)
async def algoriot_exception_handler(request: Request, exc: AlgoriotException):
    return exc.to_response()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "request_id": req_id,
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception(f"Unhandled server error [req_id={req_id}]: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred",
                "request_id": req_id,
            }
        },
    )


# Root entrypoint
@app.get("/", tags=["Root"])
async def root():
    """Return backend status and architectural manifest."""
    return {
        "project": "ALGORIOT",
        "sih_problem_statement": "SIH26081",
        "title": "Hybrid AI-NWP Multi-Model Forecast Blending System",
        "theme": "Disaster Management",
        "status": "online",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "frontend_repository": "https://github.com/viplovk/SIH-Frontend",
        "endpoints": {
            "health": "/api/v1/health",
            "weather": "/api/v1/weather",
            "forecast": "/api/v1/forecast",
            "models": "/api/v1/models",
            "models_contribution": "/api/v1/models/contribution",
            "extremes": "/api/v1/extremes",
            "uncertainty": "/api/v1/uncertainty",
            "map_timeline": "/api/v1/map/timeline",
            "map_wind": "/api/v1/map/wind",
            "map_temperature": "/api/v1/map/temperature",
            "map_precipitation": "/api/v1/map/precipitation",
            "map_air_quality": "/api/v1/map/air-quality",
        },
    }


# Include sub-routers
app.include_router(health_router)
app.include_router(weather_router)
app.include_router(forecast_router)
app.include_router(models_router)
app.include_router(extremes_router)
app.include_router(uncertainty_router)
app.include_router(map_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
