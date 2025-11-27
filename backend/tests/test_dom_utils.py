"""
Unit tests for dom_utils.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from dom_utils import (
    get_all_elements_in_order,
    get_element_position,
    find_first_paragraph_in_extracted_content,
    find_matching_paragraph_in_original
)


class TestGetAllElementsInOrder(unittest.TestCase):
    """Test cases for get_all_elements_in_order function."""

    def test_get_all_elements_simple(self):
        """Test getting all elements from simple HTML."""
        html = "<html><body><p>Test</p><div>Content</div></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        elements = get_all_elements_in_order(soup)
        self.assertGreater(len(elements), 0)
        self.assertIn(soup.find('p'), elements)
        self.assertIn(soup.find('div'), elements)

    def test_get_all_elements_empty(self):
        """Test getting elements from empty HTML."""
        html = "<html></html>"
        soup = BeautifulSoup(html, 'html.parser')
        elements = get_all_elements_in_order(soup)
        self.assertIsInstance(elements, list)

    def test_get_all_elements_nested(self):
        """Test getting elements from nested HTML."""
        html = "<div><p><span>Nested</span></p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        elements = get_all_elements_in_order(soup)
        self.assertIn(soup.find('span'), elements)


class TestGetElementPosition(unittest.TestCase):
    """Test cases for get_element_position function."""

    def test_get_element_position_found(self):
        """Test getting position of element that exists."""
        html = "<html><body><p>First</p><div>Second</div></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        all_elements = get_all_elements_in_order(soup)
        p_element = soup.find('p')
        position = get_element_position(p_element, all_elements)
        self.assertIsNotNone(position)
        self.assertIsInstance(position, int)
        self.assertGreaterEqual(position, 0)

    def test_get_element_position_not_found(self):
        """Test getting position of element that doesn't exist."""
        html = "<html><body><p>First</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        all_elements = get_all_elements_in_order(soup)
        # Create a new element not in the list
        new_soup = BeautifulSoup("<div>New</div>", 'html.parser')
        new_element = new_soup.find('div')
        position = get_element_position(new_element, all_elements)
        self.assertIsNone(position)

    def test_get_element_position_none(self):
        """Test getting position of None element."""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        all_elements = get_all_elements_in_order(soup)
        position = get_element_position(None, all_elements)
        self.assertIsNone(position)


class TestFindFirstParagraphInExtractedContent(unittest.TestCase):
    """Test cases for find_first_paragraph_in_extracted_content function."""

    def test_find_first_paragraph_exists(self):
        """Test finding first paragraph when it exists."""
        html = "<html><body><p>First paragraph</p><p>Second paragraph</p></body></html>"
        result = find_first_paragraph_in_extracted_content(html)
        self.assertIsNotNone(result)
        self.assertEqual(result.get_text(strip=True), "First paragraph")

    def test_find_first_paragraph_no_paragraphs(self):
        """Test finding first paragraph when none exist."""
        html = "<html><body><div>No paragraphs</div></body></html>"
        result = find_first_paragraph_in_extracted_content(html)
        self.assertIsNone(result)

    def test_find_first_paragraph_empty_html(self):
        """Test finding first paragraph in empty HTML."""
        html = "<html><body></body></html>"
        result = find_first_paragraph_in_extracted_content(html)
        self.assertIsNone(result)

    def test_find_first_paragraph_invalid_html(self):
        """Test finding first paragraph in invalid HTML."""
        html = "not valid html"
        # Should handle gracefully
        result = find_first_paragraph_in_extracted_content(html)
        # May return None or handle error
        self.assertIsInstance(result, (type(None), BeautifulSoup.Tag))


class TestFindMatchingParagraphInOriginal(unittest.TestCase):
    """Test cases for find_matching_paragraph_in_original function."""

    def test_find_matching_paragraph_exact_match(self):
        """Test finding paragraph with exact text match."""
        original_html = "<html><body><p>Exact match text</p><p>Other text</p></body></html>"
        original_soup = BeautifulSoup(original_html, 'html.parser')
        extracted_html = "<p>Exact match text</p>"
        extracted_soup = BeautifulSoup(extracted_html, 'html.parser')
        extracted_para = extracted_soup.find('p')
        
        result = find_matching_paragraph_in_original(original_soup, extracted_para)
        self.assertIsNotNone(result)
        self.assertEqual(result.get_text(strip=True), "Exact match text")

    def test_find_matching_paragraph_partial_match(self):
        """Test finding paragraph with partial text match."""
        original_html = "<html><body><p>This is a long paragraph with many words</p></body></html>"
        original_soup = BeautifulSoup(original_html, 'html.parser')
        extracted_html = "<p>This is a long paragraph with many words and more</p>"
        extracted_soup = BeautifulSoup(extracted_html, 'html.parser')
        extracted_para = extracted_soup.find('p')
        
        result = find_matching_paragraph_in_original(original_soup, extracted_para)
        self.assertIsNotNone(result)
        self.assertIn("This is a long paragraph", result.get_text())

    def test_find_matching_paragraph_no_match(self):
        """Test finding paragraph when no match exists."""
        original_html = "<html><body><p>Original text</p></body></html>"
        original_soup = BeautifulSoup(original_html, 'html.parser')
        extracted_html = "<p>Different text</p>"
        extracted_soup = BeautifulSoup(extracted_html, 'html.parser')
        extracted_para = extracted_soup.find('p')
        
        result = find_matching_paragraph_in_original(original_soup, extracted_para)
        self.assertIsNone(result)

    def test_find_matching_paragraph_none_input(self):
        """Test finding paragraph with None input."""
        original_html = "<html><body><p>Text</p></body></html>"
        original_soup = BeautifulSoup(original_html, 'html.parser')
        result = find_matching_paragraph_in_original(original_soup, None)
        self.assertIsNone(result)

    def test_find_matching_paragraph_empty_text(self):
        """Test finding paragraph with empty text."""
        original_html = "<html><body><p>Text</p></body></html>"
        original_soup = BeautifulSoup(original_html, 'html.parser')
        extracted_html = "<p></p>"
        extracted_soup = BeautifulSoup(extracted_html, 'html.parser')
        extracted_para = extracted_soup.find('p')
        
        result = find_matching_paragraph_in_original(original_soup, extracted_para)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

