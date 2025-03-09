import pandas as pd
import os
import json
import logging
from openai import OpenAI
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import predefined functions
from API_SchoolRecords import (
    excel_to_csv,
    filter_school_records,
    analyze_student_performance
)

class DynamicSchoolAgent:
    """
    Dynamic school records analysis agent that selects analyses to perform based on user queries.
    Uses GPT-4 to determine the appropriate API calls and generates a textual report.
    """
    
    def __init__(self, openai_api_key=None):
        """Initialize Agent with OpenAI API key"""
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it via the openai_api_key parameter or OPENAI_API_KEY environment variable.")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        logger.info("✅ DynamicSchoolAgent initialized")
    
    def transform_query(self, query: str) -> str:
        """
        Transform user query to focus on school records analysis
        """
        print(f"🔄 Transforming original query: '{query}'")
        
        system_prompt = """You are a query transformation assistant for a school records analysis system.

Your task is to transform general academic performance questions into specific queries about student records.

For example:
- "How is Lisa doing in class?" → "How is Lisa performing in her recent academic records?"
- "Is John good at science?" → "What are John's performance trends in science subjects?"
- "What's Mary's attendance like?" → "What are Mary's attendance records showing?"

Important rules:
1. Always transform queries to focus on what can be found in school records
2. Focus on academic performance, grades, attendance, and trends
3. Preserve student names and subjects mentioned in the original query
4. Make it clear the analysis is based on school records
5. Keep the transformed query concise and clear

Return only the transformed query without any explanation or additional text."""

        user_prompt = f"""Original query: {query}   

Transform this query to focus specifically on what can be analyzed from school records."""

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            transformed_query = completion.choices[0].message.content.strip()
            print(f"✅ Transformed query: '{transformed_query}'")
            return transformed_query
        except Exception as e:
            logger.error(f"❌ Error transforming query: {e}")
            # Return original query if transformation fails
            return query
    
    def design_analysis_plan(self, query: str, records_directory: str) -> Dict[str, Any]:
        """
        Design an analysis plan based on the query
        """
        print(f"🔍 Designing analysis plan for: '{query}'")
        
        system_prompt = """You are a school records analysis assistant that helps analyze student performance.
You can use the following functions:

1. "filter_school_records": Find relevant files based on the query
2. "excel_to_csv": Convert Excel files to CSV format for analysis
3. "analyze_student_performance": Analyze student data from CSV files

Please return an execution plan in JSON format:
{
  "plan": [
    {"function": "function_name", "description": "purpose of this step"},
    {"function": "another_function", "description": "purpose of this step"}
  ],
  "student_name": "Name of student in query or 'ALL'",
  "subject": "Subject mentioned in query or 'ALL'",
  "time_period": "Time period mentioned (recent, last semester, etc.) or 'ALL'",
  "explanation": "explanation of the execution plan"
}

Note:
- Functions have dependencies: always filter files first, then convert Excel to CSV, then analyze
- Only select necessary functions required to complete the task
- Be sure to extract the student name, subject, and time period from the query"""

        user_prompt = f"Query: {query}\nRecords directory: {records_directory}\nPlease design an analysis plan."

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
            logger.error(f"❌ Error designing analysis plan: {e}")
            return {
                "plan": [
                    {"function": "filter_school_records", "description": "Find relevant files"},
                    {"function": "excel_to_csv", "description": "Convert Excel files to CSV"},
                    {"function": "analyze_student_performance", "description": "Analyze student data"}
                ],
                "student_name": "ALL",
                "subject": "ALL",
                "time_period": "ALL",
                "explanation": f"Default plan due to error: {e}"
            }
    
    def execute_plan(self, plan: Dict[str, Any], query: str, records_directory: str) -> Dict[str, Any]:
        """
        Execute the analysis plan
        """
        print(f"📋 Executing analysis plan...")
        print(f"📝 Plan explanation: {plan.get('explanation', 'No explanation')}")
        
        # Dictionary to store intermediate results
        data = {
            "query": query,
            "records_directory": records_directory,
            "student_name": plan.get("student_name", "ALL"),
            "subject": plan.get("subject", "ALL"),
            "time_period": plan.get("time_period", "ALL"),
            "relevant_files": [],
            "converted_files": [],
            "analysis_results": {},
            "errors": []
        }
        
        # Track completed steps
        for step_idx, step in enumerate(plan.get("plan", [])):
            function_name = step.get("function")
            description = step.get("description", "No description")
            
            print(f"\n🔄 Step {step_idx+1}/{len(plan.get('plan', []))}: {function_name}")
            print(f"📌 {description}")
            
            try:
                # Filter relevant files
                if function_name == "filter_school_records":
                    print("🔍 Finding relevant school record files...")
                    relevant_files = filter_school_records(
                        records_directory, 
                        query, 
                        self.openai_api_key
                    )
                    data["relevant_files"] = relevant_files
                    print(f"✅ Found {len(relevant_files)} relevant files")
                
                # Convert Excel to CSV
                elif function_name == "excel_to_csv":
                    print("📊 Converting Excel files to CSV...")
                    if not data["relevant_files"]:
                        print("⚠️ No relevant files found, skipping conversion")
                        continue
                    
                    for excel_file in data["relevant_files"]:
                        if excel_file.endswith(('.xlsx', '.xls')):
                            csv_file = excel_file.rsplit('.', 1)[0] + '.csv'
                            success = excel_to_csv(excel_file, csv_file)
                            if success:
                                data["converted_files"].append(csv_file)
                    
                    print(f"✅ Converted {len(data['converted_files'])} Excel files to CSV")
                
                # Analyze student performance
                elif function_name == "analyze_student_performance":
                    print("📈 Analyzing student performance...")
                    csv_files = data["converted_files"] + [f for f in data["relevant_files"] if f.endswith('.csv')]
                    
                    if not csv_files:
                        print("⚠️ No CSV files available for analysis")
                        continue
                    
                    for csv_file in csv_files:
                        print(f"📊 Analyzing: {os.path.basename(csv_file)}")
                        analysis_results = analyze_student_performance(
                            csv_file, 
                            query, 
                            self.openai_api_key
                        )
                        data["analysis_results"][csv_file] = analysis_results
                    
                    print(f"✅ Analyzed {len(csv_files)} CSV files")
                
                else:
                    print(f"⚠️ Unknown function: {function_name}")
            
            except Exception as e:
                error_message = f"Error executing {function_name}: {e}"
                logger.error(f"❌ {error_message}")
                data["errors"].append(error_message)
        
        return data
    
    def generate_report(self, query: str, results: Dict[str, Any], original_query: str = None) -> str:
        """
        Generate a natural language report based on analysis results
        """
        print("✍️ Generating analysis report...")
        
        system_prompt = """You are a professional education analyst who creates reports based on student records.

Your task is to synthesize the provided analysis data into a clear, concise report that directly answers the user's query.

Important instructions:
1. Focus on directly answering the query with specific data points
2. Structure your report in a clear, readable format
3. Highlight key trends, patterns, and insights
4. If data is incomplete or missing, acknowledge this honestly
5. Use a professional but accessible tone, as if writing for parents or teachers
6. Avoid technical jargon about the data processing methods
7. Keep your report concise and to the point
8. Include specific grades, percentages, or metrics when available
9. Do not mention the analysis process itself unless there were significant errors
"""

        # Include both original and transformed queries if available
        query_info = f"Original query: {original_query}\nTransformed query: {query}" if original_query else f"Query: {query}"
        
        # Remove file paths and simplify the data structure for GPT
        simplified_results = {
            "student_name": results.get("student_name", "ALL"),
            "subject": results.get("subject", "ALL"),
            "time_period": results.get("time_period", "ALL"),
            "file_count": len(results.get("relevant_files", [])),
            "errors": results.get("errors", []),
            "analysis_results": {}
        }
        
        # Simplify analysis results
        for file_path, analysis in results.get("analysis_results", {}).items():
            file_name = os.path.basename(file_path)
            simplified_results["analysis_results"][file_name] = analysis
        
        user_prompt = f"""{query_info}

Analysis results:
{json.dumps(simplified_results, ensure_ascii=False, indent=2)}

Please generate a concise report answering the query based on these results."""

        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            report = completion.choices[0].message.content
            return report
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            return f"I apologize, but I was unable to generate a report due to an error: {e}"
    
    def process_query(self, query: str, records_directory: str = "School_records") -> str:
        """
        Main function to process user query about school records
        """
        print(f"\n🔍 Processing query: '{query}'")
        print(f"📁 Records directory: {records_directory}")
        
        if not os.path.exists(records_directory):
            return f"Error: Records directory does not exist: {records_directory}"
        
        try:
            # Store original query
            original_query = query
            
            # 1. Transform the query to focus on school records
            transformed_query = self.transform_query(query)
            
            # 2. Design analysis plan based on transformed query
            plan = self.design_analysis_plan(transformed_query, records_directory)
            
            # 3. Execute plan
            results = self.execute_plan(plan, transformed_query, records_directory)
            
            # 4. Generate report
            report = self.generate_report(transformed_query, results, original_query)
            
            return report
        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            logger.error(f"\n❌ {error_message}")
            import traceback
            traceback.print_exc()
            return error_message
