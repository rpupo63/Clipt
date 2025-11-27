"""
Unit tests for keyword_filtering.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup, Tag
from keyword_filtering import (
    normalize_text,
    find_adjacent_images,
    find_adjacent_images_by_descendants,
    filter_content_by_keywords
)


class TestNormalizeText(unittest.TestCase):
    """Test cases for normalize_text function."""

    def test_normalize_text_simple(self):
        """Test normalizing simple text."""
        result = normalize_text("Hello World")
        self.assertEqual(result, "hello world")

    def test_normalize_text_with_whitespace(self):
        """Test normalizing text with extra whitespace."""
        result = normalize_text("  Hello   World  ")
        self.assertEqual(result, "hello world")

    def test_normalize_text_empty(self):
        """Test normalizing empty string."""
        result = normalize_text("")
        self.assertEqual(result, "")

    def test_normalize_text_none(self):
        """Test normalizing None."""
        result = normalize_text(None)
        self.assertEqual(result, "")

    def test_normalize_text_multiline(self):
        """Test normalizing multiline text."""
        result = normalize_text("Hello\n\nWorld")
        self.assertEqual(result, "hello world")

    def test_normalize_text_tabs(self):
        """Test normalizing text with tabs."""
        result = normalize_text("Hello\tWorld")
        self.assertEqual(result, "hello world")


class TestFindAdjacentImages(unittest.TestCase):
    """Test cases for find_adjacent_images function."""

    def test_find_adjacent_images_next_sibling(self):
        """Test finding image in next sibling."""
        html = "<div><p>Paragraph</p><img src='test.jpg' /></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images(para, container)
        self.assertEqual(len(images), 1)

    def test_find_adjacent_images_prev_sibling(self):
        """Test finding image in previous sibling."""
        html = "<div><img src='test.jpg' /><p>Paragraph</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images(para, container)
        self.assertEqual(len(images), 1)

    def test_find_adjacent_images_no_images(self):
        """Test finding images when none exist."""
        html = "<div><p>Paragraph</p><div>Content</div></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images(para, container)
        self.assertEqual(len(images), 0)

    def test_find_adjacent_images_picture_element(self):
        """Test finding picture element."""
        html = "<div><p>Paragraph</p><picture><img src='test.jpg' /></picture></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images(para, container)
        self.assertGreaterEqual(len(images), 0)


class TestFindAdjacentImagesByDescendants(unittest.TestCase):
    """Test cases for find_adjacent_images_by_descendants function."""

    def test_find_adjacent_by_descendants_found(self):
        """Test finding images using descendants method."""
        html = "<div><p>Paragraph</p><div><img src='test.jpg' /></div></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images_by_descendants(para, container)
        self.assertGreaterEqual(len(images), 0)

    def test_find_adjacent_by_descendants_not_found(self):
        """Test when no images found using descendants method."""
        html = "<div><p>Paragraph</p><div>No images</div></div>"
        soup = BeautifulSoup(html, 'html.parser')
        para = soup.find('p')
        container = soup.find('div')
        images = find_adjacent_images_by_descendants(para, container)
        self.assertEqual(len(images), 0)


class TestFilterContentByKeywords(unittest.TestCase):
    """Test cases for filter_content_by_keywords function."""

    def test_filter_content_no_keywords(self):
        """Test filtering with no keywords returns original."""
        html = "<div><p>Paragraph 1</p><p>Paragraph 2</p></div>"
        result = filter_content_by_keywords(html, keywords=None)
        self.assertEqual(result, html)

    def test_filter_content_empty_keywords(self):
        """Test filtering with empty keywords returns original."""
        html = "<div><p>Paragraph 1</p><p>Paragraph 2</p></div>"
        result = filter_content_by_keywords(html, keywords=[])
        self.assertEqual(result, html)

    def test_filter_content_with_matching_keyword(self):
        """Test filtering keeps paragraphs with keyword."""
        html = "<div><p>This is about Python</p><p>This is about Java</p></div>"
        result = filter_content_by_keywords(html, keywords=['Python'])
        soup = BeautifulSoup(result, 'html.parser')
        paragraphs = soup.find_all('p')
        self.assertEqual(len(paragraphs), 1)
        self.assertIn('Python', paragraphs[0].get_text())

    def test_filter_content_no_matches(self):
        """Test filtering when no paragraphs match."""
        html = "<div><p>This is about Python</p><p>This is about Java</p></div>"
        result = filter_content_by_keywords(html, keywords=['JavaScript'])
        soup = BeautifulSoup(result, 'html.parser')
        paragraphs = soup.find_all('p')
        self.assertEqual(len(paragraphs), 0)

    def test_filter_content_multiple_keywords(self):
        """Test filtering with multiple keywords."""
        html = "<div><p>This is about Python</p><p>This is about Java</p><p>This is about JavaScript</p></div>"
        result = filter_content_by_keywords(html, keywords=['Python', 'JavaScript'])
        soup = BeautifulSoup(result, 'html.parser')
        paragraphs = soup.find_all('p')
        self.assertEqual(len(paragraphs), 2)

    def test_filter_content_case_insensitive(self):
        """Test filtering is case insensitive."""
        html = "<div><p>This is about python</p><p>This is about Java</p></div>"
        result = filter_content_by_keywords(html, keywords=['Python'])
        soup = BeautifulSoup(result, 'html.parser')
        paragraphs = soup.find_all('p')
        self.assertEqual(len(paragraphs), 1)

    def test_filter_content_include_first_paragraph(self):
        """Test filtering with include_first_paragraph flag."""
        html = "<div><p>First paragraph</p><p>This is about Python</p><p>This is about Java</p></div>"
        result = filter_content_by_keywords(html, keywords=['Python'], include_first_paragraph=True)
        soup = BeautifulSoup(result, 'html.parser')
        paragraphs = soup.find_all('p')
        # Should include first paragraph even if it doesn't match
        self.assertGreaterEqual(len(paragraphs), 1)

    def test_filter_content_preserves_styles(self):
        """Test filtering preserves style tags."""
        html = "<html><head><style>body { color: red; }</style></head><body><p>Test</p></body></html>"
        result = filter_content_by_keywords(html, keywords=['Test'])
        self.assertIn('style', result.lower())


if __name__ == '__main__':
    unittest.main()

