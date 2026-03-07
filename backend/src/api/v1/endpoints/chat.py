from fastapi import APIRouter, Depends, Path, status
from fastapi.responses import StreamingResponse
from typing import Dict,List
from src.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from src.schemas.auth import UserResponse
from src.services.chat_service import ChatService
from src.api.dependencies import get_current_user, get_chat_service

router = APIRouter()


@router.post(
    "/", 
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation for a document",
)
async def create_conversation(
    request: ConversationCreate, 
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """ 
    reates a new chat conversation linked to a specific processed document.

    A conversation is required before sending any messages. Each conversation belongs exclusively to the authenticated user and is scoped to a single document.

    **Body (`ConversationCreate`):**
    | Field | Required | Description |
    |---|---|---|
    | `document_id` | ✅ | UUID of the processed document to chat about |
    | `title` | ❌ | Optional display name (defaults to `"Untitled"`) |

    **Returns:** `ConversationResponse` with `id`, `user_id`, `document_id`, `title`, and `created_at`.

    """
    return await chat_service.create_conversation(current_user.id, request)


@router.post(
    "/{conversation_id}/chat", 
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message and receive a grounded AI response",
)
async def chat(
    conversation_id: str = Path(..., description="UUID of the conversation"),
    request: ChatRequest = Depends(), 
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Sends a user message to the AI assistant within the given conversation.

    The assistant retrieves the most relevant chunks from the linked document via semantic search, then generates a grounded answer using the configured LLM.
    The full exchange (user message + assistant response) is persisted and included in conversation history.

    **Path parameter:**
    - `conversation_id` — UUID of the conversation

    **Body (`ChatRequest`):**
    | Field | Default | Description |
    |---|---|---|
    | `message` | *(required)* | User question (1–2000 characters) |
    | `top_k` | `10` | Number of chunks to retrieve for context (1–20) |
    | `similarity_threshold` | `0.2` | Minimum similarity score for retrieved chunks (0.0–1.0) |

    **Returns:** `ChatResponse` with both the user and assistant messages, a list of `citations` (matched chunks with similarity scores), and timestamps.

    """
    return await chat_service.chat(conversation_id, current_user.id, request)





@router.post(
    "/{conversation_id}/chat/stream", 
    status_code=status.HTTP_200_OK,
    summary="Stream an AI response token-by-token via Server-Sent Events",
)
async def stream_chat(
    conversation_id: str = Path(..., description="UUID of the conversation"),
    request: ChatRequest = Depends(), 
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """
    Same as `POST /{conversation_id}/chat` but streams the assistant's response incrementally using **Server-Sent Events (SSE)**.

    The response is streamed as a series of `text/event-stream` events. Each event contains a text delta. The stream ends when the model finishes generating.

    **Headers set automatically:**
    - `Content-Type: text/event-stream`
    - `Cache-Control: no-cache`
    - `Connection: keep-alive`
    - `X-Accel-Buffering: no` (disables Nginx proxy buffering)

    **Path parameter:**
    - `conversation_id` — UUID of the conversation

    **Body (`ChatRequest`):** Same as the non-streaming `chat` endpoint.

    """
    return StreamingResponse(
        chat_service.chat_stream(conversation_id, current_user.id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



@router.get(
    "/{conversation_id}/history", 
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve the full message history of a conversation",
)
async def get_conversation_history(
    conversation_id: str = Path(..., description="UUID of the conversation"),
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationHistoryResponse:
    """
    Returns all messages in a conversation in chronological order, including citations attached to each assistant message.

    **Path parameter:**
    - `conversation_id` — UUID of the conversation

    **Returns:** `ConversationHistoryResponse` containing:
    - `conversation_id`, `document_id`, `title`
    - `messages` — ordered list of `MessageWithCitations`, each with `role` (`user` | `assistant`), `content`, `created_at`, and optional `citations`
    """
    return await chat_service.get_conversation_history(conversation_id, current_user.id)


@router.delete(
    "/{conversation_id}", 
    status_code=status.HTTP_200_OK,
    summary="Delete a conversation and all its messages",
)
async def delete_conversation(
    conversation_id: str = Path(..., description="UUID of the conversation"),
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> Dict:
    """
    Permanently deletes a conversation and all associated messages and citations.

    **Path parameter:**
    - `conversation_id` — UUID of the conversation to delete

    **Returns:** `{ "message": "Conversation deleted successfully" }`

    """
    return await chat_service.delete_conversation(conversation_id, current_user.id)



@router.get(
    "/", 
    response_model=List[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List all conversations for the authenticated user",
)
async def get_user_conversations(
    current_user: UserResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> List[ConversationResponse]:
    """
    Returns all conversations belonging to the authenticated user, ordered by `created_at` descending.

    Each conversation is linked to a document and has a title.
    To retrieve messages within a conversation, use `GET /{conversation_id}/history`.

    **Returns:** List of `ConversationResponse` objects.
    """
    return await chat_service.get_user_conversations(current_user.id)