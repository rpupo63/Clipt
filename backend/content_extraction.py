#!/usr/bin/env python3
"""
HTML content extraction by finding the smallest container
that contains both a first and last sentence.
"""

from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Optional, Tuple, List
import re

# Import utilities
from logger import get_logger
from clean_content import clean_extracted_content

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


def find_element_containing_sentence(soup: BeautifulSoup, sentence: str) -> Optional[Tag]:
    """
    Find the deepest element that contains the given sentence.
    
    Args:
        soup: BeautifulSoup object to search in
        sentence: The sentence to find
        
    Returns:
        The deepest Tag containing the sentence, or None if not found
    """
    normalized_sentence = normalize_text(sentence)
    if not normalized_sentence:
        return None
    
    # Find all text nodes that might contain the sentence
    candidates = []
    
    for element in soup.descendants:
        if isinstance(element, Tag):
            # Get direct text content of this element (including children)
            element_text = normalize_text(element.get_text())
            if normalized_sentence in element_text:
                candidates.append(element)
    
    if not candidates:
        return None
    
    # Return the deepest element (most specific) that contains the sentence
    # The deepest element is the one with the most ancestors
    def depth(tag: Tag) -> int:
        count = 0
        parent = tag.parent
        while parent:
            count += 1
            parent = parent.parent
        return count
    
    # Sort by depth descending and return the deepest
    candidates.sort(key=depth, reverse=True)
    return candidates[0]


def contains_element(container: Tag, target: Tag) -> bool:
    """
    Check if the container element contains the target element.
    
    Args:
        container: The potential container Tag
        target: The Tag to check for containment
        
    Returns:
        True if container contains target, False otherwise
    """
    if container is target:
        return True
    
    # Walk up from target to see if we reach container
    current = target.parent
    while current:
        if current is container:
            return True
        current = current.parent
    
    return False


def find_common_container(element1: Tag, element2: Tag) -> Optional[Tag]:
    """
    Find the smallest container that contains both elements.
    
    Starts from element1 and walks up the tree until finding
    a container that also contains element2.
    
    Args:
        element1: First element
        element2: Second element
        
    Returns:
        The smallest common container Tag, or None if none found
    """
    if element1 is element2:
        return element1
    
    # Check if one already contains the other
    if contains_element(element1, element2):
        return element1
    if contains_element(element2, element1):
        return element2
    
    # Walk up from element1 until we find a parent that contains element2
    current = element1.parent
    while current:
        if isinstance(current, Tag) and contains_element(current, element2):
            return current
        current = current.parent
    
    return None


def extract_content_between_sentences(
    html_content: str,
    first_sentence: str,
    last_sentence: str
) -> Tuple[Optional[str], Optional[Tag]]:
    """
    Extract the smallest HTML container that contains both the first and last sentence.

    Args:
        html_content: The full HTML content as a string
        first_sentence: The first sentence to find
        last_sentence: The last sentence to find

    Returns:
        Tuple of (extracted HTML string, container Tag) or (None, None) if not found
    """
    logger.debug("Extracting content between sentences")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find elements containing each sentence
    first_element = find_element_containing_sentence(soup, first_sentence)
    if first_element is None:
        logger.warning("Could not find element containing first sentence")
        return None, None

    logger.debug(f"Found first sentence in <{first_element.name}> element")

    last_element = find_element_containing_sentence(soup, last_sentence)
    if last_element is None:
        logger.warning("Could not find element containing last sentence")
        return None, None

    logger.debug(f"Found last sentence in <{last_element.name}> element")

    # Find the smallest common container
    container = find_common_container(first_element, last_element)
    if container is None:
        logger.warning("Could not find common container for sentences")
        return None, None

    logger.debug(f"Found common container: <{container.name}>")

    # Return container as HTML string
    # Note: str(container) preserves all HTML attributes including:
    # - Inline styles (style attribute)
    # - CSS classes (class attribute)
    # - IDs (id attribute)
    # - All other HTML attributes
    return str(container), container


