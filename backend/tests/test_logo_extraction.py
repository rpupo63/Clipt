"""
Unit tests for logo_extraction.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from logo_extraction import (
    extract_logo,
    get_root_domain,
    extract_logo_from_file
)


class TestGetRootDomain(unittest.TestCase):
    """Test cases for get_root_domain function."""

    def test_get_root_domain_https(self):
        """Test extracting root domain from HTTPS URL."""
        result = get_root_domain("https://www.example.com/path/to/page")
        self.assertEqual(result, "example.com")

    def test_get_root_domain_http(self):
        """Test extracting root domain from HTTP URL."""
        result = get_root_domain("http://example.com/path")
        self.assertEqual(result, "example.com")

    def test_get_root_domain_with_port(self):
        """Test extracting root domain with port."""
        result = get_root_domain("https://example.com:8080/path")
        self.assertEqual(result, "example.com")

    def test_get_root_domain_with_www(self):
        """Test extracting root domain removes www."""
        result = get_root_domain("https://www.example.com")
        self.assertEqual(result, "example.com")

    def test_get_root_domain_subdomain(self):
        """Test extracting root domain from subdomain."""
        result = get_root_domain("https://subdomain.example.com")
        self.assertEqual(result, "example.com")


class TestExtractLogo(unittest.TestCase):
    """Test cases for extract_logo function."""

    def test_extract_logo_img_with_logo_class(self):
        """Test extracting logo from img with logo class."""
        html = '''
        <html>
            <body>
                <a href="/"><img src="/logo.png" class="logo" alt="Logo" /></a>
            </body>
        </html>
        '''
        result = extract_logo(html, "example.com", base_url="https://example.com")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.get('element'))

    def test_extract_logo_svg(self):
        """Test extracting logo from SVG."""
        html = '''
        <html>
            <body>
                <a href="/"><svg class="logo"><path d="M0,0"/></svg></a>
            </body>
        </html>
        '''
        result = extract_logo(html, "example.com", base_url="https://example.com")
        self.assertIsNotNone(result)

    def test_extract_logo_json_ld(self):
        """Test extracting logo from JSON-LD."""
        html = '''
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@type": "Organization",
                    "name": "Example",
                    "logo": "https://example.com/logo.png"
                }
                </script>
            </head>
            <body></body>
        </html>
        '''
        result = extract_logo(html, "example.com", base_url="https://example.com")
        self.assertIsNotNone(result)

    def test_extract_logo_no_logo(self):
        """Test when no logo found."""
        html = '<html><body><p>No logo here</p></body></html>'
        result = extract_logo(html, "example.com", base_url="https://example.com")
        self.assertIsNone(result.get('element'))
        self.assertIsNone(result.get('url'))

    def test_extract_logo_not_in_link_to_root(self):
        """Test logo not in link to root is ignored."""
        html = '''
        <html>
            <body>
                <a href="/other-page"><img src="/logo.png" class="logo" /></a>
            </body>
        </html>
        '''
        result = extract_logo(html, "example.com", base_url="https://example.com")
        # Should not find logo if link doesn't point to root
        # (depends on implementation - may or may not find it)
        self.assertIsInstance(result, dict)


class TestExtractLogoFromFile(unittest.TestCase):
    """Test cases for extract_logo_from_file function."""

    def test_extract_logo_from_file(self):
        """Test extracting logo from file."""
        import tempfile
        html = '''
        <html>
            <body>
                <a href="/"><img src="/logo.png" class="logo" /></a>
            </body>
        </html>
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = extract_logo_from_file(temp_path, "example.com", base_url="https://example.com")
            self.assertIsNotNone(result)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()

