from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # AI services
    GOOGLE_API_KEY: SecretStr = Field(..., description="Google api key")
    COHERE_API_KEY: SecretStr = Field(..., description="COHERE api key")
    LLAMA_CLOUD_API_KEY: SecretStr = Field(..., description="Llama cloud api key")
    
    # Application Settings
    APP_NAME: str = "PDF RAG QA System"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: SecretStr = Field(..., description="Supabase anon/public key")

    # JWT Configuration
    ALGORITHM: str = "ES256"

    # CORS Settings
    BACKEND_CORS_ORIGIN: str = Field("http://localhost:3000", description="Allowed CORS origins for the backend API.")
    
    # File Upload settings
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf"]
    STORAGE_BUCKET_NAME: str = "pdfs"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
