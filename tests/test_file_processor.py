import pytest
from unittest.mock import patch, MagicMock
from src.utils.FileProcessor import (
    TextStripper,
    get_clean_text_from_html,
    docx_to_text,
    pdf_to_text,
    read_text_file,
    file_to_text_factory
)

def test_text_stripper():
    stripper = TextStripper()
    stripper.feed("<html><body><p>Hello World</p></body></html>")
    assert stripper.get_data() == "Hello World"

@patch("builtins.open")
def test_get_clean_text_from_html(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = "<html><body>Test Content</body></html>"
    result = get_clean_text_from_html("test.html")
    assert result == "Test Content"
    mock_open.assert_called_once_with("test.html", "r", encoding="utf-8", errors="replace")

@patch("docx.Document")
def test_docx_to_text(mock_docx):
    mock_doc = MagicMock()
    mock_para1 = MagicMock()
    mock_para1.text = "Hello "
    mock_para2 = MagicMock()
    mock_para2.text = "World"
    mock_doc.paragraphs = [mock_para1, mock_para2]
    mock_docx.return_value = mock_doc
    
    result = docx_to_text("test.docx")
    assert result == "Hello World"
    mock_docx.assert_called_once_with("test.docx")

@patch("src.utils.FileProcessor.PdfReader")
def test_pdf_to_text(mock_pdf_reader):
    mock_reader = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 "
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2"
    mock_reader.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader
    
    result = pdf_to_text("test.pdf")
    assert result == "Page 1 Page 2"
    mock_pdf_reader.assert_called_once_with("test.pdf")

@patch("builtins.open")
def test_read_text_file(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = "Text file content"
    result = read_text_file("test.txt")
    assert result == "Text file content"
    mock_open.assert_called_once_with("test.txt", "r", encoding="utf-8")

@patch("src.utils.FileProcessor.get_clean_text_from_html")
@patch("src.utils.FileProcessor.docx_to_text")
@patch("src.utils.FileProcessor.pdf_to_text")
@patch("src.utils.FileProcessor.read_text_file")
def test_file_to_text_factory(mock_read_txt, mock_pdf, mock_docx, mock_html):
    mock_html.return_value = "html content"
    mock_docx.return_value = "docx content"
    mock_pdf.return_value = "pdf content"
    mock_read_txt.return_value = "text content"
    
    assert file_to_text_factory("test.html") == "html content"
    assert file_to_text_factory("test.htm") == "html content"
    assert file_to_text_factory("test.docx") == "docx content"
    assert file_to_text_factory("test.pdf") == "pdf content"
    assert file_to_text_factory("test.txt") == "text content"
    assert file_to_text_factory("test.unknown") == "text content"
    
    with pytest.raises(NotImplementedError):
        file_to_text_factory("test.doc")
