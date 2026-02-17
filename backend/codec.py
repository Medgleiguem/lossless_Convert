

import io
import math
import struct
import zlib
from dataclasses import dataclass

from PIL import Image


MAGIC = b"SPXL"
VERSION = 1

HEADER_PREFIX_SIZE = 22
MAX_FILENAME_BYTES = 255



class CodecError(Exception):
    """Base class for all codec errors."""


class CorruptedImageError(CodecError):
    """Raised when the image data is corrupted (bad magic, CRC mismatch)."""


class UnsupportedVersionError(CodecError):
    """Raised when the image was encoded with an unsupported codec version."""



@dataclass(frozen=True)
class EncodeResult:
    png_bytes: bytes
    image_width: int
    image_height: int
    total_pixels: int
    payload_size: int 


@dataclass(frozen=True)
class DecodeResult:
    data: bytes
    filename: str
    data_length: int



def _build_header(data: bytes, filename: str) -> bytes:
    """Build the binary header that precedes the payload."""
    fname_bytes = filename.encode("utf-8")
    if len(fname_bytes) > MAX_FILENAME_BYTES:
        fname_bytes = fname_bytes[:MAX_FILENAME_BYTES]

    crc = zlib.crc32(data) & 0xFFFFFFFF
    data_len = len(data)
    fname_len = len(fname_bytes)

    header = struct.pack(
        ">4sIQIH",
        MAGIC,
        VERSION,
        data_len,
        crc,
        fname_len,
    ) + fname_bytes

    assert len(header) == HEADER_PREFIX_SIZE + fname_len
    return header


def _parse_header(stream: bytes) -> tuple[int, int, int, str, int]:

    if len(stream) < HEADER_PREFIX_SIZE:
        raise CorruptedImageError(
            f"Stream too short for header: {len(stream)} bytes"
        )

    magic, version, data_len, crc32, fname_len = struct.unpack_from(
        ">4sIQIH", stream, 0
    )

    if magic != MAGIC:
        raise CorruptedImageError(
            f"Invalid magic bytes: expected {MAGIC!r}, got {magic!r}. "
            "This PNG was not created by SoundPixel."
        )

    if version != VERSION:
        raise UnsupportedVersionError(
            f"Unsupported codec version: {version}. This build supports v{VERSION}."
        )

    header_total = HEADER_PREFIX_SIZE + fname_len
    if len(stream) < header_total:
        raise CorruptedImageError("Stream truncated inside filename field.")

    filename = stream[HEADER_PREFIX_SIZE : header_total].decode("utf-8", errors="replace")
    return version, data_len, crc32, filename, header_total


def _compute_image_dimensions(num_pixels: int) -> tuple[int, int]:
    width = math.ceil(math.sqrt(num_pixels))
    height = math.ceil(num_pixels / width)
    return width, height



def encode(data: bytes, filename: str = "audio.mp3") -> EncodeResult:

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"data must be bytes, got {type(data).__name__}")
    if not filename:
        filename = "file.bin"

    header = _build_header(data, filename)
    payload = header + data

    remainder = len(payload) % 3
    if remainder:
        payload += bytes(3 - remainder)

    num_pixels = len(payload) // 3
    width, height = _compute_image_dimensions(num_pixels)
    total_pixels = width * height

    payload += bytes((total_pixels - num_pixels) * 3)

    img = Image.frombytes("RGB", (width, height), payload)

    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=1, optimize=False)
    png_bytes = buf.getvalue()

    return EncodeResult(
        png_bytes=png_bytes,
        image_width=width,
        image_height=height,
        total_pixels=total_pixels,
        payload_size=len(payload),
    )


def decode(png_bytes: bytes) -> DecodeResult:
    try:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as exc:
        raise CorruptedImageError(f"Could not open image: {exc}") from exc

    stream = img.tobytes()  # flat RGB bytes, width*height*3

    version, data_len, expected_crc, filename, header_size = _parse_header(stream)

    data_start = header_size
    data_end = data_start + data_len

    if data_end > len(stream):
        raise CorruptedImageError(
            f"Data length field claims {data_len} bytes but stream only has "
            f"{len(stream) - data_start} bytes available after the header."
        )

    data = stream[data_start:data_end]

    # Verify integrity
    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise CorruptedImageError(
            f"CRC-32 mismatch: expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}. "
            "The image may have been re-saved as JPEG or otherwise modified."
        )

    return DecodeResult(data=data, filename=filename, data_length=data_len)
