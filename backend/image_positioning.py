#!/usr/bin/env python3
"""
Image positional extraction utilities.
Finds images around paragraphs, above titles, and below titles in HTML documents.
"""

from bs4 import BeautifulSoup
from typing import Optional, Dict
import image_utils
from logger import get_logger
from dom_utils import (
    get_all_elements_in_order,
    get_element_position,
)

logger = get_logger(__name__)


def is_image_element(element) -> bool:
    """
    Check if an element is an image (img tag, picture tag, or figure with img).

    Args:
        element: BeautifulSoup element

    Returns:
        bool: True if element is or contains an image
    """
    if element is None or not hasattr(element, 'name'):
        return False

    # Check if it's an img tag
    if element.name == 'img':
        return True

    # Check if it's a picture tag
    if element.name == 'picture':
        return True

    # Check if it's a figure tag with an img inside
    if element.name == 'figure':
        if element.find('img'):
            return True

    # Check if element contains an img and is likely an image container
    # (e.g., div with class containing "image", "photo", "img", etc.)
    img = element.find('img')
    if img:
        # Check if element has image-related classes or IDs
        classes = element.get('class', [])
        class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
        element_id = element.get('id', '')

        image_keywords = ['image', 'img', 'photo', 'picture', 'figure', 'media']
        has_image_keyword = any(keyword in class_str.lower() or keyword in element_id.lower()
                                for keyword in image_keywords)

        # If it has image keywords, consider it an image element
        if has_image_keyword:
            return True

        # Otherwise, check if img is a direct child (likely an image wrapper)
        if img.parent == element:
            return True

    return False


def _extract_image_info(img_element, base_url: Optional[str] = None, fetch_dimensions: bool = True, fetch_content: bool = False) -> Dict:
    """
    Extract information from an image element.

    This is a wrapper around image_utils.extract_image_info for internal use.

    Args:
        img_element: BeautifulSoup image element (img, picture, or figure)
        base_url: Base URL for converting relative paths to absolute URLs
        fetch_dimensions: If True, fetch actual image dimensions from URL (default: True)
        fetch_content: If True, download and store image content to avoid re-downloading (default: False)

    Returns:
        dict: Dictionary with image information (see image_utils.extract_image_info)
    """
    return image_utils.extract_image_info(img_element, base_url, fetch_dimensions, fetch_content)


def get_image_container(img_element) -> Optional[object]:
    """
    Get the best container element for an image (figure, picture, or direct parent).

    Args:
        img_element: BeautifulSoup img element

    Returns:
        BeautifulSoup element: Best container or the img itself
    """
    if img_element is None:
        return None

    # If it's already a container type, return it
    if img_element.name in ['figure', 'picture']:
        return img_element

    # If it's an img, find its best container
    if img_element.name == 'img':
        # Look for figure or picture parent
        container = img_element.find_parent(['figure', 'picture'])
        if container:
            return container

        # Look for div/section with image-related classes
        parent = img_element.find_parent(['div', 'section', 'article'])
        if parent and is_image_element(parent):
            return parent

        # Return the img itself
        return img_element

    return img_element


def find_nearest_image_below(paragraph_element, original_soup: BeautifulSoup,
                              max_distance: int = 5) -> Optional[object]:
    """
    Find the nearest image element below the paragraph in the DOM.

    Args:
        paragraph_element: BeautifulSoup paragraph element
        original_soup: BeautifulSoup object of original HTML
        max_distance: Maximum number of sibling elements to check (default: 5)

    Returns:
        BeautifulSoup image element or None
    """
    if paragraph_element is None:
        return None

    # Strategy 1: Check next siblings
    current = paragraph_element.next_sibling
    distance = 0
    while current and distance < max_distance:
        if hasattr(current, 'name') and current.name:
            if is_image_element(current):
                return current
            # Check if it contains an image
            img = current.find('img')
            if img:
                return get_image_container(img)
            distance += 1
        current = current.next_sibling

    # Strategy 2: Check parent's next siblings
    parent = paragraph_element.find_parent()
    if parent:
        current = parent.next_sibling
        distance = 0
        while current and distance < max_distance:
            if hasattr(current, 'name') and current.name:
                # Look for images in this sibling
                if is_image_element(current):
                    return current
                # Look for images within this sibling
                img = current.find('img', recursive=True)
                if img:
                    return get_image_container(img)
                distance += 1
            current = current.next_sibling if hasattr(current, 'next_sibling') else None

    # Strategy 3: Check all next elements in document order (within reasonable distance)
    all_elements = get_all_elements_in_order(original_soup)
    para_pos = get_element_position(paragraph_element, all_elements)

    if para_pos is not None:
        # Look forwards up to max_distance * 10 elements
        search_range = min(max_distance * 10, len(all_elements) - para_pos - 1)
        for i in range(1, search_range + 1):
            if para_pos + i < len(all_elements):
                candidate = all_elements[para_pos + i]
                if is_image_element(candidate):
                    return candidate
                # Check if candidate contains an img
                img = candidate.find('img')
                if img:
                    return get_image_container(img)

    return None


