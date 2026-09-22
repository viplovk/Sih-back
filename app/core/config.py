"""Application configuration management using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for ALGORIOT Backend."""

    APP_NAME: str = Field(default="Algoriot Backend")
    SERVICE_NAME: str = Field(default="algoriot-backend")
    VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Frontend integration
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    PRODUCTION_FRONTEND_URL: str = Field(default="https://sih-fr-v.vercel.app")

    # Data provider endpoints
    OPEN_METEO_BASE_URL: str = Field(default="https://api.open-meteo.com")

    # Operational modes
    USE_DEMO_MODE: bool = Field(default=True)

    # Optional services
    DATABASE_URL: Optional[str] = Field(default=None)
    REDIS_URL: Optional[str] = Field(default=None)

    # Observability
    LOG_LEVEL: str = Field(default="INFO")

    # Cache TTL in seconds (10 minutes for weather forecasts)
    CACHE_TTL_SECONDS: int = Field(default=600)

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
