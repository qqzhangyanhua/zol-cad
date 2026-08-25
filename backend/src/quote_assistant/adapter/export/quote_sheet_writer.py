from __future__ import annotations

import csv
from io import BytesIO, StringIO

from openpyxl import Workbook

from quote_assistant.domain.quote_sheet import QuoteSheetFileFormat


class OpenpyxlQuoteSheetFileWriter:
    """Generate xlsx / csv bytes. Domain rules do not live here."""

    def write(
        self,
        headers: tuple[str, ...],
        rows: tuple[tuple[str, ...], ...],
        file_format: QuoteSheetFileFormat,
    ) -> bytes:
        if file_format is QuoteSheetFileFormat.CSV:
            return _write_csv(headers, rows)
        return _write_xlsx(headers, rows)


def _write_csv(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _write_xlsx(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "报价底稿"
    sheet.append(list(headers))
    for row in rows:
        sheet.append(list(row))
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
