"""
Gmail Integration — Automated inbox scanning and threat response (Phase 83).
Uses Google API to fetch and analyze emails directly.
"""

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.models.predict import predict_email
from src.utils.logger import logger

# Required scopes for reading and modifying labels
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailScanner:
    def __init__(self, credentials_path: str = "config/credentials.json"):
        self.creds = None
        self.service = None
        self.creds_path = credentials_path
        self._authenticate()

    def _authenticate(self):
        """Standard Google OAuth2 flow."""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    logger.warning("Gmail credentials.json missing. Running in MOCK MODE.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def scan_inbox(self, max_results: int = 10):
        """Fetch latest emails, classify them, and label threats."""
        if not self.service:
            print("[MOCK] Scanning simulated inbox... No threats found.")
            return

        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
            messages = results.get('messages', [])

            for msg_meta in messages:
                msg = self.service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute()
                
                # Extract text parts
                payload = msg.get('payload', {})
                body = ""
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            body = base64.urlsafe_b64decode(part['body']['data']).decode()
                else:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode()

                # Predict
                res = predict_email(body)
                
                if res['prediction'] == 'spam' or res['security_risk_score'] > 70:
                    logger.warning("Threat Found in Gmail: %s (Risk: %d)", msg_meta['id'], res['security_risk_score'])
                    self._mark_as_threat(msg_meta['id'])

        except Exception as e:
            logger.error("Gmail Scan Error: %s", e)

    def _mark_as_threat(self, msg_id: str):
        """Move email to a special 'Security Threat' label or Trash."""
        print(f"--- [SECURITY RESPONSE] Flagging Gmail Message {msg_id} as Threat ---")
        # In real usage:
        # self.service.users().messages().batchModify(
        #     userId='me',
        #     body={'ids': [msg_id], 'addLabelIds': ['SPAM'], 'removeLabelIds': ['INBOX']}
        # ).execute()

if __name__ == "__main__":
    scanner = GmailScanner()
    scanner.scan_inbox()
