# from email.mime.text import MIMEText
# import base64
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# import os

# SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# class GmailService:
#     creds = None
#     def __init__(self):
#         self.creds = None
#         self.token_path = "/Users/zoro/Downloads/AI_Screen/credentials/token.json"
#         self.cred_path = "/Users/zoro/Downloads/AI_Screen/credentials/gmail_credentials.json"
#         self.creds = self.get_credentials()

#     def get_credentials(self):
#         if os.path.exists(self.token_path):
#             from google.oauth2.credentials import Credentials
#             creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
#             return creds

#         flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, SCOPES)
#         creds = flow.run_local_server(port=0)

#         with open(self.token_path, "w") as token:
#             token.write(creds.to_json())

#         return creds

#     def build_service(self):
#         return build("gmail", "v1", credentials=self.creds)

#     def send_email(self, to_email: str, subject: str, message_text: str):
#         service = self.build_service()

#         message = MIMEText(message_text)
#         message["to"] = to_email
#         message["subject"] = subject

#         raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

#         sent = service.users().messages().send(
#             userId="me",
#             body={"raw": raw}
#         ).execute()

#         return {"message_id": sent["id"], "status": "Email sent successfully!"}

# app/services/gmail_services.py
from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailService:
    """
    Gmail service for sending emails via Google API
    Automatically handles token refresh when expired
    """
    
    def __init__(self):
        self.creds = None
        
        # Use relative paths from project root
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.token_path = base_dir / "credentials" / "token.json"
        self.cred_path = base_dir / "credentials" / "gmail_credentials.json"
        
        # Ensure credentials directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.creds = self.get_credentials()

    def get_credentials(self):
        """Get or refresh credentials"""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
                creds = None
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
                print("Token refreshed successfully")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        # Generate new token if needed
        if not creds or not creds.valid:
            if not self.cred_path.exists():
                raise FileNotFoundError(
                    f"Gmail credentials not found at {self.cred_path}. "
                    "Please add your gmail_credentials.json file."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.cred_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            # Save new token
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            print("New token generated and saved")
        
        return creds

    def build_service(self):
        """Build Gmail API service"""
        if not self.creds or not self.creds.valid:
            self.creds = self.get_credentials()
        return build("gmail", "v1", credentials=self.creds)

    def send_email(self, to_email: str, subject: str, message_text: str):
        """
        Send an email via Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message_text: Email body (plain text)
            
        Returns:
            dict with message_id and status
        """
        try:
            service = self.build_service()

            message = MIMEText(message_text)
            message["to"] = to_email
            message["subject"] = subject
            
            # Optional: Add From header (will use authenticated account by default)
            # message["from"] = "your-email@gmail.com"

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            sent = service.users().messages().send(
                userId="me",
                body={"raw": raw}
            ).execute()

            return {
                "message_id": sent["id"],
                "status": "Email sent successfully!",
                "to": to_email
            }
        
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")