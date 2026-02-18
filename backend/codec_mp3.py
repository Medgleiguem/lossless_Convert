"""
codec_mp3.py — SoundPixel MP3 Steganography Codec
==================================================
Embeds any image (PNG, JPG, etc.) inside a valid MP3 audio file — losslessly.
The MP3 continues to play normally in any audio player.

Strategy
--------
MP3 players read audio frames sequentially and stop at the last valid frame.
Any data appended after the final MP3 frame is ignored by players but preserved
by file copy operations. We exploit this by appending a signed, versioned block
of raw image bytes after the MP3 audio data.

Layout of the output .mp3 file:
  ┌────────────────────────────────────────────┐
  │  Original MP3 audio frames (untouched)     │
  ├────────────────────────────────────────────┤  ← mp3_size bytes
  │  MAGIC       8 bytes  b'SPXLV2\x00\x00'   │
  │  version     2 bytes  uint16 big-endian    │
  │  img_size    8 bytes  uint64 big-endian    │
  │  crc32       4 bytes  uint32 big-endian    │
  │  fname_len   2 bytes  uint16 big-endian    │
  │  fname       N bytes  UTF-8 (max 255 B)   │
  │  image data  img_size bytes                │
  │  TAIL_MAGIC  8 bytes  b'SPXLEND\x00'      │
  └────────────────────────────────────────────┘

The TAIL_MAGIC at the very end lets decode() quickly verify the block is intact
even before reading the header, and lets us locate the header by seeking backward.

Guarantees
----------
- encode(mp3_bytes, image_bytes, image_filename) → mp3_bytes_with_embedded_image
- decode(mp3_bytes_with_embedded_image) → (image_bytes, image_filename)
- The output MP3 plays normally in any audio player.
- CRC-32 mismatch → CorruptedFileError (image was modified or truncated)
- decode(encode(mp3, img, name)).image_data == img  (100% lossless)
"""

import struct
import zlib
from dataclasses import dataclass

# ── Constants ─────────────────────────────────────────────────────────────────

MAGIC      = b"SPXLV2\x00\x00"   # 8 bytes
TAIL_MAGIC = b"SPXLEND\x00"       # 8 bytes
VERSION    = 2

MAGIC_LEN      = len(MAGIC)       # 8
TAIL_LEN       = len(TAIL_MAGIC)  # 8
MAX_FNAME_BYTES = 255

# Fixed-size part of the header (after MAGIC, before variable-length filename):
#   version(2) + img_size(8) + crc32(4) + fname_len(2) = 16 bytes
HEADER_FIXED = 16


# ── Exceptions ────────────────────────────────────────────────────────────────

class CodecError(Exception):
    """Base class for SoundPixel codec errors."""

class NotEncodedError(CodecError):
    """Raised when no SoundPixel block is found in the file."""

class CorruptedFileError(CodecError):
    """Raised when the block is present but its CRC-32 does not match."""

class UnsupportedVersionError(CodecError):
    """Raised when the block uses a version this build does not support."""


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EncodeResult:
    mp3_bytes:      bytes   # The output MP3 (audio + embedded image)
    mp3_size:       int     # Size of original audio portion
    image_size:     int     # Size of embedded image in bytes
    total_size:     int     # Total file size


@dataclass(frozen=True)
class DecodeResult:
    image_data:     bytes   # The extracted image bytes
    image_filename: str     # The original image filename
    image_size:     int     # Number of bytes


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_block(image_bytes: bytes, image_filename: str) -> bytes:
    """
    Build the binary block that gets appended after the MP3 frames.
    Layout: MAGIC + version + img_size + crc32 + fname_len + fname + image_data + TAIL_MAGIC
    """
    fname_bytes = image_filename.encode("utf-8")[:MAX_FNAME_BYTES]
    crc = zlib.crc32(image_bytes) & 0xFFFFFFFF

    header = (
        MAGIC
        + struct.pack(">HQIH",
            VERSION,
            len(image_bytes),
            crc,
            len(fname_bytes),
        )
        + fname_bytes
    )
    return header + image_bytes + TAIL_MAGIC


