from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    DB_SCHEMA: Optional[str] = None  # Database schema name (e.g., 'myapp', 'public')
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    PRESENTATION_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Gemini for presentations
    AGENT_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Model for agents (dashboard, analysis, etc.)
    VISION_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Model for vision tasks (color extraction, etc.)
    IMAGE_GEN_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Model for image generation (infographics)
    ENVIRONMENT: str = "development"

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATA_DIR: str = "data"
    DATASETS_DIR: str = "data/datasets"
    QUERIES_DIR: str = "data/queries"
    EMBEDDINGS_DIR: str = "data/embeddings"
    MODELS_DIR: str = "data/models"
    CODE_EXECUTIONS_DIR: str = "data/executions"

    MAX_UPLOAD_SIZE_MB: int = 100
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_QUERY_ROWS: int = 100000

    # Python execution settings
    PYTHON_EXECUTION_TIMEOUT_SECONDS: int = 120
    PYTHON_MAX_MEMORY_MB: int = 1024
    ENABLE_PYTHON_EXECUTION: bool = True

    # Email / SMTP settings (optional — if not set, reset links are logged to console)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM_ADDRESS: str = "noreply@example.com"
    EMAIL_FROM_NAME: str = "Felix Analytics"
    FRONTEND_URL: str = "http://localhost:5173"  # Used to build reset password links

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like HF_HUB_OFFLINE


settings = Settings()
