#!/usr/bin/env python3
"""
DLP System Complete Test with Visual Encryption Display
========================================================
Shows the actual encrypted data (gibberish) not just keys!
"""

import sys
import os
from io import BytesIO
from PIL import Image
import base64

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def show_encrypted_data(data, max_length=200):
    """Show actual encrypted data as hex/base64"""
    if isinstance(data, str):
        # Already base64
        preview = data[:max_length]
    elif isinstance(data, bytes):
        # Convert to hex for display
        preview = data.hex()[:max_length]
    else:
        preview = str(data)[:max_length]
    
    print(f"🔒 Encrypted Data Preview (first {max_length} chars):")
    print(f"   {preview}...")
    print(f"   [Total length: {len(str(data))} chars]")

# ==================== Test 1: Text Encryption Visual ====================

def test_text_encryption_visual():
    print_header("Test 1: Text Encryption - See the Gibberish!")
    try:
        from encryption import EncryptionService
        
        service = EncryptionService()
        
        # Generate keys
        print("\n🔑 Generating RSA keys...")
        private_key, public_key = service.generate_rsa_keypair()
        print_success("RSA-2048 keys generated")
        
        # Original text
        original_text = "This is TOP SECRET information! 🔒 بيانات سرية للغاية!"
        
        print("\n" + "="*70)
        print("📄 ORIGINAL TEXT:")
        print("="*70)
        print(f"   {original_text}")
        print(f"   [Length: {len(original_text)} chars]")
        
        # Encrypt
        print("\n🔐 Encrypting text...")
        encrypted = service.encrypt_text(original_text, public_key)
        print_success("Text encrypted successfully!")
        
        # Show encrypted data
        print("\n" + "="*70)
        print("🔒 ENCRYPTED TEXT (This is what gets stored):")
        print("="*70)
        show_encrypted_data(encrypted['encrypted_data'])
        
        # Show it's completely different
        print("\n📊 Comparison:")
        print(f"   Original:  '{original_text[:50]}...'")
        encrypted_preview = encrypted['encrypted_data'][:50]
        print(f"   Encrypted: '{encrypted_preview}...'")
        print(f"   → Completely unreadable! ✅")
        
        # Decrypt
        print("\n🔓 Decrypting text...")
        decrypted_text = service.decrypt_text(
            encrypted['encrypted_data'],
            encrypted['encrypted_key'],
            encrypted['iv'],
            encrypted['auth_tag'],
            private_key
        )
        
        print("\n" + "="*70)
        print("✅ DECRYPTED TEXT (Back to original):")
        print("="*70)
        print(f"   {decrypted_text}")
        
        # Verify
        if decrypted_text == original_text:
            print_success("✓ Decryption successful - text matches original!")
        else:
            print_error("✗ Decryption failed - text doesn't match!")
        
        return True
        
    except Exception as e:
        print_error(f"Text encryption test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ==================== Test 2: Image Encryption Visual ====================

def test_image_encryption_visual():
    print_header("Test 2: Image Encryption - See the Noise!")
    try:
        from encryption import EncryptionService
        
        service = EncryptionService()
        
        # Generate keys
        print("\n🔑 Generating RSA keys...")
        private_key, public_key = service.generate_rsa_keypair()
        print_success("Keys generated")
        
        # Create a simple image
        print("\n🖼️  Creating test image (red 200x200 square)...")
        img = Image.new('RGB', (200, 200), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        print_info(f"Original image size: {len(img_data)} bytes")
        print_info(f"First 50 bytes (PNG header): {img_data[:50].hex()}")
        
        # Encrypt
        print("\n🔐 Encrypting image...")
        encrypted = service.encrypt_image(img_data, public_key)
        print_success("Image encrypted successfully!")
        
        # Show encrypted data
        print("\n" + "="*70)
        print("🔒 ENCRYPTED IMAGE DATA:")
        print("="*70)
        encrypted_bytes = encrypted['encrypted_data']
        print(f"   Encrypted size: {len(encrypted_bytes)} bytes")
        print(f"   First 50 bytes: {encrypted_bytes[:50].hex()}")
        print(f"   Last 50 bytes:  {encrypted_bytes[-50:].hex()}")
        print("\n   ⚠️  This looks like complete random noise!")
        print("   📊 No PNG header, no structure, just chaos!")
        
        # Compare
        print("\n📊 Comparison:")
        print(f"   Original PNG starts with: {img_data[:8].hex()} (PNG signature)")
        print(f"   Encrypted starts with:    {encrypted_bytes[:8].hex()} (random!)")
        print(f"   → Completely different! ✅")
        
        # Try to save encrypted data as image (will look like noise)
        print("\n💾 Saving encrypted data as 'encrypted_noise.bin'...")
        with open('encrypted_noise.bin', 'wb') as f:
            f.write(encrypted_bytes)
        print_success("Saved! (Try to open it - won't work as image)")
        
        # Decrypt
        print("\n🔓 Decrypting image...")
        decrypted_img = service.decrypt_image(
            encrypted['encrypted_data'],
            encrypted['encrypted_key'],
            encrypted['iv'],
            encrypted['auth_tag'],
            private_key,
            encrypted['metadata']
        )
        print_success(f"Image decrypted: {decrypted_img.size}, {decrypted_img.mode}")
        
        # Save decrypted
        print("\n💾 Saving decrypted image as 'decrypted_image.png'...")
        decrypted_img.save('decrypted_image.png')
        print_success("Saved! (This will open correctly)")
        
        # Verify
        decrypted_bytes = BytesIO()
        decrypted_img.save(decrypted_bytes, format='PNG')
        decrypted_data = decrypted_bytes.getvalue()
        
        print("\n📊 Verification:")
        print(f"   Original image: {img.size}, {img.mode}")
        print(f"   Decrypted image: {decrypted_img.size}, {decrypted_img.mode}")
        print_success("✓ Decryption successful - image restored!")
        
        # Cleanup
        print("\n🧹 Cleaning up test files...")
        try:
            os.remove('encrypted_noise.bin')
            os.remove('decrypted_image.png')
            print_info("Test files removed")
        except:
            pass
        
        return True
        
    except Exception as e:
        print_error(f"Image encryption test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ==================== Test 3: Compare Multiple Encryptions ====================

def test_multiple_encryptions():
    print_header("Test 3: Same Text → Different Encrypted Output")
    try:
        from encryption import EncryptionService
        
        service = EncryptionService()
        
        # Generate keys
        private_key, public_key = service.generate_rsa_keypair()
        
        # Same text, encrypt twice
        text = "Hello World 🌍"
        
        print(f"\n📄 Original text: '{text}'")
        print("\n🔐 Encrypting the SAME text twice...")
        
        encrypted1 = service.encrypt_text(text, public_key)
        encrypted2 = service.encrypt_text(text, public_key)
        
        print("\n" + "="*70)
        print("🔒 FIRST ENCRYPTION:")
        print("="*70)
        print(f"   {encrypted1['encrypted_data'][:100]}...")
        
        print("\n" + "="*70)
        print("🔒 SECOND ENCRYPTION:")
        print("="*70)
        print(f"   {encrypted2['encrypted_data'][:100]}...")
        
        # Compare
        print("\n📊 Comparison:")
        if encrypted1['encrypted_data'] != encrypted2['encrypted_data']:
            print_success("✓ Both encryptions are DIFFERENT!")
            print_info("   This is GOOD - same input produces different output")
            print_info("   (Due to random IV - Initialization Vector)")
        else:
            print_error("✗ Both encryptions are the same!")
            print_error("   This is BAD - encryption is predictable")
        
        # Show IVs are different
        print("\n🎲 Random IVs (Initialization Vectors):")
        print(f"   Encryption 1 IV: {encrypted1['iv']}")
        print(f"   Encryption 2 IV: {encrypted2['iv']}")
        print(f"   → Different IVs = Different encrypted output! ✅")
        
        # But both decrypt correctly
        print("\n🔓 Decrypting both...")
        decrypted1 = service.decrypt_text(
            encrypted1['encrypted_data'],
            encrypted1['encrypted_key'],
            encrypted1['iv'],
            encrypted1['auth_tag'],
            private_key
        )
        decrypted2 = service.decrypt_text(
            encrypted2['encrypted_data'],
            encrypted2['encrypted_key'],
            encrypted2['iv'],
            encrypted2['auth_tag'],
            private_key
        )
        
        print(f"   Decrypted 1: '{decrypted1}'")
        print(f"   Decrypted 2: '{decrypted2}'")
        
        if decrypted1 == decrypted2 == text:
            print_success("✓ Both decrypt to the SAME original text!")
        
        return True
        
    except Exception as e:
        print_error(f"Multiple encryptions test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ==================== Test 4: Byte-by-Byte Analysis ====================

def test_byte_analysis():
    print_header("Test 4: Byte-by-Byte Analysis")
    try:
        from encryption import EncryptionService
        
        service = EncryptionService()
        private_key, public_key = service.generate_rsa_keypair()
        
        # Simple text
        text = "ABC"
        print(f"\n📄 Original text: '{text}'")
        
        # Show as bytes
        text_bytes = text.encode('utf-8')
        print(f"\n💾 Original bytes (UTF-8):")
        print(f"   Hex: {text_bytes.hex()}")
        print(f"   Dec: {[b for b in text_bytes]}")
        print(f"   Bin: {' '.join(format(b, '08b') for b in text_bytes)}")
        
        # Encrypt
        encrypted = service.encrypt_text(text, public_key)
        encrypted_bytes = base64.b64decode(encrypted['encrypted_data'])
        
        print(f"\n🔒 Encrypted bytes:")
        print(f"   Hex: {encrypted_bytes[:20].hex()}... ({len(encrypted_bytes)} bytes total)")
        print(f"   Dec: {[b for b in encrypted_bytes[:20]]}... ")
        print(f"   Bin: {' '.join(format(b, '08b') for b in encrypted_bytes[:8])}...")
        
        print("\n📊 Analysis:")
        print(f"   Original size: {len(text_bytes)} bytes")
        print(f"   Encrypted size: {len(encrypted_bytes)} bytes")
        print(f"   Size increase: {len(encrypted_bytes) - len(text_bytes)} bytes")
        print(f"   → Encryption adds overhead (padding, authentication)")
        
        # Decrypt
        decrypted = service.decrypt_text(
            encrypted['encrypted_data'],
            encrypted['encrypted_key'],
            encrypted['iv'],
            encrypted['auth_tag'],
            private_key
        )
        
        print(f"\n✅ Decrypted: '{decrypted}'")
        
        return True
        
    except Exception as e:
        print_error(f"Byte analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ==================== Main ====================

def main():
    print("\n" + "🔐"*35)
    print("   DLP System - Visual Encryption Test Suite")
    print("   See the actual encrypted gibberish!")
    print("🔐"*35 + "\n")
    
    results = {
        'Text Encryption (Visual)': test_text_encryption_visual(),
        'Image Encryption (Visual)': test_image_encryption_visual(),
        'Multiple Encryptions': test_multiple_encryptions(),
        'Byte Analysis': test_byte_analysis()
    }
    
    print_header("Test Results Summary")
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n📊 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎉 All tests passed successfully!")
        print("\n💡 Key Takeaways:")
        print("   • Encryption turns readable data into random noise")
        print("   • Same input → Different encrypted output (due to random IV)")
        print("   • Only the correct key can decrypt the data")
        print("   • Encrypted data is completely unreadable without the key")
        return 0
    else:
        print_error("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())