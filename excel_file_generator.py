import pandas as pd
import numpy as np
from datetime import datetime

# Set a random seed for reproducibility
np.random.seed(42)

# Create sample data
num_students = 30

# Student names
first_names = ['Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'William', 'Sophia', 'James',
               'Isabella', 'Benjamin', 'Mia', 'Jacob', 'Charlotte', 'Michael', 'Amelia',
               'Ethan', 'Harper', 'Daniel', 'Evelyn', 'Matthew', 'Abigail', 'Henry',
               'Emily', 'Alexander', 'Elizabeth', 'David', 'Sofia', 'Joseph', 'Madison', 'Samuel']
last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
              'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
              'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
              'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']

# Create student IDs
student_ids = [f"STU{1000 + i}" for i in range(num_students)]

# Create random scores
math_scores = np.random.randint(65, 100, num_students)
english_scores = np.random.randint(65, 100, num_students)
science_scores = np.random.randint(65, 100, num_students)
history_scores = np.random.randint(65, 100, num_students)


# Calculate GPA
def calculate_gpa(scores):
    # Convert to 4.0 scale
    gpa_points = []
    for score in scores:
        if score >= 90:
            gpa_points.append(4.0)
        elif score >= 80:
            gpa_points.append(3.0)
        elif score >= 70:
            gpa_points.append(2.0)
        else:
            gpa_points.append(1.0)
    return round(sum(gpa_points) / len(gpa_points), 2)


# Create GPAs
gpas = [calculate_gpa([m, e, s, h]) for m, e, s, h in zip(math_scores, english_scores, science_scores, history_scores)]

# Previous teachers
math_teachers = ['Ms. Johnson', 'Mr. Williams', 'Dr. Brown']
english_teachers = ['Dr. Garcia', 'Ms. Davis', 'Mr. Wilson']
science_teachers = ['Dr. Martinez', 'Ms. Thompson', 'Mr. Anderson']
history_teachers = ['Ms. Taylor', 'Dr. Moore', 'Mr. Jackson']

previous_math_teachers = [np.random.choice(math_teachers) for _ in range(num_students)]
previous_english_teachers = [np.random.choice(english_teachers) for _ in range(num_students)]
previous_science_teachers = [np.random.choice(science_teachers) for _ in range(num_students)]
previous_history_teachers = [np.random.choice(history_teachers) for _ in range(num_students)]

# Sample feedback comments
positive_feedback = [
    "Shows exceptional understanding of concepts",
    "Consistently participates in class discussions",
    "Demonstrates strong analytical skills",
    "Has shown significant improvement",
    "Very creative in assignments",
    "Excellent work ethic and dedication",
    "Outstanding problem-solving abilities",
    "Always goes beyond expectations",
    "Very attentive and focused in class",
    "Strong leadership qualities"
]

improvement_feedback = [
    "Needs to participate more in class discussions",
    "Should focus more on homework completion",
    "Would benefit from additional practice",
    "Needs to improve time management",
    "Should seek help when confused",
    "Could improve organization skills",
    "Struggles with complex concepts",
    "Attendance could be more consistent",
    "Needs to focus more during lessons",
    "Should review material more thoroughly"
]


# Generate feedback for each student
def generate_feedback(score):
    if score >= 85:
        return np.random.choice(positive_feedback)
    else:
        return np.random.choice(improvement_feedback)


math_feedback = [generate_feedback(score) for score in math_scores]
english_feedback = [generate_feedback(score) for score in english_scores]
science_feedback = [generate_feedback(score) for score in science_scores]
history_feedback = [generate_feedback(score) for score in history_scores]

# Create attendance records
attendance_rates = [round(np.random.uniform(0.80, 1.0), 2) for _ in range(num_students)]

# Create DataFrame
data = {
    'Student ID': student_ids,
    'First Name': first_names,
    'Last Name': last_names,
    'GPA': gpas,
    'Math Score': math_scores,
    'Previous Math Teacher': previous_math_teachers,
    'Math Teacher Feedback': math_feedback,
    'English Score': english_scores,
    'Previous English Teacher': previous_english_teachers,
    'English Teacher Feedback': english_feedback,
    'Science Score': science_scores,
    'Previous Science Teacher': previous_science_teachers,
    'Science Teacher Feedback': science_feedback,
    'History Score': history_scores,
    'Previous History Teacher': previous_history_teachers,
    'History Teacher Feedback': history_feedback,
    'Attendance Rate': attendance_rates
}

df = pd.DataFrame(data)

# Create a summary sheet
summary = {
    'Metric': ['Average GPA', 'Average Math Score', 'Average English Score',
               'Average Science Score', 'Average History Score', 'Average Attendance Rate'],
    'Value': [
        round(np.mean(gpas), 2),
        round(np.mean(math_scores), 2),
        round(np.mean(english_scores), 2),
        round(np.mean(science_scores), 2),
        round(np.mean(history_scores), 2),
        round(np.mean(attendance_rates), 2)
    ]
}

summary_df = pd.DataFrame(summary)

# Export to Excel with multiple sheets
output_file = 'student_data_sample.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Student Records', index=False)
    summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)

    # Get the workbook and format the cells
    workbook = writer.book

    # Format the Student Records sheet
    worksheet = writer.sheets['Student Records']

    # Make headers bold
    for col in range(1, len(df.columns) + 1):
        cell = worksheet.cell(row=1, column=col)
        cell.font = workbook.create_font(bold=True)

    # Format the Summary Statistics sheet
    worksheet = writer.sheets['Summary Statistics']

    # Make headers bold
    for col in range(1, len(summary_df.columns) + 1):
        cell = worksheet.cell(row=1, column=col)
        cell.font = workbook.create_font(bold=True)

print(f"Excel file created: {output_file}")
print(f"Generated data for {num_students} students with scores and teacher feedback.")
print(f"File contains two sheets: 'Student Records' and 'Summary Statistics'")