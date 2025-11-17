import os
from pydantic import BaseSettings, Field, AnyUrl, field_validator

class Settings(BaseSettings):
    """
    Typed configuration loaded from environment variables or .env file.

    Required:
    - GOOGLE_API_KEY
    - API_KEY (for API authentication)

    Optional with defaults:
    - REDIS_URL (for caching)
    - VECTOR_DB_URL (for embeddings search)
    - MODEL_NAME (LLM model selection)
    """
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")
    API_KEY: str = Field(..., env="API_KEY")

    REDIS_URL: AnyUrl = Field("redis://localhost:6379", env="REDIS_URL")
    VECTOR_DB_URL: AnyUrl = Field("http://localhost:8000", env="VECTOR_DB_URL")

    MODEL_NAME: str = Field("gemini-pro", env="MODEL_NAME")
    MAX_TOKENS: int = Field(1024, env="MAX_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("GOOGLE_API_KEY", "API_KEY")
    def not_empty(cls, v, field):
        if not v or v.strip() == "":
            raise ValueError(f"{field.name} must not be empty")
        return v

settings = Settings()
