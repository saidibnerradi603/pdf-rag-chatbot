import logging
from langchain_cohere import CohereEmbeddings
from supabase import AsyncClient
from fastapi import HTTPException, status
from src.schemas.retrieval import RetrievalRequest, RetrievedChunk, RetrievalResponse

logger = logging.getLogger(__name__)

class RetrievalService:
    """Performs semantic search over document chunks using Cohere query embeddings and pgvector similarity."""

    def __init__(self, embeddings: CohereEmbeddings, db: AsyncClient):
        self.embeddings = embeddings
        self.db = db

    async def retrieve_context(
        self, 
        document_id: str, 
        user_id: str, 
        request: RetrievalRequest
    ) -> RetrievalResponse:
        try:
           
            logger.info(f"Embedding search query: '{request.query}'")
            query_embedding = await self.embeddings.aembed_query(request.query)
            
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": request.similarity_threshold,
                "match_count": request.top_k,
                "arg_document_id": document_id,  
                "arg_user_id": user_id          
            }

            
            response = await self.db.rpc("match_documents", rpc_params).execute()

           
            chunks = []
            if response.data:
                for item in response.data:
                    chunks.append(
                        RetrievedChunk(
                            id=item["id"],
                            content=item["content"],
                            metadata=item.get("metadata",""),
                            similarity=item["similarity"]
                        )
                    )

            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")

            return RetrievalResponse(
                query=request.query,
                results=chunks
            )

        except Exception as e:
            logger.error(f"Vector retrieval failed for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve context from database: {str(e)}"
            )