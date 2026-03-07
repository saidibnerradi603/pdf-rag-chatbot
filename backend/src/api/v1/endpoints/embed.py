from fastapi import APIRouter, Depends, HTTPException, status,Path
from src.schemas.chunk import  ChunkResponse
from src.services.embed_service import EmbedService
from src.api.dependencies import get_current_user, get_embed_service


router = APIRouter()
@router.post(
    "/{document_id}/embed",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    summary="Embed chunks and store them as vectors in the database"
)
async def embed_store(
    chunks: ChunkResponse,
    embed_service: EmbedService = Depends(get_embed_service),
    document_id: str = Path(..., description="UUID of the document"),
) -> dict:
    """
    Generates vector embeddings for the provided text chunks using **Cohere Embeddings** and persists them to the `chunks` table in Supabase (pgvector).

    Any previously stored embeddings for this document are **deleted before inserting** the new ones, ensuring idempotency.

    This is an individual pipeline step — it is called automatically by `POST /{document_id}/process`.
    Use this endpoint directly only for debugging or custom pipelines.

    **Path parameter:**
    - `document_id` — UUID of the document whose chunks are being embedded

    **Body:** `ChunkResponse` — the output of the `/documents/chunk` endpoint.

    **Returns:** `{ "message": "Successfully embedded and stored N chunks." }`
    """
    try:

        await embed_service.embed_and_store(document_id,chunks)
        
        return {"message": f"Successfully embedded and stored {chunks.count} chunks."}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to embed and store markdown chunked content: {str(e)}"
        )