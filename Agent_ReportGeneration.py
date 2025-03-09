import os
import json
import time
from openai import OpenAI

# Import the two dynamic agents
from Agent_ClassEngagement import DynamicClassEngagementAgent  # Image analysis agent
from Agent_SchoolRecords import DynamicSchoolRecordsAgent  # School records agent

class ComprehensiveAnalysisAgent:
    """
    A comprehensive analysis agent that coordinates between the classroom engagement
    analysis agent and the school records analysis agent to generate a comprehensive report.
    """
    
    def __init__(self, openai_api_key):
        """Initialize the agent with necessary API keys and component agents"""
        self.openai_api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize component agents
        self.image_agent = DynamicClassEngagementAgent(openai_api_key)
        self.records_agent = DynamicSchoolRecordsAgent(openai_api_key)
        
        print("Comprehensive Analysis Agent initialized successfully")
    
    def analyze_query_type(self, query):
        """
        Analyze the query to determine what types of analysis are needed
        
        Args:
            query (str): User query
            
        Returns:
            dict: Analysis plan with needed agent types
        """
        print(f"Analyzing query: '{query}'")
        
        system_prompt = """You are a query analysis assistant for an educational system that can analyze both:
1. Classroom engagement (from images of students in class)
2. School records (from academic data like grades, attendance, etc.)

Given a query about a student's performance or behavior, determine which type(s) of analysis are needed.

Return a JSON object with the following structure:
{
  "needs_image_analysis": boolean,  // True if classroom engagement analysis is needed
  "needs_records_analysis": boolean,  // True if school records analysis is needed
  "student_name": string,  // Name of the student mentioned in the query (or null if none)
  "subject": string,  // Academic subject mentioned (or null if none)
  "explanation": string  // Brief explanation of your decision
}

Examples:
- "How is Emma performing in math class?" - Needs both image and records analysis
- "Is John paying attention in today's class?" - Needs only image analysis
- "What are Lisa's grades in science?" - Needs only records analysis
- "Compare Alex's classroom engagement with his academic performance" - Needs both"""

        user_prompt = f"""Query: {query}

Please determine what type of analysis is needed for this query."""

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            analysis = json.loads(completion.choices[0].message.content)
            print(f"Query analysis complete:")
            print(f"  Needs image analysis: {analysis.get('needs_image_analysis', False)}")
            print(f"  Needs records analysis: {analysis.get('needs_records_analysis', False)}")
            print(f"  Student: {analysis.get('student_name', 'None mentioned')}")
            print(f"  Subject: {analysis.get('subject', 'None mentioned')}")
            return analysis
        except Exception as e:
            print(f"Error analyzing query: {e}")
            # Default to requiring both types of analysis if there's an error
            return {
                "needs_image_analysis": True,
                "needs_records_analysis": True,
                "student_name": None,
                "subject": None,
                "explanation": "Error during analysis, defaulting to comprehensive approach."
            }
    
    def execute_analysis(self, query, analysis_plan, image_path=None, records_directory=None):
        """
        Execute the necessary analyses based on the analysis plan
        
        Args:
            query (str): User query
            analysis_plan (dict): Analysis plan from analyze_query_type
            image_path (str): Path to classroom image
            records_directory (str): Path to directory with school records
            
        Returns:
            dict: Results from all executed analyses
        """
        print("\nExecuting comprehensive analysis...")
        
        results = {
            "query": query,
            "student_name": analysis_plan.get("student_name"),
            "subject": analysis_plan.get("subject"),
            "image_analysis": None,
            "records_analysis": None,
            "error": None
        }
        
        # Execute image analysis if needed
        if analysis_plan.get("needs_image_analysis", False):
            if image_path and os.path.exists(image_path):
                print("\nPerforming classroom engagement analysis...")
                try:
                    image_results = self.image_agent.process_query(query, image_path)
                    results["image_analysis"] = image_results
                    print("✓ Classroom engagement analysis complete")
                except Exception as e:
                    error_msg = f"Error during image analysis: {str(e)}"
                    print(f"✗ {error_msg}")
                    results["image_analysis_error"] = error_msg
            else:
                error_msg = "Image analysis requested but no valid image path provided"
                print(f"✗ {error_msg}")
                results["image_analysis_error"] = error_msg
        
        # Execute records analysis if needed
        if analysis_plan.get("needs_records_analysis", False):
            if records_directory and os.path.exists(records_directory):
                print("\nPerforming school records analysis...")
                try:
                    records_results = self.records_agent.process_query(query, records_directory)
                    results["records_analysis"] = records_results
                    print("✓ School records analysis complete")
                except Exception as e:
                    error_msg = f"Error during records analysis: {str(e)}"
                    print(f"✗ {error_msg}")
                    results["records_analysis_error"] = error_msg
            else:
                error_msg = "Records analysis requested but no valid records directory provided"
                print(f"✗ {error_msg}")
                results["records_analysis_error"] = error_msg
        
        return results
    
    def generate_comprehensive_report(self, query, analysis_results):
        """
        Generate a comprehensive report based on the combined analysis results
        
        Args:
            query (str): Original user query
            analysis_results (dict): Results from execute_analysis
            
        Returns:
            str: Comprehensive report
        """
        print("\nGenerating comprehensive report...")
        
        system_prompt = """You are an expert educational analyst who can synthesize multiple sources of information about student performance.

Your task is to create a comprehensive, well-structured report based on analyses of:
1. Classroom engagement (based on image analysis of the student in class)
2. Academic records (based on grades, attendance, and other school data)

Combine these sources of information to provide a holistic view of the student's academic situation.

Your report should:
1. Directly address the original query
2. Find connections between classroom behavior and academic performance
3. Highlight patterns or discrepancies between observed behavior and recorded performance
4. Provide evidence-based insights and specific examples
5. Include concrete, actionable recommendations for teachers and/or parents
6. Be well-organized with clear sections, headings, and a professional tone

If one type of analysis is missing, acknowledge this limitation but still provide the best possible insights from the available data."""

        user_prompt = f"""Original Query: {query}

Analysis Results:
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

Please generate a comprehensive report that synthesizes all available information and directly addresses the query."""

        try:
            print("Calling GPT-4o for report generation...")
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error generating report: {e}")
            return f"Error generating comprehensive report: {str(e)}"
    
    def process_query(self, query, image_path=None, records_directory=None):
        """
        Process a user query by coordinating between component agents
        
        Args:
            query (str): User query
            image_path (str): Path to classroom image
            records_directory (str): Path to directory with school records
            
        Returns:
            str: Comprehensive analysis report
        """
        print(f"\n==== Starting Comprehensive Analysis ====")
        print(f"Query: '{query}'")
        start_time = time.time()
        
        try:
            # 1. Analyze query to determine needed analysis types
            analysis_plan = self.analyze_query_type(query)
            
            # 2. Execute the necessary analyses
            analysis_results = self.execute_analysis(
                query, 
                analysis_plan, 
                image_path, 
                records_directory
            )
            
            # 3. Generate comprehensive report
            report = self.generate_comprehensive_report(query, analysis_results)
            
            elapsed_time = time.time() - start_time
            print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
            return report
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_message = f"Error during comprehensive analysis: {str(e)}"
            print(f"\n✗ {error_message}")
            print(f"Analysis failed after {elapsed_time:.2f} seconds")
            import traceback
            traceback.print_exc()
            return error_message


# Example usage
if __name__ == "__main__":
    # Set API key directly
    openai_api_key = "your_openai_api_key_here"
    
    # Initialize agent
    agent = ComprehensiveAnalysisAgent(openai_api_key)
    
    # Set paths
    classroom_image_path = "path/to/classroom_image.jpg"
    school_records_directory = "path/to/school_records"
    
    # Get user query
    query = input("\nEnter your query about student performance: ")
    
    print("\n" + "="*50)
    print("Starting comprehensive analysis...")
    print("="*50 + "\n")
    
    # Process query
    report = agent.process_query(query, classroom_image_path, school_records_directory)
    
    print("\n" + "="*50)
    print("Comprehensive Report:")
    print("="*50 + "\n")
    print(report)