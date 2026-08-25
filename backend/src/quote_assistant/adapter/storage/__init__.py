from quote_assistant.adapter.storage.factory import build_object_storage
from quote_assistant.adapter.storage.local import LocalDirectoryObjectStorage
from quote_assistant.adapter.storage.oss import OssObjectStorage

__all__ = [
    "LocalDirectoryObjectStorage",
    "OssObjectStorage",
    "build_object_storage",
]
