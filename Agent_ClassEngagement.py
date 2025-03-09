import os
import json
import base64
from PIL import Image
import torch
import torch.nn.functional as F
from transformers import AutoProcessor, AutoModelForImageClassification
from openai import OpenAI

# Import predefined functions
from API_ImageAnalysis import (
    call_AOD, 
    emotion_analysis, 
    analyze_body_language, 
    match_face_with_name,
    modified_student_image_profile,
    describe_slide,
    classify_slide
)


class DynamicAgent:
    """
    dynamic classroom analysis agent that selects analyses to perform based on user queries
    """
    
    def __init__(self, openai_api_key):
        """Initialize Agent"""
        self.openai_api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Load emotion analysis model
        try:
            model_name = "motheecreator/vit-Facial-Expression-Recognition"
            self.emotion_processor = AutoProcessor.from_pretrained(model_name)
            self.emotion_model = AutoModelForImageClassification.from_pretrained(model_name)
            print("Emotion analysis model loaded")
        except Exception as e:
            print(f"Failed to load emotion analysis model: {e}")
            self.emotion_processor = None
            self.emotion_model = None
    
    def transform_query(self, query, image_path=None):
        """
        Transform the original query into a form that's suitable for this specific agent
        """
        print(f"🔄 Transforming original query: '{query}'")
        
        system_prompt = """You are a query transformation assistant for a classroom image analysis system.

Your task is to transform general academic performance questions into image-specific queries about classroom engagement and behavior.

For example:
- "How is Lisa doing in maths at school?" → "How is Lisa's engagement in the classroom image?"
- "Is John good at science?" → "Does John appear engaged in this class based on the image?"
- "What's Mary's academic performance like?" → "How does Mary appear to be participating in this class?"

Important rules:
1. Always transform queries to focus on what can be observed in a classroom image
2. Focus on engagement, behavior, body language, and attention
3. Preserve student names mentioned in the original query
4. Make it clear the analysis is based only on the current image
5. Do not refer to academic records, test scores, or historical performance
6. Keep the transformed query concise and clear

Return only the transformed query without any explanation or additional text."""

        user_prompt = f"""Original query: {query}   

Transform this query to focus specifically on what can be observed about student engagement in a classroom image."""   # NEED TO BE MODIFIED TO MERGE WITH THE MAIN FLOWCHART

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            transformed_query = completion.choices[0].message.content.strip()
            return transformed_query
        except Exception as e:
            print(f"Error transforming query: {e}")
            # Return original query if transformation fails
            return query
    
    def design_analysis_plan(self, query, image_path, slide_image_path = None):
        """Design analysis plan based on query"""
        system_prompt = """You are a classroom analysis assistant that helps teachers analyze student behavior.
You can use the following functions:

1. "detect_students": Detect students in the image and return bounding boxes
2. "crop_student_images": Crop student face images
3. "analyze_emotion": Analyze student emotional state
4. "analyze_body_language": Analyze student body language
5. "identify_student": Identify student
6. "describe_slide": Describe the content of the slide
7. "classify_slide": Classify the slide into a subject

Please return an execution plan in JSON format:
{
  "plan": [
    {"function": "function_name", "description": "purpose of this step"},
    {"function": "another_function", "description": "purpose of this step"}
  ],
  "explanation": "explanation of the execution plan"
}

Note:
- Functions have dependencies: always detect students first, then crop images, then perform analysis
- Do not include any parameter information in the plan, the system will handle parameter passing automatically
- Only select necessary functions required to complete the task"""

        user_prompt = f"Query: {query}\nImage path: {image_path}\nSlide image path: {slide_image_path}\n Please design an analysis plan."

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            plan = json.loads(completion.choices[0].message.content)
            print(f"📝 Analysis plan: {json.dumps(plan, indent=2, ensure_ascii=False)}")
            return plan
        except Exception as e:
            print(f"❌ Error designing analysis plan: {e}")
            return {"plan": [], "explanation": f"Error designing analysis plan: {e}"}
    
    def execute_plan(self, plan, image_path, students_folder="students", slide_image_path = None):
        """Execute analysis plan"""
        print(f"📋 Executing analysis plan...")
        print(f"📝 Plan explanation: {plan.get('explanation', 'No explanation')}")
        
        # Dictionary to store intermediate results
        data = {
            "image_path": image_path,
            "slide_image_path": slide_image_path,
            "students_folder": students_folder
        }
        
        # Track completed steps
        for step_idx, step in enumerate(plan.get("plan", [])):
            function_name = step.get("function")
            description = step.get("description", "No description")
            
            print(f"\n🔄 Step {step_idx+1}/{len(plan.get('plan', []))}: {function_name}")
            print(f"📌 {description}")
            
            try:
                # Detect students
                if function_name == "detect_students":
                    print("🔍 Detecting students in image...")
                    response = call_AOD(image_path)
                    if response.status_code == 200:
                        detection_json = response.json()
                        formatted_data = []
                        
                        if "data" in detection_json and len(detection_json["data"]) > 0:
                            detections = detection_json["data"][0]
                            if isinstance(detections, list):
                                formatted_data = detections
                                print(f"✅ Found {len(formatted_data)} students")
                        
                        data["detection_data"] = formatted_data
                
                # Crop student images
                elif function_name == "crop_student_images":
                    print("✂️ Cropping student images...")
                    if "detection_data" not in data or not data["detection_data"]:
                        print("⚠️ No detection data, skipping cropping")
                        continue
                    
                    cropped_paths = modified_student_image_profile(
                        data["detection_data"], 
                        image_path
                    )
                    data["cropped_images"] = cropped_paths
                    
                    # Use first student image as current student by default
                    if cropped_paths:
                        data["current_student_image"] = cropped_paths[0]
                
                # Analyze emotion
                elif function_name == "analyze_emotion":
                    print("😊 Analyzing student emotion...")
                    if "current_student_image" not in data:
                        print("⚠️ No student image, skipping emotion analysis")
                        continue
                    
                    results = emotion_analysis(
                        data["current_student_image"], 
                        self.emotion_processor, 
                        self.emotion_model
                    )
                    data["emotion_data"] = results
                
                # Analyze body language
                elif function_name == "analyze_body_language":
                    print("🧍 Analyzing body language...")
                    if "current_student_image" not in data:
                        print("⚠️ No student image, skipping body language analysis")
                        continue
                    
                    result = analyze_body_language(
                        self.openai_api_key, 
                        data["current_student_image"]
                    )
                    data["body_language"] = result
                
                # Identify student
                elif function_name == "identify_student":
                    print("👤 Identifying student...")
                    if "current_student_image" not in data:
                        print("⚠️ No student image, skipping identification")
                        continue
                    
                    identity = match_face_with_name(
                        self.openai_api_key,
                        data["current_student_image"],
                        data["students_folder"]
                    )
                    data["identity"] = identity
                
                elif function_name == "classify_slide":
                    print("📚 Classifying slide...")
                    subject = classify_slide(slide_image_path)
                    data["slide_subject"] = subject
                
                elif function_name == "describe_slide":
                    print("📝 Describing slide content...")
                    subject_classification = classify_slide(slide_image_path)
                    description = describe_slide(self.openai_api_key, slide_image_path, subject_classification)
                    data["slide_description"] = description
                
                else:
                    print(f"⚠️ Unknown function: {function_name}")
            
            except Exception as e:
                print(f"❌ Error executing {function_name}: {e}")
                data[f"{function_name}_error"] = str(e)
        
        return data
    
    def generate_response(self, query, results, original_query=None):
        """Generate analysis response"""
        print("✍️ Generating analysis response...")
        
        system_prompt = """You are a professional education analyst who answers user queries based on the provided analysis data.
The data may include:
- detection_data: Detected student data
- cropped_student_images: Paths to cropped student images
- slide_images: Paths to images corresponding to lesson slides
- emotion_data: Emotion analysis results
- body_language: Body language analysis
- identity: Student identity

Important instructions:
1. Even if the data is incomplete, provide valuable analysis when possible
2. If data is missing, acknowledge this honestly and provide improvement suggestions
3. Be clear that your analysis is based ONLY on the current classroom image
4. If the original query was about long-term academic performance, explain that you can only analyze what's visible in the current image
5. Do not make claims about academic performance unless directly observable in the image data
6. Stay focused on engagement, behavior, and what can be observed in a single moment
"""

        # Include both original and transformed queries if available
        query_info = f"Original query: {original_query}\nTransformed query: {query}" if original_query else f"Query: {query}"
        
        user_prompt = f"""{query_info}

Analysis results:
{json.dumps(results, ensure_ascii=False, indent=2)}

Please answer the query based on these results."""

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return f"Error generating response: {e}"
    
    def process_query(self, query, image_path, slide_image_path = None, students_folder="students"):
        """Main function to process user query"""
        print(f"\n🔍 Processing query: '{query}'")
        print(f"📸 Image path: {image_path}")
        
        if not os.path.exists(image_path):
            return f"Error: Image file does not exist: {image_path}"
        
        try:
            # Store original query
            original_query = query
            
            # 1. Transform the query
            transformed_query = self.transform_query(query, image_path, slide_image_path)
            
            # 2. Design analysis plan based on transformed query
            plan = self.design_analysis_plan(transformed_query, image_path)
            
            # 3. Execute plan
            results = self.execute_plan(plan, image_path, students_folder)
            
            # 4. Generate response (passing both original and transformed queries)
            response = self.generate_response(transformed_query, results, original_query)
            
            return response
        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            print(f"\n❌ {error_message}")
            import traceback
            traceback.print_exc()
            return error_message


openai_api_key = "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"
image_path = "/Users/wangyinghao/Desktop/AI_Agent/test_images/webcam_demo.PNG"
slide_image_path = r"ppts_and_images/image.png"

if __name__ == "__main__":
    # Initialize Agent
    agent = DynamicAgent(openai_api_key)
    
    # Get user query
    query = input("\nEnter your query: ")
    
    # Get image path
    image_path = image_path
    slide_image_path = slide_image_path
    
    print("\n" + "="*50)
    print("Starting analysis...")
    print("="*50 + "\n")
    
    # Process query
    response = agent.process_query(query, image_path, slide_image_path)
    
    print("\n" + "="*50)
    print("Analysis results:")
    print("="*50 + "\n")
    print(response)