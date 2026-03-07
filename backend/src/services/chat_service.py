import json 
import logging
from typing import List, Dict, AsyncGenerator
from supabase import AsyncClient
from fastapi import HTTPException, status
from langchain_core.language_models import BaseChatModel
from src.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ChatRequest,
    ChatResponse,
    CitationResponse,
    ConversationHistoryResponse,
    MessageWithCitations,
)
from src.schemas.retrieval import RetrievedChunk
from src.services.retrieval_service import RetrievalService
from src.services.document_service import DocumentService
from src.schemas.retrieval import RetrievalRequest
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

 
class ChatService:
    """Manages RAG-based conversations with document-grounded responses and citation tracking."""

    def __init__(
        self,
        db: AsyncClient,
        chat_model: BaseChatModel,
        retrieval_service: RetrievalService, 
        document_service: DocumentService
    ):
        self.db = db
        self.chat_model = chat_model
        self.retrieval_service = retrieval_service
        self.document_service = document_service


    async def _verify_conversation_ownership(
        self,
        conversation_id: str,
        user_id: str
    ) -> Dict:
        response = await (
            self.db.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return response.data[0]

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Dict:
        response = await self.db.table("messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content
        }).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store {role} message",
            )
        return response.data[0]

    async def create_conversation(
        self,
        user_id: str,
        request: ConversationCreate
    ) -> ConversationResponse:
        try:
            # doc_response = (
            #     self.db.table("documents")
            #     .select("id, status")
            #     .eq("id", request.document_id)
            #     .eq("user_id", user_id)
            #     .execute()
            # )
           

            # if not doc_response.data:
            #     raise HTTPException(
            #         status_code=status.HTTP_404_NOT_FOUND,
            #         detail="Document not found!",
            #     )
            # document = doc_response.data[0]
            document_status= await self.document_service.get_document_status(
                document_id=request.document_id,
                user_id=user_id
            )
            
            if document_status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document must be processed before chatting. Current status: {document_status}",
                )

            conversation_data = {
                "user_id": user_id,
                "document_id": request.document_id,
                "title": request.title or "Untitled",
            }

            response = await self.db.table("conversations").insert(conversation_data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create conversation",
                )

            conversation = response.data[0]
            logger.info(f"Created conversation {conversation['id']} for user {user_id}")
            return ConversationResponse(**conversation)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create conversation: {str(e)}",
            )

    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str
    ) -> ConversationHistoryResponse:
        try:
            conversation = await self._verify_conversation_ownership(conversation_id, user_id)

            messages_response = await (
                self.db.table("messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
                .execute()
            )
            
            messages_data = messages_response.data
            if not messages_data:
                return ConversationHistoryResponse(
                    conversation_id=conversation["id"],
                    document_id=conversation["document_id"],
                    title=conversation["title"],
                    messages=[],
                )

            assistant_msg_ids = [msg["id"] for msg in messages_data if msg["role"] == "assistant"]
            
            citations_map = {}
            if assistant_msg_ids:
                citations_response = await (
                    self.db.table("citations")
                    .select("*")
                    .in_("message_id", assistant_msg_ids)
                    .execute()
                )
                
                for cit in citations_response.data:
                    msg_id = cit["message_id"]
                    if msg_id not in citations_map:
                        citations_map[msg_id] = []
                    citations_map[msg_id].append(CitationResponse(**cit))

            messages_with_citations = []
            for msg in messages_data:
                citations = citations_map.get(msg["id"]) if msg["role"] == "assistant" else None
                messages_with_citations.append(
                    MessageWithCitations(
                        id=msg["id"],
                        role=msg["role"],
                        content=msg["content"],
                        created_at=msg["created_at"],
                        citations=citations,
                    )
                )

            return ConversationHistoryResponse(
                conversation_id=conversation["id"],
                document_id=conversation["document_id"],
                title=conversation["title"],
                messages=messages_with_citations,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve conversation history: {str(e)}",
            )

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Dict:
        try:
            await self._verify_conversation_ownership(conversation_id, user_id)

            delete_response = await (
                self.db.table("conversations")
                .delete()
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not delete_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete conversation",
                )

            logger.info(f"Deleted conversation {conversation_id}")
            return {"message": "Conversation deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete conversation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete conversation: {str(e)}",
            )

    async def chat( 
        self,
        conversation_id: str,
        user_id: str,
        request: ChatRequest
    ) -> ChatResponse:
        try:
            conversation = await self._verify_conversation_ownership(conversation_id, user_id)
            document_id = conversation["document_id"]
            
            if conversation.get("title") == "Untitled":
                new_title = request.message[:50] + "..." if len(request.message) > 50 else request.message
                
                await self.db.table("conversations").update({"title": new_title}).eq("id", conversation_id).execute()
                
            

            logger.info(f"Retrieving context for query: '{request.message}'")
            retrieval_req = RetrievalRequest(
                query=request.message,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            
            retrieval_response = await self.retrieval_service.retrieve_context(
                document_id=document_id,
                user_id=user_id,
                request=retrieval_req
            )
            retrieved_chunks = retrieval_response.results

            history_messages = await (
                self.db.table("messages")
                .select("role, content")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=True)
                .limit(10)  
                .execute()
            )

            messages = self._format_rag_messages(
                user_question=request.message,
                chunks=retrieved_chunks,
                history=history_messages.data[::-1] if history_messages.data else [],
            )
            
            await self._save_message(conversation_id, "user", request.message)
            
            logger.info("Generating response with LLM...")
            ai_response = await self.chat_model.ainvoke(messages)

            assistant_message = ai_response.content

            assistant_msg = await self._save_message(conversation_id, "assistant", assistant_message)

            citations = []
            if retrieved_chunks:
                citations = await self._store_citations(
                    message_id=assistant_msg["id"], chunks=retrieved_chunks
                )

            logger.info(f"Chat completed for conversation {conversation_id} with {len(citations)} citations")

            return ChatResponse(
                message_id=assistant_msg["id"],
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=assistant_message,
                citations=citations,
                created_at=assistant_msg["created_at"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Chat failed for conversation {conversation_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process chat message: {str(e)}",
            )

    async def _store_citations(
        self,
        message_id: str,
        chunks: List[RetrievedChunk]
    ) -> List[CitationResponse]:
        citations_to_insert = []

        for chunk in chunks:
            metadata_dict = chunk.metadata.model_dump()

            citation_data = {
                "message_id": message_id,
                "chunk_id": chunk.id,                  
                "cited_text": chunk.content,          
                "metadata": metadata_dict,            
                "similarity_score": chunk.similarity,   
            }
            citations_to_insert.append(citation_data)

        if citations_to_insert:
            citations_response = await (
                self.db.table("citations").insert(citations_to_insert).execute()
            )

            if citations_response.data:
                return [
                    CitationResponse(**citation) for citation in citations_response.data
                ]

        return []
    
    # def _format_rag_messages(
    #     self,
    #     user_question: str,
    #     chunks: List[RetrievedChunk],
    #     history: List[Dict]
    # ) -> ChatPromptTemplate:
        
    #     if not chunks:
    #         context_text = "No relevant information found in the document."
    #     else:
    #         context_text = "\n\n".join([
    #             f"[Source {i+1}]\n{chunk.content}" 
    #             for i, chunk in enumerate(chunks)
    #         ])
        
    #     prompt = ChatPromptTemplate.from_messages([
    #         (
    #             "system",
    #             """You are an expert AI assistant specializing in document analysis and question answering.

    #             **YOUR ROLE:**
    #             - Provide accurate, well-reasoned answers based strictly on the document context provided
    #             - Think step-by-step before answering
    #             - Be precise and cite your sources
    #             - Format all responses in Markdown

    #             **GUIDELINES:**
    #             1. **Answer from Context Only**: Base your response exclusively on the information in the CONTEXT section below
    #             2. **Citation Required**: Always cite sources using IEEE notation when making claims
    #             3. **Acknowledge Limitations**: If the context lacks sufficient information, clearly state: "The provided context does not contain enough information to answer this question."
    #             4. **Be Comprehensive**: When information is available, provide complete answers with relevant details
    #             5. **Stay Focused**: Address the question directly without adding unrelated information
    #             6. **Handle Ambiguity**: If the question is unclear, provide the most reasonable interpretation or ask for clarification

    #             **CONTEXT FROM DOCUMENT:**
    #             {context}

    #             **Remember**: Quality over quantity. A precise, well-cited partial answer is better than speculation."""
    #         ),
    #         MessagesPlaceholder(variable_name="chat_history", optional=True),
    #         ("human", "{question}")
    #     ])
        
    #     formatted_history = []
    #     if history:
    #         for msg in history:
    #             if msg["role"] == "user":
    #                 formatted_history.append(("human", msg["content"]))
    #             elif msg["role"] == "assistant":
    #                 formatted_history.append(("ai", msg["content"]))
        
    #     return prompt.format_messages(
    #         context=context_text,
    #         chat_history=formatted_history if formatted_history else [],
    #         question=user_question
    #     )
    
    
    
    def _format_rag_messages(
        self,
        user_question: str,
        chunks: List[RetrievedChunk],
        history: List[Dict]
    ) -> ChatPromptTemplate:
        # 1. Format the context chunks exactly as your prompt expects (numbered)
        if not chunks:
            context_text = "No relevant information found in the document."
        else:
            context_text = "\n\n".join([
                f"Context #{i+1}:\n{chunk.content}" 
                for i, chunk in enumerate(chunks)
            ])
        
        # 2. Build the System Prompt as a plain string with {context} placeholder.
        #    IMPORTANT: Do NOT use an f-string here. LangChain's ChatPromptTemplate
        #    will substitute {context} safely, so curly braces inside chunk content
        #    (e.g. mathematical notation like {X1, ..., Xb}) won't be misinterpreted
        #    as template variables.
        system_template = """You are an expert AI assistant.

        CONTEXT (numbered): 
        {context}

        INSTRUCTIONS
        1. Relevance  
        • Read every context block, but USE ONLY the blocks needed to answer the question.  
        • Ignore the rest and do not cite them.

        2. Answer quality  
        • Give a complete, well-reasoned explanation in a clear academic style.  
        • If data is missing, say so ("Information on X is not provided.").

        3. Markdown formatting  
        • Headings: ##, ###  
        • **Bold**, *italic*, `inline code`  
        • Bullet/number lists, tables, blockquotes (>), code blocks (```), horizontal rules (---).  
        • LaTeX math between $$ … $$.

        4. Citations (IEEE)  
        • Map Context #1 → [1], Context #2 → [2], etc.  
        • Cite only the blocks you actually used, e.g. "… mechanism [1, 3]."
        
        5. Follow-up suggestion (required)  
        • After the main answer, add **one short, contextual follow-up suggestion phrased as a question** that offers to explain something related or next-step help.  
        • Use the conversation history and context blocks to choose a related suggestion. Make it specific when possible.  
        • Place the suggestion after a horizontal rule (---) and make it visually prominent (e.g., **bold**).

        Return ONLY the formatted Markdown answer."""

        # 3. Create the LangChain Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            # LangChain natively injects the conversation history here
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            # The current user question goes last
            ("human", "{question}")
        ])
        
        # 4. Format the history array for LangChain
        formatted_history = []
        if history:
            for msg in history:
                if msg["role"] == "user":
                    formatted_history.append(("human", msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_history.append(("ai", msg["content"]))
        
        # 5. Return the final formatted messages ready for self.chat_model.ainvoke()
        return prompt.format_messages(
            context=context_text,
            chat_history=formatted_history if formatted_history else [],
            question=user_question
        )
        
        
    async def get_user_conversations(
        self,
        user_id: str
    ) -> List[ConversationResponse]:
        try:
            response = await (
                self.db.table("conversations")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True) 
                .execute()
            )
            
            if not response.data:
                return []
                
            return [ConversationResponse(**conv) for conv in response.data]

        except Exception as e:
            logger.error(f"Failed to fetch conversations for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch conversations: {str(e)}",
            )
    
    async def chat_stream( 
        self,
        conversation_id: str,
        user_id: str,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        try:
            conversation = await self._verify_conversation_ownership(conversation_id, user_id)
            document_id = conversation["document_id"]
            
            if conversation.get("title") == "Untitled":
                new_title = request.message[:50] + "..." if len(request.message) > 50 else request.message
                await self.db.table("conversations").update({"title": new_title}).eq("id", conversation_id).execute()

            logger.info(f"Retrieving context for query: '{request.message}'")
            retrieval_req = RetrievalRequest(
                query=request.message,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            
            retrieval_response = await self.retrieval_service.retrieve_context(
                document_id=document_id,
                user_id=user_id,
                request=retrieval_req
            )
            retrieved_chunks = retrieval_response.results

            history_messages = await (
                self.db.table("messages")
                .select("role, content")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=True)
                .limit(10)  
                .execute()
            )

            messages = self._format_rag_messages(
                user_question=request.message,
                chunks=retrieved_chunks,
                history=history_messages.data[::-1] if history_messages.data else [],
            )
            
            await self._save_message(conversation_id, "user", request.message)
            
            logger.info("Generating streaming response with LLM...")
            
            full_response = ""
            async for chunk in self.chat_model.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    # yield f"data: {chunk.content}\n\n"
                    yield f"data: {json.dumps(chunk.content)}\n\n"

            assistant_msg = await self._save_message(conversation_id, "assistant", full_response)

            citations = []
            if retrieved_chunks:
                citations = await self._store_citations(
                    message_id=assistant_msg["id"], chunks=retrieved_chunks
                )
            citations_payload = {
                "type": "metadata",
                "message_id": assistant_msg["id"],
                "citations": [citation.model_dump() for citation in citations],
            }
            logger.info(f"Stream Chat completed for conversation {conversation_id} with {len(citations)} citations")
            yield f"data: {json.dumps(citations_payload)}\n\n"
            yield "data: [DONE]\n\n"

        except HTTPException as he:
            yield f"data: [ERROR] {he.detail}\n\n"
        except Exception as e:
            logger.error(f"Stream chat failed for conversation {conversation_id}: {str(e)}")
            yield f"data: [ERROR] Failed to process chat message: {str(e)}\n\n"
