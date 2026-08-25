from __future__ import annotations

from pathlib import Path

from quote_assistant.adapter.storage.local import LocalDirectoryObjectStorage
from quote_assistant.adapter.storage.oss import OssObjectStorage
from quote_assistant.config import Settings


def build_object_storage(settings: Settings) -> LocalDirectoryObjectStorage | OssObjectStorage:
    if settings.object_store_backend == "oss":
        missing = [
            name
            for name, value in (
                ("QA_OSS_ACCESS_KEY_ID", settings.oss_access_key_id),
                ("QA_OSS_ACCESS_KEY_SECRET", settings.oss_access_key_secret),
                ("QA_OSS_ENDPOINT", settings.oss_endpoint),
                ("QA_OSS_BUCKET", settings.oss_bucket),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("OSS 配置不完整，缺少：" + "、".join(missing))
        return OssObjectStorage(
            access_key_id=settings.oss_access_key_id,
            access_key_secret=settings.oss_access_key_secret,
            endpoint=settings.oss_endpoint,
            bucket_name=settings.oss_bucket,
        )
    root = Path(settings.local_object_dir)
    root.mkdir(parents=True, exist_ok=True)
    return LocalDirectoryObjectStorage(
        root=root,
        public_base_url=settings.public_base_url,
        sign_secret=settings.object_sign_secret,
    )
