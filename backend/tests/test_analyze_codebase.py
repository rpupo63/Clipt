"""
Unit tests for analyze_codebase.py
"""

import unittest
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_codebase import (
    count_file_lines,
    analyze_functions
)


class TestCountFileLines(unittest.TestCase):
    """Test cases for count_file_lines function."""

    def test_count_file_lines(self):
        """Test counting lines in a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("line 1\nline 2\nline 3\n")
            temp_path = f.name
        
        try:
            count = count_file_lines(temp_path)
            self.assertEqual(count, 3)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_count_file_lines_empty(self):
        """Test counting lines in empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            temp_path = f.name
        
        try:
            count = count_file_lines(temp_path)
            self.assertEqual(count, 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_count_file_lines_nonexistent(self):
        """Test counting lines in nonexistent file."""
        count = count_file_lines("/nonexistent/file.py")
        self.assertEqual(count, 0)


class TestAnalyzeFunctions(unittest.TestCase):
    """Test cases for analyze_functions function."""

    def test_analyze_functions_simple(self):
        """Test analyzing functions in a simple Python file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("""
def function1():
    pass

def function2():
    pass
""")
            temp_path = f.name
        
        try:
            functions = analyze_functions(temp_path)
            self.assertEqual(len(functions), 2)
            function_names = [f[0] for f in functions]
            self.assertTrue(any('function1' in name for name in function_names))
            self.assertTrue(any('function2' in name for name in function_names))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_functions_no_functions(self):
        """Test analyzing file with no functions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("x = 1\ny = 2\n")
            temp_path = f.name
        
        try:
            functions = analyze_functions(temp_path)
            self.assertEqual(len(functions), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_functions_invalid_syntax(self):
        """Test analyzing file with invalid syntax."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("def invalid syntax here\n")
            temp_path = f.name
        
        try:
            functions = analyze_functions(temp_path)
            # Should return empty list on error
            self.assertEqual(len(functions), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()

