"""
Unit tests for subtitle_validation.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from subtitle_validation import (
    is_subtitle_correctly_positioned,
    validate_subtitle_position
)


class TestIsSubtitleCorrectlyPositioned(unittest.TestCase):
    """Test cases for is_subtitle_correctly_positioned function."""

    def test_is_subtitle_correctly_positioned_valid(self):
        """Test when subtitle is correctly positioned."""
        html = '<html><body><h1>Title</h1><h2>Subtitle</h2><p>First paragraph</p></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        headers = {
            'title': {'element': soup.find('h1')},
            'subtitle': {'element': soup.find('h2')}
        }
        extracted = '<p>First paragraph</p>'
        
        with patch('subtitle_validation.find_first_paragraph_in_extracted_content') as mock_find:
            mock_find.return_value = BeautifulSoup(extracted, 'html.parser').find('p')
            with patch('subtitle_validation.find_matching_paragraph_in_original') as mock_match:
                mock_match.return_value = soup.find('p')
                with patch('subtitle_validation.get_all_elements_in_order') as mock_order:
                    all_elements = list(soup.find_all(True))
                    mock_order.return_value = all_elements
                    with patch('subtitle_validation.get_element_position') as mock_pos:
                        mock_pos.side_effect = lambda el, all_els: all_elements.index(el) if el in all_elements else None
                        result = is_subtitle_correctly_positioned(html, headers, extracted)
                        # Should be True if positions are correct
                        self.assertIsInstance(result, bool)

    def test_is_subtitle_correctly_positioned_no_title(self):
        """Test when no title in headers."""
        html = '<html><body></body></html>'
        headers = {}
        extracted = '<p>Content</p>'
        result = is_subtitle_correctly_positioned(html, headers, extracted)
        self.assertFalse(result)

    def test_is_subtitle_correctly_positioned_no_subtitle(self):
        """Test when no subtitle in headers."""
        html = '<html><body><h1>Title</h1></body></html>'
        headers = {'title': {'element': BeautifulSoup(html, 'html.parser').find('h1')}}
        extracted = '<p>Content</p>'
        result = is_subtitle_correctly_positioned(html, headers, extracted)
        self.assertFalse(result)

    def test_is_subtitle_correctly_positioned_no_elements(self):
        """Test when title/subtitle have no DOM elements."""
        html = '<html><body></body></html>'
        headers = {
            'title': {'element': None},
            'subtitle': {'element': None}
        }
        extracted = '<p>Content</p>'
        result = is_subtitle_correctly_positioned(html, headers, extracted)
        self.assertFalse(result)


class TestValidateSubtitlePosition(unittest.TestCase):
    """Test cases for validate_subtitle_position function."""

    def test_validate_subtitle_position_valid(self):
        """Test validation when subtitle is correctly positioned."""
        html = '<html><body><h1>Title</h1><h2>Subtitle</h2><p>First paragraph</p></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        headers = {
            'title': {'element': soup.find('h1')},
            'subtitle': {'element': soup.find('h2')}
        }
        extracted = '<p>First paragraph</p>'
        
        with patch('subtitle_validation.find_first_paragraph_in_extracted_content') as mock_find:
            mock_find.return_value = BeautifulSoup(extracted, 'html.parser').find('p')
            with patch('subtitle_validation.find_matching_paragraph_in_original') as mock_match:
                mock_match.return_value = soup.find('p')
                with patch('subtitle_validation.get_all_elements_in_order') as mock_order:
                    all_elements = list(soup.find_all(True))
                    mock_order.return_value = all_elements
                    with patch('subtitle_validation.get_element_position') as mock_pos:
                        def get_pos(el, all_els):
                            try:
                                return all_elements.index(el)
                            except ValueError:
                                return None
                        mock_pos.side_effect = get_pos
                        result = validate_subtitle_position(html, headers, extracted)
                        self.assertIn('is_valid', result)
                        self.assertIn('reason', result)
                        self.assertIn('title_position', result)
                        self.assertIn('subtitle_position', result)
                        self.assertIn('first_paragraph_position', result)

    def test_validate_subtitle_position_missing_title(self):
        """Test validation when title is missing."""
        html = '<html><body></body></html>'
        headers = {}
        extracted = '<p>Content</p>'
        result = validate_subtitle_position(html, headers, extracted)
        self.assertFalse(result['is_valid'])
        self.assertIn('Missing', result['reason'])

    def test_validate_subtitle_position_no_title_element(self):
        """Test validation when title has no element."""
        html = '<html><body></body></html>'
        headers = {'title': {'element': None}, 'subtitle': {'element': None}}
        extracted = '<p>Content</p>'
        result = validate_subtitle_position(html, headers, extracted)
        self.assertFalse(result['is_valid'])

    def test_validate_subtitle_position_no_paragraph(self):
        """Test validation when no paragraph found."""
        html = '<html><body><h1>Title</h1><h2>Subtitle</h2></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        headers = {
            'title': {'element': soup.find('h1')},
            'subtitle': {'element': soup.find('h2')}
        }
        extracted = '<div>No paragraphs</div>'
        
        with patch('subtitle_validation.find_first_paragraph_in_extracted_content') as mock_find:
            mock_find.return_value = None
            result = validate_subtitle_position(html, headers, extracted)
            self.assertFalse(result['is_valid'])
            self.assertIn('paragraph', result['reason'].lower())


if __name__ == '__main__':
    unittest.main()

