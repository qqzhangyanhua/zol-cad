from __future__ import annotations

import threading
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized bodies from Content-Length before multipart parsing buffers them."""

    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw = request.headers.get("content-length")
        if raw:
            try:
                length = int(raw)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "无效的 Content-Length"})
            if length > self._max_bytes:
                return JSONResponse(status_code=413, content={"detail": "请求体超出上限"})
        return await call_next(request)


class _SlidingWindow:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            cutoff = now - self._window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self._max_requests:
                return False
            bucket.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-process limits for login and upload. Not a WAF; one process is the deploy shape."""

    def __init__(
        self,
        app,
        *,
        login_per_minute: int,
        upload_per_minute: int,
    ) -> None:
        super().__init__(app)
        self._login = _SlidingWindow(login_per_minute, 60.0)
        self._upload = _SlidingWindow(upload_per_minute, 60.0)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path.rstrip("/") or "/"
        if request.method == "POST" and path == "/auth/login":
            limiter, label = self._login, "登录"
        elif request.method == "POST" and path == "/part-drawings":
            limiter, label = self._upload, "上传"
        else:
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        if not limiter.allow(key):
            return JSONResponse(
                status_code=429,
                content={"detail": f"{label}过于频繁，请稍后再试"},
            )
        return await call_next(request)
