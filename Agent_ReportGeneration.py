import os
import json
from openai import OpenAI
import logging
from typing import List, Dict, Any

# Import the existing agents
from Agent_ClassEngagement import DynamicAgent
from Agent_SchoolRecords import DynamicSchoolAgent

class StudentFeedbackIntegrationAgent:
    """
    Comprehensive integration agent that combines multi-image classroom engagement 
    and school records analysis to generate detailed student feedback
    """
    
    def __init__(self, openai_api_key=None):
        """
        Initialize the integration agent with OpenAI API key
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required.")
        
        # Initialize the agents
        self.class_engagement_agent = DynamicAgent(self.openai_api_key)
        self.school_records_agent = DynamicSchoolAgent(self.openai_api_key)
        
        # Initialize OpenAI client for final feedback generation
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def analyze_multiple_classroom_images(self, 
                                          query: str, 
                                          image_paths: List[str], 
                                          slide_image_path: str) -> str:
        """
        Analyze multiple classroom images and generate a comprehensive engagement report
        
        :param query: Original user query
        :param image_paths: List of paths to classroom images
        :param slide_image_path: Path to the slide image
        :return: Comprehensive multi-image engagement analysis
        """
        # Validate inputs
        if not image_paths:
            raise ValueError("At least one image path must be provided")
        
        # Store individual image analysis results
        image_analyses = []
        
        # Analyze each image
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n📸 Analyzing Image {i}/{len(image_paths)}")
            try:
                # Process each image with the engagement agent
                single_image_analysis = self.class_engagement_agent.process_query(
                    query, 
                    image_path, 
                    slide_image_path
                )
                image_analyses.append({
                    "image_path": image_path,
                    "analysis": single_image_analysis
                })
            except Exception as e:
                self.logger.error(f"Error analyzing image {i}: {e}")
        
        # Generate comprehensive analysis
        return self._generate_comprehensive_engagement_analysis(query, image_analyses)
    
    def _generate_comprehensive_engagement_analysis(self, 
                                                    query: str, 
                                                    image_analyses: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive analysis from multiple image analyses
        
        :param query: Original user query
        :param image_analyses: List of individual image analysis results
        :return: Synthesized comprehensive engagement report
        """
        system_prompt = """You are an expert educational analyst tasked with creating a comprehensive, 
unbiased student engagement report from multiple classroom image analyses.

Your goals:
1. Synthesize insights from multiple classroom observations
2. Identify consistent patterns and potential anomalies
3. Provide a balanced, objective assessment of student engagement
4. Focus on overall trends rather than isolated moments
5. Use a constructive, supportive tone
6. Avoid over-interpreting limited data points

Key considerations:
- Look for recurring themes across different observations
- Note any significant variations in engagement
- Consider potential context or environmental factors
- Provide nuanced, multi-dimensional insights
- Recommend strategies based on observed patterns"""

        # Prepare analysis data for GPT
        analysis_summary = "\n\n".join([
            f"Image {i+1} Analysis:\n{analysis['analysis']}"
            for i, analysis in enumerate(image_analyses)
        ])

        user_prompt = f"""Original Query: {query}

Comprehensive Image Analyses:
{analysis_summary}

Please generate a synthesized, comprehensive engagement report that:
- Integrates insights from multiple classroom observations
- Identifies consistent patterns and potential variations
- Provides an objective, balanced assessment of student engagement
- Offers constructive recommendations"""

        try:
            # Generate comprehensive analysis using GPT-4
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            comprehensive_analysis = completion.choices[0].message.content
            
            print("\n" + "="*50)
            print("🎯 Comprehensive Engagement Analysis Generated")
            print("="*50 + "\n")
            
            return comprehensive_analysis
        
        except Exception as e:
            error_message = f"Error generating comprehensive analysis: {str(e)}"
            self.logger.error(f"❌ {error_message}")
            import traceback
            traceback.print_exc()
            return error_message
    
    def generate_integrated_feedback(self, 
                                     query: str, 
                                     image_paths: List[str], 
                                     slide_image_path: str, 
                                     records_directory: str = "School_records") -> str:
        """
        Generate comprehensive student feedback by combining multi-image classroom engagement 
        and school records analysis
        
        :param query: User's original query about student performance
        :param image_paths: List of paths to classroom images
        :param slide_image_path: Path to the slide image
        :param records_directory: Directory containing school records
        :return: Comprehensive student feedback
        """
        print("\n" + "="*50)
        print(f"🔍 Generating Integrated Feedback")
        print("="*50 + "\n")
        
        # Step 1: Multi-Image Classroom Engagement Analysis
        print("📸 Running Multi-Image Classroom Engagement Analysis...")
        comprehensive_engagement_analysis = self.analyze_multiple_classroom_images(
            query, 
            image_paths, 
            slide_image_path
        )
        print("\nComprehensive Engagement Analysis:")
        print(comprehensive_engagement_analysis)
        
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
1. A multi-image classroom engagement analysis
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

Comprehensive Classroom Engagement Analysis:
{comprehensive_engagement_analysis}

School Records Analysis:
{school_records_response}

Please generate a comprehensive, integrated feedback report that:
- Combines insights from multiple classroom observations
- Incorporates academic performance data
- Provides a holistic view of the student's educational experience
- Offers targeted, constructive recommendations"""

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
    query = "How's Sritej's performance at school recently?"
    
    # Set multiple image paths
    image_paths = [
        "/Users/wangyinghao/Desktop/AI_Agent/test_images/webcam_demo.PNG",
        "/Users/wangyinghao/Desktop/AI_Agent/test_images/2.PNG"
    ]
    
    # Single slide image path
    slide_image_path = "ppts_and_images/image.png"
    
    # Set records directory
    records_directory = "/Users/wangyinghao/Desktop/AI_Agent/School_Records"
    
    # Initialize Integration Agent
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    integration_agent = StudentFeedbackIntegrationAgent(openai_api_key)
    
    print("\n" + "="*50)
    print("Starting Integrated Feedback Generation...")
    print("="*50 + "\n")
    
    # Generate integrated feedback
    integrated_feedback = integration_agent.generate_integrated_feedback(
        query, 
        image_paths, 
        slide_image_path,
        records_directory
    )
    
    print("\n" + "="*50)
    print("Integrated Feedback:")
    print("="*50 + "\n")
    print(integrated_feedback)