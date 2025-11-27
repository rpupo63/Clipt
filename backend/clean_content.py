#!/usr/bin/env python3
"""
Content cleaning utilities for removing secondary/sidebar content from HTML.
"""

from bs4 import BeautifulSoup, Tag

# Import utilities
from logger import get_logger

logger = get_logger(__name__)


def remove_secondary_content(soup: BeautifulSoup) -> None:
    """
    Remove secondary/sidebar content from the BeautifulSoup object.
    
    This function removes elements that are typically not part of the main content.
    Uses conservative patterns to avoid removing main content.
    
    Args:
        soup: BeautifulSoup object to clean (modified in place)
    """
    logger.debug("Removing secondary content from HTML")
    
    # 1. Remove by semantic HTML elements (SAFE - these are explicitly for aside content)
    removed_count = 0
    for element in soup.find_all(['aside']):
        element.decompose()
        removed_count += 1
    
    if removed_count > 0:
        logger.debug(f"Removed {removed_count} <aside> elements")
    
    # 2. Remove by role attribute (SAFE - explicit semantic meaning)
    removed_count = 0
    for element in soup.find_all(attrs={'role': 'complementary'}):
        element.decompose()
        removed_count += 1
    
    if removed_count > 0:
        logger.debug(f"Removed {removed_count} elements with role='complementary'")
    
    # 3. CONSERVATIVE class/id patterns - only very specific matches
    # Match complete class names, not substrings
    removed_count = 0
    
    # Collect elements to remove (don't modify during iteration)
    elements_to_remove = []
    
    for element in soup.find_all(True):  # Find all elements
        # Skip if not a Tag (safety check)
        if not isinstance(element, Tag):
            continue
            
        classes = element.get('class', [])
        element_id = element.get('id', '')
        
        # Skip if attrs is None (shouldn't happen but safety check)
        if element.attrs is None:
            continue
        
        # Check if ANY class matches our patterns exactly
        should_remove = False
        
        for cls in classes:
            cls_lower = cls.lower()
            # Only exact matches or very specific patterns
            if cls_lower in ['sidebar', 'aside', 'rail', 'side-rail', 'right-rail', 
                            'left-rail', 'sticky-box', 'sticky-rail']:
                should_remove = True
                break
            # Recirc patterns (very specific to recommendation widgets)
            if 'recircmostpopular' in cls_lower.replace('-', '').replace('_', ''):
                should_remove = True
                break
            # Ad patterns (very specific)
            if cls_lower in ['adwrapper', 'ad-wrapper', 'ad-slot', 'ad-container']:
                should_remove = True
                break
        
        # Check ID with same conservative approach
        if element_id:
            id_lower = element_id.lower()
            if id_lower in ['sidebar', 'aside', 'rail', 'side-rail', 'right-rail', 'left-rail']:
                should_remove = True
        
        if should_remove:
            elements_to_remove.append(element)
    
    # Now remove collected elements
    for element in elements_to_remove:
        try:
            element.decompose()
            removed_count += 1
        except Exception as e:
            logger.debug(f"Failed to remove element: {e}")
    
    if removed_count > 0:
        logger.debug(f"Removed {removed_count} elements by class/id patterns")
    
    logger.info("Secondary content removal completed")


def remove_grid_aside_columns(soup: BeautifulSoup) -> None:
    """
    Remove aside columns from grid layouts.
    
    Only removes if VERY confident it's a sidebar (multiple strong indicators).
    
    Args:
        soup: BeautifulSoup object to clean (modified in place)
    """
    logger.debug("Removing grid aside columns")
    
    # Look for grid containers - be more specific
    grid_containers = []
    for element in soup.find_all(True):
        # Skip if not a Tag
        if not isinstance(element, Tag):
            continue
            
        classes = element.get('class', [])
        class_str = ' '.join(classes).lower()
        # Must have 'grid' or 'layout' AND not be the main content
        if ('grid' in class_str or 'layout' in class_str) and 'main' not in class_str:
            grid_containers.append(element)
    
    removed_count = 0
    for container in grid_containers:
        children = [child for child in container.children if isinstance(child, Tag)]
        
        # If there are exactly 2 direct children (typical main + aside layout)
        if len(children) == 2:
            first_child = children[0]
            second_child = children[1]
            
            # Analyze both children to determine which is main content
            first_classes = ' '.join(first_child.get('class', [])).lower()
            second_classes = ' '.join(second_child.get('class', [])).lower()
            
            first_id = first_child.get('id', '').lower()
            second_id = second_child.get('id', '').lower()
            
            # Count strong indicators for each
            first_is_aside = 0
            second_is_aside = 0
            
            # Strong positive indicators for aside (worth 3 points each)
            aside_strong = ['aside', 'sidebar', 'rail']
            for term in aside_strong:
                if term in first_classes or term in first_id:
                    first_is_aside += 3
                if term in second_classes or term in second_id:
                    second_is_aside += 3
            
            # Moderate indicators (worth 1 point each)
            aside_moderate = ['secondary', 'widget', 'sticky']
            for term in aside_moderate:
                if term in first_classes:
                    first_is_aside += 1
                if term in second_classes:
                    second_is_aside += 1
            
            # Strong indicators for main content (negative points for aside)
            main_strong = ['main', 'content', 'article', 'primary']
            for term in main_strong:
                if term in first_classes or term in first_id:
                    first_is_aside -= 3
                if term in second_classes or term in second_id:
                    second_is_aside -= 3
            
            # Only remove if we have strong confidence (score >= 3)
            try:
                if second_is_aside >= 3 and second_is_aside > first_is_aside:
                    logger.debug(f"Removing second column (aside score: {second_is_aside})")
                    second_child.decompose()
                    removed_count += 1
                elif first_is_aside >= 3 and first_is_aside > second_is_aside:
                    logger.debug(f"Removing first column (aside score: {first_is_aside})")
                    first_child.decompose()
                    removed_count += 1
            except Exception as e:
                logger.debug(f"Failed to remove grid column: {e}")
    
    if removed_count > 0:
        logger.debug(f"Removed {removed_count} grid aside columns")


