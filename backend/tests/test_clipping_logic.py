"""
Unit tests for clipping_logic.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from clipping_logic import (
    extract_css_styles,
    process_url_to_file,
    build_final_html,
    process_url_to_html
)


class TestExtractCssStyles(unittest.TestCase):
    """Test cases for extract_css_styles function."""

    def test_extract_css_styles_found(self):
        """Test extracting CSS styles from HTML."""
        html = '''
        <html>
            <head>
                <style>
                    body { color: red; }
                    .test { font-size: 14px; }
                </style>
            </head>
            <body>
                <div class="test">Content</div>
            </body>
        </html>
        '''
        extracted = '<div class="test">Content</div>'
        result = extract_css_styles(html, extracted)
        self.assertIn('body', result)
        self.assertIn('color: red', result)

    def test_extract_css_styles_no_styles(self):
        """Test extracting CSS when no styles present."""
        html = '<html><body><div>Content</div></body></html>'
        extracted = '<div>Content</div>'
        result = extract_css_styles(html, extracted)
        self.assertIsInstance(result, str)

    def test_extract_css_styles_error_handling(self):
        """Test error handling in CSS extraction."""
        # Invalid HTML should be handled gracefully
        html = "not valid html"
        extracted = "also not valid"
        result = extract_css_styles(html, extracted)
        self.assertIsInstance(result, str)


class TestProcessUrlToFile(unittest.TestCase):
    """Test cases for process_url_to_file function."""

    @patch('clipping_logic.site_preprocessing.scrape_page')
    @patch('clipping_logic.logo_extraction.extract_logo')
    @patch('clipping_logic.logo_extraction.get_root_domain')
    @patch('clipping_logic.header_extraction.extract_headers')
    @patch('clipping_logic.find_image_below_title')
    @patch('clipping_logic.find_first_and_last_sentences.find_first_and_last_sentences_from_url')
    @patch('clipping_logic.content_extraction.extract_main_content')
    @patch('clipping_logic.validate_subtitle_position')
    @patch('clipping_logic.download_image')
    @patch('clipping_logic.resize_image')
    @patch('clipping_logic.extract_image_info')
    def test_process_url_to_file_basic(self, mock_extract_img, mock_resize, mock_download,
                                        mock_validate, mock_extract_content, mock_sentences,
                                        mock_find_img, mock_headers, mock_get_domain, mock_logo, mock_scrape):
        """Test basic URL processing."""
        # Setup mocks
        mock_scrape.return_value = "<html><body></body></html>"
        mock_get_domain.return_value = "example.com"
        mock_logo.return_value = {'element': None, 'url': None}
        mock_headers.return_value = {
            'title': {'text': 'Test Title'},
            'subtitle': None
        }
        mock_find_img.return_value = None
        mock_sentences.return_value = {'success': False}
        mock_extract_content.return_value = "<div><p>Content</p></div>"
        mock_validate.return_value = {'is_valid': True}
        mock_download.return_value = (None, None, None)
        mock_resize.return_value = (b'data', 800, 600)
        mock_extract_img.return_value = {'url': None}
        
        result = process_url_to_file("https://example.com", use_ai_extraction=False)
        self.assertIn('title', result)
        self.assertIn('paragraphs', result)
        self.assertIn('images', result)
        self.assertEqual(result['title'], 'Test Title')


class TestBuildFinalHtml(unittest.TestCase):
    """Test cases for build_final_html function."""

    def test_build_final_html_basic(self):
        """Test building final HTML from content dict."""
        content_dict = {
            'title': 'Test Title',
            'subtitle': None,
            'logo': {'element': None},
            'paragraphs': [
                {'paragraph': '<p>Paragraph 1</p>', 'position': 1}
            ],
            'images': [],
            'css': ''
        }
        result = build_final_html(content_dict)
        self.assertIn('Test Title', result)
        self.assertIn('Paragraph 1', result)
        self.assertIn('<!DOCTYPE html>', result)

    def test_build_final_html_with_subtitle(self):
        """Test building HTML with subtitle."""
        content_dict = {
            'title': 'Test Title',
            'subtitle': 'Test Subtitle',
            'logo': {'element': None},
            'paragraphs': [],
            'images': [],
            'css': ''
        }
        result = build_final_html(content_dict)
        self.assertIn('Test Subtitle', result)

    def test_build_final_html_with_images(self):
        """Test building HTML with images."""
        content_dict = {
            'title': 'Test Title',
            'subtitle': None,
            'logo': {'element': None},
            'paragraphs': [
                {'paragraph': '<p>Paragraph 1</p>', 'position': 1}
            ],
            'images': [
                {'image': '<img src="test.jpg" />', 'position': 1.5}
            ],
            'css': ''
        }
        result = build_final_html(content_dict)
        self.assertIn('test.jpg', result)

    def test_build_final_html_with_logo(self):
        """Test building HTML with logo."""
        html = '<img src="/logo.png" alt="Logo" />'
        soup = BeautifulSoup(html, 'html.parser')
        logo_elem = soup.find('img')
        
        content_dict = {
            'title': 'Test Title',
            'subtitle': None,
            'logo': {'element': logo_elem, 'url': '/logo.png'},
            'paragraphs': [],
            'images': [],
            'css': ''
        }
        result = build_final_html(content_dict)
        self.assertIn('logo.png', result)


class TestProcessUrlToHtml(unittest.TestCase):
    """Test cases for process_url_to_html function."""

    @patch('clipping_logic.process_url_to_file')
    @patch('clipping_logic.build_final_html')
    def test_process_url_to_html(self, mock_build, mock_process):
        """Test processing URL to HTML."""
        mock_process.return_value = {
            'title': 'Test',
            'subtitle': None,
            'logo': {'element': None},
            'paragraphs': [],
            'images': [],
            'css': ''
        }
        mock_build.return_value = "<html><body>Test</body></html>"
        
        result = process_url_to_html("https://example.com")
        self.assertIn('Test', result)


if __name__ == '__main__':
    unittest.main()