def extract_from_file(
    filepath: str,
    first_sentence: str,
    last_sentence: str
) -> Tuple[Optional[str], Optional[Tag]]:
    """
    Extract content from an HTML file between two sentences.
    
    Args:
        filepath: Path to the HTML file
        first_sentence: The first sentence to find
        last_sentence: The last sentence to find
        
    Returns:
        Tuple of (extracted HTML string, container Tag) or (None, None) if not found
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return extract_content_between_sentences(
        html_content, 
        first_sentence, 
        last_sentence
    )


def get_ancestors(element: Tag) -> List[Tag]:
    """
    Get all ancestors of an element, from immediate parent to root.

    Args:
        element: The element to get ancestors for

    Returns:
        List of ancestor Tags, from nearest to farthest
    """
    ancestors = []
    current = element.parent
    while current:
        if isinstance(current, Tag):
            ancestors.append(current)
        current = current.parent
    return ancestors


def remove_padding_from_style(style: str) -> str:
    """
    Remove padding-related CSS properties from a style string.
    
    Args:
        style: CSS style string (e.g., "padding: 10px; color: red;")
        
    Returns:
        Style string with padding properties removed
    """
    if not style:
        return ""
    
    # List of padding-related properties to remove
    padding_properties = [
        'padding',
        'padding-top',
        'padding-right',
        'padding-bottom',
        'padding-left'
    ]
    
    # Split style string by semicolons
    style_parts = [part.strip() for part in style.split(';')]
    
    # Filter out padding-related properties (case-insensitive)
    filtered_parts = []
    for part in style_parts:
        if not part:
            continue
        # Check if this part starts with any padding property
        is_padding = False
        for prop in padding_properties:
            if part.lower().startswith(prop.lower() + ':'):
                is_padding = True
                break
        if not is_padding:
            filtered_parts.append(part)
    
    # Rejoin the style parts
    return '; '.join(filtered_parts) + (';' if filtered_parts else '')


def remove_padding_from_container(container: Tag) -> None:
    """
    Remove padding from a container element's style attribute.
    
    Args:
        container: BeautifulSoup Tag element to modify
    """
    if not container or not isinstance(container, Tag):
        return
    
    style = container.get('style')
    if style:
        cleaned_style = remove_padding_from_style(style)
        if cleaned_style.strip():
            container['style'] = cleaned_style
        else:
            # Remove style attribute if it's now empty
            del container['style']


def extract_main_content(
    html_content: str,
    first_sentence: Optional[str] = None,
    last_sentence: Optional[str] = None
) -> str:
    """
    Extract main content from HTML, optionally using first/last sentences.

    If first_sentence and last_sentence are provided, extracts the smallest container
    containing both. Otherwise, attempts to extract the main content body.
    
    After extraction, removes secondary content like sidebars, ads, and trending sections.

    Args:
        html_content: The full HTML content as a string
        first_sentence: Optional first sentence to find
        last_sentence: Optional last sentence to find

    Returns:
        Extracted and cleaned HTML string
    """
    logger.debug("Extracting main content from HTML")

    # If we have both first and last sentences, use the precise extraction
    if first_sentence and last_sentence:
        logger.debug("Using AI-guided extraction with first/last sentences")
        extracted_html, container = extract_content_between_sentences(
            html_content,
            first_sentence,
            last_sentence
        )
        if extracted_html:
            logger.info("Successfully extracted content using sentence boundaries")
            # Remove padding from container if present
            if container:
                remove_padding_from_container(container)
                # Re-extract HTML after removing padding
                extracted_html = str(container)
            # Clean the extracted content before returning
            cleaned_html = clean_extracted_content(extracted_html)
            return cleaned_html
        logger.warning("Sentence-based extraction failed, falling back to heuristic method")

    # Fallback: Use heuristic approach to find main content
    logger.debug("Using heuristic content extraction")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Try to find main content area using common patterns
    main_content = None

    # Try common main content selectors in order of specificity
    content_selectors = [
        'main',
        'article',
        '[role="main"]',
        '.main-content',
        '.article-content',
        '.post-content',
        '.entry-content',
        '#main-content',
        '#content',
        '.content'
    ]

    for selector in content_selectors:
        try:
            main_content = soup.select_one(selector)
            if main_content:
                logger.debug(f"Found main content using selector: {selector}")
                break
        except Exception as e:
            logger.debug(f"Selector '{selector}' failed: {e}")
            continue

    # If no main content found, use body
    if not main_content:
        logger.debug("No main content selector matched, using body element")
        main_content = soup.find('body')

    # If still nothing, use the whole soup
    if not main_content:
        logger.warning("Could not find body element, using entire document")
        main_content = soup

    logger.info("Main content extraction completed")
    
    # Clean the extracted content before returning
    # Note: str(main_content) preserves all HTML attributes including:
    # - Inline styles (style attribute)
    # - CSS classes (class attribute)
    # - IDs (id attribute)
    # - All other HTML attributes
    cleaned_html = clean_extracted_content(str(main_content))
    return cleaned_html


def main():
    """
    Main function demonstrating usage.
    """
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python html_content_extraction.py <html_file> <first_sentence> <last_sentence>")
        print("\nExample:")
        print('  python html_content_extraction.py page.html "This is the beginning" "This is the end"')
        sys.exit(1)
    
    html_file = sys.argv[1]
    first_sentence = sys.argv[2]
    last_sentence = sys.argv[3]
    
    print(f"HTML file: {html_file}")
    print(f"First sentence: {first_sentence}")
    print(f"Last sentence: {last_sentence}")
    print("=" * 80)
    
    extracted_html, container = extract_from_file(html_file, first_sentence, last_sentence)
    
    if extracted_html is None:
        print("Could not find a common container for the given sentences.")
        sys.exit(1)
    
    # Clean the extracted content
    cleaned_html = clean_extracted_content(extracted_html)
    
    print(f"\nContainer tag: <{container.name}>")
    if container.get('class'):
        print(f"Container class: {container.get('class')}")
    if container.get('id'):
        print(f"Container id: {container.get('id')}")
    
    print("\n" + "=" * 80)
    print("EXTRACTED AND CLEANED HTML:")
    print("=" * 80 + "\n")
    print(cleaned_html)
    
    return cleaned_html


if __name__ == "__main__":
    main()