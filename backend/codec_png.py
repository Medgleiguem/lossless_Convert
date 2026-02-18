"""
codec_png.py — SoundPixel PNG Codec (with optional AES-256 encryption)
=========================================================================
Converts any file (MP3, audio, etc.) to a lossless PNG image and back.
Optionally encrypts the payload with AES-256-GCM using password-based key derivation.

HOW IT WORKS
------------
Raw file bytes are packed 3-per-pixel into RGB channels of a PNG image.
A binary header is prepended that stores:
  - Magic signature  (detects non-SoundPixel PNGs)
  - Original filename  (recovered on decode)
  - Exact data length  (trims padding on decode)
  - CRC-32 checksum  (detects corruption)

If a password is provided:
  - Entire payload (header + data) is encrypted using AES-256-GCM
  - Encryption adds ~56 bytes of metadata (salt, nonce, tag)
  - Authentication tag ensures data integrity and password correctness

PNG is inherently lossless, so every byte survives the round-trip exactly.

FORMAT LAYOUT (inside PNG pixel data)
--------------------------------------
UNENCRYPTED:
  Bytes  0–3   Magic:        b'SPXL'
  Bytes  4–7   Version:      uint32 big-endian
  Bytes  8–15  Data length:  uint64 big-endian
  Bytes 16–19  CRC-32:       uint32 big-endian
  Bytes 20–21  Filename len: uint16 big-endian
  Bytes 22–N   Filename:     UTF-8 (max 255 bytes)
  Bytes N+1…   Original file bytes

ENCRYPTED (when password is provided):
  Bytes  0–7   Encryption magic: b'SPXLENC\x00'
  Bytes  8–23  Salt:        16 bytes (for PBKDF2)
  Bytes 24–39  Nonce:       16 bytes (for AES-GCM)
  Bytes 40–55  Auth tag:    16 bytes (authentication)
  Bytes 56+    Ciphertext:  encrypted [header + data]

GUARANTEE
---------
  decode(encode(data, name)) == data   (100% lossless, CRC-32 verified)
  With password:
    - Confidentiality via AES-256-GCM
    - Authenticity verified via AEAD authentication tag
    - Tampered/corrupted data detected immediately
"""
import io
import math
import struct
import zlib
from dataclasses import dataclass

from PIL import Image

import encryption


# ── Constants ─────────────────────────────────────────────────────────────────

MAGIC   = b"SPXL"
VERSION = 1

# Fixed prefix size: magic(4) + version(4) + data_len(8) + crc32(4) + fname_len(2) = 22 bytes
HEADER_PREFIX = 22
MAX_FNAME_LEN = 255


# ── Exceptions ────────────────────────────────────────────────────────────────

class PngCodecError(Exception):
    """Base class for PNG codec errors."""

class NotAPngCodecFile(PngCodecError):
    """The PNG does not contain a SoundPixel payload."""

class PngCorruptedError(PngCodecError):
    """CRC-32 mismatch — the payload has been modified."""

class PngVersionError(PngCodecError):
    """The PNG was encoded with an unsupported codec version."""


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PngEncodeResult:
    png_bytes:    bytes  # The output PNG file
    image_width:  int    # PNG width in pixels
    image_height: int    # PNG height in pixels
    input_size:   int    # Original file size in bytes

@dataclass(frozen=True)
class PngDecodeResult:
    data:          bytes  # The recovered original file bytes
    filename:      str    # The original filename
    data_size:     int    # Byte count (== len(data))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_header(data: bytes, filename: str) -> bytes:
    """Pack the binary header that precedes the payload bytes."""
    fname_bytes = filename.encode("utf-8")[:MAX_FNAME_LEN]
    crc         = zlib.crc32(data) & 0xFFFFFFFF

    header = struct.pack(
        ">4sIQIH",
        MAGIC,
        VERSION,
        len(data),
        crc,
        len(fname_bytes),
    ) + fname_bytes

    assert len(header) == HEADER_PREFIX + len(fname_bytes)
    return header


