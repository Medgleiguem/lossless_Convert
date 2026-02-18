"""
SoundPixel API Server
======================
Unified REST API serving all 4 conversion modes:

  PNG CODEC (file → pixel data → PNG)
    POST /api/png/encode   { file: <any file> }          → PNG download
    POST /api/png/decode   { file: <soundpixel .png> }   → original file download

  MP3 STEGANOGRAPHY CODEC (image hidden inside MP3)
    POST /api/mp3/encode   { mp3: <file>, image: <file> } → MP3 download
    POST /api/mp3/decode   { file: <soundpixel .mp3> }    → image download

  HEALTH
    GET  /api/health   → { status, version, codecs }

  FRONTEND
    GET  /             → React app (served from ../frontend/build)
"""

import logging
import os
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

# Both codec modules live in the same directory
sys.path.insert(0, os.path.dirname(__file__))

import codec_png as png_codec
import codec_mp3 as mp3_codec

from codec_png import PngCodecError, NotAPngCodecFile, PngCorruptedError, PngVersionError
from codec_mp3 import CodecError,    NotEncodedError,  CorruptedFileError, UnsupportedVersionError


# ── Configuration ─────────────────────────────────────────────────────────────

MAX_UPLOAD_MB    = int(os.environ.get("MAX_UPLOAD_MB", "200"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
FRONTEND_BUILD   = Path(__file__).parent.parent / "frontend" / "build"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("soundpixel")


# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    static_folder=str(FRONTEND_BUILD) if FRONTEND_BUILD.exists() else None,
)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


# ── CORS (manual, no flask-cors needed) ──────────────────────────────────────

# In production, set ALLOWED_ORIGIN env var to your Netlify URL.
# Multiple origins: comma-separated  e.g. "https://a.netlify.app,https://custom.com"
_ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    *[o.strip() for o in os.environ.get("ALLOWED_ORIGIN", "").split(",") if o.strip()],
}
_EXPOSED_HEADERS = ", ".join([
    "Content-Disposition",
    "X-Input-Size", "X-Output-Size",
    "X-Image-Width", "X-Image-Height",
    "X-Mp3-Size", "X-Image-Size", "X-Total-Size",
    "X-Original-Filename",
])

@app.after_request
def add_cors(response: Response) -> Response:
    origin = request.headers.get("Origin", "")
    if origin in _ALLOWED_ORIGINS or app.debug:
        response.headers["Access-Control-Allow-Origin"]   = origin or "*"
        response.headers["Access-Control-Allow-Methods"]  = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"]  = "Content-Type"
        response.headers["Access-Control-Expose-Headers"] = _EXPOSED_HEADERS
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def options_handler(_path):
    return "", 204


# ── Shared helpers ────────────────────────────────────────────────────────────

def _error(message: str, status: int = 400) -> tuple[Response, int]:
    """Return a JSON error response."""
    return jsonify({"error": message}), status


def _require_file(field: str):
    """
    Extract an uploaded file from the request.
    Returns (file, None) on success or (None, error_response) on failure.
    """
    f = request.files.get(field)
    if not f or not f.filename:
        return None, _error(
            f"Missing file field '{field}'. "
            "Send a multipart/form-data request with the correct field name."
        )
    return f, None


# MIME type map for common file extensions
_MIME_TYPES = {
    # Audio
    "mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
    "ogg": "audio/ogg",  "aac": "audio/aac", "m4a":  "audio/mp4",
    "aiff":"audio/aiff", "opus":"audio/opus",
    # Images
    "png": "image/png",  "jpg": "image/jpeg", "jpeg":"image/jpeg",
    "gif": "image/gif",  "webp":"image/webp",  "bmp": "image/bmp",
    "tiff":"image/tiff", "svg": "image/svg+xml",
}

def _mime_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _MIME_TYPES.get(ext, "application/octet-stream")


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status":     "ok",
        "version":    "2.0",
        "max_upload": f"{MAX_UPLOAD_MB} MB",
        "codecs": {
            "png": "file → pixel-packed PNG (lossless round-trip)",
            "mp3": "image hidden inside MP3 audio (steganography)",
        },
    })


# ── PNG Codec Routes ──────────────────────────────────────────────────────────

@app.route("/api/png/encode", methods=["POST"])
def png_encode():
    """
    Encode any file into a SoundPixel PNG.

    Form fields:
      file — any file (MP3, WAV, FLAC, etc.)
    """
    f, err = _require_file("file")
    if err:
        return err

    raw      = f.read()
    filename = f.filename or "file.bin"

    logger.info("PNG encode: '%s' (%d B)", filename, len(raw))

    try:
        result = png_codec.encode(raw, filename)
    except Exception as exc:
        logger.exception("PNG encode failed for '%s'", filename)
        return _error(f"Encoding failed: {exc}", 500)

    stem     = filename.rsplit(".", 1)[0] if "." in filename else filename
    out_name = f"{stem}_soundpixel.png"

    resp = Response(result.png_bytes, mimetype="image/png")
    resp.headers["Content-Disposition"] = f'attachment; filename="{out_name}"'
    resp.headers["X-Image-Width"]  = str(result.image_width)
    resp.headers["X-Image-Height"] = str(result.image_height)
    resp.headers["X-Input-Size"]   = str(result.input_size)
    resp.headers["X-Output-Size"]  = str(len(result.png_bytes))

    logger.info(
        "PNG encode done: %dx%d, %d B → %d B",
        result.image_width, result.image_height,
        result.input_size, len(result.png_bytes),
    )
    return resp


