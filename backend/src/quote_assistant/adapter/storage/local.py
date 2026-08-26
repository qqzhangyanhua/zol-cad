from __future__ import annotations

import hashlib
import hmac
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote


class LocalDirectoryObjectStorage:
    """Object storage backed by a local directory. Used in tests and local development."""

    def __init__(self, root: Path, public_base_url: str, sign_secret: str) -> None:
        self._root = root
        self._public_base_url = public_base_url.rstrip("/")
        self._sign_secret = sign_secret.encode("utf-8")

    def store(self, key: str, content: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self._content_type_path(path).write_text(content_type, encoding="utf-8")

    def fetch(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def content_type_of(self, key: str) -> str:
        sidecar = self._content_type_path(self._path(key))
        if sidecar.is_file():
            return sidecar.read_text(encoding="utf-8").strip() or "application/octet-stream"
        return "application/octet-stream"

    def sign_access_url(self, key: str, ttl: timedelta) -> str:
        expires = int(time.time() + ttl.total_seconds())
        signature = self._sign(key, expires)
        quoted = quote(key, safe="/")
        path = f"/object-store/{quoted}?expires={expires}&sig={signature}"
        if self._public_base_url:
            return f"{self._public_base_url}{path}"
        return path

    def verify_signature(self, key: str, expires: int, signature: str) -> bool:
        if expires <= int(time.time()):
            return False
        expected = self._sign(key, expires)
        return hmac.compare_digest(expected, signature)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()
        sidecar = self._content_type_path(path)
        if sidecar.is_file():
            sidecar.unlink()

    def _path(self, key: str) -> Path:
        parts = [part for part in key.split("/") if part]
        if not parts or any(part == ".." for part in parts):
            raise ValueError("非法对象键")
        return self._root.joinpath(*parts)

    def _sign(self, key: str, expires: int) -> str:
        payload = f"{key}:{expires}".encode()
        return hmac.new(self._sign_secret, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _content_type_path(path: Path) -> Path:
        return path.with_name(path.name + ".content-type")