def _parse_header(stream: bytes) -> tuple[int, int, int, str, int]:
    """
    Parse the header from the flat pixel byte stream.

    Returns:
        (version, data_len, crc32, filename, header_total_bytes)
    """
    if len(stream) < HEADER_PREFIX:
        raise NotAPngCodecFile("Stream too short to contain a SoundPixel header.")

    magic, version, data_len, crc32, fname_len = struct.unpack_from(">4sIQIH", stream, 0)

    if magic != MAGIC:
        raise NotAPngCodecFile(
            f"Magic mismatch: expected {MAGIC!r}, got {magic!r}. "
            "This PNG was not created by SoundPixel."
        )

    if version != VERSION:
        raise PngVersionError(
            f"Unsupported codec version {version} (this build supports v{VERSION})."
        )

    header_total = HEADER_PREFIX + fname_len
    if len(stream) < header_total:
        raise PngCorruptedError("Filename field is truncated.")

    filename = stream[HEADER_PREFIX:header_total].decode("utf-8", errors="replace")
    return version, data_len, crc32, filename, header_total


def _square_dimensions(num_pixels: int) -> tuple[int, int]:
    """Return (width, height) for the smallest near-square image that fits num_pixels."""
    width  = math.ceil(math.sqrt(num_pixels))
    height = math.ceil(num_pixels / width)
    return width, height


# ── Public API ────────────────────────────────────────────────────────────────

def encode(data: bytes, filename: str = "audio.mp3", password: str = None) -> PngEncodeResult:
    """
    Encode any binary data into a lossless PNG image.

    Args:
        data:     Raw bytes of the file to encode.
        filename: Original filename embedded in the PNG (recovered on decode).
        password: Optional password for AES-256-GCM encryption. If provided,
                  the payload is encrypted before embedding in PNG.

    Returns:
        PngEncodeResult with the PNG bytes and metadata.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"data must be bytes, got {type(data).__name__}")

    filename = filename or "file.bin"
    header   = _build_header(bytes(data), filename)
    payload  = header + bytes(data)
    
    # Encrypt payload if password provided
    if password:
        payload = encryption.encrypt(payload, password)

    # Pad to a multiple of 3 so every pixel is fully populated
    remainder = len(payload) % 3
    if remainder:
        payload += bytes(3 - remainder)

    num_pixels = len(payload) // 3
    width, height = _square_dimensions(num_pixels)
    total_pixels  = width * height

    # Pad to fill the rectangular canvas
    payload += bytes((total_pixels - num_pixels) * 3)

    img = Image.frombytes("RGB", (width, height), payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=1, optimize=False)

    return PngEncodeResult(
        png_bytes=buf.getvalue(),
        image_width=width,
        image_height=height,
        input_size=len(data),
    )


def decode(png_bytes: bytes, password: str = None) -> PngDecodeResult:
    """
    Decode a SoundPixel PNG back to the original file bytes.

    Args:
        png_bytes: Raw PNG file bytes.
        password:  Optional password if the PNG was encrypted during encoding.
                   Required if encryption was used, must match the encoding password.

    Returns:
        PngDecodeResult with the data, filename, and size.

    Raises:
        NotAPngCodecFile: The PNG has no SoundPixel payload.
        PngCorruptedError: CRC-32 mismatch.
        PngVersionError: Unknown codec version.
        encryption.DecryptionFailedError: Wrong password or data tampered.
    """
    try:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as exc:
        raise NotAPngCodecFile(f"Could not open as PNG: {exc}") from exc

    stream = img.tobytes()  # flat R,G,B,R,G,B,… byte sequence
    
    # Check if payload is encrypted
    if encryption.is_encrypted(stream):
        if not password:
            raise PngCorruptedError(
                "PNG contains encrypted data but no password was provided."
            )
        try:
            stream = encryption.decrypt(stream, password)
        except encryption.DecryptionFailedError as exc:
            raise PngCorruptedError(
                f"Decryption failed: {str(exc)}"
            ) from exc
        except encryption.InvalidPasswordError as exc:
            raise PngCorruptedError(
                f"Invalid password: {str(exc)}"
            ) from exc

    _, data_len, expected_crc, filename, header_size = _parse_header(stream)

    data_start = header_size
    data_end   = data_start + data_len

    if data_end > len(stream):
        raise PngCorruptedError(
            f"Data length claims {data_len} bytes but only "
            f"{len(stream) - data_start} bytes remain after the header."
        )

    data = stream[data_start:data_end]

    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise PngCorruptedError(
            f"CRC-32 mismatch (expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}). "
            "The PNG may have been re-saved as JPEG or otherwise modified."
        )

    return PngDecodeResult(data=data, filename=filename, data_size=data_len)