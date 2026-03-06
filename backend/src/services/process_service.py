import logging
from fastapi import HTTPException, status
from src.services.document_service import DocumentService
from src.services.parse_service import ParseService
from src.services.chunk_service import ChunkService
from src.services.embed_service import EmbedService
from src.schemas.process import ProcessRequest, ProcessResponse
from src.schemas.chunk import ChunkRequest, MarkdownPage as ChunkMarkdownPage

logger = logging.getLogger(__name__)


class ProcessService:
    """Orchestrates the full RAG ingestion pipeline: parse → chunk → embed → store with status tracking."""

    def __init__(
        self,
        document_service: DocumentService,
        parse_service: ParseService,
        chunk_service: ChunkService,
        embed_service: EmbedService
    ):
        self.document_service = document_service
        self.parse_service = parse_service
        self.chunk_service = chunk_service
        self.embed_service = embed_service

    async def run_pipeline(
        self,
        document_id: str,
        user_id: str,
        request: ProcessRequest
    ) -> ProcessResponse:
        try:
            # --- Validate & mark as processing ---
            await self.document_service.validate_document_status(document_id, user_id)
            await self.document_service.update_document_status(document_id, user_id, "processing")
            logger.info(f"Pipeline started for document: {document_id}")

            # --- Parse ---
            parse_result = await self.parse_service.parse_pdf(
                options=request.parse_options,
                document_id=document_id,
                user_id=user_id
            )

            if parse_result.status != "COMPLETED" or not parse_result.markdown_pages:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Parsing did not complete successfully. LlamaParse status: {parse_result.status}",
                )

            pages_parsed = len(parse_result.markdown_pages)

            # --- Chunk ---
            doc_meta = await self.document_service.get_document_by_id(document_id, user_id)

            mapped_pages = [
                ChunkMarkdownPage(page_number=p.page_number, markdown=p.markdown)
                for p in parse_result.markdown_pages
            ]

            chunk_request = ChunkRequest(
                file_name=doc_meta.file_name,
                markdown_pages=mapped_pages
            )

            chunk_result = await self.chunk_service.chunk_markdown(
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                request=chunk_request
            )

            chunks_stored = len(chunk_result.chunks) if chunk_result and chunk_result.chunks else 0

            # --- Embed & store ---
            await self.embed_service.embed_and_store(
                document_id=document_id,
                chunks=chunk_result
            )

            # --- Mark completed ---
            await self.document_service.update_document_status(document_id, user_id, "completed")
            logger.info(f"Pipeline successfully finished for document: {document_id}")

            return ProcessResponse(
                message="Document processed successfully.",
                document_id=document_id,
                status="completed",
                pages_parsed=pages_parsed,
                chunks_stored=chunks_stored,
            )

        except HTTPException:
            # Semantic errors (404, 409, 422 …) — update status and re-raise so the
            # endpoint can return the correct HTTP status code to the client.
            logger.warning(
                f"Pipeline aborted for document {document_id} due to a known error."
            )
            await self.document_service.update_document_status(document_id, user_id, "failed")
            raise

        except Exception as e:
            # Unexpected errors — log, mark failed, surface as 500.
            logger.error(f"Pipeline crashed for document {document_id}: {str(e)}", exc_info=True)
            await self.document_service.update_document_status(document_id, user_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while processing the document: {str(e)}",
            )