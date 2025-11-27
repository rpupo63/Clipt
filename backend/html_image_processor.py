#!/usr/bin/env python3
"""
HTML image preprocessing utilities.
Handles image downloading, deduplication, resizing, and conversion to data URIs.
Properly identifies and processes img, picture, and figure elements.
"""

import base64
from io import BytesIO
from typing import Optional
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor, as_completed

from logger import get_logger
from url_utils import normalize_image_url
from image_utils import extract_image_info, download_image, resize_image, apply_image_styling

logger = get_logger(__name__)

# Try to import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - image resizing will be limited")


def process_images_in_extracted_content(
    html_content: str,
    base_url: Optional[str] = None,
    target_width: int = 800,
    width_percent: float = 33.333,
    position: str = 'center'
) -> str:
    """
    Process all images in extracted HTML content: identify, download, and resize.
    
    This function properly handles:
    - img tags (with src, srcset, data-src, etc.)
    - picture elements (with source tags)
    - figure elements (containing img tags)
    
    Args:
        html_content: HTML content as string (from content extraction)
        base_url: Base URL for resolving relative image URLs
        target_width: Target width for all images in pixels (default: 800)
        width_percent: Width as percentage of container (default: 33.333 for 1/3 width)
        position: Image position - 'center', 'left', or 'right' (default: 'center')
        
    Returns:
        str: HTML content with processed images (as data URIs)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all image-related elements: img, picture, and figure
    all_image_elements = soup.find_all(['img', 'picture', 'figure'])
    
    if not all_image_elements:
        logger.debug("No images found in extracted content")
        return html_content
    
    logger.info(f"Found {len(all_image_elements)} image elements to process")
    
    # Track elements to skip (children of processed elements)
    elements_to_skip = set()
    
    # Collect unique image URLs using extract_image_info for proper identification
    image_url_map = {}  # Maps normalized URL to original URL
    element_to_url = {}  # Maps element to normalized URL
    
    for img_element in all_image_elements:
        # Skip if this element is a child of another image element we're processing
        if img_element in elements_to_skip:
            continue
        
        # If this is a picture or figure, mark its img children to skip
        if img_element.name in ('picture', 'figure'):
            for child_img in img_element.find_all('img'):
                elements_to_skip.add(child_img)
        
        # Check if this img is a child of a picture/figure that we are also processing
        if img_element.name == 'img':
            parent = img_element.parent
            if parent and parent.name in ('picture', 'figure') and parent in all_image_elements:
                continue
        
        # Use extract_image_info to properly identify the image URL
        # This handles srcset, picture sources, lazy loading, etc.
        img_info = extract_image_info(
            img_element,
            base_url=base_url,
            fetch_dimensions=False,  # We'll fetch dimensions during download
            fetch_content=False  # We'll download during processing
        )
        
        img_url = img_info.get('url')
        if not img_url:
            logger.debug(f"Could not extract URL from {img_element.name} element")
            continue
        
        normalized_url = normalize_image_url(img_url)
        if normalized_url not in image_url_map:
            image_url_map[normalized_url] = img_url
        
        element_to_url[img_element] = normalized_url
    
    if not image_url_map:
        logger.warning("No valid image URLs found in extracted content")
        return html_content
    
    logger.info(f"Processing {len(image_url_map)} unique images")
    
    # Download and process each unique image in parallel
    processed_images = {}  # Maps normalized URL to (resized_bytes, width, height)
    
    def download_and_process_image(normalized_url, original_url):
        """Helper function to download and process a single image."""
        try:
            image_bytes, width, height = download_image(original_url)
            
            if image_bytes:
                # Resize to target width
                resized_bytes, new_width, new_height = resize_image(image_bytes, target_width)
                return normalized_url, (resized_bytes, new_width, new_height)
        except Exception as e:
            logger.warning(f"Failed to download/process image {original_url}: {e}")
        return normalized_url, None
    
    # Use ThreadPoolExecutor for parallel downloads (max 5 concurrent downloads)
    max_workers = min(5, len(image_url_map)) if image_url_map else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_url = {
            executor.submit(download_and_process_image, norm_url, orig_url): norm_url
            for norm_url, orig_url in image_url_map.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            normalized_url, result = future.result()
            if result is not None:
                processed_images[normalized_url] = result
    
    logger.info(f"Successfully processed {len(processed_images)}/{len(image_url_map)} images")
    
    # Replace all image elements with processed versions
    for img_element in all_image_elements:
        if img_element in elements_to_skip:
            continue
        
        # Check if this img is a child of a picture/figure that we are also processing
        if img_element.name == 'img':
            parent = img_element.parent
            if parent and parent.name in ('picture', 'figure') and parent in all_image_elements:
                continue
        
        normalized_url = element_to_url.get(img_element)
        if not normalized_url or normalized_url not in processed_images:
            continue
        
        resized_bytes, new_width, new_height = processed_images[normalized_url]
        
        # Convert to data URI
        # Determine image format from bytes (more reliable than URL extension)
        img_format = 'png'  # Default
        if PIL_AVAILABLE:
            try:
                img_check = Image.open(BytesIO(resized_bytes))
                format_map = {
                    'JPEG': 'jpeg',
                    'PNG': 'png',
                    'GIF': 'gif',
                    'WEBP': 'webp'
                }
                img_format = format_map.get(img_check.format, 'png')
            except Exception:
                # Fallback to URL-based detection
                img_url = image_url_map.get(normalized_url, '')
                if img_url.lower().endswith(('.jpg', '.jpeg')):
                    img_format = 'jpeg'
                elif img_url.lower().endswith('.gif'):
                    img_format = 'gif'
                elif img_url.lower().endswith('.webp'):
                    img_format = 'webp'
        else:
            # Fallback to URL-based detection if PIL not available
            img_url = image_url_map.get(normalized_url, '')
            if img_url.lower().endswith(('.jpg', '.jpeg')):
                img_format = 'jpeg'
            elif img_url.lower().endswith('.gif'):
                img_format = 'gif'
            elif img_url.lower().endswith('.webp'):
                img_format = 'webp'
        
        base64_data = base64.b64encode(resized_bytes).decode('utf-8')
        data_uri = f'data:image/{img_format};base64,{base64_data}'
        
        # Update the image element based on its type
        if img_element.name == 'img':
            # Simple img tag - update src and dimensions
            img_element['src'] = data_uri
            # Remove srcset and other responsive image attributes
            for attr in ['srcset', 'data-srcset', 'data-src', 'data-lazy-src', 'data-original', 'sizes']:
                if attr in img_element.attrs:
                    del img_element[attr]
            if new_width:
                img_element['width'] = str(new_width)
            if new_height:
                img_element['height'] = str(new_height)
            # Apply styling with width_percent and position
            apply_image_styling(img_element, width_percent=width_percent, position=position)
        elif img_element.name == 'picture':
            # Picture element - replace with simple img tag
            # Find the img tag inside picture
            inner_img = img_element.find('img')
            if inner_img:
                # Create a new img tag with the processed image
                new_img = soup.new_tag('img')
                new_img['src'] = data_uri
                # Preserve alt text if present
                if inner_img.get('alt'):
                    new_img['alt'] = inner_img.get('alt')
                if new_width:
                    new_img['width'] = str(new_width)
                if new_height:
                    new_img['height'] = str(new_height)
                # Apply styling with width_percent and position
                apply_image_styling(new_img, width_percent=width_percent, position=position)
                # Replace picture with img
                img_element.replace_with(new_img)
            else:
                # No img found, just update the picture element itself (shouldn't happen)
                logger.warning("Picture element has no img tag")
        elif img_element.name == 'figure':
            # Figure element - update the img inside it
            inner_img = img_element.find('img')
            if inner_img:
                inner_img['src'] = data_uri
                # Remove srcset and other responsive image attributes
                for attr in ['srcset', 'data-srcset', 'data-src', 'data-lazy-src', 'data-original', 'sizes']:
                    if attr in inner_img.attrs:
                        del inner_img[attr]
                if new_width:
                    inner_img['width'] = str(new_width)
                if new_height:
                    inner_img['height'] = str(new_height)
                # Apply styling with width_percent and position
                apply_image_styling(inner_img, width_percent=width_percent, position=position)
            else:
                logger.warning("Figure element has no img tag")
    
    logger.debug("Image processing complete")
    return str(soup)
