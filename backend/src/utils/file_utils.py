from fastapi import UploadFile, HTTPException, status
from typing import List
import os
from datetime import datetime, timezone
from src.core.config import settings
import hashlib
import unicodedata


def validate_file(
    file: UploadFile,
    max_file_size: int,
    allowed_mime_types: List[str] = ["application/pdf"],
) -> None:
    
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .pdf extension",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty"
        )


def generate_unique_filename(
    original_filename: str,
    user_id: str
) -> str:
    
    name, ext = os.path.splitext(original_filename)

    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_name = safe_name.replace(" ", "_")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    return f"{user_id}/{timestamp}_{safe_name}{ext}"


def calculate_file_hash(
    file_content: bytes
) -> str:
    
    return hashlib.sha256(file_content).hexdigest()
