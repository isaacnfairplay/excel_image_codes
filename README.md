# excel-image-codes

`excel-image-codes` is a tiny Python toolkit that produces QR codes and barcodes that play nicely with Excel's [`IMAGE()`](https://support.microsoft.com/en-us/office/image-function-629fd048-b64e-4f91-bb60-205b1909640e) function. It ships with a reusable library API, a pluggable format system, a CLI, and a lightweight HTTP server that exposes URLs Excel can fetch directly.

## Features

* 📦 MIT licensed and built entirely on permissively licensed dependencies (`qrcode`, `Pillow`, `python-barcode`).
* 🔌 Pluggable format architecture – add a new encoder by dropping a file into `src/excel_image_codes/formats/`.
* 🧠 Simple in-memory cache shared by the library, CLI, and server for efficient repeated renders.
* 🌐 HTTP server that understands optional path segments for human-readable toggles (`/hr` or `/nohr`) **and** hex background colours (`/<format>/<ffcc00>/<hr>/<data>.png`).
* 🛠 CLI for both rendering single images and running the server, including flags for background colours and human-readable text.

## Installation

```bash
pip install excel-image-codes
```

## Usage

### CLI examples

Start the HTTP server on port 8080:

```bash
excel-image-codes serve --port 8080
```

Render a QR code once and save to a file:

```bash
echo "Hello" | excel-image-codes render --format qr --ext png --output hello.png "Hello"
```

Render a Code128 barcode without the caption text and a pale-yellow background:

```bash
excel-image-codes render --format code128 --ext svg --no-human-readable --background ffefaa "ABC123"
```

### HTTP server

Excel-friendly URL patterns (segments in square brackets are optional):

```
http://localhost:8080/<format>/<ENCODEURL(data)>.<ext>
http://localhost:8080/<format>/<hr|nohr>/<ENCODEURL(data)>.<ext>
http://localhost:8080/<format>/<hex-colour>/<ENCODEURL(data)>.<ext>
http://localhost:8080/<format>/<hex-colour>/<hr|nohr>/<ENCODEURL(data)>.<ext>
```

Examples:

```
http://localhost:8080/qr/Hello%20World.png
http://localhost:8080/code128/nohr/Hello%20World.svg
http://localhost:8080/ean13/ffefaa/hr/5901234123457.png
```

* The optional colour segment must be a 3- or 6-digit hexadecimal RGB string (no leading `#` is required). It controls the image background while keeping barcode lines black.
* Human-readable captions (digits beneath barcodes) can be toggled with the optional `hr` (or `human`) / `nohr` (or `raw`) segment. Omitting the flag keeps the default behaviour for that format.

Excel formula snippet:

```excel
=IMAGE("http://localhost:8080/code128/ffefaa/hr/" & ENCODEURL(A2) & ".svg")
```

### Library API

```python
from excel_image_codes import render_image

content_type, payload = render_image("qr", "Hello world", ".png", background_color="#fff0cc")
with open("hello.png", "wb") as fh:
    fh.write(payload)

_, barcode_svg = render_image(
    "code128",
    "ABC123",
    ".svg",
    human_readable=False,
    background_color="ffefaa",
)
```

## Supported formats and extensions

| Format                      | Extensions                      |
|-----------------------------|----------------------------------|
| `qr`                        | `.png`, `.jpg`, `.jpeg`, `.svg` |
| `code128`                   | `.png`, `.jpg`, `.jpeg`, `.svg` |
| `ean13`                     | `.png`, `.jpg`, `.jpeg`, `.svg` |
| `datamatrix` (`datamaxtrix` alias) | `.png`, `.jpg`, `.jpeg`       |

## Adding a new format

1. Create `src/excel_image_codes/formats/<name>.py`.
2. Subclass `CodeImageFormat` and implement `supported_extensions()` plus `render()`.
3. Call `register_format(YourFormatClass)` at module import time.

The registry automatically exposes your format to the CLI, HTTP server, and library users. You can opt-in to the human-readable or background-colour hints by accepting the keyword arguments in your implementation.

## Caching

The package maintains a thread-safe in-memory cache keyed by `(format, data, extension, human_readable flag, background colour)`. All rendering helpers and the HTTP server check the cache before rendering, which keeps repeated Excel requests fast even when colours or human-readable settings change. The cache lives in-process and is safe to use across threads thanks to a simple lock around the shared dictionary.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Automated releases

Every push to the `main` branch triggers the `Bump version and publish` GitHub
Actions workflow. The workflow performs the following steps automatically:

1. Runs `scripts/bump_version.py` to increment the patch component in
   `pyproject.toml` and commit the change back to `main` with a matching Git
   tag (for example `v0.1.1`).
2. Builds the source distribution and wheel via `python -m build`.
3. Publishes the artifacts to PyPI using the official `pypa/gh-action-pypi-publish`
   action.

To avoid an infinite loop of self-triggered releases, the workflow skips runs
initiated by the `github-actions[bot]` account (which is the identity used for
the commit it creates after bumping the version).

To enable publishing you only need to add a `PYPI_API_TOKEN` secret to the
repository that contains a valid PyPI token with publishing rights for the
`excel-image-codes` project.

## License

MIT © Excel Image Codes Developers
