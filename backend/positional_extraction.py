#!/usr/bin/env python3
"""
Positional validation for extracted headers and content.
Verifies that subtitle is correctly positioned between title and first paragraph.
Finds images around paragraphs and below titles.
"""

from bs4 import BeautifulSoup
from typing import Optional, Dict
import image_utils


def _get_all_elements_in_order(soup: BeautifulSoup) -> list:
    """
    Get all elements in document order.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        list: List of all elements in document order
    """
    return list(soup.find_all(True))  # True matches all tags


def _get_element_position(element, all_elements: list) -> Optional[int]:
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


def _find_first_paragraph_in_extracted_content(extracted_html: str) -> Optional[object]:
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


def _find_matching_paragraph_in_original(original_soup: BeautifulSoup, 
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
        first_paragraph_extracted = _find_first_paragraph_in_extracted_content(
            extracted_content_html
        )
        
        if first_paragraph_extracted is None:
            # No paragraph found in extracted content, can't verify
            return False
        
        # Find matching paragraph in original HTML
        first_paragraph_original = _find_matching_paragraph_in_original(
            original_soup,
            first_paragraph_extracted
        )
        
        if first_paragraph_original is None:
            # Couldn't find matching paragraph, can't verify
            return False
        
        # Get all elements in document order
        all_elements = _get_all_elements_in_order(original_soup)
        
        # Get DOM positions
        title_pos = _get_element_position(title_element, all_elements)
        subtitle_pos = _get_element_position(subtitle_element, all_elements)
        first_para_pos = _get_element_position(first_paragraph_original, all_elements)
        
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
        return result
    
    title_info = headers['title']
    subtitle_info = headers['subtitle']
    
    title_element = title_info.get('element')
    subtitle_element = subtitle_info.get('element')
    
    if title_element is None:
        result['reason'] = 'Title element not found (may be from meta/structured data)'
        return result
    
    if subtitle_element is None:
        result['reason'] = 'Subtitle element not found (may be from meta/structured data)'
        return result
    
    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')
        
        # Find first paragraph in extracted content
        first_paragraph_extracted = _find_first_paragraph_in_extracted_content(
            extracted_content_html
        )
        
        if first_paragraph_extracted is None:
            result['reason'] = 'No paragraph found in extracted content'
            return result
        
        # Find matching paragraph in original HTML
        first_paragraph_original = _find_matching_paragraph_in_original(
            original_soup,
            first_paragraph_extracted
        )
        
        if first_paragraph_original is None:
            result['reason'] = 'Could not find matching paragraph in original HTML'
            return result
        
        # Get all elements in document order
        all_elements = _get_all_elements_in_order(original_soup)
        
        # Get DOM positions
        title_pos = _get_element_position(title_element, all_elements)
        subtitle_pos = _get_element_position(subtitle_element, all_elements)
        first_para_pos = _get_element_position(first_paragraph_original, all_elements)
        
        result['title_position'] = title_pos
        result['subtitle_position'] = subtitle_pos
        result['first_paragraph_position'] = first_para_pos
        
        if title_pos is None or subtitle_pos is None or first_para_pos is None:
            result['reason'] = 'Could not determine element positions'
            return result
        
        # Verify order: title < subtitle < first_paragraph
        if title_pos >= subtitle_pos:
            result['reason'] = f'Subtitle (pos {subtitle_pos}) comes before or same as title (pos {title_pos})'
            return result
        
        if subtitle_pos >= first_para_pos:
            result['reason'] = f'Subtitle (pos {subtitle_pos}) comes after or same as first paragraph (pos {first_para_pos})'
            return result
        
        result['is_valid'] = True
        result['reason'] = 'Subtitle is correctly positioned between title and first paragraph'
        return result
        
    except Exception as e:
        result['reason'] = f'Error during validation: {str(e)}'
        return result


def _is_image_element(element) -> bool:
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


def _get_image_container(img_element) -> Optional[object]:
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
        if parent and _is_image_element(parent):
            return parent
        
        # Return the img itself
        return img_element
    
    return img_element


def _find_nearest_image_above(paragraph_element, original_soup: BeautifulSoup, 
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
            if _is_image_element(current):
                return current
            # Check if it contains an image
            img = current.find('img')
            if img:
                return _get_image_container(img)
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
                if _is_image_element(current):
                    return current
                # Look for images within this sibling
                img = current.find('img', recursive=True)
                if img:
                    return _get_image_container(img)
                distance += 1
            current = current.previous_sibling if hasattr(current, 'previous_sibling') else None
    
    # Strategy 3: Check all previous elements in document order (within reasonable distance)
    all_elements = _get_all_elements_in_order(original_soup)
    para_pos = _get_element_position(paragraph_element, all_elements)
    
    if para_pos is not None:
        # Look backwards up to max_distance * 10 elements
        search_range = min(max_distance * 10, para_pos)
        for i in range(1, search_range + 1):
            if para_pos - i >= 0:
                candidate = all_elements[para_pos - i]
                if _is_image_element(candidate):
                    return candidate
                # Check if candidate contains an img
                img = candidate.find('img')
                if img:
                    return _get_image_container(img)
    
    return None


def _find_nearest_image_below(paragraph_element, original_soup: BeautifulSoup,
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
            if _is_image_element(current):
                return current
            # Check if it contains an image
            img = current.find('img')
            if img:
                return _get_image_container(img)
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
                if _is_image_element(current):
                    return current
                # Look for images within this sibling
                img = current.find('img', recursive=True)
                if img:
                    return _get_image_container(img)
                distance += 1
            current = current.next_sibling if hasattr(current, 'next_sibling') else None
    
    # Strategy 3: Check all next elements in document order (within reasonable distance)
    all_elements = _get_all_elements_in_order(original_soup)
    para_pos = _get_element_position(paragraph_element, all_elements)
    
    if para_pos is not None:
        # Look forwards up to max_distance * 10 elements
        search_range = min(max_distance * 10, len(all_elements) - para_pos - 1)
        for i in range(1, search_range + 1):
            if para_pos + i < len(all_elements):
                candidate = all_elements[para_pos + i]
                if _is_image_element(candidate):
                    return candidate
                # Check if candidate contains an img
                img = candidate.find('img')
                if img:
                    return _get_image_container(img)
    
    return None


def find_images_around_paragraph(extracted_paragraph,
                                original_html: str,
                                base_url: Optional[str] = None,
                                max_distance: int = 5) -> Dict:
    """
    Find images immediately above and below a paragraph from extracted content.
    
    This function:
    1. Matches the paragraph from extracted content to the original HTML
    2. Finds the nearest image above the paragraph
    3. Finds the nearest image below the paragraph
    
    Args:
        extracted_paragraph: BeautifulSoup paragraph element from extracted content
        original_html: Full original HTML content as string
        base_url: Base URL for converting relative image paths to absolute URLs
        max_distance: Maximum number of sibling elements to search (default: 5)
        
    Returns:
        dict: Dictionary with keys:
            - 'paragraph_matched': bool - Whether paragraph was found in original HTML
            - 'paragraph_element': BeautifulSoup element or None - Matched paragraph in original
            - 'image_above': str or None - Image URL (unique identifier) or None
            - 'image_below': str or None - Image URL (unique identifier) or None
    """
    result = {
        'paragraph_matched': False,
        'paragraph_element': None,
        'image_above': None,
        'image_below': None
    }
    
    if extracted_paragraph is None:
        return result
    
    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')
        
        # Find matching paragraph in original HTML
        matched_paragraph = _find_matching_paragraph_in_original(
            original_soup,
            extracted_paragraph
        )
        
        if matched_paragraph is None:
            return result
        
        result['paragraph_matched'] = True
        result['paragraph_element'] = matched_paragraph
        
        # Find images above and below
        image_above_element = _find_nearest_image_above(
            matched_paragraph,
            original_soup,
            max_distance
        )
        
        image_below_element = _find_nearest_image_below(
            matched_paragraph,
            original_soup,
            max_distance
        )
        
        # Extract image URLs only (unique identifiers)
        if image_above_element:
            image_info = _extract_image_info(image_above_element, base_url, fetch_dimensions=False, fetch_content=False)
            result['image_above'] = image_info.get('url') if image_info else None
        
        if image_below_element:
            image_info = _extract_image_info(image_below_element, base_url, fetch_dimensions=False, fetch_content=False)
            result['image_below'] = image_info.get('url') if image_info else None
        
        return result
        
    except Exception as e:
        return result


def find_images_around_paragraph_from_extracted_content(extracted_content_html: str,
                                                         paragraph_index: int,
                                                         original_html: str,
                                                         base_url: Optional[str] = None,
                                                         max_distance: int = 5) -> Dict:
    """
    Find images around a specific paragraph from extracted content by index.
    
    This is a convenience function that:
    1. Extracts the paragraph at the given index from extracted content
    2. Finds matching paragraph in original HTML
    3. Returns images above and below
    
    Args:
        extracted_content_html: HTML string from content_extraction.extract_main_content()
        paragraph_index: Index of paragraph to find (0-based, 0 = first paragraph)
        original_html: Full original HTML content as string
        base_url: Base URL for converting relative image paths to absolute URLs
        max_distance: Maximum number of sibling elements to search (default: 5)
        
    Returns:
        dict: Same format as find_images_around_paragraph()
    """
    try:
        # Parse extracted content
        extracted_soup = BeautifulSoup(extracted_content_html, 'html.parser')
        
        # Find all paragraphs
        paragraphs = extracted_soup.find_all('p')
        
        if paragraph_index < 0 or paragraph_index >= len(paragraphs):
            return {
                'paragraph_matched': False,
                'paragraph_element': None,
                'image_above': None,
                'image_below': None
            }
        
        # Get the paragraph at the specified index
        target_paragraph = paragraphs[paragraph_index]
        
        # Find images around it
        return find_images_around_paragraph(
            target_paragraph,
            original_html,
            base_url,
            max_distance
        )
        
    except Exception:
        return {
            'paragraph_matched': False,
            'paragraph_element': None,
            'image_above': None,
            'image_below': None
        }


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
    if not headers or not headers.get('title'):
        return None
    
    title_info = headers['title']
    title_element = title_info.get('element')
    
    # Title must have a DOM element (not from meta/structured data)
    if title_element is None:
        return None
    
    try:
        # Parse original HTML
        original_soup = BeautifulSoup(original_html, 'html.parser')
        
        # Find image below title
        image_element = _find_nearest_image_below(
            title_element,
            original_soup,
            max_distance
        )
        
        if image_element is None:
            return None
        
        # Extract image URL only (unique identifier)
        image_info = _extract_image_info(image_element, base_url, fetch_dimensions=False, fetch_content=False)
        return image_info.get('url') if image_info else None
        
    except Exception:
        return None

