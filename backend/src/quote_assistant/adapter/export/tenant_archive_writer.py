from __future__ import annotations

import zipfile
from io import BytesIO

from quote_assistant.domain.tenant_data import TenantArchiveFile


class ZipTenantArchiveWriter:
    """Pack already-built export files into a zip. Domain rules do not live here."""

    def write(self, files: tuple[TenantArchiveFile, ...]) -> bytes:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in files:
                archive.writestr(file.path, file.content)
        return buffer.getvalue()
