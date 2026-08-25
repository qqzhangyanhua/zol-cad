from __future__ import annotations

from dataclasses import dataclass

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_FILE_SIZE_MB = 20
MAX_PDF_PAGES = 20

PDF_MEDIA_TYPE = "application/pdf"

ALLOWED_MEDIA_LABELS = ("PDF", "JPEG", "PNG", "WebP", "TIFF")

_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_TIFF_LE = b"II*\x00"
_TIFF_BE = b"MM\x00*"


def detect_media_type(content: bytes) -> str | None:
    """Identify PDF / common image types from magic bytes. Does no IO."""
    if content.startswith(b"%PDF"):
        return PDF_MEDIA_TYPE
    if content.startswith(_JPEG):
        return "image/jpeg"
    if content.startswith(_PNG):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    if content.startswith(_TIFF_LE) or content.startswith(_TIFF_BE):
        return "image/tiff"
    return None


def format_megabytes(byte_size: int) -> str:
    megabytes = byte_size / (1024 * 1024)
    text = f"{megabytes:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return f"{text} MB"


@dataclass(frozen=True)
class AcceptedDrawingFile:
    original_filename: str
    content: bytes
    media_type: str
    byte_size: int
    page_count: int
    selected_page: int


def assess_drawing_upload(
    *,
    original_filename: str,
    content: bytes,
    selected_page: int,
    pdf_page_count: int | None,
) -> AcceptedDrawingFile | str:
    """Return an accepted file or a rejection message that names the reason and limits."""
    display_name = original_filename or "未命名文件"
    byte_size = len(content)
    media_type = detect_media_type(content)
    if media_type is None:
        allowed = "、".join(ALLOWED_MEDIA_LABELS)
        return f"文件「{display_name}」不是 PDF 或常见图片（支持 {allowed}）"
    if byte_size > MAX_FILE_BYTES:
        return (
            f"文件「{display_name}」超出单文件大小上限（{MAX_FILE_SIZE_MB} MB），"
            f"当前为 {format_megabytes(byte_size)}"
        )
    if media_type == PDF_MEDIA_TYPE:
        if pdf_page_count is None or pdf_page_count < 1:
            return f"文件「{display_name}」无法读取 PDF 页数"
        if pdf_page_count > MAX_PDF_PAGES:
            return (
                f"文件「{display_name}」超出 PDF 页数上限（{MAX_PDF_PAGES} 页），"
                f"当前为 {pdf_page_count} 页"
            )
        if selected_page < 1 or selected_page > pdf_page_count:
            return (
                f"文件「{display_name}」指定页码 {selected_page} 超出范围"
                f"（该文件共 {pdf_page_count} 页）"
            )
        page_count = pdf_page_count
        page = selected_page
    else:
        page_count = 1
        page = 1
    return AcceptedDrawingFile(
        original_filename=display_name[:500],
        content=content,
        media_type=media_type,
        byte_size=byte_size,
        page_count=page_count,
        selected_page=page,
    )
