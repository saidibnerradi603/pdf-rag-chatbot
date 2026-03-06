from pydantic import BaseModel, Field
from src.schemas.parse import ParsePDFOptions

class ProcessRequest(BaseModel):
    parse_options: ParsePDFOptions = Field(default_factory=ParsePDFOptions)
    chunk_size: int = Field(default=2000, ge=100, description="Max characters per chunk")
    chunk_overlap: int = Field(default=200, ge=0, description="Overlap between chunks")

class ProcessResponse(BaseModel):
    message: str
    document_id: str
    status: str
    pages_parsed: int = 0
    chunks_stored: int = 0