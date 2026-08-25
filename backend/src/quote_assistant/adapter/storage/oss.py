from __future__ import annotations

from datetime import timedelta

import oss2


class OssObjectStorage:
    """阿里云 OSS adapter.

    The bucket must stay private (no public-read ACL). Every put enables
    server-side AES256 encryption. Callers obtain bytes only through
    short-lived signed URLs.
    """

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
    ) -> None:
        auth = oss2.Auth(access_key_id, access_key_secret)
        self._bucket = oss2.Bucket(auth, endpoint, bucket_name)

    def store(self, key: str, content: bytes, content_type: str) -> None:
        headers = {
            "Content-Type": content_type,
            "x-oss-server-side-encryption": "AES256",
            "x-oss-object-acl": "private",
        }
        self._bucket.put_object(key, content, headers=headers)

    def fetch(self, key: str) -> bytes:
        result = self._bucket.get_object(key)
        return result.read()

    def sign_access_url(self, key: str, ttl: timedelta) -> str:
        return self._bucket.sign_url(
            "GET",
            key,
            int(ttl.total_seconds()),
            slash_safe=True,
        )

    def delete(self, key: str) -> None:
        self._bucket.delete_object(key)
