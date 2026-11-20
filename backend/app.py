from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import sys
import secrets
import json
import uuid
import base64
from io import BytesIO
from encryption import EncryptionService

app = Flask(__name__)

# ==================== CORS Configuration ====================
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ==================== Configuration ====================
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dlp_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = 'encrypted_storage'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
encryption_service = EncryptionService()

# ==================== Database Models ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    department = db.Column(db.String(50))
    role = db.Column(db.String(50))
    clearance_level = db.Column(db.Integer, default=1)
    
    public_key = db.Column(db.Text)
    encrypted_private_key = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    files = db.relationship('File', backref='owner', lazy=True)

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(100), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    
    encrypted_path = db.Column(db.String(500), nullable=False)
    encryption_metadata = db.Column(db.Text)
    encryption_algorithm = db.Column(db.String(50), default='AES-256-GCM')
    
    watermark_hash = db.Column(db.String(200))
    has_watermark = db.Column(db.Boolean, default=False)
    
    access_policy = db.Column(db.Text)
    classification = db.Column(db.String(50))
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    audit_logs = db.relationship('AuditLog', backref='file', lazy=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(100), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    
    action = db.Column(db.String(50), nullable=False)
    action_result = db.Column(db.String(20), nullable=False)
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    location = db.Column(db.String(100))
    details = db.Column(db.Text)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='audit_logs')

# ==================== API Endpoints ====================

