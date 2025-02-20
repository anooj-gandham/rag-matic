import os
import json
import re
import tempfile
from pdf2image import convert_from_path
import pytesseract
import requests
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from docx import Document


def download_file(url, suffix=None):
    """
    Download a file from the provided URL and return the local file path.
    
    If no suffix is provided, the function will attempt to extract it from the URL.
    The downloaded file is stored as a temporary file.
    """
    response = requests.get(url)
    response.raise_for_status()
    
    # Try to guess the file extension if not provided
    if not suffix:
        base = url.split('?')[0]  # remove query params if any
        _, ext = os.path.splitext(base)
        if ext in ['.pdf', '.docx', '.txt', 'json']:
            suffix = ext
        else:
            # If no extension, try to guess based on content type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type.lower():
                suffix = '.pdf'
            elif 'word' in content_type.lower():
                suffix = '.docx'
            elif 'text' in content_type.lower() or 'html' in content_type.lower():
                suffix = '.txt'
            else:
                raise ValueError("Unable to determine file type from URL or Content-Type")
    try:          
        suffix = f".{suffix}"
        # Create a temporary file. delete=False allows us to reopen it by path.
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(response.content)
        temp_file.flush()
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"Error saving file: {e}")
        raise e
    
def parse_pdf(file_path):
    """
    Parse a PDF file and extract text from each page.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        list: A list where each element is the extracted text of a page.
    """
    page_texts = []
    for page_layout in extract_pages(file_path):
        page_text = ''
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                page_text += element.get_text()
        page_texts.append(page_text)
    return page_texts

def get_pdf_page_count(file_path):
    """
    Get the total number of pages in a PDF.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        int: Number of pages in the PDF.
    """
    try:
        pages = extract_pages(file_path)
        return sum(1 for _ in pages)
    except Exception as e:
        print(f"Error reading PDF pages: {e}")
        return 1  # Assume 1 page if reading fails

def is_text_valid(text, page_count):
    """
    Check if extracted text is valid based on PDF length.
    
    Args:
        text (str): Extracted text from the PDF.
        page_count (int): Number of pages in the PDF.
    
    Returns:
        bool: True if the extracted text is sufficient, False otherwise.
    """
    clean_text = re.sub(r'\s+', '', text)  # Remove whitespace
    min_length = max(50 * page_count, 100)  # Minimum 50 chars per page, at least 100 chars
    return len(clean_text) >= min_length

# def extract_text_pypdf2(file_path):
#     """
#     Extract text from a PDF using PyPDF2.

#     Args:
#         file_path (str): Path to the PDF file.
    
#     Returns:
#         str: Extracted text.
#     """
#     texts = []
#     try:
#         with open(file_path, "rb") as f:
#             reader = PyPDF2.PdfReader(f)
#             for page in reader.pages:
#                 page_text = page.extract_text()
#                 if page_text:
#                     texts.append(page_text)
#     except Exception as e:
#         print(f"PyPDF2 extraction failed: {e}")
#         raise e
    
#     return texts

def extract_text_ocr(file_path):
    """
    Extract text from a scanned PDF using OCR.

    Args:
        file_path (str): Path to the PDF file.
    
    Returns:
        str: Extracted text.
    """
    texts = []
    try:
        images = convert_from_path(file_path)
        for image in images:
            texts.append(pytesseract.image_to_string(image))
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        raise e
    
    return texts

def parse_pdf_with_fallback(file_path):
    """
    Attempt text extraction using pdfminer.six first.
    If extracted text is insufficient, use OCR as a fallback.
    
    Args:
        file_path (str): Path to the PDF file.
    
    Returns:
        str: Extracted text from the best available method.
    """
    page_count = get_pdf_page_count(file_path)
    print(f"PDF has {page_count} pages.")

    extracted_text = parse_pdf(file_path)

    if is_text_valid("\n".join(extracted_text), page_count):
        print("Successfully extracted text using pdfminer.six.")
        return extracted_text
    
    print("pdfminer.six extraction failed or insufficient. Falling back to OCR...")
    return extract_text_ocr(file_path)

def parse_pdf_with_ocr(file_path):
    """
    Parse a scanned PDF file using OCR.
    
    Converts each PDF page to an image and extracts text using pytesseract.
    
    Returns:
        Extracted text as a string.
    """
    text = ""
    # Convert PDF to a list of PIL Image objects
    images = convert_from_path(file_path)
    
    # Loop through each page image and extract text
    for image in images:
        page_text = pytesseract.image_to_string(image)
        text += page_text + "\n"
    
    return text

def parse_docx(file_path):
    """
    Parse a DOCX file and extract its text.

    Args:
        file_path (str): The path to the DOCX file.

    Returns:
        str: The extracted text.
    """
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return full_text

def parse_txt(file_path):
    """
    Parse a TXT file using built-in file I/O.
    
    Returns:
        The file's text content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print("Error parsing TXT file.")
        raise e

def parse_json(file_path):
    """
    Parse a JSON file using the built-in json module.
    
    Returns:
        The parsed JSON object.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [json.dumps(json.load(f))]
    except Exception as e:
        print("Error parsing JSON file.")
        raise e

def parse_file(file_path, ext):
    """
    Detect the file type based on its extension and parse accordingly.
    
    Supported file types: PDF, DOCX, TXT, JSON.
    
    Returns:
        The extracted text (for PDF, DOCX, TXT) or the parsed JSON object.
    """
    ext = ext.lower()
    if ext == 'pdf':
        return parse_pdf_with_fallback(file_path), ext
    elif ext == 'docx':
        return parse_docx(file_path), ext
    elif ext == 'txt':
        return parse_txt(file_path), ext
    elif ext == 'json':
        return parse_json(file_path), ext
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def parse_file_from_url(url, type):
    """
    Download a file from a URL and parse it automatically.
    
    The file is downloaded to a temporary location, parsed, and then deleted.
    
    Returns:
        The extracted text or parsed JSON.
    """
    # Determine suffix from URL (if possible)
    base = url.split('?')[0]
    temp_file_path = download_file(url, type)
    try:
        result, ext = parse_file(temp_file_path, type)
        os.remove(temp_file_path)


    except Exception as e:
        # Clean up the temporary file if parsing fails
        os.remove(temp_file_path)
        raise e

    return result, ext

if __name__ == '__main__':
    # Example: local file parsing
    try:
        # pdf_text, ext = parse_file("/Users/anoojgandham/codes/rag-matic/static/documents/2502.05138v1.pdf")
        url = "https://arxiv.org/pdf/2402.04806"
        temp_file_name = download_file(url)
        print("Temporary file name:", temp_file_name)
        
        # pdf_text, ext = parse_file_from_url("https://arxiv.org/pdf/2402.04806")
        # print("PDF Text:\n", pdf_text)
    except Exception as e:
        print("Error parsing sample.pdf:", e)
