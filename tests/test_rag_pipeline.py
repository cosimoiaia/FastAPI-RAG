import pytest
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import os
from unittest.mock import patch
from app.services.rag_pipeline import RAGPipeline

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch.object(RAGPipeline, '_create_workflow')
def test_query_endpoint(mock_workflow):
    # Mock the workflow response
    mock_workflow.return_value.invoke.return_value = {
        "messages": [{"content": "Test response"}],
        "context": "Test context",
        "query": "What is RAG?"
    }
    
    query_data = {"text": "What is RAG?"}
    response = client.post("/api/query", json=query_data)
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()
    assert "confidence" in response.json()

@patch.object(RAGPipeline, 'ingest_document')
def test_document_ingestion(mock_ingest):
    # Mock the ingest_document response
    mock_ingest.return_value = {
        "num_documents": 1,
        "file_type": "csv"
    }
    
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
        assert "message" in response.json()
        assert response.json()["message"] == "Document ingested successfully"
    finally:
        os.unlink(temp_file_path)
