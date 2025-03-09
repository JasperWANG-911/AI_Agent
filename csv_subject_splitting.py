import pandas as pd
import numpy as np
from collections import OrderedDict
def split_csv_by_subjects(subjects : list, input_csv : str, output_folder : str):
    """Takes a CSV file with student grades and splits it into separate CSV files based on subjects.

    Args:
        subjects (list): A list of subject names to split the CSV file by.
        input_csv (str): Path to the input CSV file.
        output_folder (str): Path to the output folder where the split CSV files will be saved.
    """

    df = pd.read_csv(input_csv)

    subject_names = subjects

    for i in subject_names:
        initial_dict = OrderedDict()
        matched_headers = [col for col in df.columns if i.lower() in col.lower()]
        if matched_headers:
            initial_dict["First Name"] = df["First Name"]
            initial_dict["Last Name"] = df["Last Name"]
            initial_dict["GPA"] = df["GPA"]
        for header in matched_headers:
            initial_dict[header] = df[header]
        initial_dict = pd.DataFrame(initial_dict)
        initial_dict.to_csv(f"{output_folder}/all_student_{i}_grades_feedback.csv", index=False)
    print(f"Created {i}_grades.csv file.")
    
    
