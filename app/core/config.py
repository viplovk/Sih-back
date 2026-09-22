"""Application configuration management using Pydantic Settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for ALGORIOT Backend."""

    APP_NAME: str = Field(default="Algoriot Backend")
    SERVICE_NAME: str = Field(default="algoriot-backend")
    VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="production")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=3000)

    # Frontend integration
    FRONTEND_URL: str = Field(default="https://sih-fr-v.vercel.app")
    PRODUCTION_FRONTEND_URL: str = Field(default="https://sih-fr-v.vercel.app")

    # Data provider endpoints (Open-Meteo is open and does not require an API key)
    OPEN_METEO_BASE_URL: str = Field(default="https://api.open-meteo.com")
    OPEN_METEO_AIR_QUALITY: str = Field(default="https://air-quality-api.open-meteo.com")
    OPEN_METEO_AIR_QUALITY_BASE_URL: Optional[str] = Field(default=None)

    # Operational modes (Production uses real data, no demo mocks)
    USE_DEMO_MODE: bool = Field(default=False)

    # Optional services (Completely optional; backend operates in-memory when absent)
    DATABASE_URL: Optional[str] = Field(default=None)
    REDIS_URL: Optional[str] = Field(default=None)

    # Observability
    LOG_LEVEL: str = Field(default="INFO")

    # Cache TTL in seconds (In-memory cache)
    CACHE_TTL_SECONDS: int = Field(default=600)
    LIVE_CACHE_TTL_SECONDS: int = Field(default=60)
    MAP_CACHE_TTL_SECONDS: int = Field(default=300)
    GRID_CACHE_TTL_SECONDS: int = Field(default=600)
    AIR_QUALITY_CACHE_TTL_SECONDS: int = Field(default=900)

    @property
    def air_quality_url(self) -> str:
        """Resolve Air Quality base URL without treating it as an API key."""
        return (
            self.OPEN_METEO_AIR_QUALITY_BASE_URL
            or self.OPEN_METEO_AIR_QUALITY
            or "https://air-quality-api.open-meteo.com"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cors_origins(self) -> List[str]:
        """Construct deterministic allowed CORS origins."""
        origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "https://sih-fr-v.vercel.app",
        ]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        if self.PRODUCTION_FRONTEND_URL and self.PRODUCTION_FRONTEND_URL not in origins:
            origins.append(self.PRODUCTION_FRONTEND_URL)
        return origins


settings = Settings()
