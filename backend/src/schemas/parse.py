from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ParsingTier(str, Enum):
    FAST = "fast"
    COST_EFFECTIVE = "cost_effective"
    AGENTIC = "agentic"
    AGENTIC_PLUS = "agentic_plus"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    TEXT = "text"
    ALL = "all"


class ParsePDFOptions(BaseModel):
    tier: ParsingTier = Field(
        default=ParsingTier.COST_EFFECTIVE,
        description="Parsing tier: fast, cost_effective, agentic, or agentic_plus",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format: markdown, text or all",
    )
    invalidate_cache: bool = Field(
        default=False,
        description="Force re-parse even if a cached result exists",
    )
    max_pages: Optional[int] = Field(
        default=None,
        description="Maximum number of pages to process",
        ge=1
    )
    target_pages: Optional[str] = Field(
        default=None,
        description="Specific pages to process (e.g., '1,3,5-10')"
    )
    parsing_instruction: Optional[str] = Field(
        default=None,
        description="Custom parsing instruction for agentic tiers"
    )
    output_tables_as_markdown: bool = Field(
        default=True,
        description="Output table as markdown"
    )
    ignore_diagonal_text: bool = Field(
        default=False,
        description="Ignore diagonal text"
    )
    ignore_text_in_image: bool = Field(
        default=False,
        description="Ignore text in images"
    )
    
    
    model_config = ConfigDict(
        json_schema_extra=lambda schema, model: schema.update(
            example=model().model_dump()
        )
    )


class MarkdownPage(BaseModel):
    page_number: int = Field(description="Page number (1-based)")
    markdown: str = Field(description="Markdown content of the page")


class TextPage(BaseModel):
    page_number: int = Field(description="Page number (1-based)")
    text: str = Field(description="Plain text content of the page")


class ParsePDFResponse(BaseModel):
    job_id: str = Field(description="LlamaParse job ID")
    status: str = Field(description="Job status")
    created_at: datetime = Field(description="When the job was created")
    completed_at: Optional[datetime] = Field(
        default=None, description="When the job finished"
    )

    file_name: Optional[str] = Field(default=None)
    total_pages: Optional[int] = Field(default=None)
    tier_used: ParsingTier = Field(description="Tier that was used")

    markdown_pages: Optional[List[MarkdownPage]] = Field(default=None)
    text_pages: Optional[List[TextPage]] = Field(default=None)
    
    
    error_message: Optional[str] = Field(default=None)

    model_config = ConfigDict(
        exclude_none=True,
    )
