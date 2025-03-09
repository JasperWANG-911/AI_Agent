import cv2
import pytesseract
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib  # For saving/loading models
import easyocr  # For extracting text from images
import os

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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


def classify_slide(image_path_folder, model_name ="subject_classifier.pkl") -> str:
    """Classifies a folder of slides (images) into a subject."""
    # Load trained model
    model = joblib.load(model_name)
    extracted_text = None
    all_extracted_text = ""
    # Extract text from slide
    if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        extracted_text_function = extract_text_from_image
    else:
        extracted_text_function = extract_text_from_image_easy
    for image_path_rel in os.listdir(image_path_folder):
        image_path = os.path.join(image_path_folder, image_path_rel)
        extracted_text = extracted_text_function(image_path)
        all_extracted_text += " " + extracted_text
    # Predict subject
    if not all_extracted_text:
        print("No text was extracted from the images. This either means that there are no images in the folder or none of the images had any text.")
        return "No text could be extracted from the slides."
    predicted_subject = model.predict([all_extracted_text])[0]
    return predicted_subject


# Example Usage
# slide_path_folder = "ppts_and_images/slide_images"  # Update with the actual slide image path
# print(classify_slide(slide_path_folder))
