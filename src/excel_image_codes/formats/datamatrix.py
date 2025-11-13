"""Data Matrix format implementation."""

from __future__ import annotations

import io
from typing import Set, Tuple

from PIL import Image, ImageOps
from pystrich.datamatrix import DataMatrixEncoder

from ..base_format import CodeImageFormat
from ..registry import register_format


class DataMatrixFormat(CodeImageFormat):
    name = "datamatrix"

    @classmethod
    def supported_extensions(cls) -> Set[str]:
        return {".png", ".jpg", ".jpeg"}

    def render(
        self,
        data: str,
        ext: str,
        *,
        human_readable: bool | None = None,
        background_color: str | None = None,
    ) -> Tuple[str, bytes]:
        del human_readable  # Data Matrix symbols do not have human-readable captions.
        ext = self.normalize_extension(ext)
        encoder = DataMatrixEncoder(data)
        renderer = encoder.init_renderer()
        grayscale = renderer.get_pilimage(cellsize=5).convert("L")
        mask = ImageOps.invert(grayscale)
        modules = Image.new("RGB", grayscale.size, "black")
        bg_color = background_color or "#FFFFFF"
        background = Image.new("RGB", grayscale.size, bg_color)
        img = Image.composite(modules, background, mask)
        buffer = io.BytesIO()
        fmt = "PNG" if ext == ".png" else "JPEG"
        content_type = "image/png" if ext == ".png" else "image/jpeg"
        img.save(buffer, format=fmt)
        return content_type, buffer.getvalue()


class DataMaxtrixFormat(DataMatrixFormat):
    """Backwards compatible alias for the commonly misspelled name."""

    name = "datamaxtrix"


register_format(DataMatrixFormat)
register_format(DataMaxtrixFormat)
