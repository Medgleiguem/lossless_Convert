import logging
import mimetypes
import os
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory
from PIL import Image

# Allow importing codec from same directory
sys.path.insert(0, os.path.dirname(__file__))

from backend.codec import (
    CodecError,
    CorruptedImageError,
    UnsupportedVersionError,
    decode,
    encode,
)

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "100"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

FRONTEND_BUILD = Path(__file__).parent.parent / "frontend" / "build"


app = Flask(
    __name__,
    static_folder=str(FRONTEND_BUILD) if FRONTEND_BUILD.exists() else None,
)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)



ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}


@app.after_request
def add_cors_headers(response: Response) -> Response:
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or app.debug:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response


@app.route("/api/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return "", 204


def _error(message: str, status: int = 400) -> tuple[Response, int]:
    return jsonify({"error": message}), status


def _get_uploaded_file(field: str = "file"):
    """Validate and return the uploaded file or raise."""
    if field not in request.files:
        return None, _error(f"No '{field}' field in request. Use multipart/form-data.")
    f = request.files[field]
    if not f or not f.filename:
        return None, _error("Empty file upload.")
    return f, None


AUDIO_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "aac": "audio/aac",
    "m4a": "audio/mp4",
    "aiff": "audio/aiff",
    "aif": "audio/aiff",
    "opus": "audio/opus",
    "wma": "audio/x-ms-wma",
}


def _mime_for_filename(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return AUDIO_MIME_TYPES.get(ext, "application/octet-stream")



@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": 1, "max_upload_mb": MAX_UPLOAD_MB})


@app.route("/api/encode", methods=["POST"])
def api_encode():
    """
    Encode an audio file into a lossless PNG.
    Accepts: multipart/form-data with field 'file'
    Returns: PNG binary download
    """
    f, err = _get_uploaded_file("file")
    if err:
        return err

    data = f.read()
    filename = f.filename or "audio.mp3"

    logger.info("Encoding '%s' (%d bytes)", filename, len(data))

    try:
        result = encode(data, filename)
    except Exception as exc:
        logger.exception("Encode failed for '%s'", filename)
        return _error(f"Encoding failed: {exc}", 500)

    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    out_name = f"{stem}_soundpixel.png"

    response = Response(result.png_bytes, mimetype="image/png")
    response.headers["Content-Disposition"] = f'attachment; filename="{out_name}"'
    response.headers["X-Image-Width"] = str(result.image_width)
    response.headers["X-Image-Height"] = str(result.image_height)
    response.headers["X-Original-Size"] = str(len(data))

    logger.info(
        "Encoded '%s' → %dx%d PNG (%d bytes)",
        filename,
        result.image_width,
        result.image_height,
        len(result.png_bytes),
    )
    return response


@app.route("/api/decode", methods=["POST"])
def api_decode():
    """
    Decode a SoundPixel PNG back to the original audio file.
    Accepts: multipart/form-data with field 'file'
    Returns: original audio binary download
    """
    f, err = _get_uploaded_file("file")
    if err:
        return err

    png_bytes = f.read()
    logger.info("Decoding PNG '%s' (%d bytes)", f.filename, len(png_bytes))

    try:
        result = decode(png_bytes)
    except CorruptedImageError as exc:
        return _error(str(exc), 422)
    except UnsupportedVersionError as exc:
        return _error(str(exc), 422)
    except CodecError as exc:
        return _error(f"Codec error: {exc}", 422)
    except Exception as exc:
        logger.exception("Decode failed for '%s'", f.filename)
        return _error(f"Decoding failed: {exc}", 500)

    mime = _mime_for_filename(result.filename)
    response = Response(result.data, mimetype=mime)
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{result.filename}"'
    )
    response.headers["X-Original-Filename"] = result.filename
    response.headers["X-Decoded-Size"] = str(result.data_length)

    logger.info("Decoded → '%s' (%d bytes)", result.filename, result.data_length)
    return response



if FRONTEND_BUILD.exists():

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        if path and (FRONTEND_BUILD / path).exists():
            return send_from_directory(FRONTEND_BUILD, path)
        return send_from_directory(FRONTEND_BUILD, "index.html")



@app.errorhandler(413)
def request_too_large(e):
    return _error(f"File too large. Maximum size is {MAX_UPLOAD_MB} MB.", 413)


@app.errorhandler(404)
def not_found(e):
    return _error("Endpoint not found.", 404)


@app.errorhandler(500)
def server_error(e):
    return _error("Internal server error.", 500)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    logger.info("Starting SoundPixel API on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
