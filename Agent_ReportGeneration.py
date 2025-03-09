import os
import json
from openai import OpenAI
import logging

# Import the two existing agents
from Agent_ClassEngagement import DynamicAgent
from Agent_SchoolRecords import DynamicSchoolAgent

class StudentFeedbackIntegrationAgent:
    """
    Integration agent that combines class engagement and school records analysis
    to generate comprehensive student feedback
    """
    
    def __init__(self, openai_api_key=None):
        """
        Initialize the integration agent with OpenAI API key
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it via the openai_api_key parameter or OPENAI_API_KEY environment variable.")
        
        # Initialize the two agents
        self.class_engagement_agent = DynamicAgent(self.openai_api_key)
        self.school_records_agent = DynamicSchoolAgent(self.openai_api_key)
        
        # Initialize OpenAI client for final feedback generation
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def generate_integrated_feedback(self, 
                                     query: str, 
                                     image_path: str, 
                                     slide_image_path: str, 
                                     records_directory: str = "School_records") -> str:
        """
        Generate integrated student feedback by combining class engagement and school records analysis
        
        :param query: User's original query about student performance
        :param image_path: Path to the classroom image
        :param slide_image_path: Path to the slide image
        :param records_directory: Directory containing school records
        :return: Comprehensive student feedback
        """
        print("\n" + "="*50)
        print(f"🔍 Generating Integrated Feedback")
        print("="*50 + "\n")
        
        # Step 1: Class Engagement Analysis
        print("📸 Running Class Engagement Analysis...")
        class_engagement_response = self.class_engagement_agent.process_query(
            query, 
            image_path, 
            slide_image_path
        )
        print("\nClass Engagement Analysis:")
        print(class_engagement_response)
        
        # Step 2: School Records Analysis
        print("\n📊 Running School Records Analysis...")
        school_records_response = self.school_records_agent.process_query(
            query, 
            records_directory
        )
        print("\nSchool Records Analysis:")
        print(school_records_response)
        
        # Step 3: Integrate Feedback
        system_prompt = """You are an expert educational analyst tasked with creating a comprehensive student feedback report.

Your goal is to synthesize information from two sources:
1. A real-time classroom engagement analysis
2. A detailed school records performance analysis

Key requirements for the feedback:
- Be constructive and supportive
- Provide specific, actionable insights
- Balance both classroom behavior and academic performance
- Highlight strengths and areas for improvement
- Use a tone appropriate for parents and educators
- Maintain student privacy and use a sensitive approach
- Avoid overly technical language
- Suggest personalized strategies for student development

The feedback should be structured to help the student, parents, and teachers understand:
- Current academic performance
- Classroom engagement and behavior
- Potential learning strategies
- Areas of strength
- Areas needing improvement"""

        user_prompt = f"""Original Query: {query}

Classroom Engagement Analysis:
{class_engagement_response}

School Records Analysis:
{school_records_response}

Please generate a comprehensive, integrated feedback report that combines insights from both analyses."""

        try:
            # Generate integrated feedback using GPT-4
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            integrated_feedback = completion.choices[0].message.content
            
            print("\n" + "="*50)
            print("🎯 Integrated Feedback Generated")
            print("="*50 + "\n")
            
            return integrated_feedback
        
        except Exception as e:
            error_message = f"Error generating integrated feedback: {str(e)}"
            self.logger.error(f"❌ {error_message}")
            import traceback
            traceback.print_exc()
            return error_message

# Example usage
if __name__ == "__main__":
    # Set predefined query
    query = "How's Jasper's recent performance at school recently?"
    
    # Set paths
    image_path = "/Users/wangyinghao/Desktop/AI_Agent/test_images/webcam_demo.PNG"
    slide_image_path = "ppts_and_images/image.png"
    records_directory = "School_records"
    
    # Initialize Integration Agent
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    integration_agent = StudentFeedbackIntegrationAgent(openai_api_key)
    
    print("\n" + "="*50)
    print("Starting Integrated Feedback Generation...")
    print("="*50 + "\n")
    
    # Generate integrated feedback
    integrated_feedback = integration_agent.generate_integrated_feedback(
        query, 
        image_path, 
        slide_image_path, 
        records_directory
    )
    
    print("\n" + "="*50)
    print("Integrated Feedback:")
    print("="*50 + "\n")
    print(integrated_feedback)

