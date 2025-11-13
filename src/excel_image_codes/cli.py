"""Command line entry point for excel-image-codes."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from . import get_available_formats, render_image
from .server import run_server


def _add_render_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("data", help="Data string to encode")
    parser.add_argument("-f", "--format", required=True, help="Format name (e.g. qr, code128)")
    parser.add_argument("-e", "--ext", required=True, help="File extension (png, jpg, svg)")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output file. If omitted, bytes are written to stdout.",
    )
    parser.add_argument(
        "-b",
        "--background",
        help="Optional background colour. Accepts hex (ffcc00, #ffcc00) or CSS names (gold).",
    )
    parser.set_defaults(human_readable=None)
    parser.add_argument(
        "--human-readable",
        dest="human_readable",
        action="store_true",
        help="Include human-readable text beneath barcodes when supported.",
    )
    parser.add_argument(
        "--no-human-readable",
        dest="human_readable",
        action="store_false",
        help="Suppress human-readable text where possible.",
    )


def _add_serve_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="excel-image-codes", description="QR and barcode helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the HTTP server")
    _add_serve_arguments(serve_parser)

    render_parser = subparsers.add_parser("render", help="Render a single image")
    _add_render_arguments(render_parser)

    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="Print available formats and exit",
    )
    return parser.parse_args(argv)


def _handle_render(args: argparse.Namespace) -> int:
    try:
        content_type, payload = render_image(
            args.format,
            args.data,
            args.ext,
            human_readable=args.human_readable,
            background_color=args.background,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output = args.output
    if output:
        with open(output, "wb") as fh:
            fh.write(payload)
    else:
        sys.stdout.buffer.write(payload)
    return 0


def _handle_serve(args: argparse.Namespace) -> int:
    run_server(host=args.host, port=args.port)
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_formats:
        for name in get_available_formats():
            print(name)
        return 0

    if args.command == "render":
        return _handle_render(args)
    if args.command == "serve":
        return _handle_serve(args)

    print("Unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
