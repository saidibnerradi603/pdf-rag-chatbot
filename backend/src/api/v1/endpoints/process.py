from fastapi import APIRouter, Depends, Path, status
from src.schemas.process import ProcessRequest, ProcessResponse
from src.schemas.auth import UserResponse
from src.services.process_service import ProcessService
from src.api.dependencies import get_current_user, get_process_service

router = APIRouter()


@router.post(
    "/{document_id}/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger the full RAG ingestion pipeline for a document",
)
async def process_document(
    request: ProcessRequest,
    document_id: str = Path(..., description="UUID of the document to process"),
    current_user: UserResponse = Depends(get_current_user),
    process_service: ProcessService = Depends(get_process_service),
) -> ProcessResponse:
    """
    Runs the complete **parse → chunk → embed → store** pipeline for a previously uploaded document.

    **Pipeline steps:**
    1. Validates the document status (rejects if already `processing` or `completed`)
    2. Marks the document as `processing`
    3. Submits the PDF to LlamaParse and waits for the result
    4. Splits the parsed markdown into chunks
    5. Embeds the chunks with Cohere and stores them in the vector store
    6. Marks the document as `completed`

    If any step fails, the document is marked as `failed` and an appropriate error is returned.

    **Path parameter:**
    - `document_id` — UUID of the document to process

    **Body (`ProcessRequest`):**
    | Field | Default | Description |
    |---|---|---|
    | `parse_options` | `ParsePDFOptions()` | Parsing configuration (tier, format, etc.) |
    | `chunk_size` | `1500` | Max characters per chunk (≥ 100) |
    | `chunk_overlap` | `150` | Overlap between adjacent chunks (≥ 0) |

    **Returns:** `ProcessResponse` with `status`, `pages_parsed`, and `chunks_stored` on success.

    """
    return await process_service.run_pipeline(
        document_id=document_id,
        user_id=current_user.id,
        request=request,
    )