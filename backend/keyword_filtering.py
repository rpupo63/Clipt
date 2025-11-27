#!/usr/bin/env python3
"""
Filter HTML content by keywords, keeping only text objects (paragraphs, lists, etc.)
that contain at least one of the provided keywords.
"""

from bs4 import BeautifulSoup, Tag
from typing import Optional, List
import re

# Import utilities
from logger import get_logger

logger = get_logger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by collapsing whitespace and lowercasing.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    # Collapse all whitespace to single spaces and strip
    return re.sub(r'\s+', ' ', text.lower().strip())


def find_adjacent_images(element: Tag, container: Tag) -> List[Tag]:
    """
    Find images that are immediately before or after the given element within the container.
    Looks for images that are siblings or in sibling elements.
    
    Args:
        element: The element to find adjacent images for
        container: The container to search within
        
    Returns:
        List of image elements (img, picture, figure) that are adjacent to the element
    """
    adjacent_images = []
    
    # Get all direct children of the container in document order
    container_children = [child for child in container.children if isinstance(child, Tag)]
    
    element_index = None
    try:
        # Find the index of the element's parent (or element itself if it's a direct child)
        element_parent = element.parent
        if element_parent == container:
            # Element is a direct child
            element_index = container_children.index(element)
        else:
            # Find the direct child that contains this element
            while element_parent and element_parent != container:
                if element_parent.parent == container:
                    element_index = container_children.index(element_parent)
                    break
                element_parent = element_parent.parent
            
            if element_index is None:
                # Couldn't find parent in direct children, use descendants approach
                return find_adjacent_images_by_descendants(element, container)
    except (ValueError, AttributeError):
        # Fallback to descendants approach
        return find_adjacent_images_by_descendants(element, container)
    
    if element_index is None:
        return find_adjacent_images_by_descendants(element, container)
    
    # Look for images in siblings before and after
    # Check previous sibling
    if element_index > 0:
        prev_sibling = container_children[element_index - 1]
        # Find images in previous sibling
        prev_images = prev_sibling.find_all(['img', 'picture', 'figure'])
        adjacent_images.extend(prev_images)
    
    # Check next sibling
    if element_index < len(container_children) - 1:
        next_sibling = container_children[element_index + 1]
        # Find images in next sibling
        next_images = next_sibling.find_all(['img', 'picture', 'figure'])
        adjacent_images.extend(next_images)
    
    # Also check if there are images as direct siblings (same parent as element)
    if element.parent == container:
        # Element is direct child, check siblings
        element_siblings = [sib for sib in element.parent.children if isinstance(sib, Tag)]
        try:
            elem_idx = element_siblings.index(element)
            # Check previous direct sibling
            if elem_idx > 0:
                prev = element_siblings[elem_idx - 1]
                if prev.name in ['img', 'picture', 'figure']:
                    adjacent_images.append(prev)
            # Check next direct sibling
            if elem_idx < len(element_siblings) - 1:
                next_elem = element_siblings[elem_idx + 1]
                if next_elem.name in ['img', 'picture', 'figure']:
                    adjacent_images.append(next_elem)
        except ValueError:
            pass
    
    return adjacent_images


def find_adjacent_images_by_descendants(element: Tag, container: Tag) -> List[Tag]:
    """
    Fallback method to find adjacent images by examining all descendants.
    
    Args:
        element: The element to find adjacent images for
        container: The container to search within
        
    Returns:
        List of image elements that are adjacent to the element
    """
    adjacent_images = []
    
    # Get all elements in document order
    all_elements = [elem for elem in container.descendants if isinstance(elem, Tag)]
    
    try:
        element_index = all_elements.index(element)
    except ValueError:
        return adjacent_images
    
    # Find images within 3 positions before or after
    for i in range(max(0, element_index - 3), min(len(all_elements), element_index + 4)):
        if i == element_index:
            continue
        candidate = all_elements[i]
        if candidate.name in ['img', 'picture', 'figure']:
            # Make sure it's not nested inside the element
            parent = candidate.parent
            is_nested = False
            while parent and parent != container:
                if parent == element:
                    is_nested = True
                    break
                parent = parent.parent
            if not is_nested:
                adjacent_images.append(candidate)
    
    return adjacent_images


