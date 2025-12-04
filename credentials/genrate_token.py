# from google_auth_oauthlib.flow import InstalledAppFlow
# import os

# SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# CRED_PATH = "D:/S2_REC/credentials/gmail_credentials.json"
# TOKEN_PATH = "D:/S2_REC/credentials/token.json"

# def create_token():
#     flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, SCOPES)
#     creds = flow.run_local_server(port=0)

#     with open(TOKEN_PATH, "w") as token:
#         token.write(creds.to_json())

#     print("token.json created at:", TOKEN_PATH)

# if __name__ == "__main__":
#     create_token()

# generate_token.py - Run this from your project root
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Use relative paths
BASE_DIR = Path(__file__).resolve().parent
CRED_PATH = BASE_DIR / "credentials" / "gmail_credentials.json"
TOKEN_PATH = BASE_DIR / "credentials" / "token.json"

def create_token():
    """Generate new Gmail API token"""
    
    if not CRED_PATH.exists():
        print(f"❌ Error: gmail_credentials.json not found at {CRED_PATH}")
        print("Please download your OAuth credentials from Google Cloud Console")
        return
    
    print("🔐 Generating new Gmail token...")
    print("📝 A browser window will open for authorization")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
        creds = flow.run_local_server(port=0)

        # Ensure directory exists
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

        print(f"✅ Token successfully created at: {TOKEN_PATH}")
        print("✅ You can now use the Gmail service in your application")
        
    except Exception as e:
        print(f"❌ Error creating token: {e}")

if __name__ == "__main__":
    create_token()