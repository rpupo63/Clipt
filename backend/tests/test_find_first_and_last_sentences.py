"""
Unit tests for find_first_and_last_sentences.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from find_first_and_last_sentences import (
    scrape_url_to_markdown,
    extract_first_and_last_sentences,
    process_url,
    find_first_and_last_sentences_from_url
)


class TestScrapeUrlToMarkdown(unittest.TestCase):
    """Test cases for scrape_url_to_markdown function."""

    @patch('find_first_and_last_sentences.Config.get_firecrawl_key')
    @patch('find_first_and_last_sentences.FirecrawlApp')
    def test_scrape_url_to_markdown_success(self, mock_firecrawl_class, mock_get_key):
        """Test successful URL scraping."""
        mock_get_key.return_value = "test_key"
        
        # Mock Firecrawl response
        mock_firecrawl = MagicMock()
        mock_firecrawl.scrape.return_value = {
            'markdown': '# Title\n\nContent here.',
            'metadata': {'title': 'Test Title'}
        }
        mock_firecrawl_class.return_value = mock_firecrawl
        
        result = scrape_url_to_markdown("https://example.com")
        self.assertIn('markdown', result)
        self.assertIn('url', result)
        self.assertEqual(result['markdown'], '# Title\n\nContent here.')

    @patch('find_first_and_last_sentences.Config.get_firecrawl_key')
    def test_scrape_url_to_markdown_no_key(self, mock_get_key):
        """Test scraping when API key is missing."""
        mock_get_key.return_value = None
        
        with self.assertRaises(ValueError) as context:
            scrape_url_to_markdown("https://example.com")
        self.assertIn("FIRECRAWL_API_KEY", str(context.exception))

    @patch('find_first_and_last_sentences.Config.get_firecrawl_key')
    @patch('find_first_and_last_sentences.FirecrawlApp')
    def test_scrape_url_to_markdown_empty_content(self, mock_firecrawl_class, mock_get_key):
        """Test scraping when content is empty."""
        mock_get_key.return_value = "test_key"
        
        mock_firecrawl = MagicMock()
        mock_firecrawl.scrape.return_value = {'markdown': ''}
        mock_firecrawl_class.return_value = mock_firecrawl
        
        with self.assertRaises(Exception):
            scrape_url_to_markdown("https://example.com")


class TestExtractFirstAndLastSentences(unittest.TestCase):
    """Test cases for extract_first_and_last_sentences function."""

    @patch('find_first_and_last_sentences.Config.get_openai_key')
    @patch('find_first_and_last_sentences.OpenAI')
    def test_extract_first_and_last_sentences_success(self, mock_openai_class, mock_get_key):
        """Test successful sentence extraction."""
        mock_get_key.return_value = "test_key"
        
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"first_sentence": "First.", "last_sentence": "Last."}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        result = extract_first_and_last_sentences("# Title\n\nFirst. Middle. Last.")
        self.assertIn('first_sentence', result)
        self.assertIn('last_sentence', result)
        self.assertEqual(result['first_sentence'], "First.")
        self.assertEqual(result['last_sentence'], "Last.")

    @patch('find_first_and_last_sentences.Config.get_openai_key')
    def test_extract_first_and_last_sentences_no_key(self, mock_get_key):
        """Test extraction when API key is missing."""
        mock_get_key.return_value = None
        
        with self.assertRaises(ValueError) as context:
            extract_first_and_last_sentences("Content")
        self.assertIn("OPENAI_API_KEY", str(context.exception))


class TestProcessUrl(unittest.TestCase):
    """Test cases for process_url function."""

    @patch('find_first_and_last_sentences.scrape_url_to_markdown')
    @patch('find_first_and_last_sentences.extract_first_and_last_sentences')
    def test_process_url_success(self, mock_extract, mock_scrape):
        """Test successful URL processing."""
        mock_scrape.return_value = {
            'markdown': 'Content',
            'url': 'https://example.com',
            'title': 'Test'
        }
        mock_extract.return_value = {
            'first_sentence': 'First.',
            'last_sentence': 'Last.'
        }
        
        result = process_url("https://example.com")
        self.assertIn('url', result)
        self.assertIn('first_sentence', result)
        self.assertIn('last_sentence', result)


class TestFindFirstAndLastSentencesFromUrl(unittest.TestCase):
    """Test cases for find_first_and_last_sentences_from_url function."""

    @patch('find_first_and_last_sentences.scrape_url_to_markdown')
    @patch('find_first_and_last_sentences.extract_first_and_last_sentences')
    def test_find_first_and_last_sentences_from_url_success(self, mock_extract, mock_scrape):
        """Test successful extraction from URL."""
        mock_scrape.return_value = {
            'markdown': 'Content',
            'url': 'https://example.com',
            'title': 'Test'
        }
        mock_extract.return_value = {
            'first_sentence': 'First.',
            'last_sentence': 'Last.'
        }
        
        result = find_first_and_last_sentences_from_url("https://example.com")
        self.assertTrue(result['success'])
        self.assertEqual(result['first_sentence'], 'First.')
        self.assertEqual(result['last_sentence'], 'Last.')
        self.assertIsNone(result['error'])

    def test_find_first_and_last_sentences_from_url_disabled(self):
        """Test when Firecrawl is disabled."""
        result = find_first_and_last_sentences_from_url("https://example.com", use_firecrawl=False)
        self.assertFalse(result['success'])
        self.assertIsNone(result['first_sentence'])
        self.assertIsNone(result['last_sentence'])
        self.assertIsNotNone(result['error'])

    @patch('find_first_and_last_sentences.scrape_url_to_markdown')
    def test_find_first_and_last_sentences_from_url_no_markdown(self, mock_scrape):
        """Test when no markdown is returned."""
        mock_scrape.return_value = {'markdown': ''}
        
        result = find_first_and_last_sentences_from_url("https://example.com")
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])

    @patch('find_first_and_last_sentences.scrape_url_to_markdown')
    @patch('find_first_and_last_sentences.extract_first_and_last_sentences')
    def test_find_first_and_last_sentences_from_url_exception(self, mock_extract, mock_scrape):
        """Test handling exceptions."""
        mock_scrape.side_effect = Exception("Scraping failed")
        
        result = find_first_and_last_sentences_from_url("https://example.com")
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])


if __name__ == '__main__':
    unittest.main()

