#!/usr/bin/env python3
"""
Image utility functions for downloading, parsing, and extracting image information.
Handles srcset parsing, image downloading, and dimension extraction.
"""

from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin
import requests
import re
from io import BytesIO

# Import utilities
from constants import ImageConfig, NetworkConfig
from logger import get_logger
from network_utils import download_with_size_limit

logger = get_logger(__name__)


def apply_image_styling(img_element, width_percent: float = 33.333, position: str = 'center') -> None:
    """
    Apply consistent styling to an image element.
    
    This function ensures all images have the same CSS class and inline styles
    for consistent sizing and positioning across the codebase.
    
    Args:
        img_element: BeautifulSoup img element to style
        width_percent: Width as percentage of container (default: 33.333 for 1/3 width)
        position: Image position - 'center', 'left', or 'right' (default: 'center')
    """
    if img_element is None or not hasattr(img_element, 'attrs'):
        return
    
    # Set CSS class (BeautifulSoup handles string or list automatically)
    img_element['class'] = ImageConfig.CSS_CLASS
    
    # Build inline styles based on position
    if position == 'left':
        margin = '20px 0'
        display = 'block'
    elif position == 'right':
        margin = '20px 0 20px auto'
        display = 'block'
    else:  # center (default)
        margin = '20px auto'
        display = 'block'
    
    # Build style string
    style = f"display: {display}; margin: {margin}; width: {width_percent}%; height: auto;"
    img_element['style'] = style

# Try to import PIL for getting actual image dimensions
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - image dimension detection will be limited")


def _get_dimensions_from_headers(image_bytes: bytes) -> Tuple[Optional[int], Optional[int]]:
    """
    Fallback method to get image dimensions from image file headers.
    Used when PIL is not available.

    Supports: JPEG, PNG, GIF, WebP (basic detection)

    Args:
        image_bytes: Raw image data

    Returns:
        tuple: (width, height) or (None, None) if unable to determine
    """
    if not image_bytes or len(image_bytes) < 24:
        return None, None

    # Check PNG signature
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        # PNG: width and height are at bytes 16-23
        if len(image_bytes) >= 24:
            width = int.from_bytes(image_bytes[16:20], 'big')
            height = int.from_bytes(image_bytes[20:24], 'big')
            return width, height

    # Check JPEG signature
    elif image_bytes[:2] == b'\xff\xd8':
        # JPEG: more complex, requires parsing segments
        # Simplified approach - look for SOF marker
        try:
            i = 2
            while i < len(image_bytes) - 10:
                if image_bytes[i] == 0xff:
                    marker = image_bytes[i + 1]
                    # SOF markers: 0xC0-0xC3, 0xC5-0xC7, 0xC9-0xCB, 0xCD-0xCF
                    if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
                                  0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                        # Height at i+5, width at i+7
                        height = int.from_bytes(image_bytes[i+5:i+7], 'big')
                        width = int.from_bytes(image_bytes[i+7:i+9], 'big')
                        return width, height
                    # Skip to next segment
                    length = int.from_bytes(image_bytes[i+2:i+4], 'big')
                    i += 2 + length
                else:
                    i += 1
        except Exception:
            pass

    # Check GIF signature
    elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        # GIF: width at bytes 6-7, height at 8-9 (little-endian)
        if len(image_bytes) >= 10:
            width = int.from_bytes(image_bytes[6:8], 'little')
            height = int.from_bytes(image_bytes[8:10], 'little')
            return width, height

    # Check WebP signature
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        # WebP: more complex, requires parsing chunks
        # Simplified for VP8/VP8L
        if len(image_bytes) >= 30:
            if image_bytes[12:16] == b'VP8 ':
                # Lossy WebP
                width = int.from_bytes(image_bytes[26:28], 'little') & 0x3fff
                height = int.from_bytes(image_bytes[28:30], 'little') & 0x3fff
                return width, height
            elif image_bytes[12:16] == b'VP8L':
                # Lossless WebP
                bits = int.from_bytes(image_bytes[21:25], 'little')
                width = (bits & 0x3fff) + 1
                height = ((bits >> 14) & 0x3fff) + 1
                return width, height

    return None, None


