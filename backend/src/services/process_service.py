import json
import logging
from fastapi import HTTPException, status
from langchain_core.language_models import BaseChatModel
from src.services.document_service import DocumentService
from src.services.parse_service import ParseService
from src.services.chunk_service import ChunkService
from src.services.embed_service import EmbedService
from src.schemas.process import ProcessRequest, ProcessResponse
from src.schemas.chunk import ChunkRequest, MarkdownPage as ChunkMarkdownPage

logger = logging.getLogger(__name__)

QUESTION_GENERATION_PROMPT = """Based on the following document content, generate exactly 4 concise, specific questions that a reader would likely want to ask about this document. The questions should cover different aspects of the content.

Return ONLY a valid JSON array of 4 strings, with no extra text or formatting.
Example: ["Question 1?", "Question 2?", "Question 3?", "Question 4?"]

Document content:
{content}"""


class ProcessService:
    """Orchestrates the full RAG ingestion pipeline: parse → chunk → embed → store with status tracking."""

    def __init__(
        self,
        document_service: DocumentService,
        parse_service: ParseService,
        chunk_service: ChunkService,
        embed_service: EmbedService,
        chat_model: BaseChatModel,
    ):
        self.document_service = document_service
        self.parse_service = parse_service
        self.chunk_service = chunk_service
        self.embed_service = embed_service
        self.chat_model = chat_model

    async def run_pipeline(
        self, document_id: str, user_id: str, request: ProcessRequest
    ) -> ProcessResponse:
        try:
            await self.document_service.validate_document_status(document_id, user_id)
            await self.document_service.update_document_status(
                document_id, user_id, "processing"
            )
            logger.info(f"Pipeline started for document: {document_id}")

            # --- Parse ---
            parse_result = await self.parse_service.parse_pdf(
                options=request.parse_options, document_id=document_id, user_id=user_id
            )

            if parse_result.status != "COMPLETED" or not parse_result.markdown_pages:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Parsing did not complete successfully. LlamaParse status: {parse_result.status}",
                )

            pages_parsed = len(parse_result.markdown_pages)

            # --- Chunk ---
            doc_meta = await self.document_service.get_document_by_id(
                document_id, user_id
            )

            mapped_pages = [
                ChunkMarkdownPage(page_number=p.page_number, markdown=p.markdown)
                for p in parse_result.markdown_pages
            ]

            chunk_request = ChunkRequest(
                file_name=doc_meta.file_name, markdown_pages=mapped_pages
            )

            chunk_result = await self.chunk_service.chunk_markdown(
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                request=chunk_request,
            )

            chunks_stored = (
                len(chunk_result.chunks) if chunk_result and chunk_result.chunks else 0
            )

            # --- Embed & store ---
            await self.embed_service.embed_and_store(
                document_id=document_id, chunks=chunk_result
            )

            # --- Generate suggested questions ---
            await self._generate_and_save_questions(
                document_id=document_id,
                user_id=user_id,
                chunks=chunk_result.chunks if chunk_result else [],
            )

            # --- Mark completed ---
            await self.document_service.update_document_status(
                document_id, user_id, "completed"
            )
            logger.info(f"Pipeline successfully finished for document: {document_id}")

            return ProcessResponse(
                message="Document processed successfully.",
                document_id=document_id,
                status="completed",
                pages_parsed=pages_parsed,
                chunks_stored=chunks_stored,
            )

        except HTTPException:
            logger.warning(
                f"Pipeline aborted for document {document_id} due to a known error."
            )
            await self.document_service.update_document_status(
                document_id, user_id, "failed"
            )
            raise

        except Exception as e:
            logger.error(
                f"Pipeline crashed for document {document_id}: {str(e)}", exc_info=True
            )
            await self.document_service.update_document_status(
                document_id, user_id, "failed"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while processing the document: {str(e)}",
            )

    async def _generate_and_save_questions(
        self, document_id: str, user_id: str, chunks: list
    ) -> None:
        try:
            if not chunks:
                return

            sample_chunks = chunks[:5]
            content = "\n\n".join(
                chunk.content if hasattr(chunk, "content") else str(chunk)
                for chunk in sample_chunks
            )

            prompt = QUESTION_GENERATION_PROMPT.format(content=content)
            response = await self.chat_model.ainvoke(prompt)
            raw = response.content.strip()

            # Handle markdown code fences
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            questions = json.loads(raw)

            if isinstance(questions, list) and len(questions) > 0:
                questions = [q for q in questions[:4] if isinstance(q, str)]
                await self.document_service.update_suggested_questions(
                    document_id, user_id, questions
                )
                logger.info(
                    f"Generated {len(questions)} suggested questions for document {document_id}"
                )

        except Exception as e:
            logger.warning(
                f"Question generation failed for document {document_id}: {e}"
            )
