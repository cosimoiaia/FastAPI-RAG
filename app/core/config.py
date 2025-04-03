from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "iGenius RAG"
    
    # Vector Database
    VECTORDB_PATH: str = "./data/vectordb"
    
    # Groq Configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama2-70b-4096"
    
    # Data Paths
    RAW_DATA_PATH: str = "./data/raw"
    PROCESSED_DATA_PATH: str = "./data/processed"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
