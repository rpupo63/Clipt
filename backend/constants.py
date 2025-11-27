"""
Constants and configuration values for Clipt backend.
All magic numbers and hardcoded values centralized here.
"""

# Image Configuration
class ImageConfig:
    """Image processing constants."""
    MAX_SEARCH_DISTANCE = 5  # DOM elements to search for images
    TARGET_WIDTH = 800  # pixels for image resizing
    MAX_SIZE = 10 * 1024 * 1024  # 10MB maximum image size
    QUALITY = 85  # JPEG compression quality
    TIMEOUT = 30  # seconds for image download
    MAX_DIMENSION = 4000  # maximum width or height in pixels
    
    # Image styling constants for consistent formatting
    CSS_CLASS = "content-image"  # CSS class for content images
    CSS_STYLE = "display: block; margin: 20px auto; width: 33.333%; height: auto;"  # Inline styles: 1/3 screen width, centered, maintains aspect ratio


# Page Scraping Configuration
class PageConfig:
    """Web scraping constants."""
    LOAD_WAIT_TIME = 1.0  # seconds to wait for page load
    PAGE_TIMEOUT = 30  # seconds for page load timeout
    MAX_RETRIES = 3  # maximum retry attempts
    RETRY_BACKOFF = 1.0  # exponential backoff factor


# Document Generation Configuration
class DocumentConfig:
    """Document output constants."""
    PAGE_WIDTH_INCHES = 6.5
    PAGE_HEIGHT_INCHES = 9.0
    MARGIN_INCHES = 0.5
    LOGO_WIDTH_PERCENT = 33.333  # percentage of page width
    IMAGE_WIDTH_PERCENT = 33.333  # percentage of page width


# File Configuration
class FileConfig:
    """File handling constants."""
    TEMP_DIR_NAME = "clipt_temp"
    MAX_FILENAME_LENGTH = 255
    DEFAULT_ENCODING = "utf-8"


# Network Configuration
class NetworkConfig:
    """Network request constants."""
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1.0
    POOL_CONNECTIONS = 10
    POOL_MAXSIZE = 20
    MAX_SRCSET_LENGTH = 10000  # maximum srcset attribute length
    CHUNK_SIZE = 8192  # bytes for streaming downloads


# Content Extraction Configuration
class ContentConfig:
    """Content extraction constants."""
    MIN_PARAGRAPH_LENGTH = 10  # minimum characters in a paragraph
    MAX_DISTANCE_FROM_TITLE = 5  # DOM elements

    # Common main content selectors (in priority order)
    MAIN_CONTENT_SELECTORS = [
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


# Logo Extraction Configuration
class LogoConfig:
    """Logo extraction constants."""
    MIN_LOGO_SIZE = 20  # minimum width/height in pixels
    MAX_LOGO_SIZE = 500  # maximum width/height in pixels
    LOGO_SCORE_THRESHOLD = 0.5  # minimum score for logo candidacy


# Security Configuration
class SecurityConfig:
    """Security-related constants."""
    ALLOWED_URL_SCHEMES = {'http', 'https'}

    # Blocked IPs and hostnames
    BLOCKED_HOSTS = {
        '127.0.0.1', 'localhost', '::1',
        '169.254.169.254',  # AWS metadata
        'metadata.google.internal',  # GCP metadata
    }

    # Private IP ranges (checked separately)
    ALLOW_PRIVATE_IPS = False  # set to True for development only

    # File upload limits
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


# Cache Configuration
class CacheConfig:
    """Caching constants."""
    IMAGE_CACHE_SIZE = 100  # number of images to cache in memory
    IMAGE_CACHE_TTL = 3600  # seconds (1 hour)
