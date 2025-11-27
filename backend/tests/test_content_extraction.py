"""
Unit tests for content_extraction.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup, Tag
from content_extraction import (
    normalize_text,
    find_element_containing_sentence,
    contains_element,
    find_common_container,
    extract_content_between_sentences,
    extract_from_file,
    get_ancestors,
    extract_main_content
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


class TestFindElementContainingSentence(unittest.TestCase):
    """Test cases for find_element_containing_sentence function."""

    def test_find_element_containing_sentence_found(self):
        """Test finding element that contains sentence."""
        html = "<div><p>This is a test sentence.</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        result = find_element_containing_sentence(soup, "test sentence")
        self.assertIsNotNone(result)
        self.assertIn("test sentence", result.get_text().lower())

    def test_find_element_containing_sentence_not_found(self):
        """Test when sentence not found."""
        html = "<div><p>Different content</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        result = find_element_containing_sentence(soup, "test sentence")
        self.assertIsNone(result)

    def test_find_element_containing_sentence_empty(self):
        """Test with empty sentence."""
        html = "<div><p>Content</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        result = find_element_containing_sentence(soup, "")
        self.assertIsNone(result)

    def test_find_element_containing_sentence_case_insensitive(self):
        """Test finding is case insensitive."""
        html = "<div><p>This is a TEST sentence.</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        result = find_element_containing_sentence(soup, "test sentence")
        self.assertIsNotNone(result)


class TestContainsElement(unittest.TestCase):
    """Test cases for contains_element function."""

    def test_contains_element_true(self):
        """Test when container contains target."""
        html = "<div><p>Content</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        container = soup.find('div')
        target = soup.find('p')
        self.assertTrue(contains_element(container, target))

    def test_contains_element_false(self):
        """Test when container does not contain target."""
        html = "<div><p>Content</p></div><span>Other</span>"
        soup = BeautifulSoup(html, 'html.parser')
        container = soup.find('div')
        target = soup.find('span')
        self.assertFalse(contains_element(container, target))

    def test_contains_element_same(self):
        """Test when container is the same as target."""
        html = "<div>Content</div>"
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        self.assertTrue(contains_element(element, element))


class TestFindCommonContainer(unittest.TestCase):
    """Test cases for find_common_container function."""

    def test_find_common_container_found(self):
        """Test finding common container."""
        html = "<div><p>First</p><p>Second</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        element1 = soup.find_all('p')[0]
        element2 = soup.find_all('p')[1]
        container = find_common_container(element1, element2)
        self.assertIsNotNone(container)
        self.assertEqual(container.name, 'div')

    def test_find_common_container_same_element(self):
        """Test when elements are the same."""
        html = "<p>Content</p>"
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('p')
        container = find_common_container(element, element)
        self.assertEqual(container, element)

    def test_find_common_container_one_contains_other(self):
        """Test when one element contains the other."""
        html = "<div><p>Content</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')
        p = soup.find('p')
        container = find_common_container(div, p)
        self.assertEqual(container, div)


class TestExtractContentBetweenSentences(unittest.TestCase):
    """Test cases for extract_content_between_sentences function."""

    def test_extract_content_between_sentences_found(self):
        """Test extracting content between sentences."""
        html = "<div><p>First sentence here.</p><p>Middle content.</p><p>Last sentence here.</p></div>"
        result, container = extract_content_between_sentences(
            html, "First sentence", "Last sentence"
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(container)
        self.assertIn("First sentence", result)
        self.assertIn("Last sentence", result)

    def test_extract_content_between_sentences_not_found(self):
        """Test when sentences not found."""
        html = "<div><p>Different content</p></div>"
        result, container = extract_content_between_sentences(
            html, "First sentence", "Last sentence"
        )
        self.assertIsNone(result)
        self.assertIsNone(container)


class TestGetAncestors(unittest.TestCase):
    """Test cases for get_ancestors function."""

    def test_get_ancestors(self):
        """Test getting ancestors of element."""
        html = "<div><span><p>Content</p></span></div>"
        soup = BeautifulSoup(html, 'html.parser')
        p = soup.find('p')
        ancestors = get_ancestors(p)
        self.assertGreater(len(ancestors), 0)
        # Should include span and div
        ancestor_names = [a.name for a in ancestors]
        self.assertIn('span', ancestor_names)
        self.assertIn('div', ancestor_names)


class TestExtractMainContent(unittest.TestCase):
    """Test cases for extract_main_content function."""

    def test_extract_main_content_with_sentences(self):
        """Test extracting main content with first/last sentences."""
        html = "<div><p>First sentence here.</p><p>Middle content.</p><p>Last sentence here.</p></div>"
        result = extract_main_content(
            html,
            first_sentence="First sentence",
            last_sentence="Last sentence"
        )
        self.assertIsNotNone(result)
        self.assertIn("First sentence", result)

    def test_extract_main_content_without_sentences(self):
        """Test extracting main content without sentences (heuristic)."""
        html = "<html><body><main><p>Content</p></main></body></html>"
        result = extract_main_content(html)
        self.assertIsNotNone(result)
        self.assertIn("Content", result)

    def test_extract_main_content_fallback_to_body(self):
        """Test fallback to body when no main content selector matches."""
        html = "<html><body><p>Content</p></body></html>"
        result = extract_main_content(html)
        self.assertIsNotNone(result)
        self.assertIn("Content", result)


if __name__ == '__main__':
    unittest.main()

