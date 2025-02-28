import re
import pdfplumber
from collections import defaultdict

def parse_transcript(pdf_path):
    """
    Parse a university transcript PDF and extract only the most recent quarter information.
    
    Args:
        pdf_path (str): Path to the transcript PDF file
        
    Returns:
        dict: A dictionary containing student information and most recent quarter data
    """
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
                
            text_blocks = [block.strip() for block in full_text.split("\n") if block.strip()]

            # Extract name
            if len(text_blocks) >= 6:
                name_text = text_blocks[4]
                name_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Engineering', name_text)
                name = name_match.group(1) if name_match else "Unknown"
            else:
                name = "Unknown"
            
            # Extract student ID
            student_id_match = re.search(r'(\d{7})', full_text)
            student_id = student_id_match.group(1) if student_id_match else "Unknown"
        
            # Extract total credits and cumulative GPA
            cumulative_summary_match = re.search(r'CUMULATIVE CREDIT SUMMARY:[\s\S]*?\*{50,}', full_text)
            if cumulative_summary_match:
                total_credits_match = re.search(r'(?<!UW\s)CREDITS EARNED\s+(\d+\.\d+)', cumulative_summary_match.group(0))
                total_credits = float(total_credits_match.group(1)) if total_credits_match else 0.0
                cum_gpa_match = re.search(r'UW GRADE POINT AVG.\s+(\d+\.\d+)', cumulative_summary_match.group(0))
                cumulative_gpa = float(cum_gpa_match.group(1)) if cum_gpa_match else 0.0
            else:
                total_credits = 0.0
                cumulative_gpa = 0.0
            

            # Create the basic student record
            student = {
                "student_id": student_id,
                "total_credits": total_credits,
                "quarters": [],
                "name": name,
                "cumulative_gpa": cumulative_gpa,
                "most_recent_quarter": {
                    "quarter_name": "Unknown",
                    "quarter_year": "Unknown",
                    "quarter_gpa": 0.0,
                    "quarter_credits": 0.0,
                    "deans_list": False,
                    "cumulative_gpa": cumulative_gpa,
                    "courses": []
                }
            }
            
            # Process each page to extract quarters with column awareness
            all_quarters = []
            
            # Since transcripts are formatted with columns, need to handle them
            for page_num, page in enumerate(pdf.pages):
                # Extract words with positions
                words = page.extract_words()
                
                if not words:  # Skip empty pages
                    continue
                    
                # Find the middle of the page to separate columns
                page_width = page.width
                middle_x = page_width / 2
                
                # Group words by approximate y-coordinate (line)
                line_groups = defaultdict(list)
                for word in words:

                    y_key = round(word['top'] / 5) * 5
                    line_groups[y_key].append(word)

                left_lines = []
                right_lines = []
                
                for y_key in sorted(line_groups.keys()):
                    line_words = sorted(line_groups[y_key], key=lambda w: w['x0'])
                    
                    left_text = " ".join(w['text'] for w in line_words if w['x0'] < middle_x)
                    right_text = " ".join(w['text'] for w in line_words if w['x0'] >= middle_x)
                    
                    if left_text.strip():
                        left_lines.append(left_text)
                    if right_text.strip():
                        right_lines.append(right_text)
                
                left_column = "\n".join(left_lines)
                right_column = "\n".join(right_lines)
                
                for column_text in [left_column, right_column]:
                    quarter_pattern = r'(AUTUMN|WINTER|SPRING|SUMMER)\s+(\d{4})\s+([A-Z]+)\s+(\d+)'
                    quarter_matches = list(re.finditer(quarter_pattern, column_text))
                    
                    for i, qtr_match in enumerate(quarter_matches):
                        quarter_name = qtr_match.group(1)
                        quarter_year = qtr_match.group(2)
                        quarter_level = qtr_match.group(3)
                        
                        start_pos = qtr_match.end()
                        if i < len(quarter_matches) - 1:
                            end_pos = quarter_matches[i+1].start()
                        else:
                            end_pos = len(column_text)
                        
                        quarter_text = column_text[start_pos:end_pos]
                        
                        qtr_gpa_match = re.search(r'GPA:\s+(\d+\.\d+)', quarter_text)
                        if not qtr_gpa_match:
                            continue
                            
                        quarter_gpa = float(qtr_gpa_match.group(1))
                        
                        qtr_credits_match = re.search(r'QTR ATTEMPTED:\s+(\d+\.\d+)', quarter_text)
                        quarter_credits = float(qtr_credits_match.group(1)) if qtr_credits_match else 0.0
                        
                        deans_list = "DEAN'S LIST" in quarter_text
                        
                        cum_gpa_match = re.search(r'CUM GPA:\s+(\d+\.\d+)', quarter_text)
                        cum_gpa = float(cum_gpa_match.group(1)) if cum_gpa_match else 0.0
                        

                        courses = []
                        pattern = re.compile(r"(?P<dept_code>[A-Z ]{2,})\s+(?P<course_number>\d{3})\s+(?P<course_name>[A-Z &/]+)\s+(?P<course_credits>\d+\.\d+)\s+(?P<course_grade>\d+\.\d+)")
                        
                        matches = pattern.finditer(quarter_text)
                        for match in matches:
                            course = {
                                "dept_code": match.group("dept_code").strip(),
                                "course_number": match.group("course_number").strip(),
                                "course_name": match.group("course_name").strip(),
                                "credits": match.group("course_credits").strip(),
                                "grade": match.group("course_grade").strip()
                            }
                            courses.append(course)
                        
                        quarter = {
                            "quarter_name": quarter_name,
                            "quarter_year": quarter_year,
                            "quarter_level": quarter_level,
                            "quarter_gpa": quarter_gpa,
                            "quarter_credits": quarter_credits,
                            "deans_list": deans_list,
                            "cumulative_gpa": cum_gpa,
                            "courses": courses
                        }
                        
                        all_quarters.append(quarter)
            
            if all_quarters:
                term_order = {"WINTER": 0, "SPRING": 1, "SUMMER": 2, "AUTUMN": 3}
                
                sorted_quarters = sorted(
                    all_quarters,
                    key=lambda q: (int(q["quarter_year"]), term_order.get(q["quarter_name"], 0)),
                    reverse=True
                )
                
                student["quarters"] = sorted_quarters
                student["most_recent_quarter"] = sorted_quarters[0]
                
                
            else:
                student["most_recent_quarter"] = {
                    "quarter_name": "Unknown",
                    "quarter_year": "Unknown",
                    "quarter_gpa": 0.0,
                    "quarter_credits": 0.0,
                    "deans_list": False,
                    "cumulative_gpa": cumulative_gpa,
                    "courses": []
                }
                
                student["quarters"] = []
                print("No quarters found in transcript.")
            
            return student
            
    except Exception as e:
        print(f"Error parsing transcript: {e}")
        import traceback
        traceback.print_exc()
        return None