"""
Configuration management for Clipt backend.
Validates environment variables at startup.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


class Config:
    """Application configuration with validation."""

    # Required API keys (will cause startup failure if missing)
    REQUIRED_KEYS = []

    # Optional API keys (features gracefully degrade if missing)
    OPTIONAL_KEYS = ['FIRECRAWL_API_KEY', 'OPENAI_API_KEY']

    # Internal configuration
    _validated = False

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Value from environment or default
        """
        return os.getenv(key, default)

    @classmethod
    def validate(cls, strict: bool = False) -> bool:
        """
        Validate required configuration at startup.

        Args:
            strict: If True, treat optional keys as required

        Returns:
            bool: True if all required keys present

        Raises:
            EnvironmentError: If required keys are missing
        """
        if cls._validated:
            return True

        missing_required = []
        missing_optional = []

        # Check required keys
        for key in cls.REQUIRED_KEYS:
            if not os.getenv(key):
                missing_required.append(key)

        # Check optional keys
        for key in cls.OPTIONAL_KEYS:
            if not os.getenv(key):
                missing_optional.append(key)

        # Report missing required keys
        if missing_required:
            error_msg = (
                f"Missing required API keys: {', '.join(missing_required)}\n"
                f"Please set them in your .env file."
            )
            raise EnvironmentError(error_msg)

        # Report missing optional keys
        if missing_optional:
            logger.warning(
                f"Missing optional API keys: {', '.join(missing_optional)}\n"
                f"Some features may be disabled."
            )

        # In strict mode, optional keys become required
        if strict and missing_optional:
            error_msg = (
                f"Missing API keys in strict mode: {', '.join(missing_optional)}\n"
                f"Please set them in your .env file or disable strict mode."
            )
            raise EnvironmentError(error_msg)

        cls._validated = True
        logger.info("Configuration validated successfully")
        return True

    @classmethod
    def has_firecrawl(cls) -> bool:
        """Check if Firecrawl API key is configured."""
        return bool(os.getenv('FIRECRAWL_API_KEY'))

    @classmethod
    def has_openai(cls) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(os.getenv('OPENAI_API_KEY'))

    @classmethod
    def get_firecrawl_key(cls) -> Optional[str]:
        """Get Firecrawl API key."""
        return os.getenv('FIRECRAWL_API_KEY')

    @classmethod
    def get_openai_key(cls) -> Optional[str]:
        """Get OpenAI API key."""
        return os.getenv('OPENAI_API_KEY')
