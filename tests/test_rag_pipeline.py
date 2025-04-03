import pytest
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.services.rag_pipeline import RAGPipeline

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch('app.services.rag_pipeline.ChatGroq')
@patch('app.services.rag_pipeline.HuggingFaceEmbeddings')
def test_query_endpoint_with_context(mock_embeddings, mock_chat):
    """Test query endpoint with context retrieval"""
    # Mock embeddings
    mock_embeddings_instance = MagicMock()
    mock_embeddings.return_value = mock_embeddings_instance
    mock_embeddings_instance.embed_query.return_value = [0.1] * 384  # MiniLM embedding size
    mock_embeddings_instance.embed_documents.return_value = [[0.1] * 384]  # Mock document embeddings
    
    # Mock chat completion
    mock_chat_instance = MagicMock()
    mock_chat.return_value = mock_chat_instance
    mock_chat_instance.invoke.return_value = "Test response based on context"
    
    # Test query with context
    query_data = {"text": "What is RAG?"}
    response = client.post("/api/query", json=query_data)
    
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()
    assert "confidence" in response.json()

@patch('app.services.rag_pipeline.HuggingFaceEmbeddings')
def test_structured_data_ingestion(mock_embeddings):
    """Test ingestion of structured data (CSV)"""
    
    with open("/home/mimmo/projects/igenius-rag/examples/nvda_stock_data.csv", "rb") as f:
        response = client.post(
            "/api/ingest/document",
            files={"file": ("nvda_stock_data.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "details" in response.json()


    # Test querying the ingested structured data
    query = {"text": "What was NVIDIA's stock price?"}
    response = client.post("/api/query", json=query)
    assert response.status_code == 200
    assert "answer" in response.json()

@patch('app.services.rag_pipeline.HuggingFaceEmbeddings')
def test_unstructured_data_ingestion(mock_embeddings):
    """Test ingestion of unstructured data (PDF)"""
    
    with open("/home/mimmo/projects/igenius-rag/examples/NVIDIAAn.pdf", "rb") as f:
        response = client.post(
            "/api/ingest/document",
            files={"file": ("NVIDIAAn.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "details" in response.json()

    # Test querying the ingested unstructured data
    query = {"text": "What is NVIDIA's business?"}
    response = client.post("/api/query", json=query)
    assert response.status_code == 200
    assert "answer" in response.json()

def test_error_handling():
    """Test error handling for invalid requests"""
    # Test invalid file type
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as tf:
        tf.write(b"invalid content")
        temp_file_path = tf.name

    try:
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/ingest/document",
                files={"file": ("test.exe", f, "application/octet-stream")}
            )
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Unsupported file type" in response.json()["detail"]
    finally:
        os.unlink(temp_file_path)

    # Test invalid query
    response = client.post("/api/query", json={})
    assert response.status_code == 422  # FastAPI validation error

