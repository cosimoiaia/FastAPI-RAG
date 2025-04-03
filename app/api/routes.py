from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.models.query import QueryRequest, QueryResponse
from app.services.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()

@router.post("/query", response_model=QueryResponse)
async def process_query(query: QueryRequest):
    """
    Process a query using the RAG pipeline
    """
    try:
        response = await rag_pipeline.process_query(query.text)
        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            confidence=response["confidence"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a new document (PDF or CSV) into the vector database
    """
    try:
        result = await rag_pipeline.ingest_document(file)
        return {"message": "Document ingested successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
