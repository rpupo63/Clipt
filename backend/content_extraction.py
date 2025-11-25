#!/usr/bin/env python3
"""
HTML content extraction by finding the smallest container
that contains both a first and last sentence.
"""

from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Optional, Tuple, List
import re


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


def filter_paragraphs_and_lists(
    container: Tag,
    keywords: Optional[List[str]] = None,
    return_first_paragraph: bool = False
) -> Tag:
    """
    Filter discrete content units (paragraphs, divs, lists, list items) within a container by keywords.
    
    A "paragraph" here means any discrete unit of content: <p>, <div>, <li>, <ul>, <ol>, etc.
    If keywords are provided, only returns content units that contain at least one keyword.
    If return_first_paragraph is True, always includes the first content unit regardless of keyword matching.
    
    Args:
        container: The container Tag to filter
        keywords: Optional list of keywords to filter by
        return_first_paragraph: If True, always include first content unit (only useful if keywords provided)
        
    Returns:
        A new Tag with filtered content (or original if no keywords provided)
    """
    # If no keywords provided, return all content units
    if not keywords:
        return container
    
    # Normalize keywords for comparison
    normalized_keywords = [normalize_text(kw) for kw in keywords if kw]
    if not normalized_keywords:
        return container
    
    # Create a copy of the container to modify (to avoid modifying the original)
    container_str = str(container)
    filtered_soup = BeautifulSoup(container_str, 'html.parser')
    
    # Get the root element (should be the container tag)
    # BeautifulSoup wraps the content, so we need to get the actual tag
    if filtered_soup.contents:
        container_tag = filtered_soup.contents[0] if isinstance(filtered_soup.contents[0], Tag) else None
    else:
        container_tag = None
    
    # If we couldn't get a proper tag, try to find it by name
    if container_tag is None:
        container_tag = filtered_soup.find(container.name)
        if container_tag is None:
            # Last resort: return original container
            return container
    
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
    
    # Track first content unit for return_first_paragraph logic
    # (already in document order from find_all)
    first_unit = top_level_units[0] if top_level_units else None
    
    # Filter content units
    for unit in top_level_units:
        unit_text = normalize_text(unit.get_text())
        contains_keyword = any(kw in unit_text for kw in normalized_keywords)
        
        # Always include first content unit if return_first_paragraph is True
        if return_first_paragraph and unit is first_unit:
            continue
        
        # Remove content unit if it doesn't contain any keyword
        if not contains_keyword:
            unit.decompose()
    
    # Return the filtered container tag
    return container_tag


def extract_content_between_sentences(
    html_content: str,
    first_sentence: str,
    last_sentence: str,
    keywords: Optional[List[str]] = None,
    return_first_paragraph: bool = False
) -> Tuple[Optional[str], Optional[Tag]]:
    """
    Extract the smallest HTML container that contains both the first and last sentence.
    Optionally filter paragraphs and lists by keywords.
    
    Args:
        html_content: The full HTML content as a string
        first_sentence: The first sentence to find
        last_sentence: The last sentence to find
        keywords: Optional list of keywords to filter paragraphs/lists by
        return_first_paragraph: If True, always include first paragraph regardless of keywords
        
    Returns:
        Tuple of (extracted HTML string, container Tag) or (None, None) if not found
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find elements containing each sentence
    first_element = find_element_containing_sentence(soup, first_sentence)
    if first_element is None:
        return None, None
    
    last_element = find_element_containing_sentence(soup, last_sentence)
    if last_element is None:
        return None, None
    
    # Find the smallest common container
    container = find_common_container(first_element, last_element)
    if container is None:
        return None, None
    
    # Apply keyword filtering if keywords are provided
    if keywords:
        container = filter_paragraphs_and_lists(container, keywords, return_first_paragraph)
    
    return str(container), container


def extract_from_file(
    filepath: str,
    first_sentence: str,
    last_sentence: str,
    keywords: Optional[List[str]] = None,
    return_first_paragraph: bool = False
) -> Tuple[Optional[str], Optional[Tag]]:
    """
    Extract content from an HTML file between two sentences.
    Optionally filter paragraphs and lists by keywords.
    
    Args:
        filepath: Path to the HTML file
        first_sentence: The first sentence to find
        last_sentence: The last sentence to find
        keywords: Optional list of keywords to filter paragraphs/lists by
        return_first_paragraph: If True, always include first paragraph regardless of keywords
        
    Returns:
        Tuple of (extracted HTML string, container Tag) or (None, None) if not found
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return extract_content_between_sentences(
        html_content, 
        first_sentence, 
        last_sentence,
        keywords=keywords,
        return_first_paragraph=return_first_paragraph
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


def extract_main_content(
    html_content: str,
    first_sentence: Optional[str] = None,
    last_sentence: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    include_first_paragraph: bool = False
) -> str:
    """
    Extract main content from HTML, optionally using first/last sentences and keyword filtering.

    If first_sentence and last_sentence are provided, extracts the smallest container
    containing both. Otherwise, attempts to extract the main content body.

    Args:
        html_content: The full HTML content as a string
        first_sentence: Optional first sentence to find
        last_sentence: Optional last sentence to find
        keywords: Optional list of keywords to filter paragraphs/lists by
        include_first_paragraph: If True, always include first paragraph regardless of keywords

    Returns:
        Extracted HTML string
    """
    # If we have both first and last sentences, use the precise extraction
    if first_sentence and last_sentence:
        extracted_html, container = extract_content_between_sentences(
            html_content,
            first_sentence,
            last_sentence,
            keywords=keywords,
            return_first_paragraph=include_first_paragraph
        )
        if extracted_html:
            return extracted_html
        # If extraction failed, fall through to heuristic method

    # Fallback: Use heuristic approach to find main content
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
                break
        except:
            continue

    # If no main content found, use body
    if not main_content:
        main_content = soup.find('body')

    # If still nothing, use the whole soup
    if not main_content:
        main_content = soup

    # Apply keyword filtering if requested
    if keywords:
        main_content = filter_paragraphs_and_lists(
            main_content,
            keywords,
            include_first_paragraph
        )

    return str(main_content)


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
    
    print(f"\nContainer tag: <{container.name}>")
    if container.get('class'):
        print(f"Container class: {container.get('class')}")
    if container.get('id'):
        print(f"Container id: {container.get('id')}")
    
    print("\n" + "=" * 80)
    print("EXTRACTED HTML:")
    print("=" * 80 + "\n")
    print(extracted_html)
    
    return extracted_html


if __name__ == "__main__":
    main()