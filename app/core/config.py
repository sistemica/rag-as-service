from pydantic_settings import BaseSettings
from enum import Enum
from typing import Literal, Optional

class EmbeddingProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Service"
    # Database
    POSTGRES_USER: str = "raguser"
    POSTGRES_PASSWORD: str = "ragpass"
    POSTGRES_DB: str = "ragdb"
    DATABASE_URL: str = "postgresql://raguser:ragpass@db:5432/ragdb"

    # Embedding configuration
    EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.OLLAMA
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 1536  # Default to OpenAI's dimension
    OLLAMA_EMBEDDING_DIMENSION: int = 768  # Ollama's default dimension
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Optional OpenAI configuration (only needed if using OpenAI provider)
    OPENAI_API_KEY: Optional[str] = None

    # App configuration
    LOG_LEVEL: str = "DEBUG"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()
