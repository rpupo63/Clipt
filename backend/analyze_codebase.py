#!/usr/bin/env python3
"""
Analyze codebase to get file and function statistics.
"""

import os
import ast
from pathlib import Path
from typing import List, Tuple, Dict

def count_file_lines(filepath: str) -> int:
    """Count lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0

def analyze_functions(filepath: str) -> List[Tuple[str, int, int]]:
    """
    Extract function names and their line counts from a Python file.

    Returns:
        List of (function_name, start_line, line_count) tuples
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=filepath)

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                line_count = end_line - start_line + 1

                # Get file name without path
                filename = os.path.basename(filepath)

                functions.append((f"{filename}:{node.name}", start_line, line_count))

        return functions
    except Exception as e:
        return []

def main():
    backend_dir = Path(__file__).parent

    # Find all Python files (excluding this analysis script)
    python_files = [
        f for f in backend_dir.glob('*.py')
        if f.name != 'analyze_codebase.py' and not f.name.startswith('.')
    ]

    # Analyze files
    file_stats = []
    all_functions = []

    for filepath in python_files:
        line_count = count_file_lines(str(filepath))
        file_stats.append((filepath.name, line_count))

        # Extract functions from this file
        functions = analyze_functions(str(filepath))
        all_functions.extend(functions)

    # Sort files by line count (descending)
    file_stats.sort(key=lambda x: x[1], reverse=True)

    # Sort functions by line count (descending)
    all_functions.sort(key=lambda x: x[2], reverse=True)

    # Print results
    print("=" * 80)
    print("FILES BY LENGTH (Lines of Code)")
    print("=" * 80)
    print(f"{'File Name':<40} {'Lines':>10}")
    print("-" * 80)
    total_lines = 0
    for filename, lines in file_stats:
        print(f"{filename:<40} {lines:>10}")
        total_lines += lines
    print("-" * 80)
    print(f"{'TOTAL':<40} {total_lines:>10}")
    print()

    print("=" * 80)
    print("FUNCTIONS BY LENGTH (Lines of Code)")
    print("=" * 80)
    print(f"{'Function Name':<50} {'Start':>8} {'Lines':>10}")
    print("-" * 80)

    # Show top 50 longest functions
    for func_name, start_line, line_count in all_functions[:50]:
        print(f"{func_name:<50} {start_line:>8} {line_count:>10}")

    if len(all_functions) > 50:
        print(f"\n... and {len(all_functions) - 50} more functions")

    print("-" * 80)
    print(f"Total functions analyzed: {len(all_functions)}")

    # Additional statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Python files: {len(file_stats)}")
    print(f"Total lines of code: {total_lines}")
    print(f"Total functions: {len(all_functions)}")
    if all_functions:
        avg_func_length = sum(f[2] for f in all_functions) / len(all_functions)
        print(f"Average function length: {avg_func_length:.1f} lines")
        print(f"Longest function: {all_functions[0][0]} ({all_functions[0][2]} lines)")
        print(f"Shortest function: {all_functions[-1][0]} ({all_functions[-1][2]} lines)")

if __name__ == "__main__":
    main()
