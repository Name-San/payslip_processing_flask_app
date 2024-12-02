import os
import base64
from dotenv import load_dotenv

# Load the environment variables from .env
load_dotenv()


try:
    credentials_base64 = os.getenv("TESSERACT_PATH")
    if credentials_base64:
        print(os.path.normpath(credentials_base64))

    else:
        print("Empty variable")

except Exception as e:
    print(f"Error: {e}")