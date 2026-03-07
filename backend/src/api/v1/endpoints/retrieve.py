from fastapi import APIRouter, Depends, Path, status
from src.schemas.retrieval import RetrievalRequest, RetrievalResponse
from src.schemas.auth import UserResponse
from src.services.retrieval_service import RetrievalService
from src.api.dependencies import get_current_user, get_retrieval_service

router = APIRouter()

@router.post(
    "/{document_id}/retrieve", 
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Run a semantic vector search over a document's embedded chunks"
)
async def retrieve_document_context(
    document_id: str = Path(..., description="UUID of the document"),
    request: RetrievalRequest = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
) -> RetrievalResponse:
    """
    Performs a **cosine-similarity vector search** against the embedded chunks of a specific document.
    
    Primarily used for debugging retrieval quality before or independently of the chat interface.

    **Path parameter:**
    - `document_id` — UUID of the document to search within

    **Body / Query (`RetrievalRequest`):**
    | Field | Default | Description |
    |---|---|---|
    | `query` | *(required)* | Natural language question or search phrase |
    | `top_k` | `10` | Maximum number of chunks to return (1–20) |
    | `similarity_threshold` | `0.2` | Minimum cosine similarity score (0.0–1.0) |

    **Returns:** `RetrievalResponse` with the original `query` and a list of `RetrievedChunk` objects, each containing the matched `content`, `metadata` (file name, page number), and `similarity` score.

    """
    return await retrieval_service.retrieve_context(
        document_id=document_id,
        user_id=current_user.id,
        request=request
    )