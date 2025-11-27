"""
Unit tests for output_generation.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from output_generation import (
    html_to_docx,
    html_to_pdf,
    html_to_markdown,
    convert_html
)


class TestHtmlToDocx(unittest.TestCase):
    """Test cases for html_to_docx function."""

    @patch('output_generation.DOCX_AVAILABLE', True)
    @patch('output_generation.HTMKDOCX_AVAILABLE', True)
    @patch('output_generation._process_images_in_html')
    @patch('output_generation.DocxDocument')
    @patch('output_generation.HtmlToDocx')
    def test_html_to_docx_success(self, mock_htmldocx_class, mock_docx_class, mock_process):
        """Test successful HTML to DOCX conversion."""
        mock_process.return_value = "<html><body><p>Test</p></body></html>"
        mock_doc = MagicMock()
        mock_docx_class.return_value = mock_doc
        mock_parser = MagicMock()
        mock_htmldocx_class.return_value = mock_parser
        
        # Mock save to BytesIO
        from io import BytesIO
        mock_buffer = BytesIO()
        mock_doc.save = MagicMock(side_effect=lambda buf: buf.write(b'docx content'))
        
        result = html_to_docx("<html><body><p>Test</p></body></html>")
        self.assertIsInstance(result, bytes)

    @patch('output_generation.DOCX_AVAILABLE', False)
    def test_html_to_docx_not_available(self):
        """Test when DOCX libraries are not available."""
        with self.assertRaises(ImportError):
            html_to_docx("<html><body></body></html>")


class TestHtmlToPdf(unittest.TestCase):
    """Test cases for html_to_pdf function."""

    @patch('output_generation.PDF_AVAILABLE', True)
    @patch('output_generation._process_images_in_html')
    @patch('output_generation.HTML')
    def test_html_to_pdf_success(self, mock_html_class, mock_process):
        """Test successful HTML to PDF conversion."""
        mock_process.return_value = "<html><body><p>Test</p></body></html>"
        mock_html = MagicMock()
        mock_html.write_pdf.return_value = b'pdf content'
        mock_html_class.return_value = mock_html
        
        result = html_to_pdf("<html><body><p>Test</p></body></html>")
        self.assertIsInstance(result, bytes)

    @patch('output_generation.PDF_AVAILABLE', False)
    def test_html_to_pdf_not_available(self):
        """Test when PDF library is not available."""
        with self.assertRaises(ImportError):
            html_to_pdf("<html><body></body></html>")


class TestHtmlToMarkdown(unittest.TestCase):
    """Test cases for html_to_markdown function."""

    @patch('output_generation.MARKDOWN_AVAILABLE', True)
    @patch('output_generation._process_images_in_html')
    @patch('output_generation.markdownify')
    def test_html_to_markdown_success(self, mock_markdownify, mock_process):
        """Test successful HTML to Markdown conversion."""
        mock_process.return_value = "<html><body><p>Test</p></body></html>"
        mock_markdownify.markdownify.return_value = "Test"
        
        result = html_to_markdown("<html><body><p>Test</p></body></html>")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Test")

    @patch('output_generation.MARKDOWN_AVAILABLE', False)
    def test_html_to_markdown_not_available(self):
        """Test when Markdown library is not available."""
        with self.assertRaises(ImportError):
            html_to_markdown("<html><body></body></html>")


class TestConvertHtml(unittest.TestCase):
    """Test cases for convert_html function."""

    @patch('output_generation.html_to_docx')
    def test_convert_html_to_docx(self, mock_docx):
        """Test converting HTML to DOCX."""
        mock_docx.return_value = b'docx content'
        result = convert_html("<html></html>", "docx")
        self.assertEqual(result, b'docx content')

    @patch('output_generation.html_to_pdf')
    def test_convert_html_to_pdf(self, mock_pdf):
        """Test converting HTML to PDF."""
        mock_pdf.return_value = b'pdf content'
        result = convert_html("<html></html>", "pdf")
        self.assertEqual(result, b'pdf content')

    @patch('output_generation.html_to_markdown')
    def test_convert_html_to_markdown(self, mock_md):
        """Test converting HTML to Markdown."""
        mock_md.return_value = "markdown content"
        result = convert_html("<html></html>", "md")
        self.assertEqual(result, "markdown content")

    def test_convert_html_invalid_format(self):
        """Test converting with invalid format."""
        with self.assertRaises(ValueError):
            convert_html("<html></html>", "invalid")


if __name__ == '__main__':
    unittest.main()

