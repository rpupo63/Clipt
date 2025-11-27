"""
Functions to extract first and last contentful sentences from web articles.
Uses Firecrawl for web scraping and OpenAI for intelligent content extraction.
"""

from typing import Dict, Optional
from firecrawl import FirecrawlApp
from openai import OpenAI

# Import utilities
from config import Config
from logger import get_logger

logger = get_logger(__name__)


def scrape_url_to_markdown(url: str) -> Dict[str, str]:
    """
    Scrape a URL using Firecrawl and convert it to markdown.

    Args:
        url: The URL to scrape

    Returns:
        Dictionary containing:
        - 'markdown': The markdown content of the page
        - 'url': The original URL
        - 'title': Page title (if available)

    Raises:
        ValueError: If FIRECRAWL_API_KEY is not set in environment
        Exception: If scraping fails
    """
    # Get API key from config
    api_key = Config.get_firecrawl_key()
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY not found in environment variables. "
            "Please add it to your .env file."
        )

    # Initialize Firecrawl
    firecrawl = FirecrawlApp(api_key=api_key)

    try:
        logger.info(f"Scraping URL with Firecrawl: {url}")
        
        # According to Firecrawl docs: SDKs return the data object directly
        # Structure: {'markdown': '...', 'html': '...', 'metadata': {...}}
        # See: https://docs.firecrawl.dev/introduction
        result = firecrawl.scrape(url, formats=["markdown"])

        if result is None:
            logger.error("Firecrawl returned None result")
            raise Exception("Firecrawl returned None - no data retrieved")
        
        # Handle response objects (SDK may return object with attributes)
        if hasattr(result, 'markdown'):
            markdown_content = result.markdown
            metadata = result.metadata if hasattr(result, 'metadata') else {}
        elif isinstance(result, dict):
            # SDK returns data object directly: {'markdown': '...', 'metadata': {...}}
            # But also handle case where it's wrapped in 'data' key (API response format)
            if 'data' in result:
                data = result['data']
                markdown_content = data.get('markdown', '') if isinstance(data, dict) else ''
                metadata = data.get('metadata', {}) if isinstance(data, dict) and isinstance(data.get('metadata'), dict) else {}
            else:
                # Direct data object (SDK format)
                markdown_content = result.get('markdown', '')
                metadata = result.get('metadata', {}) if isinstance(result.get('metadata'), dict) else {}
        else:
            logger.error(f"Unexpected Firecrawl response type: {type(result)}")
            raise Exception(f"Unexpected response type from Firecrawl: {type(result)}")

        # Validate markdown content
        markdown_content = markdown_content.strip() if markdown_content else ''
        
        if not markdown_content:
            logger.error(f"Firecrawl returned empty markdown content")
            if isinstance(result, dict):
                logger.error(f"Response keys: {list(result.keys())}")
            raise Exception("Firecrawl returned empty markdown content - the page may not be accessible or may have no content")

        logger.info(f"Retrieved {len(markdown_content)} characters of markdown from Firecrawl")

        return {
            'markdown': markdown_content,
            'url': url,
            'title': metadata.get('title', '') if isinstance(metadata, dict) else ''
        }
    except Exception as e:
        logger.error(f"Failed to scrape URL with Firecrawl: {e}", exc_info=True)
        raise Exception(f"Failed to scrape URL with Firecrawl: {str(e)}")


def extract_first_and_last_sentences(markdown_content: str) -> Dict[str, str]:
    """
    Extract the first and last contentful sentences from markdown content using OpenAI.

    Args:
        markdown_content: The markdown content to analyze

    Returns:
        Dictionary containing:
        - 'first_sentence': The first contentful sentence
        - 'last_sentence': The last contentful sentence

    Raises:
        ValueError: If OPENAI_API_KEY is not set in environment
        Exception: If OpenAI API call fails
    """
    # Get API key from config
    api_key = Config.get_openai_key()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please add it to your .env file."
        )

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Construct the prompt
    prompt = f"""What are the first and last contentful sentences in this article? 

Important guidelines:
- The first sentence should be found directly below the article title, within the main article body
- The last sentence MUST be from the main article content, NOT from any author bio, author information, writer bio, author profile, or related sections
- Stop extracting BEFORE reaching any section that contains author information, bio, writer details, or "about the author" content
- The last sentence should be the final meaningful sentence from the actual article content, which typically ends well before any author bio section
- Focus on sentences that are directly within the article content, not external links
- Avoid external links, menu items, navigation elements, and advertisements
- The sentences could be brief list items if the article has listicle elements
- Exclude any advertisements, notices, or superfluous material found on websites
- Exclude author bios, writer profiles, author information sections, and any content about the writer
- Only extract what is relevant to the main article being discussed
- If you encounter any author-related section (bio, profile, "about", etc.), the last sentence must come from content BEFORE that section

Article content:
{markdown_content}

Please respond in JSON format with the following structure:
{{
    "first_sentence": "...",
    "last_sentence": "..."
}}"""

    try:
        logger.info("Extracting sentences with OpenAI")
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts the first and last meaningful sentences from articles. The first sentence should be found directly below the article title. The last sentence MUST be from the main article content only - it must come BEFORE any author bio, writer profile, author information, or 'about the author' sections. Never include content from author bios or writer profiles. Stop extracting when you reach the end of the actual article content, well before any author-related sections. Focus on sentences within the main article body, avoiding external links, menu items, navigation elements, advertisements, and all author bio content. The sentences may be brief list items if the article is a listicle. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
        )

        # Parse the response
        import json
        result = json.loads(response.choices[0].message.content)

        logger.debug(f"Extracted sentences successfully")

        return {
            'first_sentence': result.get('first_sentence', ''),
            'last_sentence': result.get('last_sentence', '')
        }
    except Exception as e:
        logger.error(f"Failed to extract sentences with OpenAI: {e}", exc_info=True)
        raise Exception(f"Failed to extract sentences with OpenAI: {str(e)}")


