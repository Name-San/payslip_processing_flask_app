
from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, send_from_directory, render_template, url_for, session
from modules.image_ocr import ocr
from modules.image_editor import edit_image
from modules.connect_gdrive import access_drive
from modules.creds_manager import save_credentials
from google_auth_oauthlib.flow import Flow
import os
import shutil
import json
import csv

# Load the environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
with open("configs/config.json", "r") as file:
    data = json.load(file)

# Generate CSV report
def generate_csv(report):
    if not os.path.exists("reports"):
        os.makedirs("reports")
    heading = [v for k, v in enumerate(report[0])]
    with open('reports/report.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=heading)
        writer.writeheader()
        writer.writerows(report)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Upload route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    os.makedirs(data['upload_folder'], exist_ok=True)
    file = request.files['file']
    if file:
        file_path = os.path.join(data['upload_folder'], file.filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 200
    return jsonify({'message': 'No file uploaded'}), 400

# Process route to handle image processing and OCR
@app.route('/process', methods=['POST'])
def process_file():    
    # Get the uploaded file path
    file_path = request.json['file_path']
    slices_count = data["slice_count_default"]
    
    # Process image
    sliced_images = edit_image(file_path, data["output_folder"], slices_count)
    
    # OCR processing
    items = ocr(sliced_images, data["search_terms"])
    
    service_id = redirect(url_for('get_credential'))
    
    # Google Drive access and upload
    reports = access_drive("user1", items, service_id)
    
    # Generate CSV report
    generate_csv(reports)

    for dir in [data["output_folder"], data["upload_folder"], "tokens"]:
        shutil.rmtree(dir)

    return jsonify({
        'message': 'Processing complete',
        'sliced_images': sliced_images,
        'csv_report': 'reports/report.csv',
        'drive_links': reports
    })

# Download route to get the generated files
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('outputs', filename, as_attachment=True)

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        'credentials/credentials_temp.json',  # Path to your client secrets file
        scopes=['https://www.googleapis.com/auth/drive.file'],  # Set necessary scopes
        redirect_uri='http://localhost:5000/oauth2callback'  # Your redirect URI (update for your domain)
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state  # Store the state in the session to protect against CSRF attacks
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    # Save the credentials for the user (e.g., use user session or database)
    user_id = "user1" # You can generate a user ID based on the session
    save_credentials(credentials, user_id)
    return redirect(url_for('get_creds'))

@app.route('/get_creds')
def get_credential():
    user_id = ''
    credentials = load_credentials("user1")

    if not credentials:
        return redirect(url_for('authorize'))

    # Build Google Drive service
    return build('drive', 'v3', credentials=credentials)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
    