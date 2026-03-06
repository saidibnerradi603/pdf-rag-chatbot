from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ConversationCreate(BaseModel):
    document_id: str = Field(..., description="UUID of the document to chat about")
    title: Optional[str] = Field(default="Untitled", description="Optional conversation title")


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    document_id: str
    title: str
    created_at: datetime



class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime



class CitationResponse(BaseModel):
    id: str
    chunk_id: str
    cited_text: str
    metadata: dict
    similarity_score: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question")
    top_k: int = Field(default=10, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.2, ge=0.0, le=1.0, description="Minimum similarity score")


class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    user_message: str
    assistant_message: str
    citations: List[CitationResponse]
    created_at: datetime



class MessageWithCitations(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    citations: Optional[List[CitationResponse]] = None


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    document_id: str
    title: str
    messages: List[MessageWithCitations]
