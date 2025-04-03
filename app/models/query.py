from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    text: str
    
class Source(BaseModel):
    document_id: str
    content: str
    relevance_score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
