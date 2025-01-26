import PyPDF2 as pdf
import openai as ai
from dotenv import load_dotenv

load_dotenv()
import os

API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_PATH = os.getenv('DATABASE_PATH')

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = pdf.PdfFileReader(pdf_file)
        text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            text += page.extract_text()
    return text

def process_text_with_ai(text):
    response = ai.chatCompletion.create(
        model = 'TBD',
        messages = [
            {'TBD'}
        ]
    )
    
    return response['choices'][0]['message']['content']

def insert_to_db(courses, summary, db_path = DATABASE_PATH):
    pass

if __name__ == '__main__':
    pdf_path = 'sample.pdf'
    text = extract_text_from_pdf(pdf_path)
    extracted_data = process_text_with_ai(text)
    
    # Sample code to insert data into database
    import json
    data = json.loads(extracted_data)
    courses = data['courses']
    summary = data['summary']
    insert_to_db(courses, summary)