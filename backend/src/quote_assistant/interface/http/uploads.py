from __future__ import annotations

from typing import Protocol

from quote_assistant.domain.drawing_upload import (
    MAX_FILE_BYTES,
    MAX_FILE_SIZE_MB,
    format_megabytes,
)

READ_CHUNK_BYTES = 64 * 1024


class ReadableUpload(Protocol):
    filename: str | None

    async def read(self, size: int = -1) -> bytes: ...

    async def close(self) -> None: ...


async def read_upload_bounded(
    upload: ReadableUpload,
    limit: int = MAX_FILE_BYTES,
) -> bytes | str:
    """Read an upload incrementally. Over-limit files abort without keeping the bytes."""
    display_name = upload.filename or "未命名文件"
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            chunks.clear()
            try:
                await upload.close()
            except Exception:
                pass
            return (
                f"文件「{display_name}」超出单文件大小上限（{MAX_FILE_SIZE_MB} MB），"
                f"当前为 {format_megabytes(total)}"
            )
        chunks.append(chunk)
    return b"".join(chunks)
