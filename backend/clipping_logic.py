#!/usr/bin/env python3
"""
Main function to process a URL and generate output in various formats.
Combines all extraction modules to create a formatted document.
"""

import sys
import os
import html
import tempfile
import uuid
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urlunparse, parse_qs, urljoin

# Import all the extraction modules
import site_preprocessing
import content_extraction
import header_extraction
from subtitle_validation import validate_subtitle_position
from image_positioning import find_image_below_title, find_image_above_title
import logo_extraction
import output_generation
import find_first_and_last_sentences
import keyword_filtering
import html_image_processor

# Import utilities
from url_utils import normalize_image_url
from image_utils import download_image, resize_image, extract_image_info, process_and_format_image
from constants import FileConfig, ContentConfig
from logger import get_logger

logger = get_logger(__name__)


# Note: normalize_image_url removed - now using normalize_image_url from url_utils


def extract_css_styles(html_content: str, extracted_content_html: str) -> str:
    """
    Extract CSS styles from original HTML that are relevant to the extracted content.
    
    This function:
    1. Extracts all <style> tags from the original HTML
    2. Identifies CSS classes and IDs used in the extracted content
    3. Filters CSS rules to only include those relevant to the extracted content
    4. Returns a combined CSS string
    
    Args:
        html_content: Original full HTML content
        extracted_content_html: Extracted content HTML
        
    Returns:
        str: Combined CSS styles as a string
    """
    try:
        original_soup = BeautifulSoup(html_content, 'html.parser')
        extracted_soup = BeautifulSoup(extracted_content_html, 'html.parser')
        
        # Collect all classes and IDs from extracted content
        extracted_classes = set()
        extracted_ids = set()
        extracted_tags = set()
        
        # Find all elements in extracted content
        for element in extracted_soup.find_all(True):  # True matches all tags
            # Collect tag names
            if element.name:
                extracted_tags.add(element.name)
            
            # Collect classes
            classes = element.get('class', [])
            if classes:
                if isinstance(classes, list):
                    extracted_classes.update(classes)
                else:
                    extracted_classes.add(classes)
            
            # Collect IDs
            element_id = element.get('id')
            if element_id:
                extracted_ids.add(element_id)
        
        # Extract all <style> tags from original HTML
        style_tags = original_soup.find_all('style')
        
        # Combine all CSS from style tags
        combined_css = []
        
        for style_tag in style_tags:
            if style_tag.string:
                css_content = style_tag.string
                combined_css.append(css_content)
        
        # If we have extracted classes/IDs, try to filter CSS (optional optimization)
        # For now, we'll include all CSS to ensure nothing is lost
        # This is safer than trying to parse and filter CSS rules
        
        return '\n\n'.join(combined_css)
        
    except Exception as e:
        logger.warning(f"Error extracting CSS styles: {e}")
        return ''


