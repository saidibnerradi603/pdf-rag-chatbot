from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)
from src.schemas.chunk import ChunkRequest, ChunkMetadata, Chunk, ChunkResponse
import logging

logger = logging.getLogger(__name__)

class ChunkService:
    """Splits markdown documents into semantic chunks using header-aware and recursive text splitting."""
    
    def __init__(self):
        pass
    
    async def chunk_markdown(
        self,
        chunk_size: int,
        chunk_overlap: int,
        request: ChunkRequest
    ) -> ChunkResponse:
        try:
            
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")],
                return_each_line=False,
                strip_headers=False
            )
            
            
            recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            all_docs: List[Document] = []
            
            for page in request.markdown_pages:
                page_docs = self._process_page(
                    page_data={
                        "page_number": page.page_number,
                        "markdown": page.markdown
                    },
                    file_name=request.file_name,
                    markdown_splitter=markdown_splitter,
                    recursive_splitter=recursive_splitter,
                    chunk_size=chunk_size
                )
                all_docs.extend(page_docs)
            
          
            all_docs = self._merge_small_chunks(all_docs, min_size=100)
            
            logger.info(
                f"Successfully chunked {request.file_name}: "
                f"{len(request.markdown_pages)} pages :  {len(all_docs)} chunks"
            )
            
            chunk_models = []
            for doc in all_docs:
                chunk_models.append(
                    Chunk(
                        page_content=doc.page_content,
                        metadata=ChunkMetadata(
                            file_name=doc.metadata["file_name"],
                            page_number=doc.metadata["page_number"]
                        )
                    )
                )
            
            return ChunkResponse(chunks=chunk_models)
            
        except Exception as e:
            logger.error(f"Chunking failed for {request.file_name}: {str(e)}")
            raise
    
    def _merge_small_chunks(self, docs: List[Document], min_size: int) -> List[Document]:
        """
        Merges chunks that are smaller than min_size into the previous chunk
        to avoid single-word or single-line noise chunks.
        """
        if not docs:
            return []

        merged_docs = [docs[0]]
        
        for current_doc in docs[1:]:
            prev_doc = merged_docs[-1]
            
            if len(current_doc.page_content.strip()) < min_size:
                
                prev_doc.page_content += "\n" + current_doc.page_content
                if prev_doc.metadata.get("page_number") != current_doc.metadata.get("page_number"):
                     pass
            else:
                
                merged_docs.append(current_doc)
                
        return merged_docs

    def _process_page(
        self, 
        page_data: Dict, 
        file_name: str,
        markdown_splitter: MarkdownHeaderTextSplitter,
        recursive_splitter: RecursiveCharacterTextSplitter,
        chunk_size: int
    ) -> List[Document]:
       
        page_number: int = page_data["page_number"]
        markdown: str = page_data.get("markdown", "").strip()

        if not markdown:
            return []

        base_meta = {
            "file_name": file_name,
            "page_number": page_number,
        }

        try:
            
            semantic_chunks = markdown_splitter.split_text(markdown)
        except Exception as e:
            logger.warning(f"Header split failed on page {page_number}: {e}")
            semantic_chunks = [Document(page_content=markdown)]

        documents: List[Document] = []

        for chunk in semantic_chunks:
            text = chunk.page_content.strip()
            if not text:
                continue

            if len(text) <= chunk_size:
                documents.append(Document(page_content=text, metadata=base_meta))
            else:
                for sub_text in recursive_splitter.split_text(text):
                    sub_text = sub_text.strip()
                    if sub_text:
                        documents.append(Document(
                            page_content=sub_text,
                            metadata=base_meta   
                        ))

        return documents