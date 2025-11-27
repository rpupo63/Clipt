"""
Unit tests for logger.py
"""

import unittest
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logger, get_logger


class TestLogger(unittest.TestCase):
    """Test cases for logger functions."""

    def test_setup_logger(self):
        """Test setup_logger function."""
        logger = setup_logger('test_logger', level='DEBUG')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logger_with_file(self):
        """Test setup_logger with log file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            logger = setup_logger('test_logger_file', level='INFO', log_file=log_file)
            self.assertIsInstance(logger, logging.Logger)
            logger.info("Test message")
            
            # Check file was created and has content
            self.assertTrue(os.path.exists(log_file))
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertIn("Test message", content)
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger('test_get_logger')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_get_logger')

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger('test_same')
        logger2 = get_logger('test_same')
        self.assertIs(logger1, logger2)

    def test_logger_levels(self):
        """Test different log levels."""
        logger = setup_logger('test_levels', level='WARNING')
        self.assertEqual(logger.level, logging.WARNING)
        
        logger = setup_logger('test_levels2', level='ERROR')
        self.assertEqual(logger.level, logging.ERROR)


if __name__ == '__main__':
    unittest.main()

