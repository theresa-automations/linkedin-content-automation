"""
LinkedIn Drive Sync — v1.0
Theresa Erhumwunse | LinkedIn Content System

Syncs markdown files from the LinkedIn Project folder to Google Drive.
Called by generator, auditor, and runner after each run.

First run: opens browser for OAuth authentication (one-time only).
Subsequent runs: uses saved token and auto-refreshes when expired.

Run directly once for the initial upload of all .md files:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_drive_sync.py"
"""

import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

PROJECT_DIR     = r"C:\Users\pc\Documents\LinkedIn Project"
OAUTH_KEYS      = r"C:\Users\pc\gdrive-personal-mcp\credentials\gcp-oauth.keys.json"
TOKEN_FILE      = r"C:\Users\pc\gdrive-personal-mcp\credentials\.gdrive-write-token.json"
FILE_ID_MAP     = r"C:\Users\pc\Documents\LinkedIn Project\drive-file-ids.json"
DRIVE_FOLDER_ID = "19ott1CnfEbvva99aK71XQ_9ffadSlMit"
SCOPES          = ["https://www.googleapis.com/auth/drive"]

# ── AUTH ───────────────────────────────────────────────────────────────────────

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_KEYS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())

# ── FILE ID MAP ────────────────────────────────────────────────────────────────

def load_file_id_map():
    if os.path.exists(FILE_ID_MAP):
        with open(FILE_ID_MAP) as f:
            return json.load(f)
    return {}

def save_file_id_map(mapping):
    with open(FILE_ID_MAP, "w") as f:
        json.dump(mapping, f, indent=2)

# ── UPLOAD / UPDATE ────────────────────────────────────────────────────────────

def upload_or_update(service, local_path, file_id_map):
    filename = os.path.basename(local_path)
    media    = MediaFileUpload(local_path, mimetype="text/plain", resumable=False)

    if filename in file_id_map:
        service.files().update(
            fileId=file_id_map[filename],
            media_body=media
        ).execute()
        return filename, file_id_map[filename], "UPDATED"
    else:
        metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}
        result   = service.files().create(
            body=metadata,
            media_body=media,
            fields="id"
        ).execute()
        file_id_map[filename] = result["id"]
        return filename, result["id"], "UPLOADED"

# ── PUBLIC SYNC FUNCTION ───────────────────────────────────────────────────────

def sync_to_drive(files=None):
    """
    Sync markdown files to Google Drive.

    files: list of filenames e.g. ['drafts.md', 'schedule.md']
           or None to sync all .md files in the project folder.

    Returns: (success: bool, message: str)
    """
    try:
        service     = get_drive_service()
        file_id_map = load_file_id_map()

        if files:
            paths = [
                os.path.join(PROJECT_DIR, f)
                for f in files
                if f.endswith(".md") and os.path.exists(os.path.join(PROJECT_DIR, f))
            ]
        else:
            paths = sorted(Path(PROJECT_DIR).glob("*.md"))

        if not paths:
            return False, "No .md files found to sync"

        results = []
        for path in paths:
            name, fid, action = upload_or_update(service, str(path), file_id_map)
            results.append(f"  [{action}] {name}")

        save_file_id_map(file_id_map)
        summary = f"Drive sync OK — {len(paths)} file(s)\n" + "\n".join(results)
        return True, summary

    except Exception as e:
        return False, f"Drive sync FAILED: {str(e)}"

# ── STANDALONE: initial upload of all .md files ────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("LinkedIn Drive Sync — Initial Upload")
    print("=" * 60)
    print(f"Target folder: https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")
    print()

    success, message = sync_to_drive()
    print(message)
    print()

    if success:
        print(f"File ID map saved to: {FILE_ID_MAP}")
        print("Future syncs will update these files automatically.")
    else:
        print("Check the error above and try again.")
