from fastapi import HTTPException, UploadFile, status
from supabase import AsyncClient
from src.utils.file_utils import validate_file,calculate_file_hash,generate_unique_filename
from src.schemas.document import DocumentUploadResponse, DocumentResponse
from typing import Literal,List

import logging

logger = logging.getLogger(__name__)


class DocumentService:
    """Manages PDF document lifecycle: upload, storage, retrieval, and hash-based duplicate detection."""
    
    def __init__(self, db: AsyncClient, bucket_name: str, max_file_size: int, allowed_mime_types: List[str]):
        self.db = db
        self.bucket_name = bucket_name
        self.max_file_size = max_file_size
        self.allowed_mime_types = allowed_mime_types
        
    async def upload_document(
        self, file: UploadFile,
        user_id: str
    ) -> DocumentUploadResponse:
        
        
        validate_file(file, self.max_file_size, self.allowed_mime_types)

        bucket_path = generate_unique_filename(file.filename, user_id)

        try:
            file_content = await file.read()

            file_hash = calculate_file_hash(file_content)

            await self._ensure_not_duplicate(user_id=user_id, file_hash=file_hash)
            
            storage_response = await self.db.storage.from_(self.bucket_name).upload(
                path=bucket_path,
                file=file_content,
                file_options={"content-type": "application/pdf", "upsert": "false"},
            )

            if not storage_response:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload file to storage",
                )

            document_data = {
                "user_id": user_id,
                "file_name": file.filename,
                "bucket_path": bucket_path,
                "file_hash": file_hash,
                "status": "pending",
                "metadata": {
                    "file_size": f"{len(file_content)/(1024*1024):,.3f} MB",
                    "content_type": file.content_type,
                    "original_filename": file.filename,
                },
            }

            db_response = await self.db.table("documents").insert(document_data).execute()

            if not db_response.data:
                await self.db.storage.from_(self.bucket_name).remove([bucket_path])
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create document record",
                )

            document = db_response.data[0]

            return DocumentUploadResponse(
                id=document["id"],
                file_name=document["file_name"],
                bucket_path=document["bucket_path"],
                status=document["status"],
                created_at=document["created_at"],
                message="Document uploaded successfully.",
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed for user {user_id}: {str(e)}")
            try:
                await self.db.storage.from_(self.bucket_name).remove([bucket_path])
                logger.info(f"Successfully rolled back stranded file: {bucket_path}")
            except Exception as cleanup_error:
                logger.critical(
                    f"Failed to delete {bucket_path} from storage "
                    f"after DB insert failed. Cleanup Error: {str(cleanup_error)}"
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing your document. Please try again.",
            )

    async def get_user_documents(
        self,
        user_id: str,
        status_filter: Literal["pending", "processing", "completed", "failed"],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocumentResponse]:
        try:
            query =  self.db.table("documents").select("*").eq("user_id", user_id)

            if status_filter:
                query = query.eq("status", status_filter)

            query = query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            )

            response = await query.execute()

            return [DocumentResponse(**doc) for doc in response.data]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve documents: {str(e)}",
            )

    async def get_document_by_id(
        self,
        document_id: str,
        user_id: str
    ) -> DocumentResponse:
        try:
            doc_response = await (
                self.db.table("documents")
                .select("*")
                .eq("id", document_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not doc_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            document = doc_response.data[0]

            return DocumentResponse(
                **document,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve document: {str(e)}",
            )

    async def delete_document(
        self,
        document_id: str,
        user_id: str
    ) -> dict:
        try:
            doc_response = await (
                self.db.table("documents")
                .select("bucket_path")
                .eq("id", document_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not doc_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            bucket_path = doc_response.data[0]["bucket_path"]

            try:
                await self.db.storage.from_(self.bucket_name).remove([bucket_path])
            except Exception as storage_error:
                logger.warning(f"Warning: Failed to delete file from storage: {storage_error}")

            delete_response = await (
                self.db.table("documents")
                .delete()
                .eq("id", document_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not delete_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete document",
                )

            return {
                "message": "Document deleted successfully",
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            )

    async def get_document_download_url(
        self,
        document_id: str,
        user_id: str,
        expires_in: int = 3600
    ) -> str:
        try:
            doc_response = await (
                self.db.table("documents")
                .select("bucket_path")
                .eq("id", document_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not doc_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            bucket_path = doc_response.data[0]["bucket_path"]

            signed_url = await self.db.storage.from_(self.bucket_name).create_signed_url(
                bucket_path, expires_in
            )

            if not signed_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate download URL",
                )

            return signed_url["signedURL"]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {str(e)}",
            )
    
    async def _ensure_not_duplicate(
        self,
        user_id: str,
        file_hash: str
    ) -> None:
        try:
            duplicate_check = await (
                self.db.table("documents")
                .select("id, file_name, status")
                .eq("user_id", user_id)
                .eq("file_hash", file_hash)
                .execute()
            )

            if duplicate_check.data:
                existing_doc = duplicate_check.data[0]
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"This file has already been uploaded as '{existing_doc['file_name']}'",
                )

        except HTTPException:
            raise  
        except Exception as e:
            logger.error(f"Duplicate check failed for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check for duplicate documents",
            )
    
    async def get_document_status(
        self,
        document_id: str,
        user_id: str
    ) -> str:
        response = await (
            self.db.table("documents")
            .select("status")
            .eq("id", document_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )

        return response.data[0]["status"]
    
    async def validate_document_status(
        self,
        document_id: str,
        user_id: str
    ) -> None:
        current_status = await self.get_document_status(document_id, user_id)

        if current_status == "processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is currently being processed. Please wait for it to complete.",
            )

        if current_status == "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has already been processed successfully.",
            )

    async def update_document_status(
        self,
        document_id: str,
        user_id: str,
        new_status: str
    ) -> None:
        await self.db.table("documents").update({"status": new_status}).eq("id", document_id).eq("user_id", user_id).execute()
        logger.info("Document %s → status: %s", document_id, new_status)

    async def update_suggested_questions(
        self,
        document_id: str,
        user_id: str,
        questions: list[str]
    ) -> None:
        await (
            self.db.table("documents")
            .update({"suggested_questions": questions})
            .eq("id", document_id)
            .eq("user_id", user_id)
            .execute()
        )
        logger.info("Saved %d suggested questions for document %s", len(questions), document_id)