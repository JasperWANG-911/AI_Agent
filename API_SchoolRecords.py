import pandas as pd
import os
from openai import OpenAI
import json

def excel_to_csv(excel_file, csv_file):
    """
    Convert Excel file to CSV format
    """
    if os.path.basename(excel_file).startswith("~$"):
        print(f"Skipping temporary file: {excel_file}")
        return False
    
    print(f"Reading Excel file: {excel_file}")
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
        df.to_csv(csv_file, index=False)
        print(f"Conversion successful. CSV file saved at: {csv_file}")
        return True
    except Exception as e:
        print(f"Error converting Excel file: {e}")
        return False

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

def analyze_student_performance(csv_file_path, query, api_key=None):
    """
    Analyze student performance based on a specific query.
    Only analyzes data for the student mentioned in the query.
    """
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "No API key provided. Please provide an API key or set the OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)
    
    # Extract student name from query
    # First, use OpenAI to extract the student name
    student_extraction_prompt = f"""
    Extract the student name from the following query:
    "{query}"
    
    Return ONLY the student name, nothing else.
    If no specific student name is mentioned, return "ALL".
    """
    
    try:
        student_extraction = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract student names from queries."},
                {"role": "user", "content": student_extraction_prompt}
            ],
            temperature=0.3
        )
        
        student_name = student_extraction.choices[0].message.content.strip()
        
        # If no specific student, return empty result
        if student_name == "ALL":
            print("No specific student mentioned in query. Analyzing all students.")
        else:
            print(f"Extracting data for student: {student_name}")
    except Exception as e:
        print(f"Error extracting student name: {e}")
        student_name = None
        
    # Ensure CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        return {}
        
    try:
        df = pd.read_csv(csv_file_path)
        
        # extract student data
        if 'Student ID' not in df.columns:
            print(f"No 'Student ID' column found in {csv_file_path}")
            return {}
        
        has_separate_name_columns = 'First Name' in df.columns and 'Last Name' in df.columns
        has_combined_name_column = 'Name' in df.columns
        
        if student_name and student_name != "ALL":
            matching_students = None
            
            if has_separate_name_columns:

                name_parts = student_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    
                    matching_students = df[
                        (df['First Name'].str.lower() == first_name.lower()) & 
                        (df['Last Name'].str.lower() == last_name.lower())
                    ]
                    
                    if matching_students.empty:
                        matching_students = df[
                            (df['First Name'].str.lower().str.contains(first_name.lower(), na=False)) |
                            (df['Last Name'].str.lower().str.contains(last_name.lower(), na=False))
                        ]
                else:

                    matching_students = df[
                        df['First Name'].str.lower().str.contains(student_name.lower(), na=False) |
                        df['Last Name'].str.lower().str.contains(student_name.lower(), na=False)
                    ]
            
            elif has_combined_name_column:

                matching_students = df[df['Name'].str.lower().str.contains(student_name.lower(), na=False)]
            
            if matching_students is None or matching_students.empty:
                print(f"No student named '{student_name}' found in {csv_file_path}")
                return {}
                
            student_ids = matching_students['Student ID'].unique()
            print(f"Found {len(student_ids)} student ID(s) matching '{student_name}'")
        else:
            
            student_ids = df['Student ID'].unique()
        
        # Analyze student data
        student_analyses = {}
        
        for student_id in student_ids:
            # Filter data for the student
            student_df = df[df['Student ID'] == student_id]
            
            if len(student_df) == 0:
                continue
            
            student_info = {}
            
            # get student name
            if has_separate_name_columns:
                student_info['name'] = f"{student_df['First Name'].iloc[0]} {student_df['Last Name'].iloc[0]}"
            elif has_combined_name_column:
                student_info['name'] = student_df['Name'].iloc[0]
            else:
                student_info['name'] = f"Student ID: {student_id}"
            
            # add student ID
            student_info['student_id'] = student_id
            
            # add GPA
            if 'GPA' in student_df.columns:
                student_info['gpa'] = float(student_df['GPA'].iloc[0])
            
            # add scores
            student_info['scores'] = {}
            for subject in ['Math', 'English', 'Science', 'History']:
                score_col = f"{subject} Score"
                if score_col in student_df.columns:
                    student_info['scores'][subject.lower()] = int(student_df[score_col].iloc[0])
            
            # add attendance rate
            if 'Attendance Rate' in student_df.columns:
                student_info['attendance'] = float(student_df['Attendance Rate'].iloc[0])
            
            # add teacher feedback
            student_info['feedback'] = {}
            for subject in ['Math', 'English', 'Science', 'History']:
                feedback_col = f"{subject} Teacher Feedback"
                if feedback_col in student_df.columns:
                    student_info['feedback'][subject.lower()] = student_df[feedback_col].iloc[0]
            
            student_analyses[student_id] = student_info
        
        return student_analyses
    except Exception as e:
        print(f"Error reading {csv_file_path}: {str(e)}")
        return {}