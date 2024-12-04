# Use an official Python base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y poppler-utils tesseract-ocr libtesseract-dev && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app port (default is 5000)
EXPOSE 5000

# Command to start the Flask app
CMD ["python", "app.py"]
