"""Central registry for image formats and caching helpers."""

from __future__ import annotations

import importlib
import pkgutil
import string
import threading
from typing import Dict, List, Tuple, Type

from .base_format import CodeImageFormat

_FORMATS: Dict[str, Type[CodeImageFormat]] = {}
_FORMAT_INSTANCES: Dict[str, CodeImageFormat] = {}
_CACHE: Dict[Tuple[str, str, str, bool | None, str | None], Tuple[str, bytes]] = {}
_CACHE_LOCK = threading.Lock()


def register_format(format_cls: Type[CodeImageFormat]) -> None:
    """Register *format_cls* under its ``name`` attribute."""

    if not format_cls.name:
        raise ValueError("Format classes must define a non-empty 'name' attribute")
    key = format_cls.name.lower()
    _FORMATS[key] = format_cls


def get_format(name: str) -> CodeImageFormat:
    """Return an instance of the named format."""

    key = name.lower()
    format_cls = _FORMATS.get(key)
    if format_cls is None:
        raise ValueError(f"Unknown format '{name}'. Available: {', '.join(available_formats())}")
    if key not in _FORMAT_INSTANCES:
        _FORMAT_INSTANCES[key] = format_cls()
    return _FORMAT_INSTANCES[key]


def available_formats() -> List[str]:
    """Return the sorted list of available format names."""

    return sorted(_FORMATS.keys())


def _load_builtin_formats() -> None:
    """Import every module inside ``excel_image_codes.formats`` once."""

    package = __name__.rsplit(".", 1)[0] + ".formats"
    pkg = importlib.import_module(package)
    for module in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):
        importlib.import_module(module.name)


def _normalize_background(color: str | None) -> str | None:
    if color is None:
        return None
    value = color.strip().lower()
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6 or any(ch not in string.hexdigits.lower() for ch in value):
        raise ValueError("Background colour must be a hex string like 'ff00aa'.")
    return f"#{value.upper()}"


def render_image(
    format_name: str,
    data: str,
    ext: str,
    *,
    human_readable: bool | None = None,
    background_color: str | None = None,
) -> Tuple[str, bytes]:
    """Render *data* for ``format_name`` and ``ext`` with caching."""

    ext = CodeImageFormat.normalize_extension(ext)
    normalized_color = _normalize_background(background_color)
    cache_key = (format_name.lower(), data, ext, human_readable, normalized_color)
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None:
            return cached

    fmt = get_format(format_name)
    fmt.validate_extension(ext)
    result = fmt.render(
        data,
        ext,
        human_readable=human_readable,
        background_color=normalized_color,
    )
    with _CACHE_LOCK:
        _CACHE[cache_key] = result
    return result


def clear_cache() -> None:
    """Clear the in-memory render cache (useful for tests)."""

    with _CACHE_LOCK:
        _CACHE.clear()


# Auto-load built-in formats on import.
_load_builtin_formats()
