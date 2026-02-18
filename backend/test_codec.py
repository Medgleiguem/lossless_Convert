"""
SoundPixel Codec v2 — Test Suite
Run with: python test_codec.py
"""

import io
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))

from codec import (
    CorruptedFileError,
    NotEncodedError,
    decode,
    encode,
    TAIL_MAGIC,
)

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
_results = []


def run(name, fn):
    try:
        fn()
        print(f"  {PASS}  {name}")
        _results.append(True)
    except AssertionError as e:
        print(f"  {FAIL}  {name}  →  {e}")
        _results.append(False)
    except Exception as e:
        print(f"  {FAIL}  {name}  →  {type(e).__name__}: {e}")
        _results.append(False)


print("\nSoundPixel Codec v2 Tests\n" + "─" * 44)


def t_basic_roundtrip():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(4096)
    img = os.urandom(1024)
    enc = encode(mp3, img, "photo.png")
    dec = decode(enc.mp3_bytes)
    assert dec.image_data == img
    assert dec.image_filename == "photo.png"
    assert dec.image_size == len(img)
run("Basic round-trip: MP3 + PNG", t_basic_roundtrip)


def t_mp3_preserved():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(8192)
    img = os.urandom(512)
    enc = encode(mp3, img, "pic.jpg")
    assert enc.mp3_bytes[:len(mp3)] == mp3, "MP3 audio was modified"
    assert enc.mp3_size == len(mp3)
run("MP3 audio portion is preserved untouched", t_mp3_preserved)


def t_large_image():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(1024)
    img = os.urandom(2 * 1024 * 1024)
    dec = decode(encode(mp3, img, "big.png").mp3_bytes)
    assert dec.image_data == img
run("Large image (2 MB) round-trip", t_large_image)


def t_unicode_filename():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(256)
    enc = encode(mp3, os.urandom(256), "фото_отпуск.png")
    dec = decode(enc.mp3_bytes)
    assert dec.image_filename == "фото_отпуск.png"
run("Unicode filename preserved", t_unicode_filename)


def t_fname_truncated():
    long_name = "a" * 300 + ".png"
    enc = encode(b"\xff\xfb\x90\x00" + os.urandom(256), os.urandom(64), long_name)
    dec = decode(enc.mp3_bytes)
    assert len(dec.image_filename.encode("utf-8")) <= 255
run("Filename truncated at 255 bytes", t_fname_truncated)


def t_idempotent():
    mp3  = b"\xff\xfb\x90\x00" + os.urandom(512)
    img1 = os.urandom(256)
    img2 = os.urandom(512)
    enc1 = encode(mp3, img1, "first.png")
    enc2 = encode(enc1.mp3_bytes, img2, "second.png")
    dec  = decode(enc2.mp3_bytes)
    assert dec.image_data == img2
    assert dec.image_filename == "second.png"
    assert enc2.mp3_bytes[:len(mp3)] == mp3
run("Encode is idempotent (re-encoding replaces block)", t_idempotent)


def t_not_encoded_plain():
    try:
        decode(b"\xff\xfb\x90\x00" + os.urandom(1024))
        assert False, "should have raised"
    except NotEncodedError:
        pass
run("NotEncodedError: plain MP3 with no block", t_not_encoded_plain)


def t_not_encoded_empty():
    try:
        decode(b"")
        assert False, "should have raised"
    except NotEncodedError:
        pass
run("NotEncodedError: empty bytes", t_not_encoded_empty)


def t_crc_mismatch():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(512)
    img = os.urandom(256)
    enc = encode(mp3, img, "test.png")
    data = bytearray(enc.mp3_bytes)
    # Flip a byte inside the image data (after header ~60 bytes in)
    flip_pos = len(mp3) + 80
    data[flip_pos] ^= 0xFF
    try:
        decode(bytes(data))
        assert False, "should have raised"
    except (CorruptedFileError, NotEncodedError):
        pass
run("CorruptedFileError: CRC mismatch", t_crc_mismatch)


def t_tail_removed():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(512)
    enc = encode(mp3, os.urandom(128), "test.png")
    try:
        decode(enc.mp3_bytes[:-8])
        assert False, "should have raised"
    except NotEncodedError:
        pass
run("NotEncodedError: tail magic removed (truncated)", t_tail_removed)


def t_metadata():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(2048)
    img = os.urandom(512)
    enc = encode(mp3, img, "meta.png")
    assert enc.mp3_size   == len(mp3)
    assert enc.image_size == len(img)
    assert enc.total_size == len(enc.mp3_bytes)
    assert enc.total_size > len(mp3)
run("EncodeResult metadata is accurate", t_metadata)


def t_decode_size():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(512)
    img = os.urandom(999)
    dec = decode(encode(mp3, img, "size.png").mp3_bytes)
    assert dec.image_size == len(img)
    assert dec.image_size == len(dec.image_data)
run("DecodeResult size matches actual data", t_decode_size)


def t_zeros():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(256)
    img = bytes(5000)
    dec = decode(encode(mp3, img, "zeros.png").mp3_bytes)
    assert dec.image_data == img
run("All-zero image bytes round-trip", t_zeros)


def t_max_bytes():
    mp3 = b"\xff\xfb\x90\x00" + os.urandom(256)
    img = bytes([255] * 5000)
    dec = decode(encode(mp3, img, "max.png").mp3_bytes)
    assert dec.image_data == img
run("All-255 image bytes round-trip", t_max_bytes)


def t_jpg_roundtrip():
    from PIL import Image
    img_obj = Image.new("RGB", (200, 200), color=(220, 100, 50))
    buf = io.BytesIO()
    img_obj.save(buf, format="JPEG")
    jpg_bytes = buf.getvalue()

    mp3 = b"\xff\xfb\x90\x00" + os.urandom(1024)
    enc = encode(mp3, jpg_bytes, "photo.jpg")
    dec = decode(enc.mp3_bytes)
    assert dec.image_data == jpg_bytes
    assert dec.image_filename == "photo.jpg"
run("Real JPEG image round-trip", t_jpg_roundtrip)


def t_png_roundtrip():
    from PIL import Image
    img_obj = Image.new("RGBA", (150, 150), color=(0, 128, 255, 200))
    buf = io.BytesIO()
    img_obj.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    mp3 = b"\xff\xfb\x90\x00" + os.urandom(1024)
    enc = encode(mp3, png_bytes, "transparent.png")
    dec = decode(enc.mp3_bytes)
    assert dec.image_data == png_bytes
run("Real PNG image round-trip", t_png_roundtrip)


print("\n" + "─" * 44)
passed = sum(_results)
failed = len(_results) - passed
color  = "\033[92m" if failed == 0 else "\033[91m"
print(f"{color}Results: {passed} passed, {failed} failed out of {len(_results)} tests\033[0m\n")
if failed:
    sys.exit(1)