def filter_content_by_keywords(
    html_content: str,
    keywords: Optional[List[str]] = None,
    include_first_paragraph: bool = False
) -> str:
    """
    Filter HTML content by keywords, keeping only text objects (paragraphs, lists, etc.)
    that contain at least one of the provided keywords.
    
    A "text object" here means any discrete unit of content: <p>, <div>, <li>, <ul>, <ol>, etc.
    If keywords are provided, only returns content units that contain at least one keyword.
    If include_first_paragraph is True, always includes the first content unit regardless of keyword matching.
    
    This function also:
    - Preserves CSS styles (style tags) from the original HTML
    - Includes images that are above or below kept text bodies
    
    Args:
        html_content: The HTML content string to filter (output from content_extraction.py)
        keywords: Optional list of keywords to filter by. If None or empty, returns original content.
        include_first_paragraph: If True, always include first content unit (only useful if keywords provided)
        
    Returns:
        Filtered HTML string with only matching content units, including adjacent images and preserved CSS
    """
    # If no keywords provided, return all content units
    if not keywords:
        return html_content
    
    # Normalize keywords for comparison
    normalized_keywords = [normalize_text(kw) for kw in keywords if kw]
    if not normalized_keywords:
        return html_content
    
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Preserve all style tags from the original HTML
        original_style_tags = soup.find_all('style')
        
        # Get the root container (could be body, article, div, etc.)
        container_tag = soup.find(['body', 'article', 'main', 'div', 'section'])
        if container_tag is None:
            # If no container found, use the root element
            container_tag = soup.contents[0] if soup.contents and isinstance(soup.contents[0], Tag) else soup
        
        # Find all discrete content units: paragraphs, divs, list items, and lists
        # These are treated as discrete units of content (any block-level element)
        # BeautifulSoup's find_all returns elements in document order
        content_units = container_tag.find_all(['p', 'div', 'li', 'ul', 'ol', 'article', 'section', 'blockquote'])
        
        # Get only top-level content units (not nested within another content unit)
        # This ensures we filter at the right level and maintain HTML structure
        top_level_units = []
        for unit in content_units:
            # Check if any parent (up to container_tag) is also a content unit
            is_nested = False
            parent = unit.parent
            while parent and parent != container_tag:
                if isinstance(parent, Tag) and parent.name in ['p', 'div', 'li', 'ul', 'ol', 'article', 'section', 'blockquote']:
                    is_nested = True
                    break
                parent = parent.parent
            if not is_nested:
                top_level_units.append(unit)
        
        # Track first content unit for include_first_paragraph logic
        # (already in document order from find_all)
        first_unit = top_level_units[0] if top_level_units else None
        
        # Track which content units to keep and their adjacent images
        units_to_keep = set()
        images_to_keep = set()
        
        # Identify content units to keep
        for unit in top_level_units:
            unit_text = normalize_text(unit.get_text())
            contains_keyword = any(kw in unit_text for kw in normalized_keywords)
            
            # Always include first content unit if include_first_paragraph is True
            if include_first_paragraph and unit is first_unit:
                units_to_keep.add(unit)
                # Find and mark adjacent images
                adjacent_imgs = find_adjacent_images(unit, container_tag)
                for img in adjacent_imgs:
                    images_to_keep.add(img)
            elif contains_keyword:
                units_to_keep.add(unit)
                # Find and mark adjacent images
                adjacent_imgs = find_adjacent_images(unit, container_tag)
                for img in adjacent_imgs:
                    images_to_keep.add(img)
        
        # Remove content units that are not in the keep set
        for unit in top_level_units:
            if unit not in units_to_keep:
                unit.decompose()
        
        # Remove images that are not adjacent to kept content units
        # But keep images that are already inside kept content units
        all_images = container_tag.find_all(['img', 'picture', 'figure'])
        for img_elem in all_images:
            # Check if image is inside a kept content unit
            is_inside_kept_unit = False
            parent = img_elem.parent
            while parent and parent != container_tag:
                if parent in units_to_keep:
                    is_inside_kept_unit = True
                    break
                parent = parent.parent
            
            # If image is not inside a kept unit and not in images_to_keep, remove it
            if not is_inside_kept_unit and img_elem not in images_to_keep:
                img_elem.decompose()
        
        # Preserve style tags - they should still be in the soup if they were in the original
        # But if the container is a fragment (not a full HTML doc), we need to handle style tags separately
        remaining_style_tags = soup.find_all('style')
        
        # Get the filtered container HTML (preserves inline styles, classes, IDs, etc.)
        container_html = str(container_tag)
        
        # If we have a full HTML document structure, return it (style tags are already preserved)
        if soup.find('html'):
            return str(soup)
        elif soup.find('head'):
            # We have head section, return the full soup
            return str(soup)
        else:
            # Fragment HTML - prepend style tags if they exist
            # Note: style tags are preserved in the soup, so if they were in the original,
            # they should still be accessible
            if original_style_tags:
                # Extract style content and prepend it
                style_content = '\n'.join(str(tag) for tag in original_style_tags)
                return f'{style_content}\n{container_html}'
            return container_html
        
    except Exception as e:
        logger.warning(f"Error filtering content by keywords: {e}")
        # Return original content if filtering fails
        return html_content

