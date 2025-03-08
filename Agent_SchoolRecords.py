import os
import json
import pandas as pd
from openai import OpenAI

# Import functions from API_SchoolRecords
from API_SchoolRecords import (
    excel_to_csv,
    filter_school_records,
    analyze_student_performance
)

class DynamicSchoolRecordsAgent:
    """
    Dynamic agent for analyzing school records and responding to queries about student performance.
    The agent dynamically determines which analysis functions to use based on the query.
    """
    
    def __init__(self, openai_api_key):
        """Initialize the agent with necessary API keys"""
        self.openai_api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.records_directory = None
        self.loaded_data = {}
        print("School Records Analysis Agent initialized")
    
    def transform_query(self, query):
        """
        Transform input query into specific school records-related queries
        """
        print(f"Transforming query: '{query}'")
        
        system_prompt = """You are a query transformation assistant for a school records analysis system.

Your task is to transform general academic performance questions into specific queries about academic records and performance.

For example:
- "How is Lisa doing in maths at school?" → "What do Lisa's academic records show about her math performance?"
- "Is John good at science?" → "What do John's science grades and teacher evaluations indicate about his performance?"
- "What's Mary's academic performance like?" → "Summarize Mary's academic performance metrics from available school records."
- "Which students are struggling in English?" → "Identify students with below-average performance in English based on grades and assessments."

Important rules:
1. Focus the query on information available in school records (grades, attendance, teacher comments, etc.)
2. Preserve student names mentioned in the original query
3. If a specific subject is mentioned, maintain that focus
4. Make the query specific and actionable for data analysis
5. Keep the transformed query concise and clear
6. Ensure the query is answerable from quantitative and qualitative academic data

Return ONLY the transformed query without any explanation or additional text."""

        user_prompt = f"""Original query: {query}

Transform this query to focus specifically on analyzing information available in school records."""

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            transformed_query = completion.choices[0].message.content.strip()
            print(f"Transformed query: '{transformed_query}'")
            return transformed_query
        except Exception as e:
            print(f"Error: {e}")
            # Return original query if transformation fails
            return query
    
    def design_analysis_plan(self, query, directory_path):
        """
        Design a plan for analyzing school records based on the query
        
        Args:
            query (str): The transformed user query
            directory_path (str): Path to the directory containing school records
            
        Returns:
            dict: Analysis plan with steps to execute
        """
        print("Designing analysis plan...")
        
        system_prompt = """You are a school records analysis assistant that helps analyze student academic performance.

You have access to the following functions:
1. "filter_school_records": Find relevant files in a directory based on the query
2. "excel_to_csv": Convert Excel files to CSV format for analysis
3. "analyze_student_performance": Analyze performance metrics from student records

Based on the user's query, design a plan for how to best retrieve and analyze the necessary school records data.

Return a JSON object with the following structure:
{
  "plan": [
    {"step": "function_name", "description": "Explanation of what this step will achieve"}
  ],
  "expected_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "explanation": "Overall explanation of the analysis approach"
}

Focus on creating an efficient, targeted analysis that directly addresses the user's query."""

        user_prompt = f"""Query: {query}

Records directory: {directory_path}

Please design an analysis plan that efficiently answers this query using the available school records."""

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
            print(f"Analysis plan created:")
            print(f"Explanation: {plan.get('explanation', 'No explanation provided')}")
            return plan
        except Exception as e:
            print(f"Error designing analysis plan: {e}")
            # Return a basic plan if the advanced planning fails
            return {
                "plan": [
                    {"step": "filter_school_records", "description": "Find relevant files"},
                    {"step": "excel_to_csv", "description": "Convert files to CSV format"},
                    {"step": "analyze_student_performance", "description": "Analyze student data"}
                ],
                "explanation": "Basic analysis of relevant school records."
            }
    
    def execute_plan(self, plan, query, directory_path):
        """
        Execute the analysis plan
        
        Args:
            plan (dict): The analysis plan to execute
            query (str): The user's query
            directory_path (str): Path to the directory with school records
            
        Returns:
            dict: Results of the analysis
        """
        print("Executing analysis plan...")
        
        # Set the records directory
        self.records_directory = directory_path
        
        # Store results
        results = {
            "query": query,
            "data": {},
            "analyses": {},
            "files_processed": []
        }
        
        # Track completed steps
        for step_idx, step in enumerate(plan.get("plan", [])):
            function_name = step.get("step")
            description = step.get("description", "No description")
            
            print(f"\nStep {step_idx+1}/{len(plan.get('plan', []))}: {function_name}")
            print(f"{description}")
            
            try:
                # Filter school records
                if function_name == "filter_school_records":
                    relevant_files = filter_school_records(directory_path, query, self.openai_api_key)
                    results["files_processed"] = relevant_files
                    print(f" Found {len(relevant_files)} relevant files")
                
                # Convert Excel to CSV
                elif function_name == "excel_to_csv":
                    csv_files = []
                    for file in results.get("files_processed", []):
                        if file.endswith('.xlsx') or file.endswith('.xls'):
                            csv_file = file.rsplit('.', 1)[0] + '.csv'
                            excel_to_csv(file, csv_file)
                            csv_files.append(csv_file)
                        elif file.endswith('.csv'):
                            csv_files.append(file)
                    
                    results["csv_files"] = csv_files
                    print(f" Prepared {len(csv_files)} CSV files for analysis")
                
                # Analyze student performance
                elif function_name == "analyze_student_performance":
                    for csv_file in results.get("csv_files", []):
                        try:
                            analysis = analyze_student_performance(csv_file, self.openai_api_key)
                            results["analyses"][os.path.basename(csv_file)] = analysis
                        except Exception as e:
                            print(f" Error analyzing {csv_file}: {e}")
                
                else:
                    print(f" Unknown function: {function_name}")
            
            except Exception as e:
                print(f" Error executing {function_name}: {e}")
                results[f"{function_name}_error"] = str(e)
        
        return results
    
    def consolidate_analyses(self, query, results):
        """
        Consolidate analysis results from multiple files into a single coherent response
        
        Args:
            query (str): The user's query
            results (dict): Results from executing the analysis plan
            
        Returns:
            dict: Consolidated analysis results
        """
        print(" Consolidating analysis results...")
        
        # Prepare consolidated data structure
        consolidated = {
            "query": query,
            "summary": {},
            "student_data": {},
            "insights": []
        }
        
        # Extract and organize data
        for filename, analysis in results.get("analyses", {}).items():
            for student_id, student_data in analysis.items():
                if isinstance(student_data, dict):
                    # If student not in consolidated data yet, add them
                    if student_id not in consolidated["student_data"]:
                        consolidated["student_data"][student_id] = student_data
                    else:
                        # Merge data if student already exists
                        for key, value in student_data.items():
                            if key not in consolidated["student_data"][student_id]:
                                consolidated["student_data"][student_id][key] = value
        
        return consolidated
    
    def generate_response(self, query, consolidated_results, original_query=None):
        """
        Generate a comprehensive response based on analysis results
        
        Args:
            query (str): Transformed user query
            consolidated_results (dict): Consolidated analysis results
            original_query (str): Original user query
            
        Returns:
            str: Generated response
        """
        print("✍️ Generating response...")
        
        system_prompt = """You are an expert educational analyst specializing in interpreting student performance data.

Generate a comprehensive, well-structured response based on the provided analysis of school records.

Your response should:
1. Directly address the user's original query
2. Synthesize information across all analyzed records
3. Present a balanced view of student performance with specific evidence
4. Highlight key insights, patterns, and trends
5. Be organized with clear sections and formatting
6. Recommend specific, actionable steps where appropriate
7. Acknowledge any limitations in the available data

Use a professional but accessible tone, and format your response for clarity with headings, bullet points, and paragraphs as appropriate."""

        # Include both original and transformed queries if available
        query_info = f"Original query: {original_query}\nTransformed query: {query}" if original_query else f"Query: {query}"
        
        user_prompt = f"""{query_info}

Analysis Results:
{json.dumps(consolidated_results, indent=2, ensure_ascii=False)}

Please provide a comprehensive response that addresses the query based on these analysis results."""

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
            print(f" Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def process_query(self, query, directory_path):
        """
        Process a user query about student performance using school records
        
        Args:
            query (str): User query
            directory_path (str): Path to directory containing school records
            
        Returns:
            str: Generated response
        """
        print(f"\n Processing query: '{query}'")
        print(f" School records directory: {directory_path}")
        
        if not os.path.exists(directory_path):
            return f"Error: Directory does not exist: {directory_path}"
        
        try:
            # Store original query
            original_query = query
            
            # 1. Transform the query
            transformed_query = self.transform_query(query)
            
            # 2. Design analysis plan
            plan = self.design_analysis_plan(transformed_query, directory_path)
            
            # 3. Execute plan
            results = self.execute_plan(plan, transformed_query, directory_path)
            
            # 4. Consolidate analyses
            consolidated_results = self.consolidate_analyses(transformed_query, results)
            
            # 5. Generate response
            response = self.generate_response(transformed_query, consolidated_results, original_query)
            
            return response
        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            print(f"\n {error_message}")
            import traceback
            traceback.print_exc()
            return error_message


# Example usage
if __name__ == "__main__":
    # Set API key directly
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Initialize the agent
    agent = DynamicSchoolRecordsAgent(openai_api_key)
    
    # Set school records directory
    records_directory = "/path/to/school_records"
    
    # Get user query
    query = input("\nEnter your query (e.g., 'How is Jasper doing in math?'): ")
    
    print("\n" + "="*50)
    print("Starting school records analysis...")
    print("="*50 + "\n")
    
    # Process query
    response = agent.process_query(query, records_directory)
    
    print("\n" + "="*50)
    print("Analysis results:")
    print("="*50 + "\n")
    print(response)