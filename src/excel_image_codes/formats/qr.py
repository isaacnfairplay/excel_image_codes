"""QR code format implementation."""

from __future__ import annotations

import io
from typing import Set, Tuple

import qrcode
from qrcode.image.svg import SvgImage

from ..base_format import CodeImageFormat
from ..registry import register_format


class QRCodeFormat(CodeImageFormat):
    name = "qr"

    @classmethod
    def supported_extensions(cls) -> Set[str]:
        return {".png", ".jpg", ".jpeg", ".svg"}

    def render(
        self,
        data: str,
        ext: str,
        *,
        human_readable: bool | None = None,
        background_color: str | None = None,
    ) -> Tuple[str, bytes]:
        del human_readable  # QR codes have no human-readable toggle.
        ext = self.normalize_extension(ext)
        back_color = background_color or "white"
        if ext == ".svg":
            img = qrcode.make(data, image_factory=SvgImage, back_color=back_color, fill_color="black")
            buffer = io.BytesIO()
            img.save(buffer)
            return "image/svg+xml", buffer.getvalue()

        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color=back_color).convert("RGB")
        fmt = "PNG" if ext == ".png" else "JPEG"
        content_type = "image/png" if ext == ".png" else "image/jpeg"
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return content_type, buffer.getvalue()


register_format(QRCodeFormat)