def process_url_to_file(url: str, filetype: str = 'html', output_file: str = None, keywords: list = None, include_first_paragraph: bool = False, use_ai_extraction: bool = True, image_width: float = 33.333, image_position: str = 'center') -> dict:
    """
    Process a URL and extract structured content.

    This function:
    1. Scrapes the webpage with ad-blocking
    2. Extracts logo, headers (title/subtitle), and main content
    3. (Optional) Uses AI to identify first/last contentful sentences for precise extraction
    4. Validates subtitle position
    5. Finds and inserts images around paragraphs
    6. Returns structured dictionary with title, subtitle, paragraphs, and images

    Args:
        url: URL to process
        filetype: Output format ('html', 'docx', 'pdf', 'md', 'markdown') - kept for compatibility
        output_file: Optional output file path - kept for compatibility
        keywords: Optional list of keywords to filter paragraphs. Only paragraphs
                 containing at least one keyword will be included.
        include_first_paragraph: If True, always include the first paragraph even if it
                                doesn't contain any keywords. Only applies when keywords are provided.
        use_ai_extraction: If True (default), uses Firecrawl + OpenAI to identify content boundaries.
                          Requires FIRECRAWL_API_KEY and OPENAI_API_KEY in .env file.
                          If False or if extraction fails, falls back to heuristic extraction.
        image_width: Width as percentage of container for images (default: 33.333 for 1/3 width)
        image_position: Image position - 'center', 'left', or 'right' (default: 'center')

    Returns:
        dict: Structured dictionary with:
            - title: str (not null)
            - subtitle: str or None
            - logo: dict with logo information
            - paragraphs: list of dicts with 'paragraph' (formatted HTML) and 'position' (int)
            - images: list of dicts with 'image' (formatted HTML) and 'position' (float)
    """
    logger.info("=" * 80)
    logger.info("Step 1: Scraping webpage with ad-blocker...")
    logger.info("=" * 80)

    # Step 1: Scrape the page
    html_content = site_preprocessing.scrape_page(url, wait_time=1)

    if not html_content:
        raise Exception("Failed to scrape the page")

    logger.info("=" * 80)
    logger.info("Step 2: Extracting logo...")
    logger.info("=" * 80)

    # Step 2: Extract logo
    root_domain = logo_extraction.get_root_domain(url)
    logo_result = logo_extraction.extract_logo(html_content, root_domain, base_url=url)

    if logo_result['element']:
        logger.info(f"✓ Logo found: {logo_result['url'] or logo_result['src']}")
    else:
        logger.info("⚠ No logo found")
    
    # Process logo with image sizing preferences if logo exists
    logo_html = None
    if logo_result.get('element'):
        logo_url = logo_result.get('url') or logo_result.get('src')
        if logo_url:
            # Use centralized image processing for logo
            logo_img_result = process_and_format_image(
                logo_url, 
                target_width=800, 
                width_percent=image_width, 
                position=image_position
            )
            logo_html = logo_img_result['html']
            # Store processed logo HTML in logo_result for later use
            logo_result['processed_html'] = logo_html
            logo_result['processed_width'] = logo_img_result['width']
            logo_result['processed_height'] = logo_img_result['height']
        elif logo_result.get('element') and hasattr(logo_result['element'], 'name') and logo_result['element'].name == 'svg':
            # For inline SVG, we'll handle it in build_final_html
            # but we can still apply sizing if needed
            logo_result['processed_html'] = None  # Will use original SVG

    logger.info("=" * 80)
    logger.info("Step 3: Extracting headers (title and subtitle)...")
    logger.info("=" * 80)

    # Step 3: Extract headers
    headers = header_extraction.extract_headers(html_content)

    # Extract title (must not be null)
    title_text = ""
    if headers.get('title') and headers['title'].get('text'):
        title_text = headers['title']['text']
    elif headers.get('title') and headers['title'].get('formatted_html'):
        # Extract text from formatted HTML if available
        title_soup = BeautifulSoup(headers['title']['formatted_html'], 'html.parser')
        title_text = title_soup.get_text(strip=True)
    
    if not title_text:
        # Fallback: try to get from HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        title_elem = soup.find('title') or soup.find('h1')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
    
    if not title_text:
        title_text = "Untitled"  # Ensure title is never null
    
    # Extract subtitle (nullable)
    subtitle_text = None
    if headers.get('subtitle') and headers['subtitle'].get('text'):
        subtitle_text = headers['subtitle']['text']
    elif headers.get('subtitle') and headers['subtitle'].get('formatted_html'):
        subtitle_soup = BeautifulSoup(headers['subtitle']['formatted_html'], 'html.parser')
        subtitle_text = subtitle_soup.get_text(strip=True)

    if headers['title']:
        logger.info(f"✓ Title found: {title_text[:80]}...")
    else:
        logger.info("⚠ No title found, using default")

    if subtitle_text:
        logger.info(f"✓ Subtitle found: {subtitle_text[:80]}...")
    else:
        logger.info("⚠ No subtitle found")

    logger.info("=" * 80)
    logger.info("Step 3.4: Finding image above title...")
    logger.info("=" * 80)

    # Step 3.4: Find image above title
    title_image_above = find_image_above_title(
        html_content,
        headers,
        base_url=url,
        max_distance=5
    )

    if title_image_above:
        img_url_above = title_image_above if isinstance(title_image_above, str) else title_image_above.get('url')
        if img_url_above:
            logger.info(f"✓ Image found above title: {img_url_above}")
    else:
        logger.info("⚠ No image found above title")

    logger.info("=" * 80)
    logger.info("Step 3.5: Finding image below title...")
    logger.info("=" * 80)

    # Step 3.5: Find image below title
    title_image = find_image_below_title(
        html_content,
        headers,
        base_url=url,
        max_distance=5
    )

    if title_image:
        img_url = title_image if isinstance(title_image, str) else title_image.get('url')
        if img_url:
            logger.info(f"✓ Title image found: {img_url}")
    else:
        logger.info("⚠ No image found below title")

    logger.info("=" * 80)
    logger.info("Step 3.75: Finding first and last contentful sentences...")
    logger.info("=" * 80)

    # Step 3.75: Extract first and last sentences using Firecrawl + OpenAI
    # This helps identify the precise content boundaries
    first_sentence = None
    last_sentence = None

    if use_ai_extraction:
        sentence_result = find_first_and_last_sentences.find_first_and_last_sentences_from_url(
            url,
            use_firecrawl=True
        )

        if sentence_result['success']:
            first_sentence = sentence_result['first_sentence']
            last_sentence = sentence_result['last_sentence']
            logger.info("✓ Successfully extracted content boundaries")
        else:
            logger.info(f"⚠ Could not extract sentences: {sentence_result['error']}")
            logger.info("  Will use heuristic content extraction instead")
    else:
        logger.info("  AI extraction disabled - using heuristic content extraction")

    logger.info("=" * 80)
    logger.info("Step 4: Extracting main content...")
    logger.info("=" * 80)

    # Step 4: Extract main content
    if first_sentence and last_sentence:
        logger.info("  Using AI-identified content boundaries for precise extraction")

    extracted_content_html = content_extraction.extract_main_content(
        html_content,
        first_sentence=first_sentence,
        last_sentence=last_sentence
    )
    logger.info("✓ Main content extracted")
    
    # Step 4.25: Process and resize images in extracted content
    logger.info("=" * 80)
    logger.info("Step 4.25: Processing images in extracted content...")
    logger.info("=" * 80)
    extracted_content_html = html_image_processor.process_images_in_extracted_content(
        extracted_content_html,
        base_url=url,
        target_width=800,
        width_percent=image_width,
        position=image_position
    )
    logger.info("✓ Images processed and resized in extracted content")

    # Step 4.5: Apply keyword filtering if keywords are provided
    if keywords:
        logger.info("=" * 80)
        logger.info("Step 4.5: Filtering content by keywords...")
        logger.info("=" * 80)
        logger.info(f"  Filtering paragraphs by keywords: {', '.join(keywords)}")
        if include_first_paragraph:
            logger.info("  Always including first paragraph (even if it doesn't match keywords)")
        
        extracted_content_html = keyword_filtering.filter_content_by_keywords(
            extracted_content_html,
            keywords=keywords,
            include_first_paragraph=include_first_paragraph
        )
        
        # Count paragraphs after filtering
        extracted_soup = BeautifulSoup(extracted_content_html, 'html.parser')
        para_count = len(extracted_soup.find_all('p'))
        logger.info(f"✓ Content filtered ({para_count} paragraphs after keyword filtering)")

    logger.info("=" * 80)
    logger.info("Step 5: Validating subtitle position...")
    logger.info("=" * 80)
    
    # Step 5: Validate subtitle position
    subtitle_validation = validate_subtitle_position(
        html_content,
        headers,
        extracted_content_html
    )
    
    include_subtitle = subtitle_validation['is_valid']
    if include_subtitle:
        logger.info("✓ Subtitle is correctly positioned - will be included")
    else:
        logger.info(f"⚠ Subtitle validation failed: {subtitle_validation['reason']}")
        logger.info("  Subtitle will not be included")
        subtitle_text = None  # Set to None if validation failed

    logger.info("=" * 80)
    logger.info("Step 6: Extracting divisible content and images from extracted content...")
    logger.info("=" * 80)
    
    # Step 6: Extract divisible content units and images from extracted content
    extracted_soup = BeautifulSoup(extracted_content_html, 'html.parser')
    
    # Get the root container (could be body, article, div, etc.)
    container_tag = extracted_soup.find(['body', 'article', 'main', 'div', 'section'])
    if container_tag is None:
        # If no container found, use the root element
        container_tag = extracted_soup.contents[0] if extracted_soup.contents and isinstance(extracted_soup.contents[0], Tag) else extracted_soup
    
    # Find all discrete content units: paragraphs, divs, list items, and lists
    # These are the divisible content units from content extraction
    content_units = container_tag.find_all(['p', 'div', 'li', 'ul', 'ol', 'article', 'section', 'blockquote'])
    
    # Get only top-level content units (not nested within another content unit)
    # This matches the logic from keyword_filtering.py for identifying content units
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
    
    # Use the divisible content units as paragraphs
    paragraphs = top_level_units
    
    # Track images to avoid duplicates using normalized URLs
    seen_normalized_urls = set()  # Normalized URLs (for duplicate detection)
    image_url_to_html = {}  # Maps normalized URL to formatted HTML
    
    # Process image above title if it exists
    title_image_above_html = None
    img_url_above = None
    if title_image_above:
        img_url_above = title_image_above if isinstance(title_image_above, str) else title_image_above.get('url')
        if img_url_above:
            normalized_url_above = normalize_image_url(img_url_above)
            if normalized_url_above not in seen_normalized_urls:
                seen_normalized_urls.add(normalized_url_above)
                
                # Use centralized image processing
                img_result_above = process_and_format_image(img_url_above, target_width=800, width_percent=image_width, position=image_position)
                
                title_image_above_html = img_result_above['html']
                image_url_to_html[normalized_url_above] = {
                    'html': title_image_above_html,
                    'width': img_result_above['width'],
                    'height': img_result_above['height']
                }
    
    # Process title image if it exists
    title_image_html = None
    if title_image:
        img_url = title_image if isinstance(title_image, str) else title_image.get('url')
        if img_url:
            normalized_url = normalize_image_url(img_url)
            if normalized_url not in seen_normalized_urls:
                seen_normalized_urls.add(normalized_url)
                
                # Use centralized image processing
                img_result = process_and_format_image(img_url, target_width=800, width_percent=image_width, position=image_position)
                
                title_image_html = img_result['html']
                image_url_to_html[normalized_url] = {
                    'html': title_image_html,
                    'width': img_result['width'],
                    'height': img_result['height']
                }
    
    # Build paragraphs list with positions
    paragraphs_list = []
    
    for i, para in enumerate(paragraphs):
        # Get paragraph HTML with formatting
        # Note: str(para) preserves all HTML attributes including:
        # - Inline styles (style attribute)
        # - CSS classes (class attribute)
        # - IDs (id attribute)
        # - All other HTML attributes
        para_html = str(para)
        paragraphs_list.append({
            'paragraph': para_html,
            'position': i + 1  # Auto-incrementing positions starting from 1
        })
    
    # Extract images directly from the extracted content HTML
    # Find all image tags in the extracted content
    all_images = extracted_soup.find_all(['img', 'picture', 'figure'])
    
    # Process images found in extracted content
    # Process images found in extracted content
    content_images = []
    # Create a set of elements to skip (children of processed elements)
    elements_to_skip = set()
    
    for img_element in all_images:
        if img_element in elements_to_skip:
            continue
            
        # If this is a picture or figure, mark its img children to skip
        if img_element.name in ('picture', 'figure'):
            for child_img in img_element.find_all('img'):
                elements_to_skip.add(child_img)
        
        # Check if this img is a child of a picture/figure that we are also processing
        # (In case the order was different or logic above missed it)
        if img_element.name == 'img':
            parent = img_element.parent
            if parent and parent.name in ('picture', 'figure') and parent in all_images:
                continue

        # Use centralized image extraction logic
        # This handles srcset, lazy loading, and various attributes automatically
        img_info = extract_image_info(
            img_element, 
            base_url=url, 
            fetch_dimensions=True, 
            fetch_content=True
        )
        
        img_url = img_info.get('url')
        if not img_url:
            continue
            
        normalized_url = normalize_image_url(img_url)
        if normalized_url not in seen_normalized_urls:
            seen_normalized_urls.add(normalized_url)
            
            # Get image content and dimensions from extraction result
            image_bytes = img_info.get('content')
            
            # Use centralized image processing
            img_result = process_and_format_image(img_url, image_bytes=image_bytes, target_width=800, width_percent=image_width, position=image_position)
            
            img_html = img_result['html']
            image_url_to_html[normalized_url] = {
                'html': img_html,
                'width': img_result['width'],
                'height': img_result['height']
            }
            
            content_images.append({
                'normalized_url': normalized_url,
                'element': img_element
            })
        else:
            # Already seen this image, but we still need to add it to content_images
            # so it can be positioned correctly if it appears multiple times
            content_images.append({
                'normalized_url': normalized_url,
                'element': img_element
            })
    
    logger.info(f"✓ Found {len(seen_normalized_urls)} unique images (including title images)")
    
    # Build images list with positions based on their position in extracted content
    images_list = []
    
    # Add image above title if it exists (position 0.1 - before title at 0.25)
    if title_image_above_html:
        # Get dimensions from map if available
        title_img_above_data = image_url_to_html.get(normalize_image_url(img_url_above) if img_url_above else '', {})
        if not isinstance(title_img_above_data, dict):
             # Handle case where it might not be in map or format is different (shouldn't happen with new code)
             title_img_above_data = {'html': title_image_above_html, 'width': 0, 'height': 0}
             
        images_list.append({
            'image': title_img_above_data.get('html', title_image_above_html),
            'position': 0.1,
            'width': title_img_above_data.get('width', 0),
            'height': title_img_above_data.get('height', 0)
        })
    
    # Add title image if it exists (position 0.5 - before first paragraph)
    if title_image_html:
        # Get dimensions from map if available
        title_img_data = image_url_to_html.get(normalize_image_url(img_url) if img_url else '', {})
        if not isinstance(title_img_data, dict):
             # Handle case where it might not be in map or format is different (shouldn't happen with new code)
             title_img_data = {'html': title_image_html, 'width': 0, 'height': 0}
             
        images_list.append({
            'image': title_img_data.get('html', title_image_html),
            'position': 0.5,
            'width': title_img_data.get('width', 0),
            'height': title_img_data.get('height', 0)
        })
    
    # Position images from extracted content based on their position relative to content units
    # Find the position of each image in the document order
    for img_data in content_images:
        normalized_url = img_data['normalized_url']
        img_element = img_data['element']
        
        if normalized_url not in image_url_to_html:
            continue
            
        img_data_entry = image_url_to_html[normalized_url]
        
        # Find which content unit this image is closest to
        # Check if image is before, within, or after each content unit
        img_position_in_doc = None
        
        # Get all elements in document order
        # Try container_tag first, but fallback to extracted_soup if image not found
        all_elements = list(container_tag.descendants)
        try:
            img_index = all_elements.index(img_element)
        except ValueError:
            # Image element not found in container descendants
            # Try to find it in the full extracted soup
            try:
                all_elements = list(extracted_soup.descendants)
                img_index = all_elements.index(img_element)
            except ValueError:
                # Still not found (shouldn't happen if img_element came from extracted_soup)
                # Just append to end
                images_list.append({
                    'image': img_data_entry['html'],
                    'position': len(paragraphs) + 0.5,
                    'width': img_data_entry.get('width', 0),
                    'height': img_data_entry.get('height', 0)
                })
                continue
        
        # Find the closest content unit (paragraph) to this image
        closest_para_idx = None
        min_distance = float('inf')
        
        for para_idx, para in enumerate(paragraphs):
            try:
                para_index = all_elements.index(para)
                distance = abs(img_index - para_index)
                if distance < min_distance:
                    min_distance = distance
                    closest_para_idx = para_idx
            except ValueError:
                continue
        
        if closest_para_idx is not None:
            para_position = closest_para_idx + 1  # Paragraph position (1-indexed)
            # Determine if image is before or after the paragraph
            try:
                para_index = all_elements.index(paragraphs[closest_para_idx])
                if img_index < para_index:
                    # Image is before paragraph: position = para_position - 0.5
                    img_position = para_position - 0.5
                else:
                    # Image is after paragraph: position = para_position + 0.5
                    img_position = para_position + 0.5
            except ValueError:
                # Fallback: place after paragraph
                img_position = para_position + 0.5
        else:
            # If we can't find a close paragraph, place at the end
            img_position = len(paragraphs) + 0.5
        
        images_list.append({
            'image': img_data_entry['html'],
            'position': img_position,
            'width': img_data_entry.get('width', 0),
            'height': img_data_entry.get('height', 0)
        })
    
    # Remove image duplicates (by normalized URL)
    # Keep first occurrence of each image
    seen_normalized_in_images = set()
    unique_images_list = []
    for img_dict in images_list:
        # Extract URL from image HTML to get normalized URL
        img_soup = BeautifulSoup(img_dict['image'], 'html.parser')
        img_tag = img_soup.find('img')
        if img_tag:
            img_src = img_tag.get('src', '')
            # For data URIs, we can't easily normalize, but we can use the position and content hash or just trust the loop
            # Actually, we already have unique images by normalized URL in content_images loop
            # But images_list might have duplicates if we added same image multiple times (not likely with current logic)
            # Let's just use the image content itself as key if src is data URI
            if img_src.startswith('data:'):
                key = img_src[:100] # Use first 100 chars of data URI as key
            else:
                key = normalize_image_url(img_src)
                
            if key not in seen_normalized_in_images:
                seen_normalized_in_images.add(key)
                unique_images_list.append(img_dict)
    
    images_list = unique_images_list
    
    # Remove images with the same index (keep the upper one - higher position)
    # Group by integer position (floor of position)
    position_groups = {}
    for img_dict in images_list:
        pos = img_dict['position']
        int_pos = int(pos)
        if int_pos not in position_groups:
            position_groups[int_pos] = []
        position_groups[int_pos].append(img_dict)
    
    # For each group, keep only the one with largest area
    # If areas are equal or 0, fallback to original logic (keep the one with lowest position value)
    final_images_list = []
    for int_pos, img_group in position_groups.items():
        if len(img_group) > 1:
            # Sort by area (descending) then by position (ascending)
            # We want largest area first. If areas equal, we want lowest position (highest in doc) first.
            # Python's sort is stable, so we can sort by position first, then by area
            
            # First sort by position (ascending) - this preserves "upper one" preference for ties
            img_group.sort(key=lambda x: x['position'])
            
            # Then sort by area (descending)
            img_group.sort(key=lambda x: (x.get('width', 0) or 0) * (x.get('height', 0) or 0), reverse=True)
            
            # Keep all unique images at this position, sorted by size
            # We previously dropped smaller images, but this caused issues with galleries
            final_images_list.extend(img_group)
        else:
            final_images_list.append(img_group[0])
    
    images_list = sorted(final_images_list, key=lambda x: x['position'])
    
    logger.info(f"✓ Processed {len(paragraphs_list)} paragraphs and {len(images_list)} images")
    
    logger.info("=" * 80)
    logger.info("Step 7: Extracting CSS styles...")
    logger.info("=" * 80)
    
    # Extract CSS styles from original HTML that are relevant to extracted content
    extracted_css = extract_css_styles(html_content, extracted_content_html)
    if extracted_css:
        logger.info(f"✓ Extracted {len(extracted_css)} characters of CSS styles")
    else:
        logger.info("⚠ No CSS styles found in original HTML")
    
    # Return structured dictionary
    return {
        'title': title_text,
        'subtitle': subtitle_text,
        'logo': logo_result,
        'paragraphs': paragraphs_list,
        'images': images_list,
        'css': extracted_css,
        'image_width': image_width,
        'image_position': image_position
    }


