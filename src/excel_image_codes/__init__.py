"""Public API for excel_image_codes."""

from __future__ import annotations

from .registry import available_formats, get_format, render_image

__all__ = ["available_formats", "get_format", "render_image"]


def get_available_formats() -> list[str]:
    """Convenience wrapper returning the list of available formats."""

    return available_formats()
