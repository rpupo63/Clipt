"""
Unit tests for image_utils.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from image_utils import (
    parse_srcset,
    get_best_image_from_srcset,
    download_image,
    get_actual_image_dimensions,
    extract_image_info,
    resize_image
)


class TestParseSrcset(unittest.TestCase):
    """Test cases for parse_srcset function."""

    def test_parse_srcset_width_descriptor(self):
        """Test parsing srcset with width descriptor."""
        srcset = "image1.jpg 1920w, image2.jpg 1280w"
        result = parse_srcset(srcset)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "image1.jpg")
        self.assertEqual(result[0][1], 1920.0)

    def test_parse_srcset_density_descriptor(self):
        """Test parsing srcset with density descriptor."""
        srcset = "image1.jpg 1x, image2.jpg 2x"
        result = parse_srcset(srcset)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "image2.jpg")  # Higher density first
        self.assertEqual(result[0][1], 2.0)

    def test_parse_srcset_no_descriptor(self):
        """Test parsing srcset without descriptor."""
        srcset = "image1.jpg"
        result = parse_srcset(srcset)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], 1.0)  # Default density

    def test_parse_srcset_empty(self):
        """Test parsing empty srcset."""
        result = parse_srcset("")
        self.assertEqual(len(result), 0)

    def test_parse_srcset_sorted(self):
        """Test that results are sorted by descriptor (highest first)."""
        srcset = "image1.jpg 1x, image2.jpg 2x, image3.jpg 3x"
        result = parse_srcset(srcset)
        self.assertEqual(result[0][1], 3.0)
        self.assertEqual(result[1][1], 2.0)
        self.assertEqual(result[2][1], 1.0)


class TestGetBestImageFromSrcset(unittest.TestCase):
    """Test cases for get_best_image_from_srcset function."""

    def test_get_best_image_highest_quality(self):
        """Test getting highest quality image from srcset."""
        srcset = "image1.jpg 1x, image2.jpg 2x"
        result = get_best_image_from_srcset(srcset)
        self.assertEqual(result, "image2.jpg")

    def test_get_best_image_with_base_url(self):
        """Test getting best image with base URL."""
        srcset = "image1.jpg 1x, image2.jpg 2x"
        result = get_best_image_from_srcset(srcset, base_url="https://example.com")
        self.assertEqual(result, "https://example.com/image2.jpg")

    def test_get_best_image_absolute_url(self):
        """Test getting best image when URL is already absolute."""
        srcset = "https://example.com/image1.jpg 1x, https://example.com/image2.jpg 2x"
        result = get_best_image_from_srcset(srcset)
        self.assertEqual(result, "https://example.com/image2.jpg")

    def test_get_best_image_empty(self):
        """Test getting best image from empty srcset."""
        result = get_best_image_from_srcset("")
        self.assertIsNone(result)


class TestDownloadImage(unittest.TestCase):
    """Test cases for download_image function."""

    @patch('image_utils.download_with_size_limit')
    @patch('image_utils.PIL_AVAILABLE', True)
    @patch('PIL.Image.open')
    def test_download_image_success(self, mock_image_open, mock_download):
        """Test successful image download."""
        # Mock image bytes
        image_bytes = b'fake image data'
        mock_download.return_value = image_bytes
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (100, 200)
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        bytes_result, width, height = download_image("http://example.com/image.jpg")
        self.assertEqual(bytes_result, image_bytes)
        self.assertEqual(width, 100)
        self.assertEqual(height, 200)

    @patch('image_utils.download_with_size_limit')
    def test_download_image_failure(self, mock_download):
        """Test image download failure."""
        mock_download.side_effect = Exception("Download failed")
        bytes_result, width, height = download_image("http://example.com/image.jpg")
        self.assertIsNone(bytes_result)
        self.assertIsNone(width)
        self.assertIsNone(height)

    @patch('image_utils.download_with_size_limit')
    def test_download_image_empty_url(self, mock_download):
        """Test downloading with empty URL."""
        bytes_result, width, height = download_image("")
        self.assertIsNone(bytes_result)
        self.assertIsNone(width)
        self.assertIsNone(height)


class TestGetActualImageDimensions(unittest.TestCase):
    """Test cases for get_actual_image_dimensions function."""

    @patch('image_utils.download_image')
    def test_get_actual_image_dimensions(self, mock_download):
        """Test getting actual image dimensions."""
        mock_download.return_value = (b'data', 100, 200)
        width, height = get_actual_image_dimensions("http://example.com/image.jpg")
        self.assertEqual(width, 100)
        self.assertEqual(height, 200)


class TestExtractImageInfo(unittest.TestCase):
    """Test cases for extract_image_info function."""

    def test_extract_image_info_simple_img(self):
        """Test extracting info from simple img tag."""
        html = '<img src="http://example.com/image.jpg" alt="Test" width="100" height="200" />'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        
        with patch('image_utils.download_image') as mock_download:
            mock_download.return_value = (None, 100, 200)
            result = extract_image_info(img, base_url="http://example.com")
            
            self.assertEqual(result['src'], "http://example.com/image.jpg")
            self.assertEqual(result['alt'], "Test")
            self.assertEqual(result['width'], 100)
            self.assertEqual(result['height'], 200)
            self.assertEqual(result['type'], 'img')

    def test_extract_image_info_with_srcset(self):
        """Test extracting info from img with srcset."""
        html = '<img srcset="image1.jpg 1x, image2.jpg 2x" src="image1.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        
        with patch('image_utils.get_best_image_from_srcset') as mock_best:
            mock_best.return_value = "http://example.com/image2.jpg"
            with patch('image_utils.download_image') as mock_download:
                mock_download.return_value = (None, None, None)
                result = extract_image_info(img, base_url="http://example.com")
                self.assertIsNotNone(result['url'])

    def test_extract_image_info_picture_element(self):
        """Test extracting info from picture element."""
        html = '<picture><source srcset="image1.jpg 2x" /><img src="image1.jpg" /></picture>'
        soup = BeautifulSoup(html, 'html.parser')
        picture = soup.find('picture')
        
        with patch('image_utils.parse_srcset') as mock_parse:
            mock_parse.return_value = [("image1.jpg", 2.0)]
            with patch('image_utils.download_image') as mock_download:
                mock_download.return_value = (None, None, None)
                result = extract_image_info(picture, base_url="http://example.com")
                self.assertEqual(result['type'], 'picture')

    def test_extract_image_info_none(self):
        """Test extracting info from None element."""
        result = extract_image_info(None)
        self.assertIsNone(result['element'])
        self.assertIsNone(result['url'])


class TestResizeImage(unittest.TestCase):
    """Test cases for resize_image function."""

    @patch('image_utils.PIL_AVAILABLE', True)
    @patch('PIL.Image.open')
    def test_resize_image_with_pil(self, mock_image_open):
        """Test resizing image with PIL available."""
        # Create mock image
        mock_img = MagicMock()
        mock_img.size = (1600, 1200)
        mock_img.format = 'PNG'
        
        # Mock resize
        mock_resized = MagicMock()
        mock_resized.size = (800, 600)
        mock_img.resize.return_value = mock_resized
        
        mock_image_open.return_value = mock_img
        
        # Mock BytesIO for output
        output = BytesIO()
        mock_resized.save = MagicMock()
        
        with patch('io.BytesIO', return_value=output):
            result_bytes, width, height = resize_image(b'fake data', target_width=800)
            self.assertEqual(width, 800)
            self.assertEqual(height, 600)

    @patch('image_utils.PIL_AVAILABLE', False)
    @patch('image_utils._get_dimensions_from_headers')
    def test_resize_image_without_pil(self, mock_get_dims):
        """Test resizing image without PIL (fallback)."""
        mock_get_dims.return_value = (100, 200)
        result_bytes, width, height = resize_image(b'fake data', target_width=800)
        # Should return original bytes
        self.assertEqual(result_bytes, b'fake data')
        self.assertEqual(width, 100)
        self.assertEqual(height, 200)


if __name__ == '__main__':
    unittest.main()

