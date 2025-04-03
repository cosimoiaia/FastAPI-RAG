from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "iGenius RAG"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # API Keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    
    # Vector Database
    VECTORDB_PATH: str = os.getenv("VECTORDB_PATH", "./data/vectordb")
    
    # Groq Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
    
    # Data Paths
    RAW_DATA_PATH: str = os.getenv("RAW_DATA_PATH", "./data/raw")
    PROCESSED_DATA_PATH: str = os.getenv("PROCESSED_DATA_PATH", "./data/processed")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