def build_final_html(content_dict: dict, image_width: float = None, image_position: str = None) -> str:
    """
    Build the final HTML document from structured content dictionary.
    Orders content by position: logo, title, subtitle, then paragraphs and images by their positions.
    
    Args:
        content_dict: Dictionary with:
            - title: str (not null)
            - subtitle: str or None
            - logo: dict with logo information
            - paragraphs: list of dicts with 'paragraph' (formatted HTML) and 'position' (int)
            - images: list of dicts with 'image' (formatted HTML) and 'position' (float)
            - image_width: float (optional) - width percentage for images
            - image_position: str (optional) - position for images ('center', 'left', 'right')
        image_width: Width as percentage of container for images (overrides content_dict if provided)
        image_position: Image position - 'center', 'left', or 'right' (overrides content_dict if provided)
        
    Returns:
        str: Complete HTML document
    """
    # Extract data from content_dict
    title_text = content_dict.get('title', 'Untitled')
    subtitle_text = content_dict.get('subtitle')
    logo_result = content_dict.get('logo', {})
    paragraphs_list = content_dict.get('paragraphs', [])
    images_list = content_dict.get('images', [])
    extracted_css = content_dict.get('css', '')
    
    # Get image styling parameters (use function args if provided, otherwise from content_dict, otherwise defaults)
    img_width = image_width if image_width is not None else content_dict.get('image_width', 33.333)
    img_position = image_position if image_position is not None else content_dict.get('image_position', 'center')
    
    # Start building HTML
    html_parts = ['<!DOCTYPE html>']
    html_parts.append('<html>')
    html_parts.append('<head>')
    html_parts.append('    <meta charset="utf-8">')
    html_parts.append(f'    <title>{html.escape(title_text, quote=False)}</title>')
    html_parts.append('    <style>')
    html_parts.append('        body {')
    html_parts.append('            font-family: Georgia, serif;')
    html_parts.append('            max-width: 800px;')
    html_parts.append('            margin: 0 auto;')
    html_parts.append('            padding: 20px;')
    html_parts.append('            line-height: 1.6;')
    html_parts.append('        }')
    # Build logo container styling (just for alignment, not sizing)
    # Logo images use the same inline styles as other images via process_and_format_image
    if img_position == 'left':
        logo_text_align = 'left'
    elif img_position == 'right':
        logo_text_align = 'right'
    else:  # center
        logo_text_align = 'center'
    
    html_parts.append('        .logo-container {')
    html_parts.append(f'            text-align: {logo_text_align};')
    html_parts.append('            margin: 20px 0 40px 0;')
    html_parts.append('        }')
    # Logo images use the same .content-image class and inline styles as all other images
    # No special CSS rules needed - inline styles from process_and_format_image take precedence
    html_parts.append('        h1 {')
    html_parts.append('            text-align: center;')
    html_parts.append('            margin: 30px 0 20px 0;')
    html_parts.append('        }')
    html_parts.append('        .subtitle {')
    html_parts.append('            text-align: center;')
    html_parts.append('            font-style: italic;')
    html_parts.append('            color: #666;')
    html_parts.append('            margin: 0 0 30px 0;')
    html_parts.append('            font-size: 1.1em;')
    html_parts.append('        }')
    # Build image styling based on position
    if img_position == 'left':
        img_margin = '20px 0'
    elif img_position == 'right':
        img_margin = '20px 0 20px auto'
    else:  # center
        img_margin = '20px auto'
    
    html_parts.append('        .content-image {')
    html_parts.append(f'            width: {img_width}%;')
    html_parts.append('            max-width: 100%;')
    html_parts.append('            height: auto;')
    html_parts.append(f'            margin: {img_margin};')
    html_parts.append('            display: block;')
    html_parts.append('        }')
    html_parts.append('        p {')
    html_parts.append('            margin: 15px 0;')
    html_parts.append('        }')
    
    # Add extracted CSS from original HTML to preserve formatting
    if extracted_css:
        html_parts.append('        /* Extracted CSS from original page */')
        # Indent each line of extracted CSS
        for line in extracted_css.split('\n'):
            if line.strip():  # Only add non-empty lines
                html_parts.append(f'        {line}')
    
    html_parts.append('    </style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    
    # Add logo - position 0
    if logo_result.get('element'):
        html_parts.append('    <div class="logo-container">')
        # Use processed logo HTML if available (from process_and_format_image)
        if logo_result.get('processed_html'):
            html_parts.append(f'        {logo_result["processed_html"]}')
        else:
            # Fallback to original logo handling
            logo_url = logo_result.get('url') or logo_result.get('src')
            if logo_url:
                # SECURITY: Properly escape URL and alt text for HTML
                logo_url_escaped = html.escape(logo_url, quote=True)
                img_alt = logo_result.get('alt', '') or 'Logo'
                img_alt_escaped = html.escape(img_alt, quote=True)
                html_parts.append(f'        <img src="{logo_url_escaped}" alt="{img_alt_escaped}" />')
            elif logo_result.get('element') and hasattr(logo_result['element'], 'name') and logo_result['element'].name == 'svg':
                # Handle inline SVG
                svg_html = str(logo_result['element'])
                html_parts.append(f'        {svg_html}')
        html_parts.append('    </div>')
    
    # Add image above title if it exists (position 0.1 - before title)
    # Find image with position 0.1 in images_list
    image_above_title = None
    for img_dict in images_list:
        if img_dict.get('position') == 0.1:
            image_above_title = img_dict['image']
            break
    
    if image_above_title:
        html_parts.append(f'        {image_above_title}')
    
    # Add title - position 0.25 (between logo and subtitle)
    title_text_escaped = html.escape(title_text, quote=False)
    html_parts.append(f'    <h1>{title_text_escaped}</h1>')
    
    # Add subtitle if present - position 0.3 (after title)
    if subtitle_text:
        subtitle_text_escaped = html.escape(subtitle_text, quote=False)
        html_parts.append(f'    <div class="subtitle">{subtitle_text_escaped}</div>')
    
    # Combine paragraphs and images, then sort by position
    all_content = []
    
    # Add paragraphs with their positions
    for para_dict in paragraphs_list:
        all_content.append({
            'type': 'paragraph',
            'position': float(para_dict['position']),
            'content': para_dict['paragraph']
        })
    
    # Add images with their positions (excluding image above title which is already added)
    for img_dict in images_list:
        if img_dict.get('position') != 0.1:  # Skip image above title, already added
            all_content.append({
                'type': 'image',
                'position': float(img_dict['position']),
                'content': img_dict['image']
            })
    
    # Sort by position
    all_content.sort(key=lambda x: x['position'])
    
    # Add content in order
    for item in all_content:
        if item['type'] == 'paragraph':
            html_parts.append(f'        {item["content"]}')
        elif item['type'] == 'image':
            html_parts.append(f'        {item["content"]}')
    
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    return '\n'.join(html_parts)


def process_url_to_html(url: str, keywords: list = None, include_first_paragraph: bool = False, use_ai_extraction: bool = True, image_width: float = 33.333, image_position: str = 'center') -> str:
    """
    Process a URL and return formatted HTML.
    This is the main function to use from the API.
    
    Args:
        url: URL to process
        keywords: Optional list of keywords to filter paragraphs. Only paragraphs
                 containing at least one keyword will be included.
        include_first_paragraph: If True, always include the first paragraph even if it
                                doesn't contain any keywords. Only applies when keywords are provided.
        use_ai_extraction: If True (default), uses Firecrawl + OpenAI to identify content boundaries.
                          Requires FIRECRAWL_API_KEY and OPENAI_API_KEY in .env file.
                          If False or if extraction fails, falls back to heuristic extraction.
        image_width: Width as percentage of container for images (default: 33.333 for 1/3 width)
        image_position: Image position - 'center', 'left', or 'right' (default: 'center')
    
    Returns:
        str: Complete formatted HTML document
    """
    # Get structured content
    content_dict = process_url_to_file(
        url=url,
        keywords=keywords,
        include_first_paragraph=include_first_paragraph,
        use_ai_extraction=use_ai_extraction,
        image_width=image_width,
        image_position=image_position
    )
    
    # Build and return final HTML
    return build_final_html(content_dict, image_width=image_width, image_position=image_position)


def main():
    """
    Main function with default values for testing.
    """
    # Default values
    default_url = "https://www.vogue.com/article/thin-little-scarf-fall-winter-trend"
    default_filetype = "html"
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = default_url
        print(f"No URL provided, using default: {url}")
        print(f"Usage: python {sys.argv[0]} <url> [filetype] [keywords...] [--include-first]")
        print(f"  keywords: Optional space-separated keywords to filter paragraphs")
        print(f"  --include-first: Always include first paragraph even if it doesn't match keywords")
    
    # Get filetype from command line or use default
    if len(sys.argv) > 2:
        filetype = sys.argv[2]
    else:
        filetype = default_filetype
        print(f"No filetype provided, using default: {filetype}")
        print(f"Supported filetypes: html, docx, pdf, md, markdown")
    
    # Get keywords and flags from command line (all arguments after filetype)
    keywords = None
    include_first_paragraph = False
    
    if len(sys.argv) > 3:
        # Check for --include-first flag
        args = sys.argv[3:]
        if '--include-first' in args:
            include_first_paragraph = True
            args = [arg for arg in args if arg != '--include-first']
        
        # Remaining arguments are keywords
        if args:
            keywords = args
            print(f"Keywords provided: {', '.join(keywords)}")
    
    if include_first_paragraph:
        print("Flag set: Always including first paragraph")
    
    try:
        output_path = process_url_to_file(
            url, 
            filetype, 
            keywords=keywords,
            include_first_paragraph=include_first_paragraph
        )
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"Output file: {output_path}")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

