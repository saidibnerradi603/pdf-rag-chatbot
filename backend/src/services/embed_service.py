import logging
from typing import List, Dict, Any
from langchain_cohere import CohereEmbeddings
from supabase import AsyncClient
from src.schemas.chunk import ChunkResponse

logger = logging.getLogger(__name__)

class EmbedService:
    """Generates semantic embeddings via Cohere and stores vectors in pgvector database."""
    
    def __init__(self, embeddings: CohereEmbeddings, db: AsyncClient):
        self.embeddings = embeddings
        self.db = db

    async def embed_and_store(
        self,
        document_id: str,
        chunks: ChunkResponse
    ) -> None:
        
        if not chunks or not chunks.chunks:
            logger.warning(f"No chunks provided for document {document_id}.")
            return

        try:
            
            await self.db.table("chunks").delete().eq("document_id", document_id).execute()

            texts_to_embed = [chunk.page_content for chunk in chunks.chunks]

            logger.info(f"Sending {len(texts_to_embed)} chunks to Cohere for embedding...")
            embeddings_arrays = await self.embeddings.aembed_documents(texts_to_embed)
           
            
            records_to_insert: List[Dict[str, Any]] = []
            
            for i, chunk in enumerate(chunks.chunks):
                record = {
                    "document_id": document_id, 
                    "content": chunk.page_content,
                    "embedding": embeddings_arrays[i],
                    "metadata": {
                        "file_name": chunk.metadata.file_name,
                        "page_number": chunk.metadata.page_number,
                    }
                }
                records_to_insert.append(record)

           
            await self.db.table("chunks").insert(records_to_insert).execute()
            
            logger.info(f"Successfully embedded and stored {len(records_to_insert)} chunks for {document_id}.")

        except Exception as e:
            logger.error(f"Failed to embed and store chunks for {document_id}: {str(e)}")
            raise