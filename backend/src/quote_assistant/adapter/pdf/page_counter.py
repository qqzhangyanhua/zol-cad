from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from quote_assistant.domain.errors import PdfUnreadable


class PypdfPageCounter:
    def count_pages(self, content: bytes) -> int:
        try:
            reader = PdfReader(BytesIO(content))
            return len(reader.pages)
        except PyPdfError as exc:
            raise PdfUnreadable() from exc
        except Exception as exc:
            raise PdfUnreadable() from exc
