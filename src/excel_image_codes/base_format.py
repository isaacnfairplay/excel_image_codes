"""Base class for all code image formats."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Set, Tuple


class CodeImageFormat(ABC):
    """Abstract interface for image-producing formats."""

    #: Human-friendly name used in URLs/CLI switches.
    name: str = ""

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> Set[str]:
        """Return the set of supported extensions (including leading dots)."""

    @abstractmethod
    def render(
        self,
        data: str,
        ext: str,
        *,
        human_readable: bool | None = None,
        background_color: str | None = None,
    ) -> Tuple[str, bytes]:
        """Render *data* into *ext* and return (content_type, bytes).

        ``human_readable`` communicates whether the caller expects human-readable text
        (such as digits underneath a barcode). ``None`` signals the format should use
        its default behaviour.

        ``background_color`` is an optional hexadecimal RGB string (``#RRGGBB``)
        describing the image background colour. Formats that do not support custom
        backgrounds may ignore it.
        """

    @classmethod
    def normalize_extension(cls, ext: str) -> str:
        """Normalize an extension to its canonical lowercase dotted form."""

        ext = ext.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext

    @classmethod
    def validate_extension(cls, ext: str) -> str:
        """Ensure *ext* is supported and return the normalized value."""

        normalized = cls.normalize_extension(ext)
        if normalized not in cls.supported_extensions():
            supported = ", ".join(sorted(cls.supported_extensions()))
            raise ValueError(
                f"Extension '{ext}' is not supported by {cls.name or cls.__name__}. "
                f"Supported extensions: {supported}."
            )
        return normalized

    @classmethod
    def all_extensions(cls) -> Iterable[str]:
        """Convenience iterator for supported extensions."""

        return cls.supported_extensions()