def parse_srcset(srcset_str: str) -> List[Tuple[str, Optional[float]]]:
    """
    Parse a srcset string and return list of (url, descriptor_value) tuples.
    
    Handles both width descriptors (e.g., "image.jpg 1920w") and 
    density descriptors (e.g., "image.jpg 2x").
    
    Args:
        srcset_str: srcset attribute value
        
    Returns:
        list: List of (url, descriptor_value) tuples, sorted by descriptor (highest first)
              descriptor_value is width in pixels for 'w' descriptors, or density for 'x' descriptors
    """
    if not srcset_str:
        return []

    # SECURITY: Limit srcset length to prevent DoS
    if len(srcset_str) > NetworkConfig.MAX_SRCSET_LENGTH:
        logger.warning(f"Srcset too long: {len(srcset_str)} chars, truncating")
        srcset_str = srcset_str[:NetworkConfig.MAX_SRCSET_LENGTH]

    sources = []
    # Split by comma, but be careful of commas in URLs
    parts = []
    current_part = ''
    in_parens = False

    for i, char in enumerate(srcset_str):
        # Safety check: prevent infinite processing
        if i > NetworkConfig.MAX_SRCSET_LENGTH:
            logger.warning("Srcset parsing exceeded max length")
            break
        if char == '(':
            in_parens = True
            current_part += char
        elif char == ')':
            in_parens = False
            current_part += char
        elif char == ',' and not in_parens:
            if current_part.strip():
                parts.append(current_part.strip())
            current_part = ''
        else:
            current_part += char
    
    if current_part.strip():
        parts.append(current_part.strip())
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Filter out invalid parts
        if not is_valid_image_url(part):
            continue
        
        # Split into URL and descriptor
        # Descriptor can be at the end: "url 1920w" or "url 2x"
        # Use regex to find the descriptor
        # Match descriptor: optional number, optional decimal, followed by 'w' or 'x'
        descriptor_match = re.search(r'\s+(\d+(?:\.\d+)?)([wx])$', part)
        
        if descriptor_match:
            descriptor_value = float(descriptor_match.group(1))
            descriptor_type = descriptor_match.group(2)
            url = part[:descriptor_match.start()].strip()
            
            # For width descriptors, store as-is
            # For density descriptors, we'll prioritize higher density
            if descriptor_type == 'w':
                sources.append((url, descriptor_value))
            else:  # 'x' descriptor
                sources.append((url, descriptor_value))
        else:
            # No descriptor, treat as 1x density
            sources.append((part.strip(), 1.0))
    
    # Sort by descriptor value (highest first)
    sources.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
    return sources


