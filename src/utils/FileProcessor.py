import os
import docx
from PyPDF2 import PdfReader
from html.parser import HTMLParser
import logging

# Logger for file processing operations
logger = logging.getLogger(__name__)

class TextStripper(HTMLParser):
    """
    A simple HTML parser to extract plain text from HTML content.
    Avoids heavy dependencies like BeautifulSoup for simple stripping tasks.
    """
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, data):
        self.fed.append(data)
    def get_data(self):
        return "".join(self.fed)

def get_clean_text_from_html(file_name : str) -> str:
    """
    Reads an HTML file and strips all tags to return plain text.
    Useful for processing Word-exported HTML or web scrapes.
    """
    try:
        with open(file_name, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()

        stripper = TextStripper()
        stripper.feed(html_content)
        clean_text = stripper.get_data()
        return clean_text
    except Exception as e:
        logger.error(f"Error reading or stripping HTML file {file_name}: {e}", exc_info=True)
        raise

def docx_to_text(file_path: str) -> str:
    """
    Extracts text from a .docx file using the python-docx library.
    Iterates through all paragraphs and joins them.
    """
    try:
        document = docx.Document(file_path)
        return "".join([para.text for para in document.paragraphs])
    except Exception as e:
        logger.error(f"Error reading docx file {file_path}: {e}", exc_info=True)
        raise

def pdf_to_text(file_path: str) -> str:
    """
    Extracts text from a .pdf file using PyPDF2.
    Iterates through all pages and extracts text content.
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}", exc_info=True)
        raise

def read_text_file(file_path: str) -> str:
    """
    Standard UTF-8 text file reader.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}", exc_info=True)
        raise

def file_to_text_factory(file_path: str) -> str:
    """
    DESIGN PATTERN: Factory Method
    
    This function dispatches the extraction task to the appropriate specialized 
    function based on the file extension. It provides a uniform interface for 
    the rest of the application to ingest various document types.
    """
    try:
        extension = os.path.splitext(file_path)[1].lower()
        
        # Routing logic based on file extension
        if extension in [".html", ".htm"]:
            return get_clean_text_from_html(file_path)
        elif extension == ".docx":
            return docx_to_text(file_path)
        elif extension == ".pdf":
            return pdf_to_text(file_path)
        elif extension == ".txt":
            return read_text_file(file_path)
        elif extension == ".doc":
            # Legacy .doc is NOT supported by python-docx
            logger.error(".doc files are not supported. Please convert to .docx first.")
            raise NotImplementedError(".doc files are not supported. Please convert to .docx first.")
        else:
            # Fallback for unknown extensions
            logger.warning(f"Unsupported file type '{extension}', attempting to read as plain text.")
            return read_text_file(file_path)
    except Exception as e:
        logger.error(f"Error in file_to_text_factory for {file_path}: {e}", exc_info=True)
        raise

