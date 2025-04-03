import pytest
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import os
from app.services.rag_pipeline import RAGPipeline

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_query_endpoint():
    query_data = {"text": "What is RAG?"}
    response = client.post("/api/query", json=query_data)
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()
    assert "confidence" in response.json()

def test_document_ingestion():
    # Create a temporary CSV file for testing
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tf:
        tf.write(b"col1,col2\ntest data,more test data")
        temp_file_path = tf.name

    try:
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/ingest/document",
                files={"file": ("test.csv", f, "text/csv")}
            )
        assert response.status_code == 200
        assert response.json()["num_documents"] == 1
        assert response.json()["file_type"] == "csv"

        # Test querying the ingested document
        query_data = {"text": "What is the test data?"}
        response = client.post("/api/query", json=query_data)
        assert response.status_code == 200
        assert "answer" in response.json()
        assert "sources" in response.json()
        assert len(response.json()["sources"]) > 0
    finally:
        os.unlink(temp_file_path)
