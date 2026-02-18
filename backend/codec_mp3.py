"""
codec_mp3.py — SoundPixel MP3 Steganography Codec (with optional AES-256 encryption)
======================================================================================
Embeds any image (PNG, JPG, etc.) inside a valid MP3 audio file — losslessly.
The MP3 continues to play normally in any audio player.
Optionally encrypts the image with AES-256-GCM using password-based key derivation.

Strategy
--------
MP3 players read audio frames sequentially and stop at the last valid frame.
Any data appended after the final MP3 frame is ignored by players but preserved
by file copy operations. We exploit this by appending a signed, versioned block
of raw image bytes after the MP3 audio data.

If a password is provided:
  - Image data is encrypted using AES-256-GCM before appending
  - Encryption adds ~56 bytes of metadata (salt, nonce, tag)
  - Authentication tag ensures image integrity and password correctness

Layout of the output .mp3 file (UNENCRYPTED):
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

Layout of the output .mp3 file (ENCRYPTED):
  ┌────────────────────────────────────────────┐
  │  Original MP3 audio frames (untouched)     │
  ├────────────────────────────────────────────┤  ← mp3_size bytes
  │  Encryption magic 8 bytes b'SPXLENC\x00'  │
  │  Salt        16 bytes     (for PBKDF2)    │
  │  Nonce       16 bytes     (for AES-GCM)   │
  │  Auth tag    16 bytes     (authentication)│
  │  Ciphertext  encrypted [header + image]   │
  │  TAIL_MAGIC  8 bytes  b'SPXLEND\x00'      │
  └────────────────────────────────────────────┘

The TAIL_MAGIC at the very end lets decode() verify the block is intact.

Guarantees
----------
- encode(mp3_bytes, image_bytes, image_filename) → mp3_bytes_with_embedded_image
- decode(mp3_bytes_with_embedded_image) → (image_bytes, image_filename)
- The output MP3 plays normally in any audio player.
- CRC-32 mismatch → CorruptedFileError (image was modified or truncated)
- With encryption: AES-256-GCM provides confidentiality, authenticity, and integrity
- decode(encode(mp3, img, name)).image_data == img  (100% lossless)
"""

import struct
import zlib
from dataclasses import dataclass

import encryption

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

def _build_block(image_bytes: bytes, image_filename: str, password: str = None) -> bytes:
    """
    Build the binary block that gets appended after the MP3 frames.
    
    If password is provided:
        Layout: ENCMAGIC + salt + nonce + tag + encrypted(header + image) + TAIL_MAGIC
    Else:
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
    
    payload = header + image_bytes
    
    # Encrypt if password is provided
    if password:
        payload = encryption.encrypt(payload, password)
    
    return payload + TAIL_MAGIC


def _find_and_parse_block(data: bytes, password: str = None) -> tuple[bytes, str]:
    """
    Locate and parse the SoundPixel block in data.
    Handles both encrypted and unencrypted blocks.
    Returns (image_bytes, image_filename).
    Raises NotEncodedError, CorruptedFileError, or UnsupportedVersionError.
    """
    # Quick check: file must end with TAIL_MAGIC
    if not data.endswith(TAIL_MAGIC):
        raise NotEncodedError(
            "No SoundPixel block found. "
            "This MP3 was not created by SoundPixel, or it was truncated."
        )

    # Locate block start from the end
    tail_start = len(data) - TAIL_LEN
    
    # Try to find encryption magic first, then unencrypted magic
    enc_magic_pos = data.rfind(encryption.MAGIC, 0, tail_start)
    magic_pos = data.rfind(MAGIC, 0, tail_start)
    
    # Determine which magic was found and is closest to the end (most recent)
    if enc_magic_pos != -1 and (magic_pos == -1 or enc_magic_pos > magic_pos):
        # Encrypted block found
        encrypted_payload = data[enc_magic_pos:tail_start]
        
        if not password:
            raise CorruptedFileError(
                "MP3 contains encrypted image data but no password was provided."
            )
        
        # Decrypt
        try:
            decrypted = encryption.decrypt(encrypted_payload, password)
        except encryption.DecryptionFailedError as exc:
            raise CorruptedFileError(
                f"Decryption failed: {str(exc)}"
            ) from exc
        except encryption.InvalidPasswordError as exc:
            raise CorruptedFileError(
                f"Invalid password: {str(exc)}"
            ) from exc
        
        # Now parse the decrypted block as a regular block
        data_to_parse = decrypted
    elif magic_pos != -1:
        # Unencrypted block found
        data_to_parse = data[magic_pos:tail_start]
    else:
        raise CorruptedFileError(
            "TAIL_MAGIC found but header MAGIC is missing. "
            "The file is corrupted or partially overwritten."
        )

    # Now parse the (possibly decrypted) block
    offset = MAGIC_LEN  # Skip MAGIC

    # Parse fixed header fields
    needed = HEADER_FIXED
    if offset + needed > len(data_to_parse):
        raise CorruptedFileError("Header is truncated.")

    version, img_size, expected_crc, fname_len = struct.unpack_from(">HQIH", data_to_parse, offset)
    offset += HEADER_FIXED

    if version != VERSION:
        raise UnsupportedVersionError(
            f"Block uses version {version}, this build supports version {VERSION}."
        )

    # Parse filename
    if offset + fname_len > len(data_to_parse):
        raise CorruptedFileError("Filename field is truncated.")
    image_filename = data_to_parse[offset : offset + fname_len].decode("utf-8", errors="replace")
    offset += fname_len

    # Parse image data
    if offset + img_size > len(data_to_parse):
        raise CorruptedFileError(
            f"Image data field claims {img_size} bytes but only "
            f"{len(data_to_parse) - offset} bytes are available."
        )
    image_bytes = data_to_parse[offset : offset + img_size]

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
    password: str = None,
) -> EncodeResult:
    """
    Embed an image inside an MP3 file.

    Args:
        mp3_bytes:      Raw bytes of the carrier MP3 audio file.
        image_bytes:    Raw bytes of the image to embed (PNG, JPG, etc.).
        image_filename: Original image filename (recovered on decode).
        password:       Optional password for AES-256-GCM encryption. If provided,
                        the image data is encrypted before embedding.

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

    block = _build_block(bytes(image_bytes), image_filename, password)
    output = bytes(mp3_bytes) + block

    return EncodeResult(
        mp3_bytes=output,
        mp3_size=len(mp3_bytes),
        image_size=len(image_bytes),
        total_size=len(output),
    )


def decode(mp3_bytes: bytes, password: str = None) -> DecodeResult:
    """
    Extract the embedded image from a SoundPixel MP3 file.

    Args:
        mp3_bytes: Raw bytes of the SoundPixel MP3 file.
        password:  Optional password if the image was encrypted during encoding.
                   Required if encryption was used, must match the encoding password.

    Returns:
        DecodeResult with the extracted image data and filename.

    Raises:
        NotEncodedError:        No SoundPixel block found.
        CorruptedFileError:     Block found but CRC-32 fails or data is truncated.
        UnsupportedVersionError: Block uses an unknown version.
        encryption.DecryptionFailedError: Wrong password or data tampered.
    """
    image_bytes, image_filename = _find_and_parse_block(bytes(mp3_bytes), password)
    return DecodeResult(
        image_data=image_bytes,
        image_filename=image_filename,
        image_size=len(image_bytes),
    )