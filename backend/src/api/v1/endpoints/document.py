from fastapi import APIRouter, Depends, UploadFile, File, status, Query, Path
from src.schemas.document import DocumentUploadResponse, DocumentResponse,DocumentStatusResponse
from src.schemas.auth import UserResponse
from src.services.document_service import DocumentService
from src.api.dependencies import get_current_user,get_document_service
from typing import Literal,List,Dict

router = APIRouter()





@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: UserResponse = Depends(get_current_user),
    document_service : DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """
    Upload a PDF file to be stored and queued for processing.

    **Constraints:**
    - File must be of type `application/pdf`
    - Maximum file size is configured server-side (default 5 MB)
    - Duplicate detection is hash-based — uploading the same file twice returns `409`

    **Returns:** Document metadata including its `id`, `file_name` , `bucket_path`, and initial `status: pending`.

    Use the returned `id` with the `POST /{document_id}/process` endpoint to start the ingestion pipeline.

    """
    return await document_service.upload_document(file, current_user.id)


@router.get(
    "/",
    response_model=List[DocumentResponse],
    summary="List user documents",
)
async def list_documents(
    status_filter: Literal["pending", "processing", "completed", "failed"] = Query(
        default="pending",
        description="Filter by status: pending, processing, completed, failed",
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    current_user: UserResponse = Depends(get_current_user),
    document_service : DocumentService = Depends(get_document_service)
) -> List[DocumentResponse]:
    """ 
    Returns a paginated list of the authenticated user's documents, optionally filtered by processing status.

    **Query parameters:**
    | Parameter | Default | Description |
    |---|---|---|
    | `status_filter` | `pending` | Filter by status: `pending`, `processing`, `completed`, `failed` |
    | `limit` | `50` | Number of results to return (1–100) |
    | `offset` | `0` | Number of results to skip (for pagination) |

    Documents are ordered by `created_at` descending (newest first).
    """
    return await document_service.get_user_documents(
        current_user.id, status_filter, limit, offset
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
)
async def get_document(
    document_id: str = Path(..., description="UUID of the document"),
    current_user: UserResponse = Depends(get_current_user),
    document_service : DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Fetch full metadata for a specific document owned by the authenticated user.

    **Path parameter:**
    - `document_id` — UUID of the document

    **Returns:** `DocumentResponse` with `id`, `file_name`, `status`, `created_at`, `updated_at`, and `metadata`.
    """
    return await document_service.get_document_by_id(document_id, current_user.id)


@router.delete(
    "/{document_id}", summary="Delete a document", status_code=status.HTTP_200_OK
)
async def delete_document(
    document_id: str = Path(..., description="UUID of the document"),
    current_user: UserResponse = Depends(get_current_user),
    document_service : DocumentService = Depends(get_document_service)
) -> Dict:
    """
    Deletes the document record from the database **and** removes the underlying file from storage.

    > ⚠️ This action is irreversible. Deleting this document will automatically permanently delete all of its associated data, including chunks (embeddings), conversations, messages, and citations.

    **Path parameter:**
    - `document_id` — UUID of the document to delete

    **Returns:** `{ "message": "Document deleted successfully" }`
    """
    return await document_service.delete_document(document_id, current_user.id)


@router.get(
    "/{document_id}/download",
    summary="Get document download URL",
    status_code=status.HTTP_200_OK,
)
async def get_download_url(
    document_id: str = Path(..., description="UUID of the document"),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration time in seconds"),
    current_user: UserResponse = Depends(get_current_user),
    document_service : DocumentService = Depends(get_document_service)
) -> Dict:
    """
    Generates a pre-signed URL that allows temporary, direct access to the raw PDF file in storage.

    **Path parameter:**
    - `document_id` — UUID of the document

    **Query parameter:**
    - `expires_in` — URL validity in seconds (default: `3600`, min: `60`, max: `86400`)

    **Returns:** `{ "download_url": "<signed_url>", "expires_in": <seconds> }`

    """
    download_url = await document_service.get_document_download_url(
        document_id, current_user.id, expires_in
    )
    return {"download_url": download_url, "expires_in": expires_in}




@router.get(
    "/{document_id}/status", 
    response_model=DocumentStatusResponse,
    summary="Quickly poll the processing status of a document"
)
async def get_document_status(
    document_id: str = Path(..., description="UUID of the document"),
    current_user: UserResponse = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentStatusResponse:
    """
    Lightweight endpoint to check the current pipeline status of a document.
    Intended for polling after triggering `POST /{document_id}/process`.

    **Path parameter:**
    - `document_id` — UUID of the document

    **Possible statuses:**
    | Status | Meaning |
    |---|---|
    | `pending` | Uploaded, not yet processed |
    | `processing` | Pipeline currently running |
    | `completed` | Successfully ingested and indexed |
    | `failed` | Pipeline encountered an error |

    **Returns:** `{ "id": "<document_id>", "status": "<status>" }`
    """
    current_status = await document_service.get_document_status(document_id, current_user.id)
    
    return DocumentStatusResponse(id=document_id,status=current_status)
