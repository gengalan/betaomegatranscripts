import os
# import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from transcript_parser_module import parse_transcript

app = FastAPI(title="Transcript Parser API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect("transcripts.db")
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        name TEXT,
        total_credits REAL,
        cumulative_gpa REAL
    )
    ''')
    
    # Create quarters table (for all quarters)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quarters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        quarter_name TEXT,
        quarter_year TEXT,
        quarter_gpa REAL,
        quarter_credits REAL,
        deans_list BOOLEAN,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Create latest quarter table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS latest_quarter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        quarter_name TEXT,
        quarter_year TEXT,
        quarter_gpa REAL,
        quarter_credits REAL,
        deans_list BOOLEAN,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Create courses table (for latest quarter only)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS latest_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        dept_code TEXT,
        course_number TEXT,
        course_name TEXT,
        credits REAL,
        grade TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')

    conn.commit()
    conn.close()


class Course(BaseModel):
    dept_code: str
    course_number: str
    course_name: str
    credits: float
    grade: str


class Quarter(BaseModel):
    quarter_name: str
    quarter_year: str
    quarter_gpa: float
    quarter_credits: float
    deans_list: bool
    courses: List[Course]


class Student(BaseModel):
    student_id: str
    name: str
    total_credits: float
    cumulative_gpa: float
    most_recent_quarter: Optional[Quarter] = None


def save_to_db(student_data):
    conn = sqlite3.connect("transcripts.db")
    cursor = conn.cursor()
    
    try:
        # Always replace existing data with the new data
        cursor.execute("DELETE FROM latest_courses WHERE student_id = ?", (student_data["student_id"],))
        cursor.execute("DELETE FROM latest_quarter WHERE student_id = ?", (student_data["student_id"],))
        
        # Create a new table for all quarters if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_quarters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            quarter_name TEXT,
            quarter_year TEXT,
            quarter_level TEXT,
            quarter_gpa REAL,
            quarter_credits REAL,
            deans_list BOOLEAN,
            cumulative_gpa REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
        ''')
        
        # Create a table for all courses across all quarters
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            quarter_name TEXT,
            quarter_year TEXT,
            dept_code TEXT,
            course_number TEXT,
            course_name TEXT,
            credits REAL,
            grade TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
        ''')
        
        # Insert or update student record
        cursor.execute(
            "INSERT OR REPLACE INTO students (student_id, name, total_credits, cumulative_gpa) VALUES (?, ?, ?, ?)",
            (student_data["student_id"], student_data["name"], student_data["total_credits"], student_data["cumulative_gpa"])
        )
        
        # Clear existing quarters and courses for this student
        cursor.execute("DELETE FROM all_quarters WHERE student_id = ?", (student_data["student_id"],))
        cursor.execute("DELETE FROM all_courses WHERE student_id = ?", (student_data["student_id"],))
        
        # Process most recent quarter
        if student_data.get("most_recent_quarter"):
            quarter = student_data["most_recent_quarter"]
            cursor.execute(
                "INSERT INTO latest_quarter (student_id, quarter_name, quarter_year, quarter_gpa, quarter_credits, deans_list) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    student_data["student_id"],
                    quarter["quarter_name"],
                    quarter["quarter_year"],
                    quarter["quarter_gpa"],
                    quarter["quarter_credits"],
                    quarter["deans_list"]
                )
            )
            
            # Insert courses for most recent quarter
            for course in quarter["courses"]:
                cursor.execute(
                    "INSERT INTO latest_courses (student_id, dept_code, course_number, course_name, credits, grade) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        student_data["student_id"],
                        course["dept_code"],
                        course["course_number"],
                        course["course_name"],
                        course["credits"],
                        course["grade"]
                    )
                )
        
        # Process all quarters
        if "quarters" in student_data and student_data["quarters"]:
            for quarter in student_data["quarters"]:
                # Insert quarter record
                cursor.execute(
                    "INSERT INTO all_quarters (student_id, quarter_name, quarter_year, quarter_level, quarter_gpa, quarter_credits, deans_list, cumulative_gpa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        student_data["student_id"],
                        quarter["quarter_name"],
                        quarter["quarter_year"],
                        quarter.get("quarter_level", ""),
                        quarter["quarter_gpa"],
                        quarter["quarter_credits"],
                        quarter["deans_list"],
                        quarter.get("cumulative_gpa", 0.0)
                    )
                )
                
                # Insert all courses for this quarter
                if "courses" in quarter and quarter["courses"]:
                    for course in quarter["courses"]:
                        cursor.execute(
                            "INSERT INTO all_courses (student_id, quarter_name, quarter_year, dept_code, course_number, course_name, credits, grade) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                student_data["student_id"],
                                quarter["quarter_name"],
                                quarter["quarter_year"],
                                course["dept_code"],
                                course["course_number"],
                                course["course_name"],
                                course["credits"],
                                course["grade"]
                            )
                        )
        
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


@app.post("/upload-transcript/", response_model=Student)
async def upload_transcript(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as temp_file:
        temp_file.write(await file.read())
    
    # Parse the transcript
    student_data = parse_transcript(temp_path)
    
    # Remove the temporary file
    os.remove(temp_path)
    
    if not student_data:
        raise HTTPException(status_code=500, detail="Failed to parse transcript")
    
    # Save to database
    if not save_to_db(student_data):
        raise HTTPException(status_code=500, detail="Failed to save to database")
    
    return student_data
    


@app.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: str):
    conn = sqlite3.connect("transcripts.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get student
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        student_row = cursor.fetchone()
        
        if not student_row:
            raise HTTPException(status_code=404, detail="Student not found")
        
        student = dict(student_row)
        
        # Get latest quarter
        cursor.execute("SELECT * FROM latest_quarter WHERE student_id = ?", (student_id,))
        quarter_row = cursor.fetchone()
        
        if quarter_row:
            quarter = dict(quarter_row)
            quarter["courses"] = []
            
            # Get courses for latest quarter
            cursor.execute("SELECT * FROM latest_courses WHERE student_id = ?", (student_id,))
            courses_rows = cursor.fetchall()
            
            for course_row in courses_rows:
                course = dict(course_row)
                quarter["courses"].append(course)
            
            student["most_recent_quarter"] = quarter
        
        # Get work in progress
        
        
        return student
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve student")
    
    finally:
        conn.close()



# Add this endpoint to your existing transcript_parser.py file
# Make sure it's at the same level as your other endpoint definitions

@app.get("/student-quarters/{student_id}")
async def get_student_quarters(student_id: str):
    """
    Get all quarters for a student.
    """
    conn = sqlite3.connect("transcripts.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if student exists
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Try to get all quarters from the database
        # First check if we have the all_quarters table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='all_quarters'
        """)
        
        if cursor.fetchone():
            # If all_quarters table exists, use it
            cursor.execute("""
                SELECT * FROM all_quarters 
                WHERE student_id = ? 
                ORDER BY quarter_year DESC, 
                    CASE quarter_name 
                        WHEN 'AUTUMN' THEN 4
                        WHEN 'WINTER' THEN 1 
                        WHEN 'SPRING' THEN 2
                        WHEN 'SUMMER' THEN 3
                    END DESC
            """, (student_id,))
            
            quarters_rows = cursor.fetchall()
            
            if quarters_rows:
                # Convert quarters rows to list of quarters with their courses
                quarters = []
                for quarter_row in quarters_rows:
                    quarter_data = dict(quarter_row)
                    
                    # Get courses for this quarter
                    cursor.execute("""
                        SELECT * FROM all_courses 
                        WHERE student_id = ? AND quarter_name = ? AND quarter_year = ?
                        ORDER BY dept_code, course_number
                    """, (student_id, quarter_data["quarter_name"], quarter_data["quarter_year"]))
                    
                    courses = cursor.fetchall()
                    quarter_data["courses"] = [dict(course) for course in courses]
                    
                    quarters.append(quarter_data)
                
                return quarters
        
        # Fall back to latest quarter if no quarters in all_quarters table
        # or if the table doesn't exist
        cursor.execute("SELECT * FROM latest_quarter WHERE student_id = ?", (student_id,))
        latest_quarter = cursor.fetchone()
        
        if not latest_quarter:
            return []
            
        # Get courses for latest quarter
        cursor.execute("SELECT * FROM latest_courses WHERE student_id = ?", (student_id,))
        courses = cursor.fetchall()
        
        # Create a list with just the latest quarter
        quarters = []
        quarter_data = dict(latest_quarter)
        quarter_data["courses"] = [dict(course) for course in courses]
        quarters.append(quarter_data)
        
        return quarters
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting student quarters: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


if __name__ == "__main__":
    # Use the filename this script is saved as
    import sys
    module_name = os.path.basename(sys.argv[0]).replace('.py', '')
    uvicorn.run(f"{module_name}:app", host="0.0.0.0", port=8000, reload=True)