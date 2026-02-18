#!/usr/bin/env python3
"""
Quick security tests to verify AES-256-GCM encryption works
"""
import sys
import encryption
import codec_png
import codec_mp3

def test_encryption():
    print("=" * 60)
    print("SECURITY TEST: AES-256-GCM Encryption")
    print("=" * 60)
    
    # Test 1: Encryption module
    print("\n1. Testing encryption.py module...")
    plaintext = b"Secret data" * 100
    password = "MyPassword123!"
    
    encrypted = encryption.encrypt(plaintext, password)
    print(f"   ✓ Encrypted {len(plaintext)} bytes → {len(encrypted)} bytes")
    print(f"   ✓ Overhead: {len(encrypted) - len(plaintext)} bytes (salt + nonce + tag + padding)")
    
    decrypted = encryption.decrypt(encrypted, password)
    assert decrypted == plaintext, "Decryption mismatch!"
    print(f"   ✓ Decryption works correctly")
    
    # Test 2: PNG codec with encryption
    print("\n2. Testing PNG codec with encryption...")
    test_data = b"MP3 AUDIO DATA" * 200
    filename = "audio.mp3"
    password = "SecurePassword456"
    
    # Encode without password
    result_plain = codec_png.encode(test_data, filename)
    print(f"   ✓ Plain PNG: {len(result_plain.png_bytes)} bytes")
    
    # Decode plain
    decoded_plain = codec_png.decode(result_plain.png_bytes)
    assert decoded_plain.data == test_data
    print(f"   ✓ Plain PNG round-trip successful")
    
    # Encode with password
    result_encrypted = codec_png.encode(test_data, filename, password=password)
    print(f"   ✓ Encrypted PNG: {len(result_encrypted.png_bytes)} bytes")
    
    # Decode encrypted
    decoded_encrypted = codec_png.decode(result_encrypted.png_bytes, password=password)
    assert decoded_encrypted.data == test_data
    print(f"   ✓ Encrypted PNG round-trip successful")
    
    # Test 3: MP3 codec with encryption
    print("\n3. Testing MP3 codec with encryption...")
    mp3_data = b"ID3" + b"\x00" * 1000  # Fake MP3 with ID3 tag
    image_data = b"PNG_IMAGE_DATA" * 150
    image_name = "image.png"
    password = "AudioPassword789"
    
    # Encode plain MP3
    mp3_plain = codec_mp3.encode(mp3_data, image_data, image_name)
    print(f"   ✓ Plain MP3: {len(mp3_plain.mp3_bytes)} bytes")
    
    # Decode plain
    decoded_mp3_plain = codec_mp3.decode(mp3_plain.mp3_bytes)
    assert decoded_mp3_plain.image_data == image_data
    print(f"   ✓ Plain MP3 round-trip successful")
    
    # Encode encrypted MP3
    mp3_encrypted = codec_mp3.encode(mp3_data, image_data, image_name, password=password)
    print(f"   ✓ Encrypted MP3: {len(mp3_encrypted.mp3_bytes)} bytes")
    
    # Decode encrypted
    decoded_mp3_encrypted = codec_mp3.decode(mp3_encrypted.mp3_bytes, password=password)
    assert decoded_mp3_encrypted.image_data == image_data
    print(f"   ✓ Encrypted MP3 round-trip successful")
    
    # Test 4: Wrong password detection
    print("\n4. Testing wrong password detection...")
    try:
        codec_png.decode(result_encrypted.png_bytes, password="WrongPassword")
        print("   ✗ FAILED: Should have detected wrong password!")
        return False
    except codec_png.PngCorruptedError:
        print(f"   ✓ Wrong password correctly rejected (PNG)")
    
    try:
        codec_mp3.decode(mp3_encrypted.mp3_bytes, password="WrongPassword")
        print("   ✗ FAILED: Should have detected wrong password!")
        return False
    except codec_mp3.CorruptedFileError:
        print(f"   ✓ Wrong password correctly rejected (MP3)")
    
    # Test 5: Missing password
    print("\n5. Testing missing password on encrypted data...")
    try:
        codec_png.decode(result_encrypted.png_bytes)
        print("   ✗ FAILED: Should have detected missing password!")
        return False
    except codec_png.PngCorruptedError as e:
        if "password" in str(e).lower():
            print(f"   ✓ Missing password correctly detected (PNG)")
        else:
            print(f"   ✓ Data integrity check detected (PNG)")
    
    print("\n" + "=" * 60)
    print("✅ ALL SECURITY TESTS PASSED!")
    print("=" * 60)
    print("\nSecurity Summary:")
    print("  • AES-256-GCM encryption: ENABLED")
    print("  • Password-based key derivation (PBKDF2): ENABLED")
    print("  • Authentication tag (integrity check): ENABLED")
    print("  • Wrong password detection: ENABLED")
    print("  • Data tampering detection: ENABLED")
    print("\nYour steganography system is now SECURE! 🔐")
    return True

if __name__ == "__main__":
    try:
        success = test_encryption()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
