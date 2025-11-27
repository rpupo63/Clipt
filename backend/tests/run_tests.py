#!/usr/bin/env python3
"""
Test runner for all unit tests in the backend.
Run this script to execute all tests.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_tests():
    """Load all test modules."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover all test files
    test_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    return suite

def main():
    """Run all tests."""
    suite = load_tests()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()