@app.route("/api/png/decode", methods=["POST"])
def png_decode():
    """
    Decode a SoundPixel PNG back to the original file.

    Form fields:
      file — a SoundPixel PNG created by /api/png/encode
    """
    f, err = _require_file("file")
    if err:
        return err

    raw = f.read()
    logger.info("PNG decode: '%s' (%d B)", f.filename, len(raw))

    try:
        result = png_codec.decode(raw)
    except NotAPngCodecFile  as exc: return _error(str(exc), 422)
    except PngCorruptedError as exc: return _error(str(exc), 422)
    except PngVersionError   as exc: return _error(str(exc), 422)
    except PngCodecError     as exc: return _error(str(exc), 422)
    except Exception         as exc:
        logger.exception("PNG decode failed")
        return _error(f"Decoding failed: {exc}", 500)

    resp = Response(result.data, mimetype=_mime_for(result.filename))
    resp.headers["Content-Disposition"]  = f'attachment; filename="{result.filename}"'
    resp.headers["X-Original-Filename"]  = result.filename
    resp.headers["X-Output-Size"]        = str(result.data_size)

    logger.info("PNG decode done: '%s' (%d B)", result.filename, result.data_size)
    return resp


# ── MP3 Steganography Routes ──────────────────────────────────────────────────

@app.route("/api/mp3/encode", methods=["POST"])
def mp3_encode():
    """
    Embed an image inside an MP3 file (steganography).
    The MP3 continues to play normally in any audio player.

    Form fields:
      mp3   — the carrier audio file (.mp3)
      image — the image to embed (PNG, JPG, etc.)
    """
    mp3_file, err = _require_file("mp3")
    if err:
        return err

    img_file, err = _require_file("image")
    if err:
        return err

    mp3_bytes   = mp3_file.read()
    image_bytes = img_file.read()
    image_name  = img_file.filename or "image.png"

    logger.info(
        "MP3 encode: embed '%s' (%d B) into '%s' (%d B)",
        image_name, len(image_bytes), mp3_file.filename, len(mp3_bytes),
    )

    try:
        result = mp3_codec.encode(mp3_bytes, image_bytes, image_name)
    except Exception as exc:
        logger.exception("MP3 encode failed")
        return _error(f"Encoding failed: {exc}", 500)

    stem     = (mp3_file.filename or "audio").rsplit(".", 1)[0]
    out_name = f"{stem}_soundpixel.mp3"

    resp = Response(result.mp3_bytes, mimetype="audio/mpeg")
    resp.headers["Content-Disposition"] = f'attachment; filename="{out_name}"'
    resp.headers["X-Mp3-Size"]   = str(result.mp3_size)
    resp.headers["X-Image-Size"] = str(result.image_size)
    resp.headers["X-Total-Size"] = str(result.total_size)

    logger.info(
        "MP3 encode done: audio=%d B + image=%d B → %d B",
        result.mp3_size, result.image_size, result.total_size,
    )
    return resp


@app.route("/api/mp3/decode", methods=["POST"])
def mp3_decode():
    """
    Extract the image hidden inside a SoundPixel MP3.

    Form fields:
      file — a SoundPixel MP3 created by /api/mp3/encode
    """
    f, err = _require_file("file")
    if err:
        return err

    raw = f.read()
    logger.info("MP3 decode: '%s' (%d B)", f.filename, len(raw))

    try:
        result = mp3_codec.decode(raw)
    except NotEncodedError       as exc: return _error(str(exc), 422)
    except CorruptedFileError    as exc: return _error(str(exc), 422)
    except UnsupportedVersionError as exc: return _error(str(exc), 422)
    except CodecError            as exc: return _error(str(exc), 422)
    except Exception             as exc:
        logger.exception("MP3 decode failed")
        return _error(f"Decoding failed: {exc}", 500)

    resp = Response(result.image_data, mimetype=_mime_for(result.image_filename))
    resp.headers["Content-Disposition"] = f'attachment; filename="{result.image_filename}"'
    resp.headers["X-Original-Filename"] = result.image_filename
    resp.headers["X-Output-Size"]       = str(result.image_size)

    logger.info("MP3 decode done: '%s' (%d B)", result.image_filename, result.image_size)
    return resp


# ── React frontend ────────────────────────────────────────────────────────────

if FRONTEND_BUILD.exists():
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        target = FRONTEND_BUILD / path
        if path and target.exists():
            return send_from_directory(FRONTEND_BUILD, path)
        return send_from_directory(FRONTEND_BUILD, "index.html")


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(_e):
    return _error(f"File too large. Maximum upload size is {MAX_UPLOAD_MB} MB.", 413)

@app.errorhandler(404)
def not_found(_e):
    return _error("Endpoint not found.", 404)

@app.errorhandler(500)
def server_error(_e):
    return _error("Internal server error.", 500)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    logger.info("SoundPixel API — port %d  debug=%s", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)