import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status, Security,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings
from src.schemas.auth import UserResponse
from src.core.clients import get_supabase_client,get_llama_parse_client,get_cohere_embeddings,get_chat_model
from src.services.document_service import DocumentService
from src.services.chunk_service import ChunkService
from src.services.parse_service import ParseService
from src.services.auth_service import AuthService
from src.services.embed_service import EmbedService
from src.services.retrieval_service import RetrievalService
from src.services.process_service import ProcessService
from src.services.chat_service import ChatService

from supabase import AsyncClient
from llama_cloud import AsyncLlamaCloud
from langchain_cohere import CohereEmbeddings
from langchain_core.language_models import BaseChatModel


security = HTTPBearer()


JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
jwks_client = PyJWKClient(JWKS_URL)


def get_current_user(
    token_auth: HTTPAuthorizationCredentials = Security(security),
) -> UserResponse:
    token = token_auth.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[settings.ALGORITHM],
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            leeway=0,
        )

        return UserResponse(
            id=payload["sub"],
            email=payload.get("email"),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_auth_service(
    db: AsyncClient = Depends(get_supabase_client)
) -> AuthService:
    return AuthService(db=db)
    

def get_document_service(
    db: AsyncClient = Depends(get_supabase_client)
) -> DocumentService:
    return DocumentService(
        db=db,
        bucket_name=settings.STORAGE_BUCKET_NAME,
        max_file_size=settings.MAX_FILE_SIZE_MB * 1024 * 1024,
        allowed_mime_types=settings.ALLOWED_MIME_TYPES,
    )
    

def get_parse_service(
    llama: AsyncLlamaCloud = Depends(get_llama_parse_client),
    document_service: DocumentService = Depends(get_document_service),
) -> ParseService:
    return ParseService(llama_client=llama,document_service=document_service)


def get_chunk_service() -> ChunkService:
    return ChunkService()


def get_embed_service(
    embeddings: CohereEmbeddings = Depends(get_cohere_embeddings),
    db: AsyncClient = Depends(get_supabase_client)
) -> EmbedService :
    return EmbedService(
        embeddings=embeddings,
        db=db
    )


def get_process_service(
    document_service: DocumentService = Depends(get_document_service),
    parse_service: ParseService = Depends(get_parse_service),
    chunk_service: ChunkService = Depends(get_chunk_service),
    embed_service: EmbedService = Depends(get_embed_service),
    chat_model: BaseChatModel = Depends(get_chat_model),
) -> ProcessService:
    
    return ProcessService(
        document_service=document_service,
        parse_service=parse_service,
        chunk_service=chunk_service,
        embed_service=embed_service,
        chat_model=chat_model,
    )


def get_retrieval_service(
    embeddings: CohereEmbeddings = Depends(get_cohere_embeddings),
    db: AsyncClient = Depends(get_supabase_client)
) -> RetrievalService:
    return RetrievalService(embeddings=embeddings, db=db)


def get_chat_service(
    db: AsyncClient = Depends(get_supabase_client),
    chat_model: BaseChatModel = Depends(get_chat_model),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    document_service: DocumentService = Depends(get_document_service)
) -> ChatService:
    return ChatService(
        db=db,
        chat_model=chat_model,
        retrieval_service=retrieval_service,
        document_service=document_service
    )  