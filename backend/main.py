# Description: Main script to extract data from PDFs, process with AI, and insert into database
#   Will eventually be ran through AWS Lambda, and will be triggered by S3 bucket uploads,
#   and will insert data into AWS RDS database

import PyPDF2 as pdf
import openai as ai
from dotenv import load_dotenv

load_dotenv()
import os

API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_PATH = os.getenv('DATABASE_PATH')

def extract_text_from_pdf(pdf_path):
    """Extracts text from an uploaded PDF file using PyPDF2 library.
       TODO: Set up S3 bucket to store PDFs, and use boto3 to download PDFs to process.

    Args:
        pdf_path (String): NOTE: This is for local development, PDFs will
                                 be stored in S3 bucket in production

    Returns:
        String: Raw text extracted from PDF
    """
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = pdf.PdfFileReader(pdf_file)
        text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            text += page.extract_text()
    return text

def process_text_with_ai(text):
    """Processes text extracted from PDF using OpenAI's GPT API to allow 
       for customizable data extraction.
       NOTE: Could have used REGEX, however using AI allows for more flexibility.
    Args:
        text (String): Raw text extracted from PDF

    Returns:
        JSON: Structured information extracted from text using AI to be inserted into database
    """
    response = ai.chatCompletion.create(
        model = 'TBD',
        messages = [
            {'TBD'}
        ]
    )
    
    return response['choices'][0]['message']['content']

def insert_to_db(courses, summary, db_path = DATABASE_PATH):
    """Inserts the extracted data into the database, using SQL queries.
        Database will likely be hosted through AWS RDS, TBD
        
    Args:
        courses (_type_): _description_
        summary (_type_): _description_
        db_path (_type_, optional): _description_. Defaults to DATABASE_PATH.
        TODO: determine how to structure data, and how to handle RDS updates
    """
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