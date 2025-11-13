"""EAN-13 barcode implementation with validation."""

from __future__ import annotations

import io
from typing import Dict, Set, Tuple

from barcode import get_barcode_class
from barcode.writer import ImageWriter, SVGWriter
from PIL import Image

from ..base_format import CodeImageFormat
from ..registry import register_format


class EAN13Format(CodeImageFormat):
    name = "ean13"

    @classmethod
    def supported_extensions(cls) -> Set[str]:
        return {".png", ".jpg", ".jpeg", ".svg"}

    def _writer_options(
        self,
        human_readable: bool | None,
        background_color: str | None,
    ) -> Dict[str, object]:
        enabled = True if human_readable is None else human_readable
        options: Dict[str, object] = {"write_text": enabled, "foreground": "black"}
        if background_color:
            options["background"] = background_color
        return options

    def _validate_data(self, data: str) -> str:
        if len(data) != 13 or not data.isdigit():
            raise ValueError("EAN-13 input must be a 13-digit numeric string")
        body, checksum = data[:-1], data[-1]
        expected = self._checksum_digit(body)
        if checksum != expected:
            raise ValueError(f"Invalid EAN-13 checksum: expected {expected}, got {checksum}")
        return body

    def _checksum_digit(self, body: str) -> str:
        digits = [int(char) for char in body]
        odd_sum = sum(digits[::2])
        even_sum = sum(digits[1::2])
        total = odd_sum + even_sum * 3
        return str((10 - (total % 10)) % 10)

    def _render_svg(self, data: str, human_readable: bool | None, background_color: str | None) -> Tuple[str, bytes]:
        body = self._validate_data(data)
        barcode_cls = get_barcode_class("ean13")
        writer = SVGWriter()
        buffer = io.BytesIO()
        barcode_cls(body, writer=writer).write(
            buffer,
            options=self._writer_options(human_readable, background_color),
        )
        return "image/svg+xml", buffer.getvalue()

    def _render_raster(
        self,
        data: str,
        ext: str,
        human_readable: bool | None,
        background_color: str | None,
    ) -> Tuple[str, bytes]:
        body = self._validate_data(data)
        barcode_cls = get_barcode_class("ean13")
        writer = ImageWriter()
        buffer = io.BytesIO()
        barcode_cls(body, writer=writer).write(
            buffer,
            options=self._writer_options(human_readable, background_color),
        )
        if ext == ".png":
            return "image/png", buffer.getvalue()
        image = Image.open(io.BytesIO(buffer.getvalue())).convert("RGB")
        jpeg_buffer = io.BytesIO()
        image.save(jpeg_buffer, format="JPEG")
        return "image/jpeg", jpeg_buffer.getvalue()

    def render(
        self,
        data: str,
        ext: str,
        *,
        human_readable: bool | None = None,
        background_color: str | None = None,
    ) -> Tuple[str, bytes]:
        ext = self.normalize_extension(ext)
        if ext == ".svg":
            return self._render_svg(data, human_readable, background_color)
        return self._render_raster(data, ext, human_readable, background_color)


register_format(EAN13Format)
