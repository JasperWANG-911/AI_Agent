import pandas as pd
import os
from openai import OpenAI
import json


def excel_to_csv(excel_file, csv_file):
    print(f"Reading Excel file: {excel_file}")
    df = pd.read_excel(excel_file)

    df.to_csv(csv_file, index=False)

    print(f"Conversion successful. CSV file saved at: {csv_file}")

def filter_school_records(directory_path, input_query, api_key=None):
    """Filter files in the School_records directory based on relevance to the input query."""
    # Set the OpenAI API key
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "No API key provided. Please provide an API key or set the OPENAI_API_KEY environment variable."
            )
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Get all files in the directory
    all_files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
    # Prepare the file list for analysis
    file_list = []
    
    for file in all_files:
        # Construct the prompt for GPT-4o
        prompt = f"""
        Analyze the relevance of the file name '{file}' to the following query: '{input_query}'
        
        IMPORTANT GUIDELINES:
        1. Files with general names like "student_grades.csv", "class_records.xlsx", or "academic_performance.xlsx" should ALWAYS be considered relevant, as they likely contain data about all students.
        2. If the query mentions a specific student (e.g., "Liam"), any file containing student data should be considered relevant.
        3. If the query mentions a specific subject (e.g., "math"), any file containing academic records should be considered relevant.
        4. When in doubt about whether a file might contain relevant information, include it rather than exclude it.
        
        Provide a JSON response with the following structure:
        {{
            "is_relevant": boolean, // true if potentially relevant, false if completely unrelated
            "reason": string // brief explanation of why this file is relevant or not
        }}
        """
        
        try:
            # Call GPT-4o API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes file relevance."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = response.choices[0].message.content
            relevance_data = json.loads(result)
            
            # Only add relevant files to the list
            if relevance_data['is_relevant']:
                file_list.append(os.path.join(directory_path, file))
        
        except Exception as e:
            print(f"Error processing file {file}: {e}")
    
    return file_list

def analyze_student_performance(csv_file_path, api_key=None):
    """ Return an analysis of student performance based on the provided CSV file."""
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "No API key provided. Please provide an API key or set the OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)
    df = pd.read_csv(csv_file_path)

    student_ids = df['Student ID'].unique() if 'Student ID' in df.columns else None

    # Analyze each student individually
    student_analyses = {}

    for student_id in student_ids:
        # Filter DataFrame for this student
        student_df = df[df['Student ID'] == student_id]

        if len(student_df) == 0:
            continue

        # Convert to string
        student_csv = student_df.to_csv(index=False)

        # Create prompt for OpenAI
        prompt = f"""
        Below is CSV data for a student. Please analyze how well this student is performing based on 
        their scores, GPA, attendance, and teacher feedback.

        CSV Data:
        {student_csv}
        
        Please provide your analysis as a JSON object with the following structure:
        {{
            "name": name,
            "gpa": gpa,
            "math_score": math score,
            "english_score": english score,
            "science_score": science score,
            "history_score": history_score,
            "overall_assessment": "A concise paragraph evaluating overall performance",
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "areas_for_improvement": ["area 1", "area 2", "area 3"],
            "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
        }}
        
        Return ONLY the JSON object, no additional text.
        """

        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use an appropriate model
                messages=[
                    {"role": "system",
                     "content": "You are an experienced educational analyst tasked with evaluating student performance data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )

            analysis_json = response.choices[0].message.content
            analysis_dict = json.loads(analysis_json)


            # Combine with student info
            student_analyses[student_id] = analysis_dict

            print(f"Completed analysis for student {student_id}")

        except Exception as e:
            print(f"Error analyzing student {student_id}: {str(e)}")
            student_analyses[student_id] = f"Error: {str(e)}"

    return student_analyses


