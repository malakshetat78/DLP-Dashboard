"""
DLP Image & Text Encryption Service
====================================
AES-256-GCM encryption for images, text, and files
Supports: PNG, JPG, JPEG, BMP, GIF, WebP, Text, PDF
"""

import os
import json
import io
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64

class EncryptionService:
    """Advanced encryption service for images, text, and files"""
    
    def __init__(self):
        self.backend = default_backend()
        self.supported_image_formats = ['PNG', 'JPEG', 'JPG', 'BMP', 'GIF', 'WEBP']
    
    # ==================== RSA Key Management ====================
    
    def generate_rsa_keypair(self, key_size=2048):
        """Generate RSA key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=self.backend
        )
        
        public_key = private_key.public_key()
        #هذا الكود يحول المفاتيح من كائنات Python إلى نصوص يمكن حفظها ومشاركتها.
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        #هذا السطر بيحول من bytes لـ string**

        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    # ==================== Universal File Encryption ====================
    
    def encrypt_file(self, file_data, public_key_pem, file_type=None, filename=None):
        """
        Encrypt any file (images, text, PDF, etc.)
        
        Args:
            file_data (bytes): File data
            public_key_pem (str): Public key
            file_type (str): File type
            filename (str): Original filename
            
        Returns:
            dict: Encrypted data + metadata
        """
        print(f"🔐 Starting encryption for {file_type or 'file'}...")
        #اكتشاف نوع الملف
        # Detect file type automatically
        is_image = False
        image_metadata = {}
        
        if file_type and 'image' in file_type.lower():
            try:
                img = Image.open(io.BytesIO(file_data))
                is_image = True
                image_metadata = {
                    'format': img.format or 'PNG',
                    'size': img.size,
                    'mode': img.mode
                }
                print(f"🖼  Image detected: {img.size[0]}x{img.size[1]}, {img.mode}")
            except:
                pass
        
        # 1. Generate unique AES key (256-bit)
        aes_key = os.urandom(32)
        iv = os.urandom(12)  # 96-bit for GCM
        
        print(f"🔑 Generated unique AES-256 key")
        print(f"🎲 Generated unique IV")
        
        # 2. Encrypt data using AES-256-GCM
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        encrypted_data = encryptor.update(file_data) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        print(f"✅ Data encrypted successfully")
        print(f"📊 Original size: {len(file_data)} bytes")
        print(f"🔒 Encrypted size: {len(encrypted_data)} bytes")
        
        # 3. Encrypt AES key using RSA
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=self.backend
        )
        
        encrypted_aes_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        print(f"🔐 AES key encrypted with RSA-2048")
        
        # 4. Prepare metadata
        metadata = {
            'algorithm': 'AES-256-GCM',
            'key_size': 256,
            'iv_size': 96,
            'rsa_key_size': 2048,
            'file_type': file_type,
            'filename': filename,
            'original_size': len(file_data)
        }
        
        if is_image:
            metadata['image'] = image_metadata
        
        return {
            'encrypted_data': encrypted_data,
            'encrypted_key': base64.b64encode(encrypted_aes_key).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'auth_tag': base64.b64encode(auth_tag).decode('utf-8'),
            'metadata': metadata
        }
    
    def decrypt_file(self, encrypted_data, encrypted_key_b64, iv_b64, auth_tag_b64, 
                    private_key_pem, metadata=None):
        """
        Decrypt any file
        
        Returns:
            bytes: Original data
        """
        print(f"🔓 Starting decryption...")
        
        # 1. Decrypt AES key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=self.backend
        )
        
        encrypted_aes_key = base64.b64decode(encrypted_key_b64)
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        print(f"🔑 AES key decrypted")
        
        # 2. Decrypt data
        iv = base64.b64decode(iv_b64)
        auth_tag = base64.b64decode(auth_tag_b64)
        
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv, auth_tag),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        print(f"✅ Data decrypted successfully")
        print(f"📊 Decrypted size: {len(decrypted_data)} bytes")
        
        if metadata and 'image' in metadata:
            print(f"🖼  Image restored")
        
        return decrypted_data
    
    # ==================== Specialized Methods ====================
    
    def encrypt_image(self, image_path_or_bytes, public_key_pem, output_format='PNG'):
        """Encrypt image (specialized wrapper)"""
        if isinstance(image_path_or_bytes, str):
            with open(image_path_or_bytes, 'rb') as f:
                file_data = f.read()
            filename = os.path.basename(image_path_or_bytes)
        else:
            file_data = image_path_or_bytes
            filename = 'image.png'
        
        return self.encrypt_file(file_data, public_key_pem, 'image', filename)
    
    def decrypt_image(self, encrypted_data, encrypted_key_b64, iv_b64, auth_tag_b64, 
                     private_key_pem, metadata=None):
        """Decrypt image and return as PIL Image"""
        decrypted_bytes = self.decrypt_file(
            encrypted_data, encrypted_key_b64, iv_b64, auth_tag_b64, 
            private_key_pem, metadata
        )
        return Image.open(io.BytesIO(decrypted_bytes))
    
    def encrypt_text(self, text, public_key_pem):
        """Encrypt text"""
        text_bytes = text.encode('utf-8')
        result = self.encrypt_file(text_bytes, public_key_pem, 'text', 'text.txt')
        # Convert encrypted_data to base64 for text
        result['encrypted_data'] = base64.b64encode(result['encrypted_data']).decode('utf-8')
        return result
    
    def decrypt_text(self, encrypted_data_b64, encrypted_key_b64, iv_b64, auth_tag_b64, 
                    private_key_pem):
        """Decrypt text"""
        encrypted_data = base64.b64decode(encrypted_data_b64)
        decrypted_bytes = self.decrypt_file(
            encrypted_data, encrypted_key_b64, iv_b64, auth_tag_b64, 
            private_key_pem
        )
        return decrypted_bytes.decode('utf-8')
    
    # ==================== Save & Load ====================
    
    def save_encrypted_file(self, encrypted_result, output_path):
        """Save encrypted file with metadata"""
        # Save encrypted data
        encrypted_data = encrypted_result['encrypted_data']
        if isinstance(encrypted_data, str):
            encrypted_data = base64.b64decode(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Save metadata
        metadata = {
            'encrypted_key': encrypted_result['encrypted_key'],
            'iv': encrypted_result['iv'],
            'auth_tag': encrypted_result['auth_tag'],
            'metadata': encrypted_result['metadata']
        }
        with open(output_path + '.meta.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Encrypted file saved: {output_path}")
        print(f"💾 Metadata saved: {output_path}.meta.json")
    
    def load_encrypted_file(self, encrypted_path):
        """Load encrypted file"""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        with open(encrypted_path + '.meta.json', 'r') as f:
            metadata = json.load(f)
        
        return encrypted_data, metadata


# ==================== Test ====================

if __name__ == "__main__":
    print("\n" + "🔐"*30)
    print("   DLP Encryption Service Test")
    print("🔐"*30)
    
    service = EncryptionService()
    
    # Generate keys
    print("\n📋 Generating RSA keys...")
    private_key, public_key = service.generate_rsa_keypair()
    print("✅ Keys generated")
    
    # Test text encryption
    print("\n📋 Testing text encryption...")
    text = "Confidential data 🔒"
    encrypted = service.encrypt_text(text, public_key)
    print(f"✅ Text encrypted")
    
    decrypted = service.decrypt_text(
        encrypted['encrypted_data'],
        encrypted['encrypted_key'],
        encrypted['iv'],
        encrypted['auth_tag'],
        private_key
    )
    print(f"✅ Text decrypted: {decrypted}")
    
    print("\n✅ All tests passed!")