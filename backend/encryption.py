"""
encryption.py — Secure AES-256-GCM Encryption for SoundPixel
=============================================================
Provides password-based authenticated encryption using:
  - PBKDF2 for password→key derivation
  - AES-256 in GCM mode for authenticated encryption
  - 96-bit nonce (96 bits recommended by NIST for GCM)
  - 128-bit authentication tag

Format Layout (for encrypted payloads):
  Bytes  0–7    Magic:       b'SPXLENC\x00'  (marks as encrypted)
  Bytes  8–15   Salt:        16 bytes (PBKDF2 salt)
  Bytes  16–31  Nonce:       16 bytes (AES-GCM nonce)
  Bytes  32–47  Auth Tag:    16 bytes (authentication tag)
  Bytes  48–55  Ciphertext len: 8 bytes (uint64 big-endian, for proper extraction)
  Bytes  56+    Ciphertext:  encrypted data (AES-256-GCM)

Key Derivation:
  PBKDF2-SHA256(password, salt, iterations=100000)  →  256-bit key

Guarantees:
  - Confidentiality: AES-256-GCM encryption
  - Authenticity: 128-bit authentication tag
  - Integrity: GCM mode detects any tampering
  - Password strength: Use at least 12 characters for security
"""

import os
import struct
import zlib
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


# ── Constants ─────────────────────────────────────────────────────────────────

MAGIC            = b"SPXLENC\x00"      # 8 bytes, marks encrypted block
MAGIC_LEN        = len(MAGIC)           # 8
SALT_LEN         = 16                   # 16 bytes (128 bits)
NONCE_LEN        = 16                   # 16 bytes (128 bits, GCM typically uses 96-128 bits)
TAG_LEN          = 16                   # 16 bytes (128 bits)
CIPHER_LEN_FIELD = 8                    # 8 bytes (uint64) for ciphertext size
HEADER_LEN       = MAGIC_LEN + SALT_LEN + NONCE_LEN + TAG_LEN + CIPHER_LEN_FIELD   # 64 bytes total

PBKDF2_ITERATIONS = 100000              # NIST recommendation (min 100k)
PBKDF2_HASH_ALGO  = hashes.SHA256()

# ── Exceptions ────────────────────────────────────────────────────────────────

class EncryptionError(Exception):
    """Base encryption error."""

class DecryptionFailedError(EncryptionError):
    """Decryption failed or authentication tag mismatch (data tampered or wrong password)."""

class InvalidPasswordError(EncryptionError):
    """Password is invalid (empty or wrong type)."""


# ── Public API ────────────────────────────────────────────────────────────────

def encrypt(plaintext: bytes, password: str) -> bytes:
    """
    Encrypt plaintext with a password using AES-256-GCM.
    
    Args:
        plaintext: The data to encrypt
        password:  Password string (will be UTF-8 encoded)
    
    Returns:
        bytes: [MAGIC][SALT][NONCE][TAG][CIPHERTEXT_LEN][CIPHERTEXT]
    
    Raises:
        InvalidPasswordError: If password is empty
    """
    if not password or not isinstance(password, str):
        raise InvalidPasswordError("Password must be a non-empty string.")
    
    # Generate random salt and nonce
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    
    # Derive key from password
    key = _derive_key(password, salt)
    
    # Encrypt with AES-256-GCM
    cipher = AESGCM(key)
    
    # GCM mode returns (ciphertext + tag), we need to extract tag
    # Note: cryptography's AESGCM.encrypt returns ciphertext || tag
    ciphertext_and_tag = cipher.encrypt(nonce, plaintext, None)
    
    # Extract authentication tag (last 16 bytes) and ciphertext
    ciphertext = ciphertext_and_tag[:-TAG_LEN]
    tag = ciphertext_and_tag[-TAG_LEN:]
    
    # Assemble output: MAGIC + SALT + NONCE + TAG + CIPHERTEXT_LEN + CIPHERTEXT
    output = (MAGIC + salt + nonce + tag + 
              struct.pack(">Q", len(ciphertext)) + ciphertext)
    return output


def decrypt(encrypted_data: bytes, password: str) -> bytes:
    """
    Decrypt data encrypted with encrypt().
    
    Args:
        encrypted_data: Output from encrypt()
        password:       The password used for encryption
    
    Returns:
        bytes: The original plaintext
    
    Raises:
        DecryptionFailedError: If password is wrong or data is tampered
        InvalidPasswordError: If password is invalid
    """
    if not password or not isinstance(password, str):
        raise InvalidPasswordError("Password must be a non-empty string.")
    
    # Check minimum length
    if len(encrypted_data) < HEADER_LEN:
        raise DecryptionFailedError(
            f"Encrypted data too short. Expected at least {HEADER_LEN} bytes."
        )
    
    # Extract components
    magic = encrypted_data[:MAGIC_LEN]
    if magic != MAGIC:
        raise DecryptionFailedError(
            f"Invalid magic. Expected {MAGIC!r}, got {magic!r}. "
            "This is not an encrypted SoundPixel block."
        )
    
    salt = encrypted_data[MAGIC_LEN:MAGIC_LEN + SALT_LEN]
    nonce = encrypted_data[MAGIC_LEN + SALT_LEN:MAGIC_LEN + SALT_LEN + NONCE_LEN]
    tag = encrypted_data[MAGIC_LEN + SALT_LEN + NONCE_LEN:MAGIC_LEN + SALT_LEN + NONCE_LEN + TAG_LEN]
    
    # Extract ciphertext length
    cipher_len_offset = MAGIC_LEN + SALT_LEN + NONCE_LEN + TAG_LEN
    if len(encrypted_data) < cipher_len_offset + CIPHER_LEN_FIELD:
        raise DecryptionFailedError("Ciphertext length field is missing.")
    
    cipher_len = struct.unpack(">Q", encrypted_data[cipher_len_offset:cipher_len_offset + CIPHER_LEN_FIELD])[0]
    
    # Extract ciphertext
    ciphertext_start = cipher_len_offset + CIPHER_LEN_FIELD
    ciphertext = encrypted_data[ciphertext_start:ciphertext_start + cipher_len]
    
    if len(ciphertext) != cipher_len:
        raise DecryptionFailedError(
            f"Ciphertext size mismatch: expected {cipher_len} bytes, got {len(ciphertext)} bytes."
        )
    
    # Derive key from password and salt
    key = _derive_key(password, salt)
    
    # Decrypt with AES-256-GCM
    cipher = AESGCM(key)
    try:
        plaintext = cipher.decrypt(nonce, ciphertext + tag, None)
    except Exception as exc:
        raise DecryptionFailedError(
            "Decryption failed. Wrong password or data has been tampered with."
        ) from exc
    
    return plaintext


def is_encrypted(data: bytes) -> bool:
    """Check if data starts with encryption magic."""
    return data.startswith(MAGIC)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit (32-byte) key from password using PBKDF2-SHA256.
    
    Args:
        password: Password string
        salt:     Salt bytes
    
    Returns:
        32-byte key
    """
    kdf = pbkdf2.PBKDF2HMAC(
        algorithm=PBKDF2_HASH_ALGO,
        length=32,  # 256 bits
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))
