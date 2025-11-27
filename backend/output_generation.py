#!/usr/bin/env python3
"""
Output generation functions for converting HTML to various file formats
Supports conversion to DOCX, PDF, and Markdown formats
"""

import os
import re
from pathlib import Path
from typing import Optional, Union, Dict, Set
from bs4 import BeautifulSoup
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import utilities
from logger import get_logger
from url_utils import normalize_image_url

logger = get_logger(__name__)

# Try to import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Lazy imports for optional dependencies
DOCX_IMPORT_ERROR = None
HTMKDOCX_AVAILABLE = False
HTMKDOCX_IMPORT_ERROR = None
try:
    from docx import Document as DocxDocument
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError as e:
    DOCX_AVAILABLE = False
    DOCX_IMPORT_ERROR = str(e)

try:
    from htmldocx import HtmlToDocx
    HTMKDOCX_AVAILABLE = True
except ImportError as e:
    HTMKDOCX_AVAILABLE = False
    HTMKDOCX_IMPORT_ERROR = str(e)

try:
    from weasyprint import HTML
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import markdownify
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


from image_utils import download_image, resize_image, apply_image_styling
from constants import ImageConfig


def _process_images_in_html(html_content: str, target_width: int = 800, width_percent: float = 33.333, position: str = 'center') -> str:
    """
    Process all images in HTML: deduplicate by URL, download, and resize to consistent width.
    
    Args:
        html_content: HTML content as string
        target_width: Target width for all images in pixels (default: 800)
        width_percent: Width as percentage of container (default: 33.333 for 1/3 width)
        position: Image position - 'center', 'left', or 'right' (default: 'center')
        
    Returns:
        str: HTML content with processed images (as data URIs or base64)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all image tags
    img_tags = soup.find_all('img')
    if not img_tags:
        return html_content
    
    # Collect unique image URLs (normalized for deduplication)
    image_url_map = {}  # Maps normalized URL to original URL
    normalized_to_original = {}  # Maps normalized URL to list of original URLs
    
    for img in img_tags:
        src = img.get('src', '')
        if src and src.startswith('http'):
            normalized = normalize_image_url(src)
            if normalized not in normalized_to_original:
                normalized_to_original[normalized] = []
            normalized_to_original[normalized].append(src)
            # Use the first original URL we encounter for each normalized URL
            if normalized not in image_url_map:
                image_url_map[normalized] = src
    
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
    
    # Replace all image tags with processed versions
    for img in img_tags:
        src = img.get('src', '')
        if src and src.startswith('http'):
            normalized = normalize_image_url(src)

            if normalized in processed_images:
                resized_bytes, new_width, new_height = processed_images[normalized]
                
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
                        if src.lower().endswith(('.jpg', '.jpeg')):
                            img_format = 'jpeg'
                        elif src.lower().endswith('.gif'):
                            img_format = 'gif'
                        elif src.lower().endswith('.webp'):
                            img_format = 'webp'
                else:
                    # Fallback to URL-based detection if PIL not available
                    if src.lower().endswith(('.jpg', '.jpeg')):
                        img_format = 'jpeg'
                    elif src.lower().endswith('.gif'):
                        img_format = 'gif'
                    elif src.lower().endswith('.webp'):
                        img_format = 'webp'
                
                import base64
                base64_data = base64.b64encode(resized_bytes).decode('utf-8')
                data_uri = f'data:image/{img_format};base64,{base64_data}'
                
                # Update img tag
                img['src'] = data_uri
                if new_width:
                    img['width'] = str(new_width)
                if new_height:
                    img['height'] = str(new_height)
                # Apply consistent styling
                apply_image_styling(img, width_percent=width_percent, position=position)
    
    return str(soup)


def html_to_docx(html_content: str) -> bytes:
    """
    Convert HTML content to a DOCX document using htmldocx library
    
    Args:
        html_content: HTML content as string
        
    Returns:
        bytes: DOCX document as bytes
        
    Raises:
        ImportError: If python-docx or htmldocx is not available
    """
    # Process images: deduplicate, download, and resize
    html_content = _process_images_in_html(html_content, target_width=800)
    
    if not DOCX_AVAILABLE:
        error_msg = "python-docx is not available"
        if DOCX_IMPORT_ERROR:
            error_msg += f": {DOCX_IMPORT_ERROR}"
        error_msg += "\nPlease uninstall any old 'docx' package and ensure 'python-docx' is installed:"
        error_msg += "\n  pip uninstall docx"
        error_msg += "\n  pip install python-docx"
        raise ImportError(error_msg)
    
    if not HTMKDOCX_AVAILABLE:
        error_msg = "htmldocx is not available"
        if HTMKDOCX_IMPORT_ERROR:
            error_msg += f": {HTMKDOCX_IMPORT_ERROR}"
        error_msg += "\nPlease install htmldocx:"
        error_msg += "\n  pip install htmldocx"
        raise ImportError(error_msg)
    
    # Parse HTML for preprocessing
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Helper function to check if element is a subtitle
    def is_subtitle_element(elem):
        """Check if an element is marked as a subtitle"""
        classes = elem.get('class', [])
        class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
        element_id = elem.get('id', '')
        subtitle_patterns = ['subtitle', 'dek', 'deck', 'subheading', 'sub-heading', 'lead', 'summary', 'excerpt']
        return any(pattern in class_str.lower() for pattern in subtitle_patterns) or \
               any(pattern in element_id.lower() for pattern in subtitle_patterns)
    
    # Preprocess HTML: Convert subtitle elements to styled paragraphs
    # This ensures subtitles are rendered with italic and centered alignment
    for elem in soup.find_all(['h2', 'h3', 'p', 'div', 'section', 'article', 'main']):
        if is_subtitle_element(elem):
            # Convert to paragraph with subtitle styling
            if elem.name in ['h2', 'h3']:
                # Change h2/h3 to p with italic style
                elem.name = 'p'
                style = elem.get('style', '')
                if 'font-style' not in style.lower():
                    if style:
                        style += '; font-style: italic; text-align: center;'
                    else:
                        style = 'font-style: italic; text-align: center;'
                    elem['style'] = style
            else:
                # Add italic and center alignment to existing paragraph/div
                style = elem.get('style', '')
                if 'font-style' not in style.lower():
                    if style:
                        style += '; font-style: italic;'
                    else:
                        style = 'font-style: italic;'
                if 'text-align' not in style.lower():
                    style += '; text-align: center;'
                elem['style'] = style
    
    # Convert data URI images to temporary files for htmldocx
    # htmldocx works better with file paths than data URIs
    import base64
    import tempfile
    import os
    
    temp_files = []  # Track temp files for cleanup
    for img in soup.find_all('img'):
        img_src = img.get('src', '')
        if img_src.startswith('data:image/'):
            try:
                # Extract base64 data
                header, data = img_src.split(',', 1)
                image_bytes = base64.b64decode(data)
                
                # Determine image format
                img_format = 'png'  # Default
                if 'jpeg' in header or 'jpg' in header:
                    img_format = 'jpeg'
                elif 'gif' in header:
                    img_format = 'gif'
                elif 'webp' in header:
                    img_format = 'webp'
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{img_format}') as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_path = tmp_file.name
                    temp_files.append(tmp_path)
                    
                    # Update img src to file:// URL (htmldocx prefers this format)
                    img['src'] = f'file://{tmp_path}'
            except Exception as e:
                logger.warning(f"Failed to convert data URI image to temp file: {e}")
                # Remove the image if conversion fails
                img.decompose()
    
    # Get body content
    body = soup.find('body') or soup
    body_html = str(body) if body else str(soup)
    
    # Create DOCX document
    doc = DocxDocument()
    
    # Use htmldocx to convert HTML to DOCX
    parser = HtmlToDocx()
    parser.add_html_to_document(body_html, doc)
    
    # Clean up temporary files
    for tmp_file in temp_files:
        try:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {tmp_file}: {e}")
    
    # Save to BytesIO and return bytes
    docx_buffer = BytesIO()
    doc.save(docx_buffer)
    return docx_buffer.getvalue()


def html_to_pdf(html_content: str) -> bytes:
    """
    Convert HTML content to a PDF document
    
    Args:
        html_content: HTML content as string
        
    Returns:
        bytes: PDF document as bytes
        
    Raises:
        ImportError: If weasyprint is not available
    """
    # Process images: deduplicate, download, and resize
    html_content = _process_images_in_html(html_content, target_width=800)
    
    if not PDF_AVAILABLE:
        raise ImportError("weasyprint is not available. Please install it: pip install weasyprint")
    
    # Convert HTML to PDF using WeasyPrint and return as bytes
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


def html_to_markdown(html_content: str) -> str:
    """
    Convert HTML content to a Markdown document
    
    Args:
        html_content: HTML content as string
        
    Returns:
        str: Markdown content as string
        
    Raises:
        ImportError: If markdownify is not available
    """
    # Process images: deduplicate, download, and resize
    html_content = _process_images_in_html(html_content, target_width=800)
    
    if not MARKDOWN_AVAILABLE:
        raise ImportError("markdownify is not available. Please install it: pip install markdownify")
    
    # Parse HTML to preserve image dimensions
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Process images to preserve dimensions in markdown
    for img in soup.find_all('img'):
        src = img.get('src', '')
        alt = img.get('alt', '')
        width = img.get('width')
        height = img.get('height')
        
        # Create markdown image syntax with dimensions if available
        if width and height:
            # Markdown doesn't natively support dimensions, but we can add them as HTML
            # or use a format that some markdown processors support
            img.replace_with(f'<img src="{src}" alt="{alt}" width="{width}" height="{height}" />')
        elif src:
            # Standard markdown image syntax
            img.replace_with(f'![{alt}]({src})')
    
    # Convert HTML to Markdown
    markdown_content = markdownify.markdownify(
        str(soup),
        heading_style="ATX",  # Use # style headings
        bullets="-",  # Use - for bullet points
        strip=['script', 'style']  # Strip script and style tags
    )
    
    return markdown_content


def convert_html(html_content: str, filetype: str) -> Union[bytes, str]:
    """
    Convert HTML content to the specified file format
    
    Args:
        html_content: HTML content as string
        filetype: Desired output format ('docx', 'pdf', 'md', or 'markdown')
        
    Returns:
        bytes: For binary formats (docx, pdf)
        str: For text formats (md, markdown)
        
    Raises:
        ValueError: If filetype is not supported
    """
    # Normalize filetype (case-insensitive)
    filetype_lower = filetype.lower().strip()
    
    # Route to appropriate conversion function
    if filetype_lower in ['docx', 'doc']:
        return html_to_docx(html_content)
    elif filetype_lower == 'pdf':
        return html_to_pdf(html_content)
    elif filetype_lower in ['md', 'markdown']:
        return html_to_markdown(html_content)
    else:
        raise ValueError(
            f"Unsupported filetype: {filetype}. "
            f"Supported formats: 'docx', 'pdf', 'md', 'markdown'"
        )


def main():
    """
    Example usage of the conversion functions
    """
    import sys

    html_file = "scraped_page.html"

    if not os.path.exists(html_file):
        logger.error(f"Error: {html_file} not found")
        return

    # Read HTML content
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    logger.info("Converting HTML to various formats...")
    logger.info("Using unified convert_html function:")

    # Convert to DOCX
    logger.info("Converting to DOCX...")
    try:
        docx_content = convert_html(html_content, 'docx')
        docx_file = str(Path(html_file).with_suffix('.docx'))
        with open(docx_file, 'wb') as f:
            f.write(docx_content)
        logger.info(f"✓ DOCX saved to: {docx_file}")
    except Exception as e:
        logger.error(f"✗ Error converting to DOCX: {e}", exc_info=True)

    # Convert to PDF
    logger.info("Converting to PDF...")
    try:
        pdf_content = convert_html(html_content, 'pdf')
        pdf_file = str(Path(html_file).with_suffix('.pdf'))
        with open(pdf_file, 'wb') as f:
            f.write(pdf_content)
        logger.info(f"✓ PDF saved to: {pdf_file}")
    except Exception as e:
        logger.error(f"✗ Error converting to PDF: {e}", exc_info=True)

    # Convert to Markdown
    logger.info("Converting to Markdown...")
    try:
        md_content = convert_html(html_content, 'md')
        md_file = str(Path(html_file).with_suffix('.md'))
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"✓ Markdown saved to: {md_file}")
    except Exception as e:
        logger.error(f"✗ Error converting to Markdown: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    main()