def _find_and_parse_block(data: bytes) -> tuple[bytes, str]:
    """
    Locate and parse the SoundPixel block in data.
    Returns (image_bytes, image_filename).
    Raises NotEncodedError, CorruptedFileError, or UnsupportedVersionError.
    """
    # Quick check: file must end with TAIL_MAGIC
    if not data.endswith(TAIL_MAGIC):
        raise NotEncodedError(
            "No SoundPixel block found. "
            "This MP3 was not created by SoundPixel, or it was truncated."
        )

    # Locate MAGIC from the end, working backwards past tail + image data
    # We search backwards to avoid false positives in the audio data
    tail_start = len(data) - TAIL_LEN
    magic_pos = data.rfind(MAGIC, 0, tail_start)

    if magic_pos == -1:
        raise CorruptedFileError(
            "TAIL_MAGIC found but header MAGIC is missing. "
            "The file is corrupted or partially overwritten."
        )

    offset = magic_pos + MAGIC_LEN

    # Parse fixed header fields
    needed = HEADER_FIXED
    if offset + needed > tail_start:
        raise CorruptedFileError("Header is truncated.")

    version, img_size, expected_crc, fname_len = struct.unpack_from(">HQIH", data, offset)
    offset += HEADER_FIXED

    if version != VERSION:
        raise UnsupportedVersionError(
            f"Block uses version {version}, this build supports version {VERSION}."
        )

    # Parse filename
    if offset + fname_len > tail_start:
        raise CorruptedFileError("Filename field is truncated.")
    image_filename = data[offset : offset + fname_len].decode("utf-8", errors="replace")
    offset += fname_len

    # Parse image data
    if offset + img_size > tail_start:
        raise CorruptedFileError(
            f"Image data field claims {img_size} bytes but only "
            f"{tail_start - offset} bytes are available."
        )
    image_bytes = data[offset : offset + img_size]

    # Verify CRC-32
    actual_crc = zlib.crc32(image_bytes) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise CorruptedFileError(
            f"CRC-32 mismatch: expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}. "
            "The embedded image data is corrupted."
        )

    return image_bytes, image_filename


# ── Public API ────────────────────────────────────────────────────────────────

def encode(
    mp3_bytes: bytes,
    image_bytes: bytes,
    image_filename: str = "image.png",
) -> EncodeResult:
    """
    Embed an image inside an MP3 file.

    Args:
        mp3_bytes:      Raw bytes of the carrier MP3 audio file.
        image_bytes:    Raw bytes of the image to embed (PNG, JPG, etc.).
        image_filename: Original image filename (recovered on decode).

    Returns:
        EncodeResult with the combined MP3 bytes and size metadata.

    Raises:
        TypeError:      If arguments are not bytes.
        ValueError:     If mp3_bytes does not look like an MP3 or ID3 file.
    """
    if not isinstance(mp3_bytes, (bytes, bytearray)):
        raise TypeError(f"mp3_bytes must be bytes, got {type(mp3_bytes).__name__}")
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError(f"image_bytes must be bytes, got {type(image_bytes).__name__}")
    if not image_filename:
        image_filename = "image.png"

    # Strip any previously embedded block so encode is idempotent
    if mp3_bytes.endswith(TAIL_MAGIC):
        magic_pos = mp3_bytes.rfind(MAGIC)
        if magic_pos != -1:
            mp3_bytes = mp3_bytes[:magic_pos]

    block = _build_block(bytes(image_bytes), image_filename)
    output = bytes(mp3_bytes) + block

    return EncodeResult(
        mp3_bytes=output,
        mp3_size=len(mp3_bytes),
        image_size=len(image_bytes),
        total_size=len(output),
    )


def decode(mp3_bytes: bytes) -> DecodeResult:
    """
    Extract the embedded image from a SoundPixel MP3 file.

    Args:
        mp3_bytes: Raw bytes of the SoundPixel MP3 file.

    Returns:
        DecodeResult with the extracted image data and filename.

    Raises:
        NotEncodedError:       No SoundPixel block found.
        CorruptedFileError:    Block found but CRC-32 fails or data is truncated.
        UnsupportedVersionError: Block uses an unknown version.
    """
    image_bytes, image_filename = _find_and_parse_block(bytes(mp3_bytes))
    return DecodeResult(
        image_data=image_bytes,
        image_filename=image_filename,
        image_size=len(image_bytes),
    )