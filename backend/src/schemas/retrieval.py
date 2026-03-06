from pydantic import BaseModel, Field
from typing import List
from src.schemas.chunk import ChunkMetadata


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user question")
    top_k: int = Field(default=10, ge=1, le=20, description="How many chunks to retrieve")
    similarity_threshold : float = Field(default=0.2, ge=0.0, le=1.0, description="Minimum similarity score")

class RetrievedChunk(BaseModel):
    id: str
    content: str
    metadata: ChunkMetadata
    similarity: float

class RetrievalResponse(BaseModel):
    query: str
    results: List[RetrievedChunk]