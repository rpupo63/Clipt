"""
URL utilities for normalization and validation.
Consolidates duplicate URL handling code.
"""

import ipaddress
from urllib.parse import urlparse, urlunparse
from typing import Optional
from constants import SecurityConfig
from logger import get_logger

logger = get_logger(__name__)


def normalize_image_url(url: str) -> str:
    """
    Normalize an image URL for duplicate detection.

    Removes query parameters, fragments, and normalizes the URL to help
    identify duplicate images that might have different URLs but point to
    the same image (e.g., with tracking parameters, size parameters, etc.).

    Args:
        url: Image URL to normalize

    Returns:
        str: Normalized URL (base URL without query params or fragments)

    Example:
        >>> normalize_image_url("https://example.com/img.jpg?size=large#top")
        'https://example.com/img.jpg'
    """
    if not url:
        return url

    try:
        parsed = urlparse(url)
        # Reconstruct URL without query and fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            '',  # Remove query
            ''   # Remove fragment
        ))
        return normalized
    except Exception:
        # If parsing fails, return original
        return url


def validate_url(url: str, allow_private: bool = None) -> tuple[bool, Optional[str]]:
    """
    Validate a URL for security (SSRF protection).

    Checks:
    - Valid HTTP/HTTPS scheme
    - Not accessing blocked hosts (localhost, cloud metadata, etc.)
    - Not accessing private IP ranges (unless explicitly allowed)

    Args:
        url: The URL to validate
        allow_private: Override for allowing private IPs (defaults to SecurityConfig)

    Returns:
        tuple: (is_valid: bool, error_message: Optional[str])

    Example:
        >>> validate_url("https://example.com")
        (True, None)
        >>> validate_url("http://localhost/admin")
        (False, "Access to localhost is not allowed")
        >>> validate_url("file:///etc/passwd")
        (False, "Invalid URL scheme: file")
    """
    if allow_private is None:
        allow_private = SecurityConfig.ALLOW_PRIVATE_IPS

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in SecurityConfig.ALLOWED_URL_SCHEMES:
            error_msg = f"Invalid URL scheme: {parsed.scheme}. Only HTTP/HTTPS allowed."
            logger.warning(f"URL validation failed for {url}: {error_msg}")
            return False, error_msg

        # Check for missing hostname
        if not parsed.hostname:
            error_msg = "Invalid URL: missing hostname"
            logger.warning(f"URL validation failed for {url}: {error_msg}")
            return False, error_msg

        hostname = parsed.hostname.lower()

        # Check blocked hosts
        if hostname in SecurityConfig.BLOCKED_HOSTS:
            error_msg = f"Access to {hostname} is not allowed"
            logger.warning(f"SECURITY: Blocked access attempt to {hostname}")
            return False, error_msg

        # Check for private IP ranges
        if not allow_private:
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    error_msg = f"Access to private IP {hostname} is not allowed"
                    logger.warning(f"SECURITY: Blocked access attempt to private IP {hostname}")
                    return False, error_msg
            except ValueError:
                # Not an IP address, it's a hostname - that's OK
                pass

        logger.debug(f"URL validation passed for {url}")
        return True, None

    except Exception as e:
        error_msg = f"Invalid URL format: {str(e)}"
        logger.error(f"URL validation error for {url}: {e}", exc_info=True)
        return False, error_msg


def is_valid_http_url(url: str) -> bool:
    """
    Quick check if a URL is a valid HTTP/HTTPS URL.

    Args:
        url: URL to check

    Returns:
        bool: True if valid HTTP/HTTPS URL

    Example:
        >>> is_valid_http_url("https://example.com")
        True
        >>> is_valid_http_url("ftp://example.com")
        False
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in SecurityConfig.ALLOWED_URL_SCHEMES and bool(parsed.netloc)
    except Exception:
        return False
