
import math
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))

import backend.codec as codec
from backend.codec import (
    CorruptedImageError,
    DecodeResult,
    EncodeResult,
    UnsupportedVersionError,
    decode,
    encode,
)

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"

_results = []


def test(name):
    def decorator(fn):
        def wrapper():
            try:
                fn()
                print(f"  {PASS}  {name}")
                _results.append((name, True, None))
            except AssertionError as e:
                print(f"  {FAIL}  {name}  →  AssertionError: {e}")
                _results.append((name, False, str(e)))
            except Exception as e:
                print(f"  {FAIL}  {name}  →  {type(e).__name__}: {e}")
                _results.append((name, False, str(e)))
        wrapper()
    return decorator



print("\nSoundPixel Codec Tests\n" + "─" * 40)


@test("Empty bytes round-trip")
def _():
    data = b""
    result = decode(encode(data, "empty.mp3").png_bytes)
    assert result.data == data
    assert result.filename == "empty.mp3"


@test("Single byte round-trip")
def _():
    data = b"\xff"
    r = decode(encode(data, "single.wav").png_bytes)
    assert r.data == data


@test("Small MP3 payload round-trip")
def _():
    data = b"\xff\xfb\x90\x00" + os.urandom(1024)
    r = decode(encode(data, "song.mp3").png_bytes)
    assert r.data == data, "Data mismatch"
    assert r.filename == "song.mp3"


@test("Large random payload (1 MB) round-trip")
def _():
    data = os.urandom(1024 * 1024)
    r = decode(encode(data, "big.flac").png_bytes)
    assert r.data == data
    assert r.filename == "big.flac"


@test("Filename with unicode characters")
def _():
    data = b"hello world"
    r = decode(encode(data, "música_canción.mp3").png_bytes)
    assert r.filename == "música_canción.mp3"


@test("Filename truncated at 255 bytes")
def _():
    long_name = "a" * 300 + ".mp3"
    result = encode(b"data", long_name)
    r = decode(result.png_bytes)
    assert len(r.filename.encode("utf-8")) <= 255


@test("Payload length is exact (no off-by-one)")
def _():
    for size in [1, 2, 3, 4, 5, 6, 100, 101, 102, 999, 1000, 1001]:
        data = (bytes(range(256)) * (size // 256 + 1))[:size]
        assert len(data) == size, f"Test setup error: got {len(data)} bytes for size={size}"
        r = decode(encode(data, f"{size}.bin").png_bytes)
        assert r.data == data, f"Mismatch at size={size}"
        assert r.data_length == size


@test("CRC mismatch raises CorruptedImageError")
def _():
    from PIL import Image
    import io

    data = b"test audio data" * 100  
    enc = encode(data, "test.mp3")

    img = Image.open(io.BytesIO(enc.png_bytes)).convert("RGB")
    w, h = img.size

    import backend.codec as _codec
    header = _codec._build_header(data, "test.mp3")
    data_start_pixel = (len(header)) // 3
    target_pixel_idx = data_start_pixel + len(data) // 6  
    x = target_pixel_idx % w
    y = target_pixel_idx // w

    r, g, b = img.getpixel((x, y))
    img.putpixel((x, y), ((r ^ 0xFF) & 0xFF, g, b))

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    try:
        decode(buf.getvalue())
        assert False, "Should have raised CorruptedImageError"
    except CorruptedImageError:
        pass  


@test("Wrong magic raises CorruptedImageError")
def _():
    from PIL import Image
    import io

    img = Image.new("RGB", (10, 10), color=(1, 2, 3))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    try:
        decode(buf.getvalue())
        assert False, "Should have raised CorruptedImageError"
    except CorruptedImageError:
        pass 


@test("EncodeResult metadata is correct")
def _():
    data = os.urandom(5000)
    r = encode(data, "test.mp3")
    assert r.image_width > 0
    assert r.image_height > 0
    assert r.total_pixels == r.image_width * r.image_height
    assert r.total_pixels * 3 >= r.payload_size
    assert isinstance(r.png_bytes, bytes)
    assert r.png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  

@test("Output is valid PNG")
def _():
    from PIL import Image
    import io
    data = os.urandom(256)
    enc = encode(data, "test.mp3")
    img = Image.open(io.BytesIO(enc.png_bytes))
    assert img.format == "PNG"


@test("All-zeros payload")
def _():
    data = bytes(10000)
    r = decode(encode(data, "silence.wav").png_bytes)
    assert r.data == data


@test("All-255 payload")
def _():
    data = bytes([255] * 10000)
    r = decode(encode(data, "max.wav").png_bytes)
    assert r.data == data



print("\n" + "─" * 40)
passed = sum(1 for _, ok, _ in _results if ok)
failed = sum(1 for _, ok, _ in _results if not ok)
print(f"Results: {passed} passed, {failed} failed out of {len(_results)} tests\n")

if failed:
    sys.exit(1)
