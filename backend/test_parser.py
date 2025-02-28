import sys
import json
from pathlib import Path
from transcript_parser_module import parse_transcript

def test_parser():
    """
    Test the transcript parser with a sample PDF
    """
    # Ensure command line argument is provided
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <path_to_transcript.pdf>")
        return
    
    pdf_path = sys.argv[1]
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: File '{pdf_path}' not found.")
        return
    
    print(f"Parsing transcript: {pdf_path}")
    student_data = parse_transcript(pdf_path)
    
    if not student_data:
        print("Failed to parse transcript")
        return
    
    # Print extracted data in a readable format
    print("\n===== STUDENT INFORMATION =====")
    print(f"Name: {student_data['name']}")
    print(f"Student ID: {student_data['student_id']}")
    print(f"Cumulative GPA: {student_data['cumulative_gpa']:.2f}")
    print(f"Total Credits: {student_data['total_credits']:.1f}")
    
    print("\n===== QUARTERS =====")
    for quarter in student_data['most_recent_quarters']:
        print(f"Quarter: {quarter['quarter']}")
        print(f"  GPA: {quarter['gpa']:.2f}")
        print(f"  Credits: {quarter['credits']:.1f}")
        print(f"  Courses: {', '.join(quarter['courses'])}")
    
    # Save the extracted data to a JSON file
    output_path = Path(pdf_path).stem + "_parsed.json"
    with open(output_path, 'w') as f:
        json.dump(student_data, f, indent=2)
    
    print(f"\nParsed data saved to: {output_path}")

if __name__ == "__main__":
    test_parser()