def remove_by_data_attributes(soup: BeautifulSoup) -> None:
    """
    Remove elements based on data attributes that indicate secondary content.
    
    Very conservative - only removes very specific patterns.
    
    Args:
        soup: BeautifulSoup object to clean (modified in place)
    """
    logger.debug("Removing elements by data attributes")
    
    removed_count = 0
    
    # Only remove very specific data-testid values
    specific_testids = [
        'aside', 'sidebar', 'right-rail', 'left-rail',
        'social-icons', 'social-share',
        'recirc-most-popular', 'most-popular-wrapper'
    ]
    
    for testid in specific_testids:
        for element in soup.find_all(attrs={'data-testid': testid}):
            try:
                element.decompose()
                removed_count += 1
            except Exception as e:
                logger.debug(f"Failed to remove element with data-testid={testid}: {e}")
    
    # Remove RecircMostPopular components (very specific to Condé Nast sites)
    elements_to_remove = []
    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue
            
        classes = element.get('class', [])
        for cls in classes:
            cls_normalized = cls.lower().replace('-', '').replace('_', '')
            if 'recircmostpopular' in cls_normalized:
                elements_to_remove.append(element)
                break
    
    for element in elements_to_remove:
        try:
            element.decompose()
            removed_count += 1
        except Exception as e:
            logger.debug(f"Failed to remove RecircMostPopular element: {e}")
    
    # Remove consumer marketing units (very specific)
    elements_to_remove = []
    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue
            
        classes = element.get('class', [])
        for cls in classes:
            if 'ConsumerMarketing' in cls or 'consumer-marketing' in cls.lower():
                elements_to_remove.append(element)
                break
    
    for element in elements_to_remove:
        try:
            element.decompose()
            removed_count += 1
        except Exception as e:
            logger.debug(f"Failed to remove ConsumerMarketing element: {e}")
    
    # Remove social icon containers (safe - these are sharing widgets)
    elements_to_remove = []
    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue
            
        classes = element.get('class', [])
        for cls in classes:
            if 'SocialIcons' in cls or cls.lower() == 'social-icons':
                elements_to_remove.append(element)
                break
    
    for element in elements_to_remove:
        try:
            element.decompose()
            removed_count += 1
        except Exception as e:
            logger.debug(f"Failed to remove SocialIcons element: {e}")
    
    if removed_count > 0:
        logger.debug(f"Removed {removed_count} elements by data attributes")

def clean_extracted_content(html_string: str) -> str:
    """
    Clean extracted HTML content by removing secondary/sidebar elements.
    
    Uses conservative rules to avoid removing main content.
    
    Args:
        html_string: HTML content as a string
        
    Returns:
        Cleaned HTML string
    """
    if not html_string or len(html_string) < 100:
        logger.warning("Input HTML is too small or empty, skipping cleaning")
        return html_string
    
    logger.debug("Cleaning extracted content")
    logger.debug(f"HTML length before cleaning: {len(html_string)}")
    
    soup = BeautifulSoup(html_string, 'html.parser')
    
    # Apply all cleaning strategies
    remove_secondary_content(soup)
    remove_grid_aside_columns(soup)
    remove_by_data_attributes(soup)
    
    result = str(soup)
    logger.debug(f"HTML length after cleaning: {len(result)}")
    
    # Safety check - if we removed more than 80% of content, something went wrong
    if len(result) < len(html_string) * 0.2:
        logger.error(f"Cleaning removed too much content ({len(html_string)} -> {len(result)}), returning original")
        return html_string
    
    if len(result) < 100:
        logger.warning(f"Cleaned content is very small ({len(result)} bytes), returning original")
        return html_string
    
    logger.info(f"Content cleaning completed (removed {len(html_string) - len(result)} bytes)")
    
    return result