@app.route('/files', methods=['GET', 'OPTIONS'])
def get_files_simple():
    """Get files list"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        files = File.query.filter_by(is_active=True).all()
        result = [
            {
                'id': f.id,
                'name': f.original_filename,
                'classification': f.classification or 'Internal',
                'encrypted': True,
                'watermarked': f.has_watermark,
                'size': f'{f.file_size / 1024 / 1024:.2f} MB' if f.file_size else '0 MB',
                'uploaded': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'type': f.file_type
            }
            for f in files
        ]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in get_files: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/audit', methods=['GET', 'OPTIONS'])
def get_audit_simple():
    """Get audit logs"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
        result = [
            {
                'id': log.id,
                'action': log.action.title(),
                'file': log.file.original_filename if log.file else 'N/A',
                'user': log.user.username if log.user else 'System',
                'ip': log.ip_address or 'Unknown',
                'result': log.action_result.title(),
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for log in logs
        ]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in get_audit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_simple():
    """Upload and encrypt file"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("\n" + "="*70)
        print("📥 UPLOAD REQUEST RECEIVED")
        print("="*70)
        print(f"Files in request: {list(request.files.keys())}")
        print(f"Form data: {list(request.form.keys())}")
        
        if 'file' not in request.files:
            print("❌ No 'file' in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"📄 Received file: {file.filename}")
        print(f"📄 Content type: {file.content_type}")
        
        # Read file data
        file_data = file.read()
        print(f"📊 File size: {len(file_data)} bytes ({len(file_data) / 1024 / 1024:.2f} MB)")
        
        # Get or create default user
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("👤 Creating default admin user...")
            create_default_user()
            user = User.query.filter_by(username='admin').first()
            
        if not user:
            print("❌ Failed to create/get admin user")
            return jsonify({'error': 'User creation failed'}), 500
        
        print(f"👤 User: {user.username} (ID: {user.id})")
        
        # Get or generate user keys
        if not user.public_key or not user.encrypted_private_key:
            print("🔑 Generating RSA keys for user...")
            private_key, public_key = encryption_service.generate_rsa_keypair()
            user.public_key = public_key
            user.encrypted_private_key = private_key
            db.session.commit()
            print("✅ Keys generated and saved")
        
        # Encrypt file
        print("🔐 Starting encryption...")
        encrypted_result = encryption_service.encrypt_file(
            file_data,
            user.public_key,
            file_type=file.content_type or 'application/octet-stream',
            filename=file.filename
        )
        print("✅ Encryption completed")
        
        # Save encrypted file
        file_id = str(uuid.uuid4())
        safe_filename = secure_filename(file.filename)
        encrypted_filename = f"{file_id}_{safe_filename}.enc"
        encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_filename)
        
        print(f"💾 Saving to: {encrypted_path}")
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_result['encrypted_data'])
        print("✅ File saved")
        
        # Save encryption metadata
        encryption_metadata = {
            'encrypted_key': encrypted_result['encrypted_key'],
            'iv': encrypted_result['iv'],
            'auth_tag': encrypted_result['auth_tag'],
            'metadata': encrypted_result['metadata']
        }
        
        # Create file record
        classification = request.form.get('classification', 'Internal')
        print(f"📋 Creating database record with classification: {classification}")
        new_file = File(
            file_id=file_id,
            filename=encrypted_filename,
            original_filename=safe_filename,
            file_type=file.content_type or 'application/octet-stream',
            file_size=len(file_data),
            encrypted_path=encrypted_path,
            encryption_metadata=json.dumps(encryption_metadata),
            classification=classification,
            owner_id=user.id,
            has_watermark=True,
            access_policy='{}'
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        print(f"✅ File record created: ID={new_file.id}")
        
        # Log action
        log_audit_action(user.id, new_file.id, 'upload', 'success')
        
        print("🎉 Upload completed successfully!")
        print("="*70 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and encrypted successfully',
            'file_id': file_id,
            'filename': safe_filename
        }), 200
        
    except Exception as e:
        print(f"\n❌ UPLOAD ERROR: {str(e)}")
        print("🔍 Full traceback:")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/download/<int:file_id>', methods=['GET', 'OPTIONS'])
def download_file_simple(file_id):
    """Download and decrypt file"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print(f"\n📥 Download request for file ID: {file_id}")
        
        file_record = File.query.get(file_id)
        if not file_record:
            print(f"❌ File ID {file_id} not found in database")
            return jsonify({'error': 'File not found'}), 404
        
        print(f"📄 Found file: {file_record.original_filename}")
        
        user = file_record.owner
        if not user.encrypted_private_key:
            print("❌ User keys not found")
            return jsonify({'error': 'User keys not found'}), 500
        
        # Load encrypted file
        print(f"📂 Loading encrypted file from: {file_record.encrypted_path}")
        with open(file_record.encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        print(f"📊 Encrypted file size: {len(encrypted_data)} bytes")
        
        # Load encryption metadata
        metadata = json.loads(file_record.encryption_metadata)
        
        # Decrypt file
        print("🔓 Decrypting file...")
        decrypted_data = encryption_service.decrypt_file(
            encrypted_data,
            metadata['encrypted_key'],
            metadata['iv'],
            metadata['auth_tag'],
            user.encrypted_private_key,
            metadata.get('metadata')
        )
        
        print(f"✅ File decrypted successfully ({len(decrypted_data)} bytes)")
        
        # Log action
        log_audit_action(user.id, file_record.id, 'download', 'success')
        
        # Return decrypted file
        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.file_type
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download-encrypted/<int:file_id>', methods=['GET', 'OPTIONS'])
def download_encrypted_file(file_id):
    """Download encrypted file (without decryption)"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print(f"\n🔒 Download ENCRYPTED request for file ID: {file_id}")
        
        file_record = File.query.get(file_id)
        if not file_record:
            print(f"❌ File ID {file_id} not found in database")
            return jsonify({'error': 'File not found'}), 404
        
        print(f"📄 Found file: {file_record.original_filename}")
        
        # Load encrypted file (WITHOUT decryption)
        print(f"📂 Loading encrypted file from: {file_record.encrypted_path}")
        with open(file_record.encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        print(f"📊 Encrypted file size: {len(encrypted_data)} bytes")
        
        # Load encryption metadata
        metadata = json.loads(file_record.encryption_metadata)
        
        # Create a package with encrypted data + metadata
        package = {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'encrypted_key': metadata['encrypted_key'],
            'iv': metadata['iv'],
            'auth_tag': metadata['auth_tag'],
            'metadata': metadata['metadata'],
            'original_filename': file_record.original_filename
        }
        
        # Save as JSON file
        package_json = json.dumps(package, indent=2)
        
        print(f"✅ Encrypted package prepared ({len(package_json)} bytes)")
        
        # Log action
        user = file_record.owner
        log_audit_action(user.id, file_record.id, 'download_encrypted', 'success')
        
        # Return encrypted file
        return send_file(
            BytesIO(package_json.encode('utf-8')),
            as_attachment=True,
            download_name=f"{file_record.original_filename}.encrypted.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"❌ Download encrypted error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== Encryption Test Endpoints ====================

@app.route('/generate-keys', methods=['POST', 'OPTIONS'])
def generate_keys():
    """Generate RSA key pair"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("🔑 Generating RSA key pair...")
        private_key, public_key = encryption_service.generate_rsa_keypair()
        print("✅ Keys generated successfully")
        return jsonify({
            'private_key': private_key,
            'public_key': public_key
        }), 200
    except Exception as e:
        print(f"❌ Key generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/encrypt-file', methods=['POST', 'OPTIONS'])
def encrypt_file_endpoint():
    """Encrypt a file"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("🔐 Encrypt file endpoint called")
        file = request.files['file']
        public_key = request.form['public_key']
        
        file_data = file.read()
        print(f"📊 Encrypting {len(file_data)} bytes...")
        
        result = encryption_service.encrypt_file(
            file_data,
            public_key,
            file_type=file.content_type,
            filename=file.filename
        )
        
        # Convert encrypted_data to base64 for JSON response
        result['encrypted_data'] = base64.b64encode(result['encrypted_data']).decode('utf-8')
        
        print("✅ File encrypted successfully")
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ File encryption error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/encrypt-text', methods=['POST', 'OPTIONS'])
def encrypt_text_endpoint():
    """Encrypt text"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("🔐 Encrypt text endpoint called")
        data = request.get_json()
        text = data['text']
        public_key = data['public_key']
        
        print(f"📝 Encrypting text: '{text[:50]}...'")
        result = encryption_service.encrypt_text(text, public_key)
        print("✅ Text encrypted successfully")
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Text encryption error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/decrypt-file', methods=['POST', 'OPTIONS'])
def decrypt_file_endpoint():
    """Decrypt a file"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("🔓 Decrypt file endpoint called")
        data = request.get_json()
        
        encrypted_data = base64.b64decode(data['encrypted_data'])
        
        print(f"📊 Decrypting {len(encrypted_data)} bytes...")
        decrypted = encryption_service.decrypt_file(
            encrypted_data,
            data['encrypted_key'],
            data['iv'],
            data['auth_tag'],
            data['private_key'],
            data.get('metadata')
        )
        
        print("✅ File decrypted successfully")
        return send_file(
            BytesIO(decrypted),
            mimetype='application/octet-stream'
        )
    except Exception as e:
        print(f"❌ File decryption error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/decrypt-text', methods=['POST', 'OPTIONS'])
def decrypt_text_endpoint():
    """Decrypt text"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("🔓 Decrypt text endpoint called")
        data = request.get_json()
        
        text = encryption_service.decrypt_text(
            data['encrypted_data'],
            data['encrypted_key'],
            data['iv'],
            data['auth_tag'],
            data['private_key']
        )
        
        print(f"✅ Text decrypted: '{text[:50]}...'")
        return jsonify({'text': text}), 200
    except Exception as e:
        print(f"❌ Text decryption error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== Helper Functions ====================

def log_audit_action(user_id, file_id, action, result, details=None):
    """Log action to audit trail"""
    try:
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            file_id=file_id,
            action=action,
            action_result=result,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details=json.dumps(details) if details else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"⚠️  Audit log error: {e}")

def create_default_user():
    """Create default admin user"""
    try:
        if not User.query.filter_by(username='admin').first():
            print("👤 Creating default admin user...")
            private_key, public_key = encryption_service.generate_rsa_keypair()
            
            admin = User(
                username='admin',
                email='admin@dlp.local',
                password_hash=generate_password_hash(os.environ.get('DLP_ADMIN_PASSWORD') or secrets.token_urlsafe(32)),
                department='IT Security',
                role='admin',
                clearance_level=5,
                public_key=public_key,
                encrypted_private_key=private_key
            )
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print(f"⚠️  Error creating default user: {e}")
        db.session.rollback()

# ==================== Run Application ====================

if __name__ == '__main__':
    with app.app_context():
        print("\n🔧 Initializing database...")
        db.create_all()
        create_default_user()
        print("✅ Database initialized")
    
    print("\n" + "🚀"*30)
    print("   DLP System API Server")
    print("🚀"*30)
    print("\n📡 Server: http://127.0.0.1:5000")
    print("🔐 Features: Encryption, Decryption, Watermarking")
    print("📋 Endpoints:")
    print("   - GET  /files")
    print("   - GET  /audit")
    print("   - POST /upload")
    print("   - GET  /download/<id>")
    print("   - GET  /download-encrypted/<id>")
    print("   - POST /generate-keys")
    print("   - POST /encrypt-file")
    print("   - POST /encrypt-text")
    print("   - POST /decrypt-file")
    print("   - POST /decrypt-text")
    print("\n✅ Ready to accept connections!\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)