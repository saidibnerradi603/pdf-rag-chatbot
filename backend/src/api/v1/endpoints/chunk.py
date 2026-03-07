from fastapi import APIRouter, Depends, HTTPException, status,Query
from src.schemas.chunk import ChunkRequest, ChunkResponse
from src.services.chunk_service import ChunkService
from src.api.dependencies import get_current_user, get_chunk_service

router = APIRouter()

@router.post(
    "/chunk",
    response_model=ChunkResponse,
    status_code=status.HTTP_200_OK,
    summary="Split markdown content into semantically sized chunks",
    dependencies=[Depends(get_current_user)]
)
async def chunk_markdown(
    request: ChunkRequest,
    chunk_service: ChunkService = Depends(get_chunk_service),
    chunk_size: int = Query(1500, ge=500, le=4000, description="Maximum characters per chunk"),
    chunk_overlap: int = Query(150, ge=0, le=500, description="Overlapping characters between chunks"),
) -> ChunkResponse:
    """
    Splits markdown text (from a parsed PDF) into smaller, overlapping chunks suitable for embedding.

    The chunking strategy is two-stage:
    1. **Header-aware split** using `MarkdownHeaderTextSplitter` — respects `#` and `##` headings to preserve semantic boundaries.
    2. **Recursive character split** using `RecursiveCharacterTextSplitter` — further divides oversized sections using paragraph, newline, and sentence separators.

    This is an individual pipeline step — it is called automatically by `POST /{document_id}/process`.
    Use this endpoint directly only for debugging or custom pipelines.

    **Query parameters:**
    | Parameter | Default | Range | Description |
    |---|---|---|---|
    | `chunk_size` | `1500` | 500–4000 | Maximum characters per chunk |
    | `chunk_overlap` | `150` | 0–500 | Overlapping characters between adjacent chunks |

    **Body:** `ChunkRequest` containing `file_name` and a list of `markdown_pages`.

    **Returns:** `ChunkResponse` with a list of `Chunk` objects, each carrying `page_content` and `metadata` (file name, page number).
    """
    try:
        chunks = await chunk_service.chunk_markdown(chunk_size,chunk_overlap,request)
        return chunks
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk markdown content: {str(e)}"
        )
