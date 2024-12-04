from flask import Flask, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import pickle
import base64
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a more secure key for production

# OAuth Setup (replace with your actual credentials JSON path)
credential_base64 = os.environ.get("GOOGLE_CREDENTIALS")
if credential_base64:
    decoded_credentials = base64.b64decode(credential_base64).decode('utf-8')
    credentials = json.loads(decoded_credentials)
    with open('credentials/temp_credentials.json', "w") as file:
        file.write(json.dumps(credentials))

flow = Flow.from_client_secrets_file(
    'credentials/temp_credentials.json', 
    scopes=['https://www.googleapis.com/auth/drive.file'],  
    redirect_uri='http://localhost:5000/oauth2callback'
)

def save_credentials(credentials, user_id):
    """Save user credentials in a file (use database in production)."""
    token_file = f'tokens/{user_id}_token.pickle'
    os.makedirs('tokens', exist_ok=True)
    with open(token_file, 'wb') as token:
        pickle.dump(credentials, token)

def load_credentials(user_id):
    """Load user credentials from a file."""
    token_file = f'tokens/{user_id}_token.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            return pickle.load(token)
    return None

# Index Route
@app.route('/')
def index():
    return 'Welcome! Go to <a href="/authorize">/authorize</a> to authenticate.'

@app.route('/authorize')
def authorize():
    """Redirect to Google OAuth consent page."""
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """OAuth2 callback to handle the response from Google."""
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    user_id = 'user1'  # Replace with actual user identification logic
    save_credentials(credentials, user_id)
    return redirect(url_for('list_files'))

@app.route('/list_files')
def list_files():
    """List files in Google Drive."""
    user_id = 'user1'  # Replace with actual user identification logic
    credentials = load_credentials(user_id)

    if not credentials:
        return redirect(url_for('authorize'))

    # Build Google Drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    # Fetch file list from Google Drive
    results = drive_service.files().list(pageSize=10).execute()
    items = results.get('files', [])

    return jsonify({"files": [item['name'] for item in items]})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Upload a file to Google Drive."""
    user_id = 'unique_user_identifier'  # Replace with actual user identification logic
    credentials = load_credentials(user_id)

    if not credentials:
        return redirect(url_for('authorize'))

    # Build Google Drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    file = request.files['file']  # Get file from the request
    file_metadata = {'name': file.filename}
    media = MediaFileUpload(file, mimetype='application/octet-stream')

    # Upload file to Drive
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    return jsonify({"message": "File uploaded successfully", "file_id": file['id']})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=True)
