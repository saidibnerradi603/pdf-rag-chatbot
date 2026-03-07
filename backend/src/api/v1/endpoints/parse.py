from fastapi import APIRouter, Depends, HTTPException, status, Path
from src.schemas.parse import ParsePDFOptions, ParsePDFResponse
from src.schemas.auth import UserResponse
from src.services.parse_service import ParseService
from src.api.dependencies import get_current_user  , get_parse_service

router = APIRouter()

@router.post(
    "/{document_id}/parse",
    response_model=ParsePDFResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
    summary="Parse a stored PDF into structured markdown or text",
)
async def parse_pdf(
    document_id: str = Path(..., description="UUID of the document"),
    options: ParsePDFOptions = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    parse_service: ParseService = Depends(get_parse_service)
) -> ParsePDFResponse:
    """
    Submits the stored PDF to **LlamaParse** and returns a structured parse result.

    This is an individual pipeline step — it is called automatically by `POST /{document_id}/process`.
    Use this endpoint directly only for debugging or custom pipelines.

    **Path parameter:**
    - `document_id` — UUID of the document to parse

    **Options (query parameters from `ParsePDFOptions`):**
    - `output_format` — `markdown` (default), `text`, or `all`
    - `tier` — LlamaParse quality tier (e.g., `cost_effective` , `agentic`)
    - `max_pages` / `target_pages` — limit or target specific page ranges
    - `parsing_instruction` — custom prompt for agentic parsing
    - `output_tables_as_markdown` — render tables in markdown format
    - `ignore_diagonal_text` / `ignore_text_in_image` — skip noisy content
    - `invalidate_cache` — force a fresh parse even if cached

    **Returns:** `ParsePDFResponse` with job metadata, page count, and parsed `markdown_pages` and/or `text_pages`.

    """
    try:
        
        return await parse_service.parse_pdf(
            options=options,
            document_id=document_id,
            user_id=current_user.id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing your document : {str(e)}",
        )
