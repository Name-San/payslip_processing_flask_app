import pytesseract
from PIL import Image
import os


pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Admin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def extract_text(image_path):
    """
    Extract text from an image using Tesseract-OCR.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        str: Extracted text.
    """
    try:
        # Open the image file
        img = Image.open(image_path)
        # Extract text from the image
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

def search_for_string(text, search_term):
    """
    Search for specified strings in the extracted text.
    
    Args:
        text (str): Extracted text from the image.
        search_term (list): List of strings to search for.
    
    Returns:
        dict: Search results indicating the presence of each term.
    """

    try:
        src_results = {term: '' for term in search_term}
        # Split text into lines and search for terms
        for line in text.splitlines():
            for term in search_term:
                if term in line:  # Check if the term is in the line
                    src_results[term] = line.strip()
        
        
        for term in search_term: 
            filter_values = []
            for char in range(len(term)+2, len(src_results[term]), 1):
                filter_values.append(src_results[term][char])
            src_results[term] = ''.join(filter_values).strip()
        
        return src_results
    
    except Exception as e:
        return f"Error encoutered in searching: {e}"
         
def ocr(images, search_terms):
    items = []
    for image_path in images:
        extracted_text = extract_text(image_path)
        results = search_for_string(extracted_text, search_terms)
        if results["NAME"]:
            filename = results["NAME"]
            filedate = results["PERIOD COVERED"]
            path_fn = os.path.join(f"{os.path.dirname(image_path)}\\", f"{filename}_{filedate}.png")
            os.replace(image_path, path_fn)

            match = False
            for item in items:
                if filename == item["folder"]:
                    match = True
                    item["path"].append(path_fn)
        
            if not match:
                items.append({"folder": filename, "path": [path_fn]})
    return items


                
 

    