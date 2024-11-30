from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_user(user_id):
    """Authenticate a user and save their credentials separately."""
    token_file = f'tokens/{user_id}_token.pickle'
    creds = None

    # Check if user's token exists
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, perform OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the user
        os.makedirs('tokens', exist_ok=True)
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def create_folder(service, folder_name, parent_folder_id):
    """Create a folder in Google Drive."""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]

    folder = service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
    folder_id = folder.get('id')
    folder_url = folder.get('webViewLink')
    return folder_id, folder_url

def get_folder_id(service, folder_name):
    """Check if a folder exists and return its ID and webViewLink if it does."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(
        q=query, 
        spaces='drive', 
        fields='files(id, name, webViewLink)'
    ).execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
        folder_url = items[0]['webViewLink']
        return folder_id, folder_url
    
    print(f"Folder '{folder_name}' does not exist.")
    return None, None

def upload_file_to_folder(service, file_path, folder_id):
    """Upload a file to a specific folder in Google Drive."""
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File '{file_path}' uploaded successfully. File ID: {file.get('id')}")
    return file.get('id')

def set_permission(service, file_id):
    """Set file or folder permissions to 'Anyone with the link' and 'Viewer only'."""
    permission = {
        'type': 'anyone',
        'role': 'reader'  # 'reader' for view-only, 'writer' for edit access
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

def access_drive(user_id, items, parent_folder_id="1xEqyKg7WC5t3QVmgfZgw26BCLBQ9C4Um"):
    # Authenticate the user
    service = authenticate_user(user_id)

    reports = []
    for item in items:       
        folder_name = item["folder"]
        files_to_upload = item["path"]
        # Step 1: Create folder
        folder_id, folder_url = get_folder_id(service, folder_name)
        if not folder_id:
            folder_id, folder_url = create_folder(service, folder_name, parent_folder_id)

        # Step 2: Set permissions for the folder
        set_permission(service, folder_id)

        # Step 3: Upload files to the created folder
        for file_path in files_to_upload:
            upload_file_to_folder(service, file_path, folder_id)
            # Step 4: Set permissions for each file (optional, since the folder already has public permissions)
            # set_permission(service, file_id)
        reports.append({'folder': folder_name, 'url': folder_url})
    return reports
        
        
    