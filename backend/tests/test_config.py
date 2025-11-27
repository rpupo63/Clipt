"""
Unit tests for config.py
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""

    def setUp(self):
        """Reset validation state before each test."""
        Config._validated = False

    def test_get_existing_key(self):
        """Test getting an existing environment variable."""
        with patch.dict(os.environ, {'TEST_KEY': 'test_value'}):
            value = Config.get('TEST_KEY')
            self.assertEqual(value, 'test_value')

    def test_get_missing_key(self):
        """Test getting a missing environment variable."""
        value = Config.get('NONEXISTENT_KEY')
        self.assertIsNone(value)

    def test_get_with_default(self):
        """Test getting a key with default value."""
        value = Config.get('NONEXISTENT_KEY', default='default_value')
        self.assertEqual(value, 'default_value')

    def test_validate_no_required_keys(self):
        """Test validation with no required keys."""
        with patch.object(Config, 'REQUIRED_KEYS', []):
            result = Config.validate()
            self.assertTrue(result)
            self.assertTrue(Config._validated)

    def test_validate_missing_required_key(self):
        """Test validation fails when required key is missing."""
        with patch.object(Config, 'REQUIRED_KEYS', ['REQUIRED_KEY']):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(EnvironmentError):
                    Config.validate()

    def test_validate_with_optional_keys(self):
        """Test validation with optional keys."""
        with patch.object(Config, 'REQUIRED_KEYS', []):
            with patch.object(Config, 'OPTIONAL_KEYS', ['OPTIONAL_KEY']):
                with patch.dict(os.environ, {}, clear=True):
                    # Should not raise, just warn
                    result = Config.validate()
                    self.assertTrue(result)

    def test_validate_strict_mode(self):
        """Test validation in strict mode."""
        with patch.object(Config, 'REQUIRED_KEYS', []):
            with patch.object(Config, 'OPTIONAL_KEYS', ['OPTIONAL_KEY']):
                with patch.dict(os.environ, {}, clear=True):
                    with self.assertRaises(EnvironmentError):
                        Config.validate(strict=True)

    def test_has_firecrawl(self):
        """Test has_firecrawl method."""
        with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test_key'}):
            self.assertTrue(Config.has_firecrawl())
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(Config.has_firecrawl())

    def test_has_openai(self):
        """Test has_openai method."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            self.assertTrue(Config.has_openai())
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(Config.has_openai())

    def test_get_firecrawl_key(self):
        """Test get_firecrawl_key method."""
        with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test_key'}):
            self.assertEqual(Config.get_firecrawl_key(), 'test_key')
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(Config.get_firecrawl_key())

    def test_get_openai_key(self):
        """Test get_openai_key method."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            self.assertEqual(Config.get_openai_key(), 'test_key')
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(Config.get_openai_key())


if __name__ == '__main__':
    unittest.main()

