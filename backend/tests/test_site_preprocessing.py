"""
Unit tests for site_preprocessing.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from site_preprocessing import (
    download_ublock_extension,
    create_chrome_options,
    scrape_page
)


class TestDownloadUblockExtension(unittest.TestCase):
    """Test cases for download_ublock_extension function."""

    def test_download_ublock_extension(self):
        """Test downloading uBlock extension."""
        result = download_ublock_extension()
        # Function returns None in current implementation
        self.assertIsNone(result)


class TestCreateChromeOptions(unittest.TestCase):
    """Test cases for create_chrome_options function."""

    @patch('site_preprocessing.Path')
    def test_create_chrome_options(self, mock_path):
        """Test creating Chrome options."""
        # Mock path exists
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path_instance.is_symlink.return_value = False
        mock_path.return_value = mock_path_instance
        
        options = create_chrome_options()
        self.assertIsNotNone(options)
        from selenium.webdriver.chrome.options import Options
        self.assertIsInstance(options, Options)

    @patch('site_preprocessing.Path')
    def test_create_chrome_options_no_ublock(self, mock_path):
        """Test creating Chrome options when uBlock not found."""
        # Mock path doesn't exist
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance
        
        options = create_chrome_options()
        self.assertIsNotNone(options)


class TestScrapePage(unittest.TestCase):
    """Test cases for scrape_page function."""

    @patch('site_preprocessing.validate_url')
    @patch('site_preprocessing.create_chrome_options')
    @patch('site_preprocessing.chrome_driver_context')
    def test_scrape_page_success(self, mock_context, mock_options, mock_validate):
        """Test successful page scraping."""
        # Mock validation
        mock_validate.return_value = (True, None)
        
        # Mock Chrome options
        mock_chrome_options = MagicMock()
        mock_options.return_value = mock_chrome_options
        
        # Mock driver context
        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Content</body></html>"
        mock_context.return_value.__enter__.return_value = mock_driver
        
        result = scrape_page("https://example.com")
        self.assertIsNotNone(result)
        self.assertIn("Content", result)

    @patch('site_preprocessing.validate_url')
    def test_scrape_page_invalid_url(self, mock_validate):
        """Test scraping with invalid URL."""
        mock_validate.return_value = (False, "Invalid URL")
        
        with self.assertRaises(ValueError):
            scrape_page("http://localhost")

    @patch('site_preprocessing.validate_url')
    @patch('site_preprocessing.create_chrome_options')
    @patch('site_preprocessing.chrome_driver_context')
    def test_scrape_page_failure(self, mock_context, mock_options, mock_validate):
        """Test scraping when it fails."""
        # Mock validation
        mock_validate.return_value = (True, None)
        
        # Mock Chrome options
        mock_chrome_options = MagicMock()
        mock_options.return_value = mock_chrome_options
        
        # Mock driver context that raises exception
        mock_context.return_value.__enter__.side_effect = Exception("Scraping failed")
        
        result = scrape_page("https://example.com")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

