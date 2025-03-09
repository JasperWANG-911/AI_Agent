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

def analyze_student_performance(csv_file_paths, prompt, api_key=None):

    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "No API key provided. Please provide an API key or set the OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    # Load and combine data from all files
    combined_data = []
    for file_path in csv_file_paths:
        try:
            df = pd.read_csv(file_path)
            combined_data.append(df)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")

    # If no valid files were provided, return an error
    if not combined_data:
        return {"error": "No valid CSV files were provided"}

    # Combine all data frames
    combined_df = pd.concat(combined_data, ignore_index=True)

    # Get the student ID from the data
    if 'Student ID' in combined_df.columns and not combined_df['Student ID'].empty:
        student_id = combined_df['Student ID'].iloc[0]
    else:
        student_id = "unknown"

    # Convert to string for inclusion in the prompt
    student_csv = combined_df.to_csv(index=False)

    # If custom prompt is not provided, use a default one

    extended_prompt = f"""
    {prompt}

    CSV Data:
    {student_csv}
    
    Please provide your analysis as a JSON object with the following structure:
    {{
        "name": "student name",
        "gpa": gpa value,
        "math_score": math score,
        "english_score": english score,
        "science_score": science score,
        "history_score": history score,
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
                {"role": "user", "content": extended_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        analysis_json = response.choices[0].message.content

        # Try to parse the JSON response
        try:
            analysis_dict = json.loads(analysis_json)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'({.*})', analysis_json, re.DOTALL)
            if json_match:
                analysis_dict = json.loads(json_match.group(1))
            else:
                return {
                    "error": "Failed to parse JSON from the API response",
                    "raw_response": analysis_json
                }

        # Add student ID to the analysis
        analysis_dict["student_id"] = student_id

        print(f"Completed analysis for student {student_id}")
        return analysis_dict

    except Exception as e:
        print(f"Error analyzing student data: {str(e)}")
        return {"error": f"Error: {str(e)}"}



