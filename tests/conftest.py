import os
import pytest
from fastapi.testclient import TestClient
import tempfile
from dotenv import load_dotenv

from app.main import app

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_env_vars():
    # Create temporary directories for testing
    temp_vectordb = tempfile.mkdtemp()
    temp_raw_data = tempfile.mkdtemp()
    temp_processed_data = tempfile.mkdtemp()

    # Store original environment variables
    original_env = {
        'VECTORDB_PATH': os.getenv('VECTORDB_PATH'),
        'RAW_DATA_PATH': os.getenv('RAW_DATA_PATH'),
        'PROCESSED_DATA_PATH': os.getenv('PROCESSED_DATA_PATH')
    }

    # Set temporary paths for testing
    os.environ['VECTORDB_PATH'] = temp_vectordb
    os.environ['RAW_DATA_PATH'] = temp_raw_data
    os.environ['PROCESSED_DATA_PATH'] = temp_processed_data

    yield
    
    # Clean up temporary directories
    for path in [temp_vectordb, temp_raw_data, temp_processed_data]:
        try:
            os.rmdir(path)
        except:
            pass
