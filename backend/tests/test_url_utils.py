"""
Unit tests for url_utils.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from url_utils import normalize_image_url, validate_url, is_valid_http_url


class TestNormalizeImageUrl(unittest.TestCase):
    """Test cases for normalize_image_url function."""

    def test_normalize_with_query_params(self):
        """Test normalizing URL with query parameters."""
        url = "https://example.com/img.jpg?size=large&quality=high"
        normalized = normalize_image_url(url)
        self.assertEqual(normalized, "https://example.com/img.jpg")

    def test_normalize_with_fragment(self):
        """Test normalizing URL with fragment."""
        url = "https://example.com/img.jpg#top"
        normalized = normalize_image_url(url)
        self.assertEqual(normalized, "https://example.com/img.jpg")

    def test_normalize_with_query_and_fragment(self):
        """Test normalizing URL with both query and fragment."""
        url = "https://example.com/img.jpg?size=large#top"
        normalized = normalize_image_url(url)
        self.assertEqual(normalized, "https://example.com/img.jpg")

    def test_normalize_already_normalized(self):
        """Test normalizing already normalized URL."""
        url = "https://example.com/img.jpg"
        normalized = normalize_image_url(url)
        self.assertEqual(normalized, url)

    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        result = normalize_image_url("")
        self.assertEqual(result, "")

    def test_normalize_none(self):
        """Test normalizing None."""
        result = normalize_image_url(None)
        self.assertIsNone(result)

    def test_normalize_invalid_url(self):
        """Test normalizing invalid URL returns original."""
        url = "not-a-valid-url"
        result = normalize_image_url(url)
        self.assertEqual(result, url)


class TestValidateUrl(unittest.TestCase):
    """Test cases for validate_url function."""

    def test_validate_valid_https_url(self):
        """Test validating valid HTTPS URL."""
        is_valid, error = validate_url("https://example.com")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_valid_http_url(self):
        """Test validating valid HTTP URL."""
        is_valid, error = validate_url("http://example.com")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_invalid_scheme(self):
        """Test validating URL with invalid scheme."""
        is_valid, error = validate_url("ftp://example.com")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("scheme", error.lower())

    def test_validate_file_scheme(self):
        """Test validating file:// scheme is rejected."""
        is_valid, error = validate_url("file:///etc/passwd")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_localhost(self):
        """Test validating localhost is blocked."""
        is_valid, error = validate_url("http://localhost/admin")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("localhost", error.lower())

    def test_validate_127_0_0_1(self):
        """Test validating 127.0.0.1 is blocked."""
        is_valid, error = validate_url("http://127.0.0.1/admin")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_missing_hostname(self):
        """Test validating URL with missing hostname."""
        is_valid, error = validate_url("http://")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("hostname", error.lower())

    def test_validate_private_ip(self):
        """Test validating private IP is blocked."""
        is_valid, error = validate_url("http://192.168.1.1")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_private_ip_allowed(self):
        """Test validating private IP when allowed."""
        is_valid, error = validate_url("http://192.168.1.1", allow_private=True)
        # Should pass when explicitly allowed
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_invalid_url_format(self):
        """Test validating invalid URL format."""
        is_valid, error = validate_url("not a url")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class TestIsValidHttpUrl(unittest.TestCase):
    """Test cases for is_valid_http_url function."""

    def test_is_valid_https(self):
        """Test HTTPS URL is valid."""
        self.assertTrue(is_valid_http_url("https://example.com"))

    def test_is_valid_http(self):
        """Test HTTP URL is valid."""
        self.assertTrue(is_valid_http_url("http://example.com"))

    def test_is_invalid_ftp(self):
        """Test FTP URL is invalid."""
        self.assertFalse(is_valid_http_url("ftp://example.com"))

    def test_is_invalid_file(self):
        """Test file:// URL is invalid."""
        self.assertFalse(is_valid_http_url("file:///path"))

    def test_is_invalid_missing_netloc(self):
        """Test URL without netloc is invalid."""
        self.assertFalse(is_valid_http_url("http://"))

    def test_is_invalid_not_url(self):
        """Test non-URL string is invalid."""
        self.assertFalse(is_valid_http_url("not a url"))

    def test_is_invalid_empty(self):
        """Test empty string is invalid."""
        self.assertFalse(is_valid_http_url(""))


if __name__ == '__main__':
    unittest.main()

