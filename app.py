from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import shutil
from modules.image_ocr import ocr
from modules.image_editor import edit_image
from modules.connect_gdrive import access_drive
import json
import csv


app = Flask(__name__)

# Temporary folder for uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure necessary directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load config for default settings
def load_config(config_path="configs/config.json"):
    with open(config_path, "r") as file:
        return json.load(file)

# Generate CSV report
def generate_csv(data):
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    heading = [v for k, v in enumerate(data[0])]
    with open('outputs/report.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=heading)
        writer.writeheader()
        writer.writerows(data)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Upload route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 200
    return jsonify({'message': 'No file uploaded'}), 400

# Process route to handle image processing and OCR
@app.route('/process', methods=['POST'])
def process_file():
    data = load_config()
    
    # Get the uploaded file path
    file_path = request.json['file_path']
    slices_count = data["slice_count_default"]
    
    # Process image
    sliced_images = edit_image(file_path, data["output_folder"], slices_count)
    
    # OCR processing
    items = ocr(sliced_images, data["search_terms"])
    
    # Google Drive access and upload
    reports = access_drive("user1", items)
    
    # Generate CSV report
    generate_csv(reports)

    return jsonify({
        'message': 'Processing complete',
        'sliced_images': sliced_images,
        'csv_report': 'outputs/report.csv',
        'drive_links': reports
    })

# Download route to get the generated files
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('outputs', filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)