def find_nearest_image_above(paragraph_element, original_soup: BeautifulSoup,
                              max_distance: int = 5) -> Optional[object]:
    """
    Find the nearest image element above the paragraph in the DOM.

    Args:
        paragraph_element: BeautifulSoup paragraph element
        original_soup: BeautifulSoup object of original HTML
        max_distance: Maximum number of sibling elements to check (default: 5)

    Returns:
        BeautifulSoup image element or None
    """
    if paragraph_element is None:
        return None

    # Strategy 1: Check previous siblings
    current = paragraph_element.previous_sibling
    distance = 0
    while current and distance < max_distance:
        if hasattr(current, 'name') and current.name:
            if is_image_element(current):
                return current
            # Check if it contains an image
            img = current.find('img')
            if img:
                return get_image_container(img)
            distance += 1
        current = current.previous_sibling

    # Strategy 2: Check parent's previous siblings
    parent = paragraph_element.find_parent()
    if parent:
        current = parent.previous_sibling
        distance = 0
        while current and distance < max_distance:
            if hasattr(current, 'name') and current.name:
                # Look for images in this sibling
                if is_image_element(current):
                    return current
                # Look for images within this sibling
                img = current.find('img', recursive=True)
                if img:
                    return get_image_container(img)
                distance += 1
            current = current.previous_sibling if hasattr(current, 'previous_sibling') else None

    # Strategy 3: Check all previous elements in document order (within reasonable distance)
    all_elements = get_all_elements_in_order(original_soup)
    para_pos = get_element_position(paragraph_element, all_elements)

    if para_pos is not None:
        # Look backwards up to max_distance * 10 elements
        search_range = min(max_distance * 10, para_pos)
        for i in range(1, search_range + 1):
            if para_pos - i >= 0:
                candidate = all_elements[para_pos - i]
                if is_image_element(candidate):
                    return candidate
                # Check if candidate contains an img
                img = candidate.find('img')
                if img:
                    return get_image_container(img)

    return None


def find_image_below_title(original_html: str,
                           headers: dict,
                           base_url: Optional[str] = None,
                           max_distance: int = 5) -> Optional[Dict]:
    """
    Find the image element immediately below the title.

    This function:
    1. Gets the title element from headers
    2. Finds the nearest image below the title in the DOM
    3. Returns image information

    Args:
        original_html: Full original HTML content as string
        headers: Dictionary from header_extraction.extract_headers() with keys:
            - 'title': dict with 'element' key (BeautifulSoup element or None)
        base_url: Base URL for converting relative image paths to absolute URLs
        max_distance: Maximum number of sibling elements to search (default: 5)

    Returns:
        str: Image URL (unique identifier) or None if not found
    """
    logger.debug("Finding image below title")

    if not headers or not headers.get('title'):
        logger.debug("No title found in headers")
        return None

    title_info = headers['title']
    title_element = title_info.get('element')

    # Title must have a DOM element (not from meta/structured data)
    if title_element is None:
        logger.debug("Title element not available (may be from meta/structured data)")
        return None

    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')

        # Find image below title
        image_element = find_nearest_image_below(
            title_element,
            original_soup,
            max_distance
        )

        if image_element is None:
            logger.debug("No image found below title")
            return None

        # Extract image URL only (unique identifier)
        image_info = _extract_image_info(image_element, base_url, fetch_dimensions=False, fetch_content=False)
        image_url = image_info.get('url') if image_info else None

        if image_url:
            logger.info(f"Found image below title: {image_url}")
        else:
            logger.debug("Image element found but no URL extracted")

        return image_url

    except Exception as e:
        logger.error(f"Error finding image below title: {e}", exc_info=True)
        return None


def find_image_above_title(original_html: str,
                           headers: dict,
                           base_url: Optional[str] = None,
                           max_distance: int = 5) -> Optional[str]:
    """
    Find the image element immediately above the title.

    This function:
    1. Gets the title element from headers
    2. Finds the nearest image above the title in the DOM
    3. Returns image information

    Args:
        original_html: Full original HTML content as string
        headers: Dictionary from header_extraction.extract_headers() with keys:
            - 'title': dict with 'element' key (BeautifulSoup element or None)
        base_url: Base URL for converting relative image paths to absolute URLs
        max_distance: Maximum number of sibling elements to search (default: 5)

    Returns:
        str: Image URL (unique identifier) or None if not found
    """
    logger.debug("Finding image above title")

    if not headers or not headers.get('title'):
        logger.debug("No title found in headers")
        return None

    title_info = headers['title']
    title_element = title_info.get('element')

    # Title must have a DOM element (not from meta/structured data)
    if title_element is None:
        logger.debug("Title element not available (may be from meta/structured data)")
        return None

    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')

        # Find image above title
        image_element = find_nearest_image_above(
            title_element,
            original_soup,
            max_distance
        )

        if image_element is None:
            logger.debug("No image found above title")
            return None

        # Extract image URL only (unique identifier)
        image_info = _extract_image_info(image_element, base_url, fetch_dimensions=False, fetch_content=False)
        image_url = image_info.get('url') if image_info else None

        if image_url:
            logger.info(f"Found image above title: {image_url}")
        else:
            logger.debug("Image element found but no URL extracted")

        return image_url

    except Exception as e:
        logger.error(f"Error finding image above title: {e}", exc_info=True)
        return None
