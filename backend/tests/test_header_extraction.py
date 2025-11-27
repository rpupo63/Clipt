"""
Unit tests for header_extraction.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from header_extraction import (
    extract_headers,
    extract_headers_from_file
)


class TestExtractHeaders(unittest.TestCase):
    """Test cases for extract_headers function."""

    def test_extract_headers_h1_title(self):
        """Test extracting title from h1 tag."""
        html = '<html><body><article><h1>Article Title</h1></article></body></html>'
        result = extract_headers(html)
        self.assertIsNotNone(result.get('title'))
        self.assertEqual(result['title']['text'], "Article Title")

    def test_extract_headers_meta_title(self):
        """Test extracting title from meta tag."""
        html = '''
        <html>
            <head>
                <meta property="og:title" content="Meta Title" />
            </head>
            <body></body>
        </html>
        '''
        result = extract_headers(html)
        self.assertIsNotNone(result.get('title'))
        self.assertEqual(result['title']['text'], "Meta Title")

    def test_extract_headers_json_ld_title(self):
        """Test extracting title from JSON-LD."""
        html = '''
        <html>
            <head>
                <script type="application/ld+json">
                {"@type": "Article", "headline": "JSON-LD Title"}
                </script>
            </head>
            <body></body>
        </html>
        '''
        result = extract_headers(html)
        self.assertIsNotNone(result.get('title'))
        self.assertEqual(result['title']['text'], "JSON-LD Title")

    def test_extract_headers_subtitle(self):
        """Test extracting subtitle."""
        html = '''
        <html>
            <body>
                <article>
                    <h1>Title</h1>
                    <p class="subtitle">This is a subtitle</p>
                </article>
            </body>
        </html>
        '''
        result = extract_headers(html)
        self.assertIsNotNone(result.get('subtitle'))
        self.assertIn("subtitle", result['subtitle']['text'].lower())

    def test_extract_headers_meta_subtitle(self):
        """Test extracting subtitle from meta description."""
        html = '''
        <html>
            <head>
                <meta property="og:description" content="Meta subtitle" />
            </head>
            <body></body>
        </html>
        '''
        result = extract_headers(html)
        self.assertIsNotNone(result.get('subtitle'))
        self.assertEqual(result['subtitle']['text'], "Meta subtitle")

    def test_extract_headers_no_title(self):
        """Test when no title found."""
        html = '<html><body><p>No title</p></body></html>'
        result = extract_headers(html)
        # May return None or empty structure
        self.assertIsInstance(result, dict)

    def test_extract_headers_invalid_html(self):
        """Test with invalid HTML."""
        html = "not valid html"
        result = extract_headers(html)
        # Should handle gracefully
        self.assertIsInstance(result, dict)


class TestExtractHeadersFromFile(unittest.TestCase):
    """Test cases for extract_headers_from_file function."""

    def test_extract_headers_from_file(self):
        """Test extracting headers from file."""
        import tempfile
        html = '<html><body><h1>Title</h1></body></html>'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = extract_headers_from_file(temp_path)
            self.assertIsNotNone(result)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_extract_headers_from_file_not_found(self):
        """Test extracting headers from non-existent file."""
        result = extract_headers_from_file("/nonexistent/file.html")
        # Should return empty structure
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()

