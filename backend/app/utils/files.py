"""Safe file utilities for uploads."""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


ALLOWED_EXT = {".csv", ".xlsx", ".xls", ".pdf", ".docx"}

# First-bytes "magic numbers" for cheap MIME sniffing.
MAGIC_PREFIXES: dict[str, bytes] = {
    ".pdf": b"%PDF-",
    ".xlsx": b"PK\x03\x04",  # actually a ZIP
    ".docx": b"PK\x03\x04",
    ".xls": b"\xD0\xCF\x11\xE0",
}


def _ext(name: str) -> str:
    return Path(name).suffix.lower()


def safe_filename(original: str) -> tuple[str, str]:
    """Return ``(uuid_filename, ext)`` derived from ``original``.

    The extension is preserved (lowercased, validated). The base is a uuid4 to
    avoid collisions and path-traversal attempts via crafted filenames.
    """
    ext = _ext(original)
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension: {ext}",
        )
    return f"{uuid.uuid4().hex}{ext}", ext


def validate_size_and_save(upload: UploadFile) -> tuple[Path, int, str, str]:
    """Persist ``upload`` to ``settings.upload_path`` after validating extension + size.

    Returns ``(disk_path, size_bytes, ext, original_name)``.
    """
    name, ext = safe_filename(upload.filename or "uploaded.bin")
    disk_path = settings.upload_path / name

    size = 0
    chunk = 64 * 1024
    head: bytes | None = None
    with disk_path.open("wb") as out:
        while True:
            buf = upload.file.read(chunk)
            if not buf:
                break
            if head is None:
                head = buf[:8]
            size += len(buf)
            if size > settings.max_upload_bytes:
                out.close()
                disk_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {settings.max_upload_bytes} bytes",
                )
            out.write(buf)

    # Cheap magic-number sniff (skip CSV — it has no canonical signature).
    expected = MAGIC_PREFIXES.get(ext)
    if expected and head is not None and not head.startswith(expected):
        disk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File contents do not match extension {ext}",
        )

    return disk_path, size, ext, upload.filename or name


def guess_mime(name: str) -> str:
    return mimetypes.guess_type(name)[0] or "application/octet-stream"
