# DLP Dashboard

A local file-encryption dashboard built with React and Flask. It demonstrates how a team can upload and classify documents, encrypt them for storage, and review a history of file operations. A separate workspace lets users experiment with RSA keys and encrypt or decrypt text and files.

## Features

- Upload files and assign classification labels.
- Browse stored files and download an encrypted copy or request decryption through the dashboard.
- Generate RSA key pairs and encrypt or decrypt text and files.
- Review upload and download activity in the audit log.

## How it works

The React dashboard sends requests to the Flask API on port 5000. For an upload, the backend generates a fresh AES key, encrypts the file with AES-256-GCM, and wraps the AES key with RSA-OAEP using SHA-256. The encrypted file is stored on disk. SQLite holds the file metadata and audit records.

| Path | Purpose |
| --- | --- |
| `frontend/src/DLPDashboard.jsx` | Dashboard, file controls, encryption tools, and audit view |
| `backend/app.py` | API routes, database models, and upload and download workflows |
| `backend/encryption.py` | RSA key generation and hybrid encryption |
| `backend/access_control.py` | Attribute-based access-control helper |

## Run locally on Windows

Use Python 3.11 and Node.js with npm. Open two PowerShell windows in the project root.

**Backend**

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask Flask-SQLAlchemy Flask-CORS cryptography Pillow
.\.venv\Scripts\python.exe app.py
~~~

The backend starts on port 5000 and initializes the SQLite database. The command installs the packages imported by the local backend. The bundled requirements file declares conflicting versions for several Flask packages.

**Frontend**

~~~powershell
cd frontend
npm ci
npm start
~~~

Open [http://localhost:3000](http://localhost:3000). The dashboard expects the API at `http://127.0.0.1:5000`. To try the workflow, upload a sample file, choose a classification, and check the file list and audit log.

## Demo scope

Use sample files in a trusted local environment. The current API has unauthenticated routes and uses a default admin account for uploads. Classification labels record metadata. The active file routes lack per-user enforcement of those labels. The Flask entry point enables debug mode and listens on all interfaces.

Keep local database files, uploaded files, credentials, and private keys out of source control.
