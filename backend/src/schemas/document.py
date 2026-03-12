from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: str
    file_name: str
    bucket_path: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    message: str = "Document uploaded successfully"


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    metadata: dict = {}
    suggested_questions: list[str] = []





class DocumentStatusResponse(BaseModel):
    id: str
    status: Literal["pending", "processing", "completed", "failed"]