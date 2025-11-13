"""Tiny HTTP server exposing code images over simple URLs."""

from __future__ import annotations

import http.server
import logging
import socketserver
from typing import Dict, Tuple
from urllib.parse import unquote

from .colors import looks_like_colour_token
from .registry import render_image

LOGGER = logging.getLogger(__name__)


class ExcelImageRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "ExcelImageCodes/0.1"

    HUMAN_TRUE = {"hr", "human", "with-text", "withtext", "text", "readable", "yes", "1"}
    HUMAN_FALSE = {"nohr", "plain", "raw", "without-text", "withouttext", "notext", "no", "0"}

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        try:
            format_name, data, ext, human_readable, background = self._parse_path(self.path)
        except ValueError as exc:
            self._respond(404, str(exc))
            return

        try:
            content_type, payload = render_image(
                format_name,
                data,
                ext,
                human_readable=human_readable,
                background_color=background,
            )
        except ValueError as exc:
            self._respond(400, str(exc))
            return
        except Exception:  # pragma: no cover - unexpected failures
            LOGGER.exception("Unexpected server error")
            self._respond(500, "Internal server error")
            return

        headers = {
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000, immutable",
        }
        self._respond(200, payload, headers=headers)

    def _respond(self, status: int, payload: bytes | str, headers: Dict[str, str] | None = None) -> None:
        body: bytes
        content_headers = headers or {}
        if isinstance(payload, str):
            body = payload.encode("utf-8")
            content_headers.setdefault("Content-Type", "text/plain; charset=utf-8")
        else:
            body = payload
        self.send_response(status)
        content_headers.setdefault("Content-Length", str(len(body)))
        for key, value in content_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _parse_path(self, path: str) -> Tuple[str, str, str, bool | None, str | None]:
        """Return (format, data, extension, human_readable, background) from *path*."""

        if not path or path == "/":
            raise ValueError("Missing format or data segment")
        stripped = path.lstrip("/")
        segments = stripped.split("/")
        if len(segments) < 2:
            raise ValueError("Path must look like /<format>/<data>.<ext>")
        format_name = segments[0]
        if not format_name:
            raise ValueError("Format segment is empty")

        background: str | None = None
        human_readable: bool | None = None
        option_segments = segments[1:-1]
        data_segment = segments[-1]
        if len(option_segments) > 2:
            raise ValueError(
                "Path supports at most colour and human-readable segments before the data"
            )
        if option_segments:
            first = option_segments[0]
            if self._is_color_segment(first):
                background = first
                option_segments = option_segments[1:]
            elif len(option_segments) == 2:
                raise ValueError("Colour segments must precede the human-readable flag")
        if option_segments:
            human_readable = self._parse_human_flag(option_segments[0])

        if "." not in data_segment:
            raise ValueError("Missing extension in path")
        data_encoded, ext = data_segment.rsplit(".", 1)
        if not data_encoded:
            raise ValueError("Data segment is empty")
        data = unquote(data_encoded)
        ext = f".{ext}"
        return format_name, data, ext, human_readable, background

    def _parse_human_flag(self, flag: str) -> bool:
        lowered = flag.lower()
        if lowered in self.HUMAN_TRUE:
            return True
        if lowered in self.HUMAN_FALSE:
            return False
        raise ValueError(
            "Unknown human-readable flag. Use hr/nohr (or human/raw) before the data segment."
        )

    def _is_color_segment(self, segment: str) -> bool:
        return looks_like_colour_token(segment)

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - BaseHTTPRequestHandler API
        LOGGER.info("%s - - %s", self.client_address[0], format % args)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the HTTP server and block forever."""

    server = ThreadedHTTPServer((host, port), ExcelImageRequestHandler)
    host_display = host
    if host_display == "0.0.0.0":
        host_display = "localhost"
    LOGGER.info("Serving excel-image-codes on http://%s:%s", host_display, server.server_port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        LOGGER.info("Shutting down server")
    finally:
        server.server_close()
