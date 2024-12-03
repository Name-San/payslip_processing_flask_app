import os
import pickle
import base64
import json

def save_credentials(credentials, user_id):
    token_file = f'tokens/{user_id}_token.pickle'
    os.makedirs('tokens', exist_ok=True)
    with open(token_file, 'wb') as token:
        pickle.dump(credentials, token)

# Helper function to load user credentials
def load_credentials(user_id):
    token_file = f'tokens/{user_id}_token.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            return pickle.load(token)
    return None

def load_google_credentials():
    encoded_credentials = os.getenv('GOOGLE_CREDENTIALS')
    if not encoded_credentials:
        raise EnvironmentError("GOOGLE_CREDENTIALS not set in environment variables")
    
    # Decode the Base64 string
    credentials_json = base64.b64decode(encoded_credentials).decode('utf-8')
    credentials = json.loads(credentials_json)

    with open('credentials/credentials_temp.json', 'w') as temp_file:
        temp_file.write(json.dumps(credentials))
