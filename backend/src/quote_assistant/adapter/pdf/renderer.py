from __future__ import annotations

from io import BytesIO

import pypdfium2 as pdfium

from quote_assistant.domain.drawing_upload import PDF_MEDIA_TYPE
from quote_assistant.domain.errors import PageRenderFailed
from quote_assistant.domain.extraction import RenderedPage

RENDERED_MEDIA_TYPE = "image/png"

# Engineering drawings carry small dimension text; 72 DPI (the PDF default) is not
# legible enough for a multimodal model. The pixel cap keeps a large-format A0 sheet
# from turning into an image no vendor will accept.
DEFAULT_RENDER_DPI = 200
DEFAULT_MAX_PIXELS = 4000


class PdfiumDrawingPageRenderer:
    """Rasterize the 报价员's selected PDF page. Images pass through untouched."""

    def __init__(
        self,
        dpi: int = DEFAULT_RENDER_DPI,
        max_pixels: int = DEFAULT_MAX_PIXELS,
    ) -> None:
        self._dpi = dpi
        self._max_pixels = max_pixels

    def render(self, content: bytes, media_type: str, selected_page: int) -> RenderedPage:
        if media_type != PDF_MEDIA_TYPE:
            return RenderedPage(content=content, media_type=media_type)
        try:
            document = pdfium.PdfDocument(content)
        except Exception as exc:
            raise PageRenderFailed("零件图 PDF 无法打开，请重新上传或改用图片") from exc
        try:
            page_count = len(document)
            if selected_page < 1 or selected_page > page_count:
                raise PageRenderFailed(
                    f"指定处理第 {selected_page} 页，但该零件图共 {page_count} 页"
                )
            page = document[selected_page - 1]
            image = page.render(scale=self._scale_for(page)).to_pil()
            buffer = BytesIO()
            image.save(buffer, format="PNG")
        except PageRenderFailed:
            raise
        except Exception as exc:
            raise PageRenderFailed(
                f"零件图第 {selected_page} 页渲染失败，请重试或改用图片"
            ) from exc
        finally:
            document.close()
        return RenderedPage(content=buffer.getvalue(), media_type=RENDERED_MEDIA_TYPE)

    def _scale_for(self, page: pdfium.PdfPage) -> float:
        scale = self._dpi / 72
        longest_point_side = max(page.get_width(), page.get_height())
        if longest_point_side <= 0:
            return scale
        return min(scale, self._max_pixels / longest_point_side)
