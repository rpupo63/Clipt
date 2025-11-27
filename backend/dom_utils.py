#!/usr/bin/env python3
"""
DOM manipulation utilities for BeautifulSoup elements.
Provides helper functions for element positioning and paragraph matching.
"""

from bs4 import BeautifulSoup
from typing import Optional
from logger import get_logger

logger = get_logger(__name__)


def get_all_elements_in_order(soup: BeautifulSoup) -> list:
    """
    Get all elements in document order.

    Args:
        soup: BeautifulSoup object

    Returns:
        list: List of all elements in document order
    """
    return list(soup.find_all(True))  # True matches all tags


def get_element_position(element, all_elements: list) -> Optional[int]:
    """
    Get the position of an element in the DOM tree.

    Args:
        element: BeautifulSoup element
        all_elements: List of all elements in document order

    Returns:
        int: Position index (0-based) or None if element is None or not found
    """
    if element is None:
        return None

    try:
        # Find index of element in the ordered list
        if element in all_elements:
            return all_elements.index(element)
        return None
    except Exception:
        return None


def find_first_paragraph_in_extracted_content(extracted_html: str) -> Optional[object]:
    """
    Find the first paragraph element in the extracted content HTML.

    Args:
        extracted_html: HTML string from content_extraction.extract_main_content()

    Returns:
        BeautifulSoup element or None
    """
    try:
        soup = BeautifulSoup(extracted_html, 'html.parser')
        # Find first <p> tag in body
        first_p = soup.find('p')
        return first_p
    except Exception:
        return None


def find_matching_paragraph_in_original(original_soup: BeautifulSoup,
                                        extracted_paragraph) -> Optional[object]:
    """
    Find the matching paragraph in the original HTML by matching text content.

    Args:
        original_soup: BeautifulSoup object of original HTML
        extracted_paragraph: BeautifulSoup paragraph element from extracted content

    Returns:
        BeautifulSoup element or None
    """
    if extracted_paragraph is None:
        return None

    # Get text content of extracted paragraph (normalized)
    extracted_text = extracted_paragraph.get_text(strip=True)
    if not extracted_text:
        return None

    # Try to find matching paragraph in original HTML
    # First, try exact text match
    for p in original_soup.find_all('p'):
        p_text = p.get_text(strip=True)
        if p_text == extracted_text:
            return p

    # If exact match fails, try partial match (first 50 chars)
    if len(extracted_text) > 50:
        extracted_prefix = extracted_text[:50]
        for p in original_soup.find_all('p'):
            p_text = p.get_text(strip=True)
            if p_text.startswith(extracted_prefix):
                return p

    return None
