"""
Unit tests for image_positioning.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from image_positioning import (
    is_image_element,
    get_image_container,
    find_nearest_image_below,
    find_image_below_title
)


class TestIsImageElement(unittest.TestCase):
    """Test cases for is_image_element function."""

    def test_is_image_element_img_tag(self):
        """Test img tag is image element."""
        html = '<img src="test.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        self.assertTrue(is_image_element(img))

    def test_is_image_element_picture_tag(self):
        """Test picture tag is image element."""
        html = '<picture><img src="test.jpg" /></picture>'
        soup = BeautifulSoup(html, 'html.parser')
        picture = soup.find('picture')
        self.assertTrue(is_image_element(picture))

    def test_is_image_element_figure_with_img(self):
        """Test figure with img is image element."""
        html = '<figure><img src="test.jpg" /></figure>'
        soup = BeautifulSoup(html, 'html.parser')
        figure = soup.find('figure')
        self.assertTrue(is_image_element(figure))

    def test_is_image_element_not_image(self):
        """Test non-image element is not image element."""
        html = '<p>Not an image</p>'
        soup = BeautifulSoup(html, 'html.parser')
        p = soup.find('p')
        self.assertFalse(is_image_element(p))

    def test_is_image_element_none(self):
        """Test None is not image element."""
        self.assertFalse(is_image_element(None))


class TestGetImageContainer(unittest.TestCase):
    """Test cases for get_image_container function."""

    def test_get_image_container_figure(self):
        """Test getting figure as container."""
        html = '<figure><img src="test.jpg" /></figure>'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        container = get_image_container(img)
        self.assertEqual(container.name, 'figure')

    def test_get_image_container_picture(self):
        """Test getting picture as container."""
        html = '<picture><img src="test.jpg" /></picture>'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        container = get_image_container(img)
        self.assertEqual(container.name, 'picture')

    def test_get_image_container_img_itself(self):
        """Test getting img itself when no container."""
        html = '<img src="test.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img')
        container = get_image_container(img)
        self.assertEqual(container, img)

    def test_get_image_container_none(self):
        """Test getting container for None."""
        container = get_image_container(None)
        self.assertIsNone(container)


class TestFindNearestImageBelow(unittest.TestCase):
    """Test cases for find_nearest_image_below function."""

    def test_find_nearest_image_below_next_sibling(self):
        """Test finding image in next sibling."""
        html = '<div><p>Paragraph</p><img src="test.jpg" /></div>'
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        img = find_nearest_image_below(para, soup, max_distance=5)
        self.assertIsNotNone(img)

    def test_find_nearest_image_below_parent_sibling(self):
        """Test finding image in parent's next sibling."""
        html = '<div><p>Paragraph</p></div><div><img src="test.jpg" /></div>'
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        img = find_nearest_image_below(para, soup, max_distance=5)
        self.assertIsNotNone(img)

    def test_find_nearest_image_below_not_found(self):
        """Test when no image found."""
        html = '<div><p>Paragraph</p><p>More text</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        img = find_nearest_image_below(para, soup, max_distance=5)
        self.assertIsNone(img)

    def test_find_nearest_image_below_none_paragraph(self):
        """Test with None paragraph."""
        soup = BeautifulSoup('<div></div>', 'html.parser')
        img = find_nearest_image_below(None, soup, max_distance=5)
        self.assertIsNone(img)


class TestFindImageBelowTitle(unittest.TestCase):
    """Test cases for find_image_below_title function."""

    def test_find_image_below_title_found(self):
        """Test finding image below title."""
        html = '<html><body><h1>Title</h1><img src="test.jpg" /></body></html>'
        headers = {
            'title': {
                'element': BeautifulSoup(html, 'html.parser').find('h1')
            }
        }
        
        with patch('image_positioning.find_nearest_image_below') as mock_find:
            mock_find.return_value = BeautifulSoup(html, 'html.parser').find('img')
            with patch('image_positioning._extract_image_info') as mock_extract:
                mock_extract.return_value = {'url': 'http://example.com/test.jpg'}
                result = find_image_below_title(html, headers)
                self.assertIsNotNone(result)

    def test_find_image_below_title_no_title(self):
        """Test when no title in headers."""
        html = '<html><body></body></html>'
        headers = {}
        result = find_image_below_title(html, headers)
        self.assertIsNone(result)

    def test_find_image_below_title_no_title_element(self):
        """Test when title has no element."""
        html = '<html><body></body></html>'
        headers = {'title': {'element': None}}
        result = find_image_below_title(html, headers)
        self.assertIsNone(result)

    def test_find_image_below_title_no_image(self):
        """Test when no image found below title."""
        html = '<html><body><h1>Title</h1><p>Text</p></body></html>'
        headers = {
            'title': {
                'element': BeautifulSoup(html, 'html.parser').find('h1')
            }
        }
        
        with patch('image_positioning.find_nearest_image_below') as mock_find:
            mock_find.return_value = None
            result = find_image_below_title(html, headers)
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

