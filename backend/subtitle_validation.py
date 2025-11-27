#!/usr/bin/env python3
"""
Subtitle position validation.
Verifies that subtitle is correctly positioned between title and first paragraph.
"""

from bs4 import BeautifulSoup
from typing import Dict
from logger import get_logger
from dom_utils import (
    get_all_elements_in_order,
    get_element_position,
    find_first_paragraph_in_extracted_content,
    find_matching_paragraph_in_original
)

logger = get_logger(__name__)


def is_subtitle_correctly_positioned(original_html: str,
                                     headers: dict,
                                     extracted_content_html: str) -> bool:
    """
    Determine if the subtitle element is correctly positioned between the title
    and the first paragraph of the main content.

    This function verifies that:
    1. Title element exists and has a DOM position
    2. Subtitle element exists and has a DOM position
    3. First paragraph of extracted content exists in original HTML
    4. Subtitle comes after title in DOM order
    5. Subtitle comes before first paragraph in DOM order

    Args:
        original_html: Full original HTML content as string
        headers: Dictionary from header_extraction.extract_headers() with keys:
            - 'title': dict with 'element' key (BeautifulSoup element or None)
            - 'subtitle': dict with 'element' key (BeautifulSoup element or None)
        extracted_content_html: HTML string from content_extraction.extract_main_content()

    Returns:
        bool: True if subtitle is correctly positioned, False otherwise
    """
    # Check if we have the necessary data
    if not headers or not headers.get('title') or not headers.get('subtitle'):
        return False

    title_info = headers['title']
    subtitle_info = headers['subtitle']

    # Both title and subtitle must have DOM elements (not from meta/structured data)
    title_element = title_info.get('element')
    subtitle_element = subtitle_info.get('element')

    if title_element is None or subtitle_element is None:
        # If either is from meta/structured data, we can't verify position
        return False

    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')

        # Find first paragraph in extracted content
        first_paragraph_extracted = find_first_paragraph_in_extracted_content(
            extracted_content_html
        )

        if first_paragraph_extracted is None:
            # No paragraph found in extracted content, can't verify
            return False

        # Find matching paragraph in original HTML
        first_paragraph_original = find_matching_paragraph_in_original(
            original_soup,
            first_paragraph_extracted
        )

        if first_paragraph_original is None:
            # Couldn't find matching paragraph, can't verify
            return False

        # Get all elements in document order
        all_elements = get_all_elements_in_order(original_soup)

        # Get DOM positions
        title_pos = get_element_position(title_element, all_elements)
        subtitle_pos = get_element_position(subtitle_element, all_elements)
        first_para_pos = get_element_position(first_paragraph_original, all_elements)

        if title_pos is None or subtitle_pos is None or first_para_pos is None:
            return False

        # Verify order: title < subtitle < first_paragraph
        return title_pos < subtitle_pos < first_para_pos

    except Exception:
        # If any error occurs, return False
        return False


def validate_subtitle_position(original_html: str,
                              headers: dict,
                              extracted_content_html: str) -> dict:
    """
    Validate subtitle position and return detailed results.

    Args:
        original_html: Full original HTML content as string
        headers: Dictionary from header_extraction.extract_headers()
        extracted_content_html: HTML string from content_extraction.extract_main_content()

    Returns:
        dict: Dictionary with validation results:
            - 'is_valid': bool - Whether subtitle is correctly positioned
            - 'reason': str - Reason for validation result
            - 'title_position': int or None - DOM position of title
            - 'subtitle_position': int or None - DOM position of subtitle
            - 'first_paragraph_position': int or None - DOM position of first paragraph
    """
    logger.debug("Validating subtitle position")

    result = {
        'is_valid': False,
        'reason': '',
        'title_position': None,
        'subtitle_position': None,
        'first_paragraph_position': None
    }

    # Check if we have the necessary data
    if not headers or not headers.get('title') or not headers.get('subtitle'):
        result['reason'] = 'Missing title or subtitle in headers'
        logger.debug(f"Validation failed: {result['reason']}")
        return result

    title_info = headers['title']
    subtitle_info = headers['subtitle']

    title_element = title_info.get('element')
    subtitle_element = subtitle_info.get('element')

    if title_element is None:
        result['reason'] = 'Title element not found (may be from meta/structured data)'
        logger.debug(f"Validation failed: {result['reason']}")
        return result

    if subtitle_element is None:
        result['reason'] = 'Subtitle element not found (may be from meta/structured data)'
        logger.debug(f"Validation failed: {result['reason']}")
        return result

    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')

        # Find first paragraph in extracted content
        first_paragraph_extracted = find_first_paragraph_in_extracted_content(
            extracted_content_html
        )

        if first_paragraph_extracted is None:
            result['reason'] = 'No paragraph found in extracted content'
            logger.debug(f"Validation failed: {result['reason']}")
            return result

        # Find matching paragraph in original HTML
        first_paragraph_original = find_matching_paragraph_in_original(
            original_soup,
            first_paragraph_extracted
        )

        if first_paragraph_original is None:
            result['reason'] = 'Could not find matching paragraph in original HTML'
            logger.debug(f"Validation failed: {result['reason']}")
            return result

        # Get all elements in document order
        all_elements = get_all_elements_in_order(original_soup)

        # Get DOM positions
        title_pos = get_element_position(title_element, all_elements)
        subtitle_pos = get_element_position(subtitle_element, all_elements)
        first_para_pos = get_element_position(first_paragraph_original, all_elements)

        result['title_position'] = title_pos
        result['subtitle_position'] = subtitle_pos
        result['first_paragraph_position'] = first_para_pos

        logger.debug(f"Element positions - Title: {title_pos}, Subtitle: {subtitle_pos}, First paragraph: {first_para_pos}")

        if title_pos is None or subtitle_pos is None or first_para_pos is None:
            result['reason'] = 'Could not determine element positions'
            logger.warning(f"Validation failed: {result['reason']}")
            return result

        # Verify order: title < subtitle < first_paragraph
        if title_pos >= subtitle_pos:
            result['reason'] = f'Subtitle (pos {subtitle_pos}) comes before or same as title (pos {title_pos})'
            logger.info(f"Subtitle validation failed: {result['reason']}")
            return result

        if subtitle_pos >= first_para_pos:
            result['reason'] = f'Subtitle (pos {subtitle_pos}) comes after or same as first paragraph (pos {first_para_pos})'
            logger.info(f"Subtitle validation failed: {result['reason']}")
            return result

        result['is_valid'] = True
        result['reason'] = 'Subtitle is correctly positioned between title and first paragraph'
        logger.info("Subtitle validation passed")
        return result

    except Exception as e:
        result['reason'] = f'Error during validation: {str(e)}'
        logger.error(f"Subtitle validation error: {e}", exc_info=True)
        return result
