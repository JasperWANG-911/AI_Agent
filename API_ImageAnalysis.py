import ast
import time
import json
import torch
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import cv2
from segment_anything import sam_model_registry, SamPredictor
import warnings
import requests
import time
import torch
import matplotlib.pyplot as plt
import os
from PIL import Image
import torch
import torch.nn.functional as F
import base64
import openai
import os
import glob
from PIL import Image
import torch
import torch.nn.functional as F
from transformers import AutoProcessor, AutoModelForImageClassification
from openai import OpenAI
import joblib
from ppt_to_text_and_image import extract_text_from_image, extract_text_from_image_easy

def call_AOD(image_path):
    """
    Use the Agentic Object Detection API to detect objects(students) in an image, and return bbox
    """
    
    # 正确的 API 端点，注意 'va.' 部分
    AOD_url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"
    headers = {"Authorization": "Basic ejRkbG43a2RsaGxndnF5ZWdpbGp1Om55S1ZoWVMydlJ6QkJxSGp5Z2plQ3ZkeG42a1RmNVhi"}
    
    with open(image_path, "rb") as image_file:
        files = {"image": image_file}
        data = {"prompts": "people", "model": "agentic"}
        response = requests.post(AOD_url, files=files, data=data, headers=headers)
    
    return response

def individual_student_image_profile(json_data, input_image_path, output_folder="individual_student_profile"):
    """
    crop student faces from the input image based on the json data
    """

    # convert json_data into str
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    # get the first element of the data
    detections = data[0]

    # load the image
    image = Image.open(input_image_path)

    # create output folder if not exist
    os.makedirs(output_folder, exist_ok=True)

    # crop the student faces
    for idx, item in enumerate(detections):
        bbox = item["bounding_box"]  # 格式为 [x1, y1, x2, y2]
        cropped_image = image.crop((bbox[0], bbox[1], bbox[2], bbox[3]))

        if cropped_image.mode != "RGB":
            cropped_image = cropped_image.convert("RGB")

        output_path = os.path.join(output_folder, f"profile_{idx}.jpg")
        cropped_image.save(output_path)
        print(f"Saved cropped image: {output_path}")

def emotion_analysis(image_path, processor, model):
    """
    Use the emotion analysis model to predict the emotion of a person in an image
    N.B. The model is a pretrained model from Hugging Face: https://huggingface.co/motheecreator/vit-Facial-Expression-Recognition
    """
    # Pre-load the image
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=[image], return_tensors="pt")
    
    # Applying the model
    outputs = model(**inputs)
    logits = outputs.logits
    probs = F.softmax(logits, dim=-1)
    labels = model.config.id2label
    
    results = {labels[idx]: prob.item() for idx, prob in enumerate(probs[0])}
    return results

def analyze_body_language(api_key: str, image_path: str, question: str = "Analyze the body language of the student in the image and generate a caption describing their posture, gestures, and engagement.") -> str:
    """
    Call GPT4o API to analyze the body language of the student(Cannot load large HF models for pose analysis and prediction, so use GPT4o instead)
    """

    # initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # convert image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # send API request to GPT-4o
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an expert in behavioral analysis, specializing in interpreting human body language from images. 
Your task is to carefully examine the person in the image and provide a clear, concise caption describing their body language. 

Focus on the subject's posture, head orientation, gaze direction, hand gestures, and overall engagement in the scene. 
If the subject is interacting with an object (e.g., a book, a computer) or with other people, mention that briefly.

Be objective and factual in your description, avoiding speculative interpretations about emotions unless they are clearly inferred from body language. 
Your output should be a single sentence caption that concisely summarizes the subject's body language."""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},  # input question
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    )

    # return the response from GPT-4o
    return completion.choices[0].message.content

def match_face_with_name(api_key: str, image_path: str, students_folder: str = "students", question: str = "Please identify the face in the input image, and return his/her name.") -> str:
    """
    match face with name
    (need to define the folder called students, with files named after the respective student's name)
    """
    
    # set the API key
    openai.api_key = api_key

    # load the reference images
    reference_content = []
    try:
        for filename in os.listdir(students_folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(students_folder, filename)
                with open(filepath, "rb") as f:
                    img_bytes = f.read()
                b64_str = base64.b64encode(img_bytes).decode("utf-8")
                student_name = os.path.splitext(filename)[0]
                reference_content.append({"type": "text", "text": f"Student: {student_name}"})
                reference_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}})
    except Exception as e:
        return f"Error loading reference images: {e}"

    # load the input image
    try:
        with open(image_path, "rb") as f:
            input_img_bytes = f.read()
        input_b64_str = base64.b64encode(input_img_bytes).decode("utf-8")
    except Exception as e:
        return f"Error reading input image: {e}"

    system_prompt = (
        "You are a face recognition assistant. You are provided with reference images of students (with each image preceded by a text label indicating the student's name) "
        "and an input image containing one or more faces. Your task is to detect the faces in the input image, compare them with the provided reference images, "
        "and return the name of each recognized student. If a face does not match any reference image, indicate that the person is unknown."
    )

    # API call messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": reference_content},
        {"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{input_b64_str}"}}
        ]}
    ]

    # API call
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        response = completion.choices[0].message.content
    except Exception as e:
        response = f"API call failed: {e}"

    return response

def describe_slide(api_key: str, image_path: str, predicted_subject: str = "Chemistry") -> str:
    """Classifies a slide (image) into a subject, and uses this to aid a description."""
    
    try:
        with open(image_path, "rb") as f:
            input_img_bytes = f.read()
        input_b64_str = base64.b64encode(input_img_bytes).decode("utf-8")
    except Exception as e:
        return f"Error reading input image: {e}"

    openai.api_key = api_key
    client = OpenAI(api_key="sk-xxxxx")
    system_prompt = (
        f"You are a teaching assistant asked with describing the content of a slide. You should "
        f"describe the main subject which should be {predicted_subject}, concepts and topics covered in the slide, without directly "
        f"reading the text on the slide. Focus on the key points and provide a clear and concise "
        f"description of the slide's content."
    )

    # API call messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{input_b64_str}"}},
        ]}
    ]

    # API call
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        response = completion.choices[0].message.content
    except Exception as e:
        response = f"API call failed: {e}"

    return response

def classify_slide(image_path: str, model_name: str ="subject_classifier.pkl") -> str:
    """Classifies a slide (image) into a subject."""
    # Load trained model
    model = joblib.load(model_name)
    extracted_text = None
    # Extract text from slide
    if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        extracted_text = extract_text_from_image(image_path)
    else:
        extracted_text = extract_text_from_image_easy(image_path)
    # Predict subject
    predicted_subject = model.predict([extracted_text])[0]
    return f"Predicted Subject: {predicted_subject}"