def get_best_image_from_srcset(srcset_str: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    Extract the highest quality image URL from a srcset string.
    
    Args:
        srcset_str: srcset attribute value
        base_url: Base URL for converting relative paths to absolute URLs
        
    Returns:
        str: Best quality image URL (absolute if base_url provided) or None
    """
    if not srcset_str:
        return None
    
    sources = parse_srcset(srcset_str)
    if not sources:
        return None
    
    # Get the first (highest quality) source
    best_url = sources[0][0]
    
    # Convert to absolute URL if base_url provided
    if best_url and base_url:
        return urljoin(base_url, best_url)
    elif best_url and best_url.startswith('http'):
        return best_url
    
    return best_url


def download_image(url: str) -> Tuple[Optional[bytes], Optional[int], Optional[int]]:
    """
    Download image and get its dimensions (with memory safety).

    This is a shared utility function to avoid redundant downloads.
    Can be used by other modules to download images and get dimensions in one call.

    SECURITY: Uses size-limited download to prevent memory exhaustion.

    Args:
        url: Image URL

    Returns:
        tuple: (image_bytes, width, height) or (None, None, None) if unable to fetch
               image_bytes can be used to avoid re-downloading later
    """
    if not url:
        return None, None, None

    # Validate URL before attempting download
    if not is_valid_image_url(url):
        logger.warning(f"Skipping invalid image URL: {url}")
        return None, None, None

    try:
        # SECURITY: Download image with size limit to prevent memory exhaustion
        image_bytes = download_with_size_limit(
            url,
            max_size=ImageConfig.MAX_SIZE,
            timeout=ImageConfig.TIMEOUT
        )

        width, height = None, None

        # Get dimensions using PIL if available
        # Skip PIL for SVGs as it doesn't support them well
        is_svg = url.lower().endswith('.svg') or image_bytes.strip().startswith(b'<svg') or b'<svg' in image_bytes[:100]
        
        if is_svg:
            logger.debug(f"Detected SVG image: {url}")
            # For SVGs, we can't easily get dimensions without parsing XML, so return None
            return image_bytes, None, None
            
        if PIL_AVAILABLE:
            try:
                img_data = BytesIO(image_bytes)
                with Image.open(img_data) as img:
                    width, height = img.size  # Returns (width, height)
                    logger.debug(f"Downloaded image: {url} ({width}x{height})")
            except Exception as e:
                logger.warning(f"Could not get image dimensions for {url}: {e}")
        else:
            # PIL not available - try to extract dimensions from bytes
            width, height = _get_dimensions_from_headers(image_bytes)
            logger.debug(f"Downloaded image: {url} (dimensions via headers)")

        return image_bytes, width, height

    except ValueError as e:
        # Size limit exceeded
        error_msg = f"Image too large: {e}"
        logger.error(error_msg[:100])
        return None, None, None
    except Exception as e:
        # If anything else fails, return None
        logger.warning(f"Failed to download image {url}: {e}")
        return None, None, None


def get_actual_image_dimensions(url: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Fetch actual image dimensions from URL using PIL.
    
    This function uses the shared download_image utility to avoid code duplication.
    
    Args:
        url: Image URL
        
    Returns:
        tuple: (width, height) or (None, None) if unable to fetch
    """
    _, width, height = download_image(url)
    return width, height


def is_valid_image_url(url: str) -> bool:
    """
    Check if an image URL is valid and not a placeholder/undefined.
    """
    if not url:
        return False
        
    url_lower = url.lower().strip()
    
    # Check for invalid strings
    if url_lower in ('undefined', 'null', 'none', ''):
        return False
        
    # Check for invalid endings (common in JS errors)
    # Remove query params and fragments for checking
    url_clean = url_lower.split('?')[0].split('#')[0]
    
    if url_clean.endswith('/undefined') or url_clean.endswith('/null') or url_clean.endswith('/none'):
        return False
        
    return True


def extract_image_info(img_element, base_url: Optional[str] = None, fetch_dimensions: bool = True, fetch_content: bool = False) -> Dict:
    """
    Extract information from an image element.
    
    Args:
        img_element: BeautifulSoup image element (img, picture, or figure)
        base_url: Base URL for converting relative paths to absolute URLs
        fetch_dimensions: If True, fetch actual image dimensions from URL (default: True)
        fetch_content: If True, download and store image content to avoid re-downloading (default: False)
        
    Returns:
        dict: Dictionary with image information:
            - 'element': BeautifulSoup element
            - 'src': Image source URL (relative or absolute)
            - 'url': Absolute URL (or None)
            - 'alt': Alt text (or None)
            - 'width': Width attribute or actual width (or None)
            - 'height': Height attribute or actual height (or None)
            - 'actual_width': Actual image width from file (or None)
            - 'actual_height': Actual image height from file (or None)
            - 'type': Type of element ('img', 'picture', 'figure')
            - 'content': Image bytes (only if fetch_content=True and download successful)
    """
    if img_element is None:
        return {
            'element': None,
            'src': None,
            'url': None,
            'alt': None,
            'width': None,
            'height': None,
            'actual_width': None,
            'actual_height': None,
            'type': None
        }
    
    # Find the actual img tag if element is picture or figure
    actual_img = img_element
    is_picture = False
    if img_element.name == 'picture':
        is_picture = True
        actual_img = img_element.find('img')
        if actual_img is None:
            return {
                'element': img_element,
                'src': None,
                'url': None,
                'alt': None,
                'width': None,
                'height': None,
                'actual_width': None,
                'actual_height': None,
                'type': img_element.name
            }
    elif img_element.name != 'img':
        actual_img = img_element.find('img')
        if actual_img is None:
            return {
                'element': img_element,
                'src': None,
                'url': None,
                'alt': None,
                'width': None,
                'height': None,
                'actual_width': None,
                'actual_height': None,
                'type': img_element.name
            }
    
    # Priority order for getting highest quality image:
    # 1. picture source srcset (responsive images in picture element - get highest resolution)
    # 2. img srcset (responsive images - get highest resolution)
    # 3. data-srcset (lazy-loaded responsive images)
    # 4. data-src (lazy-loaded single image)
    # 5. data-lazy-src (alternative lazy-load attribute)
    # 6. data-original (original quality lazy-load)
    # 7. src (fallback)
    
    url = None
    src = None
    
    # If it's a picture element, check source elements first (they often have higher quality)
    if is_picture:
        source_elements = img_element.find_all('source')
        all_srcsets = []
        for source in source_elements:
            source_srcset = source.get('srcset') or source.get('data-srcset')
            if source_srcset:
                all_srcsets.append(source_srcset)
        
        # Parse all srcsets and find the highest quality image
        best_url_from_sources = None
        best_descriptor = 0
        for srcset_str in all_srcsets:
            sources = parse_srcset(srcset_str)
            if sources:
                candidate_url = sources[0][0]
                # Validate candidate URL before using it
                if not is_valid_image_url(candidate_url):
                    continue
                    
                if sources[0][1] and sources[0][1] > best_descriptor:
                    best_descriptor = sources[0][1]
                    if candidate_url and base_url:
                        best_url_from_sources = urljoin(base_url, candidate_url)
                    elif candidate_url and candidate_url.startswith('http'):
                        best_url_from_sources = candidate_url
                    else:
                        best_url_from_sources = candidate_url
        
        if best_url_from_sources and is_valid_image_url(best_url_from_sources):
            url = best_url_from_sources
            src = best_url_from_sources
    
    # Check for srcset on img element (if not already found from picture sources)
    if not url:
        srcset = actual_img.get('srcset') or actual_img.get('data-srcset')
        if srcset:
            best_url = get_best_image_from_srcset(srcset, base_url)
            if best_url and is_valid_image_url(best_url):
                url = best_url
                src = best_url  # Store the best URL as src
    
    # If no srcset, try lazy-load attributes
    if not url:
        src = (actual_img.get('data-src') or 
               actual_img.get('data-lazy-src') or
               actual_img.get('data-original') or
               actual_img.get('src') or
               '')
        
        # Get absolute URL if base_url provided
        if src:
            # Filter out invalid source strings
            if not is_valid_image_url(src):
                url = None
            elif base_url:
                candidate_url = urljoin(base_url, src)
                if is_valid_image_url(candidate_url):
                    url = candidate_url
            elif src.startswith('http'):
                url = src
    
    # Get HTML attributes
    alt = actual_img.get('alt')
    width_attr = actual_img.get('width')
    height_attr = actual_img.get('height')
    
    # Try to convert width/height attributes to integers
    width = None
    height = None
    if width_attr:
        try:
            width = int(width_attr)
        except (ValueError, TypeError):
            pass
    if height_attr:
        try:
            height = int(height_attr)
        except (ValueError, TypeError):
            pass
    
    # Fetch actual dimensions and optionally content if requested and URL is available
    actual_width = None
    actual_height = None
    image_content = None
    if (fetch_dimensions or fetch_content) and url:
        image_content, actual_width, actual_height = download_image(url)
        # Use actual dimensions if HTML attributes are missing
        if width is None and actual_width is not None:
            width = actual_width
        if height is None and actual_height is not None:
            height = actual_height
    
    result = {
        'element': img_element,
        'src': src,
        'url': url,
        'alt': alt,
        'width': width,
        'height': height,
        'actual_width': actual_width,
        'actual_height': actual_height,
        'type': img_element.name
    }
    
    # Optionally include image content to avoid re-downloading
    if fetch_content and image_content is not None:
        result['content'] = image_content
    
    return result




def resize_image(image_bytes: bytes, target_width: int) -> Tuple[bytes, Optional[int], Optional[int]]:
    """
    Resize an image to a target width while maintaining aspect ratio.

    Args:
        image_bytes: Image data as bytes
        target_width: Target width in pixels

    Returns:
        tuple: (resized_image_bytes, width, height) or (original_bytes, width, height) if PIL unavailable
    """
    if not PIL_AVAILABLE:
        # If PIL is not available, return original image
        # Try to get dimensions from image data if possible
        width, height = _get_dimensions_from_headers(image_bytes)
        return image_bytes, width, height

    # Check for SVG
    if image_bytes.strip().startswith(b'<svg') or b'<svg' in image_bytes[:100]:
        return image_bytes, None, None

    try:
        img = Image.open(BytesIO(image_bytes))
        original_width, original_height = img.size

        # Calculate new height maintaining aspect ratio
        aspect_ratio = original_height / original_width
        target_height = int(target_width * aspect_ratio)

        # Resize image
        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        # Preserve format
        img_format = img.format or 'PNG'
        resized_img.save(output, format=img_format)
        output.seek(0)

        return output.getvalue(), target_width, target_height
    except Exception as e:
        logger.warning(f"Failed to resize image: {e}")
        # If resize fails, return original
        width, height = _get_dimensions_from_headers(image_bytes)
        return image_bytes, width, height


def process_and_format_image(
    url: str, 
    image_bytes: Optional[bytes] = None, 
    target_width: int = 800,
    width_percent: float = 33.333,
    position: str = 'center'
) -> Dict:
    """
    Process an image (download, resize) and format it as an HTML <img> tag.
    
    This function handles:
    1. Downloading (if bytes not provided)
    2. Resizing to target width
    3. Converting to Data URI
    4. Generating HTML with configurable sizing and positioning styles
    
    Args:
        url: Image URL
        image_bytes: Optional image content if already downloaded
        target_width: Target width for resizing (default: 800)
        width_percent: Width as percentage of container (default: 33.333 for 1/3 width)
        position: Image position - 'center', 'left', or 'right' (default: 'center')
        
    Returns:
        dict: {
            'html': str (formatted HTML tag),
            'width': int (final width),
            'height': int (final height),
            'success': bool
        }
    """
    import base64
    import html
    
    # 1. Get image content
    width = None
    height = None
    
    if image_bytes is None:
        try:
            image_bytes, width, height = download_image(url)
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")
            
    if not image_bytes:
        # Fallback to original URL if download failed
        img_url_escaped = html.escape(url, quote=True)
        # Build style based on position
        if position == 'left':
            margin = '20px 0'
        elif position == 'right':
            margin = '20px 0 20px auto'
        else:  # center
            margin = '20px auto'
        style = f"display: block; margin: {margin}; width: {width_percent}%; height: auto;"
        return {
            'html': f'<img src="{img_url_escaped}" alt="" class="{ImageConfig.CSS_CLASS}" style="{style}" />',
            'width': 0,
            'height': 0,
            'success': False
        }
        
    # 2. Resize image
    try:
        resized_bytes, new_width, new_height = resize_image(image_bytes, target_width=target_width)
    except Exception as e:
        logger.warning(f"Failed to resize image {url}: {e}")
        resized_bytes = image_bytes
        new_width, new_height = width, height

    # 3. Convert to Data URI
    try:
        img_format = 'png'
        # Try to detect format from bytes signature or PIL
        if PIL_AVAILABLE:
            try:
                img_check = Image.open(BytesIO(resized_bytes))
                format_map = {'JPEG': 'jpeg', 'PNG': 'png', 'GIF': 'gif', 'WEBP': 'webp'}
                img_format = format_map.get(img_check.format, 'png')
            except:
                pass
        
        base64_data = base64.b64encode(resized_bytes).decode('utf-8')
        data_uri = f'data:image/{img_format};base64,{base64_data}'
        
        # 4. Generate HTML
        # Use inline styles to ensure positioning and responsiveness
        # Build style based on position
        if position == 'left':
            margin = '20px 0'
        elif position == 'right':
            margin = '20px 0 20px auto'
        else:  # center
            margin = '20px auto'
        style = f"display: block; margin: {margin}; width: {width_percent}%; height: auto;"
        
        img_html = (
            f'<img src="{data_uri}" alt="" class="{ImageConfig.CSS_CLASS}" '
            f'width="{new_width}" height="{new_height}" '
            f'style="{style}" />'
        )
        
        return {
            'html': img_html,
            'width': new_width,
            'height': new_height,
            'success': True
        }
        
    except Exception as e:
        logger.warning(f"Failed to format image {url}: {e}")
        # Fallback
        img_url_escaped = html.escape(url, quote=True)
        return {
            'html': f'<img src="{img_url_escaped}" alt="" class="{ImageConfig.CSS_CLASS}" style="{ImageConfig.CSS_STYLE}" />',
            'width': 0,
            'height': 0,
            'success': False
        }
