import asyncio
import logging
from datetime import datetime, timezone
from fastapi import HTTPException, status
from llama_cloud import AsyncLlamaCloud
from src.schemas.parse import (
    OutputFormat,
    ParsePDFOptions,
    ParsePDFResponse,
    MarkdownPage,
    TextPage,
)
from src.services.document_service import DocumentService


logger = logging.getLogger(__name__)

POLL_INTERVAL = 2
POLL_TIMEOUT = 300


class ParseService:
    """Parses PDFs to structured markdown/text via LlamaParse with async job polling and configurable options."""
    
    def __init__(self, llama_client: AsyncLlamaCloud ,document_service: DocumentService):
        self.client = llama_client
        self.document_service= document_service
           
    
    async def parse_pdf(
        self,
        options: ParsePDFOptions,
        document_id: str,
        user_id: str
    ) -> ParsePDFResponse:
        
        pdf_url = await self.document_service.get_document_download_url(
            document_id=document_id, user_id=user_id
        )
        try:
            job_id, created_at = await self._submit_job(pdf_url, options)
            logger.info("LlamaParse job submitted: %s", job_id)

            job_status = await self._wait_for_completion(job_id)
            completed_at = datetime.now(timezone.utc)

            if job_status != "COMPLETED":
                return ParsePDFResponse(
                    job_id=job_id,
                    status=job_status,
                    created_at=created_at,
                    completed_at=completed_at,
                    tier_used=options.tier,
                    error_message="Document processing failed. Please try again.",
                )

            result = await self._build_response(
                job_id=job_id,
                options=options,
                created_at=created_at,
                completed_at=completed_at,
            )

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Processing failed : %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing your document. Please try again.",
            )

    async def _submit_job(
        self,
        pdf_url: str,
        options: ParsePDFOptions
    ) -> tuple[str, datetime]:
        kwargs: dict = {
            "source_url": pdf_url,
            "tier": options.tier.value,
            "version": "latest",
        }

        if options.invalidate_cache:
            kwargs["disable_cache"] = True
        
        if options.max_pages or options.target_pages:
            page_ranges = {}
            if options.max_pages:
                page_ranges["max_pages"] = options.max_pages
            if options.target_pages:
                page_ranges["target_pages"] = options.target_pages
            kwargs["page_ranges"] = page_ranges
        
        if options.parsing_instruction:
            if "agentic_options" not in kwargs:
                kwargs["agentic_options"] = {}
            kwargs["agentic_options"]["custom_prompt"] = options.parsing_instruction
    
        if options.ignore_diagonal_text or options.ignore_text_in_image:
            if "processing_options" not in kwargs:
                kwargs["processing_options"] = {}
            ignore_opts = {}
            if options.ignore_diagonal_text:
                ignore_opts["ignore_diagonal_text"] = True
            if options.ignore_text_in_image:
                ignore_opts["ignore_text_in_image"] = True
            kwargs["processing_options"]["ignore"] = ignore_opts
    
        if options.output_tables_as_markdown:
            if "output_options" not in kwargs:
                kwargs["output_options"] = {}

            if "markdown" not in kwargs["output_options"]:
                kwargs["output_options"]["markdown"] = {}

            if "tables" not in kwargs["output_options"]["markdown"]:
                kwargs["output_options"]["markdown"]["tables"] = {}
                
            kwargs["output_options"]["markdown"]["tables"]["output_tables_as_markdown"] = True
        
      
        
        job = await self.client.parsing.create(**kwargs)

        created_at = getattr(job, "created_at", datetime.now(timezone.utc))
        return job.id, created_at

    async def _wait_for_completion(
        self,
        job_id: str
    ) -> str:
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            result = await self.client.parsing.get(job_id=job_id)

            status: str = result.job.status if result.job else "PENDING"
            logger.debug("Job %s status: %s", job_id, status)

            if status in ("COMPLETED", "FAILED", "CANCELLED"):
                return status

            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

        logger.warning("Job %s timed out after %ss", job_id, POLL_TIMEOUT)
        return "TIMEOUT"

    async def _build_response(
        self,
        job_id: str,
        options: ParsePDFOptions,
        created_at: datetime,
        completed_at: datetime,
    ) -> ParsePDFResponse:
        expand = self._resolve_expand(options.output_format)

        result = await self.client.parsing.get(job_id, expand=expand)

        job = result.job
        file_name = getattr(job, "name", None)

        markdown_pages = None
        total_pages = 0
        if options.output_format in (OutputFormat.MARKDOWN, OutputFormat.ALL):
            if result.markdown and result.markdown.pages:
                markdown_pages = [
                    MarkdownPage(page_number=p.page_number, markdown=p.markdown or "")
                    for p in result.markdown.pages
                    if hasattr(p, "success") and p.success
                ]
                total_pages = len(result.markdown.pages)

        text_pages = None
        if options.output_format in (OutputFormat.TEXT, OutputFormat.ALL):
            if result.text and result.text.pages:
                text_pages = [
                    TextPage(page_number=p.page_number, text=p.text or "")
                    for p in result.text.pages
                ]
                if total_pages == 0:
                    total_pages = len(result.text.pages)

        return ParsePDFResponse(
            job_id=job_id,
            status="COMPLETED",
            created_at=created_at,
            completed_at=completed_at,
            file_name=file_name,
            total_pages=total_pages,
            tier_used=options.tier,
            markdown_pages=markdown_pages,
            text_pages=text_pages,
        )

    @staticmethod
    def _resolve_expand(output_format: OutputFormat) -> list[str]:
        if output_format == OutputFormat.ALL:
            return ["markdown", "text"]
        if output_format == OutputFormat.TEXT:
            return ["text"]
        return ["markdown"]
