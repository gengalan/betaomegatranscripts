import PyPDF2 as pdf
import openai as ai


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

def insert_to_db(placeholder1, placeholder2, db_path):
    pass

if __name__ == '__main__':
    pdf_path = 'sample.pdf'
    text = extract_text_from_pdf(pdf_path)
    response = process_text_with_ai(text)
    insert_to_db(pdf_path, response, 'sample.db')