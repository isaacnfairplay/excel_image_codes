from __future__ import annotations

import threading
import urllib.error
import urllib.request

import pytest

from excel_image_codes import get_available_formats, render_image
from excel_image_codes.registry import clear_cache
from excel_image_codes.server import ExcelImageRequestHandler, ThreadedHTTPServer


def setup_function() -> None:
    clear_cache()


def test_available_formats() -> None:
    formats = get_available_formats()
    for name in ["qr", "code128", "ean13"]:
        assert name in formats


@pytest.mark.parametrize(
    "format_name,data,ext,content_type,human_readable",
    [
        ("qr", "hello", ".png", "image/png", None),
        ("code128", "123456789", ".jpg", "image/jpeg", False),
        ("ean13", "5901234123457", ".svg", "image/svg+xml", True),
    ],
)
def test_render_image(
    format_name: str, data: str, ext: str, content_type: str, human_readable: bool | None
) -> None:
    mime, payload = render_image(format_name, data, ext, human_readable=human_readable)
    assert mime == content_type
    assert isinstance(payload, bytes)
    assert payload


def test_background_colour_toggle() -> None:
    default = render_image("qr", "hello", ".png")[1]
    tinted = render_image("qr", "hello", ".png", background_color="ffcc00")[1]
    assert default != tinted


def test_human_readable_svg_toggle() -> None:
    readable_svg = render_image("code128", "123456789", ".svg", human_readable=True)[1].decode("utf-8")
    silent_svg = render_image("code128", "123456789", ".svg", human_readable=False)[1].decode("utf-8")
    assert "123456789" in readable_svg
    assert "123456789" not in silent_svg


def test_ean13_validation() -> None:
    with pytest.raises(ValueError):
        render_image("ean13", "1234", ".png")


def _start_server() -> ThreadedHTTPServer:
    server = ThreadedHTTPServer(("localhost", 0), ExcelImageRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server._thread = thread  # type: ignore[attr-defined]
    return server


def _stop_server(server: ThreadedHTTPServer) -> None:
    thread = getattr(server, "_thread")
    server.shutdown()
    thread.join()
    server.server_close()


def test_server_serves_images() -> None:
    server = _start_server()
    try:
        host, port = server.server_address
        with urllib.request.urlopen(f"http://{host}:{port}/qr/Hello.png") as response:
            payload = response.read()
            assert response.status == 200
            assert response.headers["Content-Type"] == "image/png"
            assert payload
    finally:
        _stop_server(server)


def test_server_human_flag_and_errors() -> None:
    server = _start_server()
    try:
        host, port = server.server_address
        with urllib.request.urlopen(f"http://{host}:{port}/code128/hr/Hello.png") as response:
            assert response.status == 200
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(f"http://{host}:{port}/code128/unknown/Hello.png")
        assert excinfo.value.code == 404
    finally:
        _stop_server(server)


def test_server_background_segment() -> None:
    server = _start_server()
    try:
        host, port = server.server_address
        url = f"http://{host}:{port}/code128/ffcc00/nohr/Hello.png"
        with urllib.request.urlopen(url) as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "image/png"
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(f"http://{host}:{port}/code128/zzzzzz/Hello.png")
        assert excinfo.value.code == 404
    finally:
        _stop_server(server)