def process_url(url: str) -> Dict[str, str]:
    """
    Convenience function to scrape a URL and extract first/last sentences in one call.

    Args:
        url: The URL to process

    Returns:
        Dictionary containing:
        - 'url': The original URL
        - 'title': Page title
        - 'first_sentence': The first contentful sentence
        - 'last_sentence': The last contentful sentence
        - 'markdown': The full markdown content
    """
    # Scrape the URL
    scrape_result = scrape_url_to_markdown(url)

    # Extract sentences
    sentences = extract_first_and_last_sentences(scrape_result['markdown'])

    # Combine results
    return {
        'url': scrape_result['url'],
        'title': scrape_result['title'],
        'first_sentence': sentences['first_sentence'],
        'last_sentence': sentences['last_sentence'],
        'markdown': scrape_result['markdown']
    }


def find_first_and_last_sentences_from_url(url: str, use_firecrawl: bool = True) -> Dict[str, Optional[str]]:
    """
    Complete integration function to extract first and last contentful sentences from a URL.

    This function brings together the full workflow:
    1. Scrapes the URL using Firecrawl to get clean markdown content
    2. Uses OpenAI to intelligently extract the first and last contentful sentences
    3. Returns the sentences for use in content extraction

    This should be called BEFORE main content extraction to identify the boundaries
    of the article content.

    Args:
        url: The URL to process
        use_firecrawl: If True (default), use Firecrawl for scraping.
                      If False, returns empty sentences (allows graceful degradation)

    Returns:
        Dictionary containing:
        - 'first_sentence': The first contentful sentence (or None if failed)
        - 'last_sentence': The last contentful sentence (or None if failed)
        - 'success': Boolean indicating if extraction was successful
        - 'error': Error message if extraction failed (None otherwise)

    Example:
        >>> result = find_first_and_last_sentences_from_url("https://example.com/article")
        >>> if result['success']:
        ...     print(f"First: {result['first_sentence']}")
        ...     print(f"Last: {result['last_sentence']}")
    """
    if not use_firecrawl:
        return {
            'first_sentence': None,
            'last_sentence': None,
            'success': False,
            'error': 'Firecrawl disabled'
        }

    try:
        # Step 1: Scrape the URL with Firecrawl
        logger.info("  → Scraping URL with Firecrawl...")
        scrape_result = scrape_url_to_markdown(url)

        if not scrape_result.get('markdown'):
            return {
                'first_sentence': None,
                'last_sentence': None,
                'success': False,
                'error': 'No markdown content retrieved from Firecrawl'
            }

        logger.info(f"  → Retrieved {len(scrape_result['markdown'])} characters of markdown")

        # Step 2: Extract sentences using OpenAI
        logger.info("  → Extracting first and last sentences with OpenAI...")
        sentences = extract_first_and_last_sentences(scrape_result['markdown'])

        if not sentences.get('first_sentence') or not sentences.get('last_sentence'):
            return {
                'first_sentence': None,
                'last_sentence': None,
                'success': False,
                'error': 'OpenAI did not return valid sentences'
            }

        logger.info(f"  ✓ First sentence: {sentences['first_sentence'][:80]}...")
        logger.info(f"  ✓ Last sentence: {sentences['last_sentence'][:80]}...")

        return {
            'first_sentence': sentences['first_sentence'],
            'last_sentence': sentences['last_sentence'],
            'success': True,
            'error': None
        }

    except ValueError as e:
        # API key missing
        return {
            'first_sentence': None,
            'last_sentence': None,
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except Exception as e:
        # Any other error
        return {
            'first_sentence': None,
            'last_sentence': None,
            'success': False,
            'error': f'Failed to extract sentences: {str(e)}'
        }


# Example usage
if __name__ == "__main__":
    # Example URL - replace with your target URL
    test_url = "https://example.com/article"

    try:
        result = process_url(test_url)
        print(f"Title: {result['title']}")
        print(f"\nFirst sentence: {result['first_sentence']}")
        print(f"\nLast sentence: {result['last_sentence']}")
    except Exception as e:
        print(f"Error: {e}")
