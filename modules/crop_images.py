import os
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np

def convert_pdf_to_image(pdf, output):
    converted_folder = f"{output}/converted"
    if not os.path.exists(converted_folder):
        os.makedirs(converted_folder)

    try:
        images = convert_from_path(pdf, poppler_path=r'poppler-24.08.0/Library/bin')
        images_path = []
        for idx, image in enumerate(images):
            image_path = os.path.join(converted_folder, f"page_{idx+1}.png")
            image.save(image_path, "PNG")
            images_path.append(image_path)
        return images_path
    except Exception as e:
        print(f"Error in converting pdf: {e}")
        return []

def dynamic_crop(image_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Read the image with OpenCV
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to detect the regions
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours of potential text blocks
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cropped_images = []
    for idx, contour in enumerate(contours):
        # Get bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)

        # Apply size filtering to eliminate very small/large contours
        if w > 100 and h > 50:  # Adjust based on your layout
            cropped = image[y-218:y+h, x:x+w]
            cropped_image_path = os.path.join(output_folder, f"{os.path.basename(image_path).split('.')[0]}_slice_{idx}.png")
            cv2.imwrite(cropped_image_path, cropped)
            cropped_images.append(cropped_image_path)

    return cropped_images

def process_image(file, output):
    if not os.path.exists(output):
        os.makedirs(output, exist_ok=True)

    if file.lower().endswith(".pdf"):
        print(f'Detected PDF file: {file}')

        output_images = []
        image_paths = convert_pdf_to_image(file, output)

        # Crop areas dynamically from each image
        for image_path in image_paths:
            crop_output_folder = os.path.join(output, "cropped_dynamic")
            cropped_images = dynamic_crop(image_path, crop_output_folder)
            output_images.extend(cropped_images)
        return output_images
    


