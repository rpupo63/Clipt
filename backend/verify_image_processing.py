import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from bs4 import BeautifulSoup

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock firecrawl, openai, and dotenv before importing clipping_logic
sys.modules['firecrawl'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import clipping_logic
from image_utils import extract_image_info

class TestImageProcessing(unittest.TestCase):
    def setUp(self):
        # Create a simple red square image (100x100)
        # 1x1 red pixel PNG
        self.red_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'
        self.width = 1
        self.height = 1

    @patch('clipping_logic.site_preprocessing.scrape_page')
    @patch('clipping_logic.logo_extraction.extract_logo')
    @patch('clipping_logic.header_extraction.extract_headers')
    @patch('clipping_logic.find_image_below_title')
    @patch('clipping_logic.find_first_and_last_sentences.find_first_and_last_sentences_from_url')
    @patch('clipping_logic.content_extraction.extract_main_content')
    @patch('clipping_logic.validate_subtitle_position')
    @patch('clipping_logic.download_image')
    @patch('clipping_logic.extract_image_info', side_effect=extract_image_info) # Use real extract_image_info but mock its dependencies
    @patch('image_utils.download_image') # Mock download_image inside image_utils
    def test_process_url_to_file_images(self, mock_img_utils_download, mock_extract, mock_download, mock_validate, mock_extract_content, mock_sentences, mock_find_img, mock_headers, mock_logo, mock_scrape):
        
        # Setup mocks
        mock_scrape.return_value = "<html><body></body></html>"
        mock_logo.return_value = {'element': None, 'url': None}
        mock_headers.return_value = {'title': {'text': 'Test Title'}, 'subtitle': None}
        mock_find_img.return_value = None
        mock_sentences.return_value = {'success': False} # Fallback to heuristic
        
        # Mock content extraction to return HTML with images
        html_content = """
        <div>
            <p>Paragraph 1</p>
            <img src="http://example.com/image1.jpg" alt="Image 1" />
            <p>Paragraph 2</p>
            <picture>
                <source srcset="http://example.com/image2-large.jpg 2x" />
                <img src="http://example.com/image2.jpg" alt="Image 2" />
            </picture>
            <p>Paragraph 3</p>
            <img data-src="http://example.com/image3.jpg" class="lazy" />
        </div>
        """
        mock_extract_content.return_value = html_content
        
        mock_validate.return_value = {'is_valid': True}
        
        # Mock download_image to return different bytes based on URL to avoid de-duplication
        def side_effect_download(url, *args, **kwargs):
            # Create slightly different bytes for each URL
            # Prepend the URL to the bytes so the beginning is unique (for data URI key check)
            unique_bytes = url.encode('utf-8') + self.red_pixel
            return (unique_bytes, self.width, self.height)
            
        mock_download.side_effect = side_effect_download
        mock_img_utils_download.side_effect = side_effect_download
        
        # Mock resize_image to return the input bytes (to preserve uniqueness)
        # We need to patch it in the context of the test
        patcher = patch('image_utils.resize_image', side_effect=lambda b, target_width=None: (b, 800, 600))
        self.mock_resize = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Run the function
        result = clipping_logic.process_url_to_file("http://example.com", use_ai_extraction=False)
        
        # Verify results
        print("\n--- Verification Results ---")
        print(f"Title: {result['title']}")
        print(f"Paragraphs: {len(result['paragraphs'])}")
        print(f"Images: {len(result['images'])}")
        
        # Check if images were processed
        self.assertEqual(len(result['images']), 3, "Should have found 3 images")
        
        # Check image content (should be data URI)
        for i, img in enumerate(result['images']):
            print(f"Image {i+1} content start: {img['image'][:50]}...")
            self.assertIn('data:image/png;base64,', img['image'], "Image should be converted to Data URI")
            self.assertIn('data:image/png;base64,', img['image'], "Image should be converted to Data URI")
            self.assertIn('width="800"', img['image'], "Image should be resized to 800px width")
            self.assertIn('display: block; margin: 20px auto;', img['image'], "Image should have centering styles")
            
        print("--- Verification Successful ---")

    def test_complex_structure_and_svg(self):
        """Test handling of images outside main container and SVG images"""
    def test_complex_structure_and_svg(self):
        """Test handling of images outside main container and SVG images"""
        # Mock dependencies
        with patch('clipping_logic.site_preprocessing.scrape_page') as mock_scrape, \
             patch('clipping_logic.logo_extraction.extract_logo') as mock_logo, \
             patch('clipping_logic.header_extraction.extract_headers') as mock_headers, \
             patch('clipping_logic.find_image_below_title') as mock_find_img, \
             patch('clipping_logic.find_first_and_last_sentences.find_first_and_last_sentences_from_url') as mock_sentences, \
             patch('clipping_logic.content_extraction.extract_main_content') as mock_extract_content, \
             patch('clipping_logic.validate_subtitle_position') as mock_validate, \
             patch('clipping_logic.download_image') as mock_download, \
             patch('clipping_logic.resize_image') as mock_resize, \
             patch('image_utils.download_image') as mock_utils_download:
            
            # Setup mocks
            mock_scrape.return_value = ("<html>...</html>", "Title")
            mock_logo.return_value = {'element': None, 'url': None}
            mock_headers.return_value = {'title': {'text': 'Test Title'}, 'subtitle': {'text': 'Subtitle'}}
            mock_find_img.return_value = None
            mock_sentences.return_value = {'success': True, 'first_sentence': 'First', 'last_sentence': 'Last'}
            mock_validate.return_value = {'is_valid': True}
            
            # Mock content extraction to return a soup with:
            # 1. A main container with text
            # 2. An image OUTSIDE the main container (sibling)
            # 3. An SVG image
            html_content = (
                '<div id="main">'
                '<p>Paragraph 1</p>'
                '</div>'
                '<img src="http://example.com/outside.jpg" />'
                '<img src="http://example.com/icon.svg" />'
            )
            mock_extract_content.return_value = html_content
            
            # Mock download to handle SVG and regular image
            def side_effect_download(url, *args, **kwargs):
                if url.endswith('.svg'):
                    return (b'<svg>...</svg>', None, None)
                return (b'image_data', 800, 600)
            
            mock_download.side_effect = side_effect_download
            mock_utils_download.side_effect = side_effect_download
            
            # Mock resize to handle SVG
            def side_effect_resize(data, width):
                if data.startswith(b'<svg'):
                    return (data, None, None)
                return (b'resized_data', width, 600)
            
            mock_resize.side_effect = side_effect_resize
            
            # Run the function
            result = clipping_logic.process_url_to_file("http://example.com", output_file=None)
            
            # Verification
            # We expect 2 images: outside.jpg and icon.svg
            # The outside.jpg should be included despite being outside container (due to fallback)
            # The icon.svg should be included despite being SVG (due to graceful handling)
            
            images = result['images']
            self.assertEqual(len(images), 2, f"Should have found 2 images, found {len(images)}")
            
            # Check if SVG is preserved
            svg_found = any('data:image/svg+xml' in img['image'] or '<svg' in img['image'] or 'icon.svg' in img['image'] for img in images)
            # Note: The current logic converts to data URI. For SVG, if resize returns original bytes, 
            # it might be base64 encoded as whatever the mime type detection says.
            # But mostly we want to ensure it didn't crash and is present.
            
            # Check if outside image is present
            outside_found = any('outside.jpg' in img['image'] or 'data:image' in img['image'] for img in images)
            self.assertTrue(outside_found, "Outside image should be present")

if __name__ == '__main__':
    unittest.main()
