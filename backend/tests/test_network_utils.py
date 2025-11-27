"""
Unit tests for network_utils.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network_utils import (
    get_session,
    create_session_with_retries,
    download_with_size_limit,
    close_session
)


class TestGetSession(unittest.TestCase):
    """Test cases for get_session function."""

    def setUp(self):
        """Reset session before each test."""
        from network_utils import _session
        import network_utils
        network_utils._session = None

    def test_get_session_creates_new(self):
        """Test get_session creates new session."""
        session = get_session()
        self.assertIsNotNone(session)
        from requests import Session
        self.assertIsInstance(session, Session)

    def test_get_session_returns_same_instance(self):
        """Test get_session returns same instance (singleton)."""
        session1 = get_session()
        session2 = get_session()
        self.assertIs(session1, session2)

    def tearDown(self):
        """Clean up session after each test."""
        close_session()


class TestCreateSessionWithRetries(unittest.TestCase):
    """Test cases for create_session_with_retries function."""

    def test_create_session_with_retries(self):
        """Test creating session with retries."""
        session = create_session_with_retries()
        self.assertIsNotNone(session)
        from requests import Session
        self.assertIsInstance(session, Session)

    def test_create_session_custom_retries(self):
        """Test creating session with custom retry count."""
        session = create_session_with_retries(total_retries=5)
        self.assertIsNotNone(session)

    def test_create_session_custom_backoff(self):
        """Test creating session with custom backoff factor."""
        session = create_session_with_retries(backoff_factor=2.0)
        self.assertIsNotNone(session)


class TestDownloadWithSizeLimit(unittest.TestCase):
    """Test cases for download_with_size_limit function."""

    @patch('network_utils.get_session')
    def test_download_within_limit(self, mock_get_session):
        """Test downloading content within size limit."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': '1000'}
        mock_response.raise_for_status = Mock()
        mock_response.iter_content = Mock(return_value=[b'chunk1', b'chunk2'])
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = download_with_size_limit('http://example.com/test', max_size=5000)
        self.assertEqual(result, b'chunk1chunk2')

    @patch('network_utils.get_session')
    def test_download_exceeds_content_length(self, mock_get_session):
        """Test downloading when Content-Length exceeds limit."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': '10000'}
        mock_response.raise_for_status = Mock()
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        with self.assertRaises(ValueError) as context:
            download_with_size_limit('http://example.com/test', max_size=5000)
        self.assertIn("too large", str(context.exception).lower())

    @patch('network_utils.get_session')
    def test_download_exceeds_during_stream(self, mock_get_session):
        """Test downloading when content exceeds limit during streaming."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {}  # No Content-Length
        mock_response.raise_for_status = Mock()
        # Return chunks that exceed limit
        mock_response.iter_content = Mock(return_value=[
            b'x' * 3000,
            b'x' * 3000  # Total exceeds 5000
        ])
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        with self.assertRaises(ValueError) as context:
            download_with_size_limit('http://example.com/test', max_size=5000)
        self.assertIn("exceeds", str(context.exception).lower())

    @patch('network_utils.get_session')
    def test_download_request_exception(self, mock_get_session):
        """Test handling request exceptions."""
        # Mock session that raises exception
        mock_session = MagicMock()
        from requests import RequestException
        mock_session.get.side_effect = RequestException("Connection error")
        mock_get_session.return_value = mock_session
        
        with self.assertRaises(RequestException):
            download_with_size_limit('http://example.com/test', max_size=5000)


class TestCloseSession(unittest.TestCase):
    """Test cases for close_session function."""

    def test_close_session(self):
        """Test closing session."""
        # Create a session first
        session = get_session()
        self.assertIsNotNone(session)
        
        # Close it
        close_session()
        
        # Verify it's closed
        import network_utils
        self.assertIsNone(network_utils._session)

    def test_close_session_when_none(self):
        """Test closing session when none exists."""
        close_session()  # Should not raise
        close_session()  # Should still not raise


if __name__ == '__main__':
    unittest.main()

