from __future__ import annotations

from urllib.parse import quote, unquote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from quote_assistant.adapter.storage.local import LocalDirectoryObjectStorage

router = APIRouter(tags=["object-store"])


@router.get("/object-store/{object_key:path}")
def fetch_signed_object(
    object_key: str,
    request: Request,
    expires: int | None = None,
    sig: str | None = None,
) -> Response:
    storage = request.app.state.object_storage
    if not isinstance(storage, LocalDirectoryObjectStorage):
        raise HTTPException(status_code=404, detail="对象不存在")
    key = unquote(object_key)
    if expires is None or not sig:
        raise HTTPException(status_code=403, detail="临时访问链接无效或已过期")
    if not storage.verify_signature(key, expires, sig):
        raise HTTPException(status_code=403, detail="临时访问链接无效或已过期")
    try:
        content = storage.fetch(key)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="对象不存在") from exc
    filename = key.rsplit("/", 1)[-1]
    quoted_name = quote(filename)
    return Response(
        content=content,
        media_type=storage.content_type_of(key),
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quoted_name}",
            "Cache-Control": "private, max-age=60",
        },
    )
