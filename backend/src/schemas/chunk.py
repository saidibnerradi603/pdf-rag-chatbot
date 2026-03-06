from typing import List
from pydantic import BaseModel, Field


class MarkdownPage(BaseModel):
    page_number: int = Field(..., ge=1)
    markdown: str = Field(default="")


class ChunkRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    markdown_pages: List[MarkdownPage] = Field(..., min_length=1)


class ChunkMetadata(BaseModel):
    file_name: str = Field(...)
    page_number: int = Field(..., ge=1)


class Chunk(BaseModel):
    page_content: str = Field(..., min_length=1)
    metadata: ChunkMetadata


class ChunkResponse(BaseModel):
    chunks:List[Chunk]
    @property
    def count(self) -> int:
        return len(self.chunks)