import cv2
import pytesseract
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib  # For saving/loading models
import easyocr  # For extracting text from images

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# then import Easyocr library
import easyocr

# Ensure Tesseract is installed and set its path (Update this path if needed)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Training data (Example slides mapped to subjects)



def extract_text_from_image_easy(image_path):
    """
    Extracts text from an image using EasyOCR.
    
    :param image_path: Path to the image file
    :return: Extracted text as a string
    """
    reader = easyocr.Reader(['en'])  # Supports English ('en')
    results = reader.readtext(image_path, detail=0)  # Extract text without extra details
    return " ".join(results)

# Example Usage



def extract_text_from_image(image_path):
    """Extracts text from an image using OCR (Tesseract)."""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    text = pytesseract.image_to_string(gray)  # Extract text
    return text.strip()


def classify_slide(image_path, model_name="subject_classifier.pkl"):
    """Classifies a slide (image) into a subject."""
    # Load trained model
    model = joblib.load(model_name)

    # Extract text from slide
    extracted_text = extract_text_from_image_easy(image_path)
    
    if not extracted_text:
        return "Could not extract text. Try a clearer image."

    # Predict subject
    predicted_subject = model.predict([extracted_text])[0]
    return f"Predicted Subject: {predicted_subject}"


# Example Usage
#slide_path = "ppts_and_images/image.png"  # Update with the actual slide image path
#print(classify_slide(slide_path))
