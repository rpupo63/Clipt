
import sys
import os
from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from image_utils import process_and_format_image, resize_image

class TestImageUtils(unittest.TestCase):
    def setUp(self):
        # Create a simple red square image (100x100)
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color = 'red')
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            self.test_image_bytes = img_byte_arr.getvalue()
            self.pil_available = True
        except ImportError:
            self.test_image_bytes = b'fake_image_bytes'
            self.pil_available = False

    def test_process_and_format_image(self):
        print("\nTesting process_and_format_image...")
        
        if not self.pil_available:
            print("PIL not available, skipping full test")
            return

        # Test with provided bytes
        result = process_and_format_image(
            url="http://example.com/test.png",
            image_bytes=self.test_image_bytes,
            target_width=50
        )
        
        print(f"Result success: {result['success']}")
        print(f"Result width: {result['width']}")
        print(f"Result height: {result['height']}")
        print(f"Result HTML: {result['html']}")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['width'], 50)
        self.assertEqual(result['height'], 50) # Square image
        
        # Check for inline styles
        expected_style = 'display: block; margin: 20px auto; max-width: 100%; height: auto;'
        self.assertIn(expected_style, result['html'])
        self.assertIn('width="50"', result['html'])
        self.assertIn('height="50"', result['html'])
        self.assertIn('data:image/png;base64,', result['html'])
        
        print("SUCCESS: Image processed and formatted correctly with styles")

    @patch('image_utils.download_image')
    def test_process_and_format_image_download(self, mock_download):
        print("\nTesting process_and_format_image with download...")
        
        if not self.pil_available:
            return

        # Mock download
        mock_download.return_value = (self.test_image_bytes, 100, 100)
        
        result = process_and_format_image(
            url="http://example.com/download.png",
            target_width=50
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['width'], 50)
        self.assertIn('display: block; margin: 20px auto;', result['html'])
        
        print("SUCCESS: Image downloaded and processed correctly")

if __name__ == "__main__":
    unittest.main()
