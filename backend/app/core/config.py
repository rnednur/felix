from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    DB_SCHEMA: Optional[str] = None  # Database schema name (e.g., 'myapp', 'public')
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    PRESENTATION_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Gemini for presentations
    ENVIRONMENT: str = "development"

    # Google Drive/Sheets Integration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

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

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like HF_HUB_OFFLINE


settings = Settings()
