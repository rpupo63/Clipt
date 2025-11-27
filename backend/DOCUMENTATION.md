# Clipt Backend Documentation

Complete documentation for all modules and functions that affect `clipping_logic.py`, including tools, technologies, and methodologies.

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Web Scraping Architecture](#web-scraping-architecture)
3. [AI-Powered Content Extraction](#ai-powered-content-extraction)
4. [Technology Stack](#technology-stack)
5. [Complete Processing Pipeline](#complete-processing-pipeline)
6. [Module Documentation](#module-documentation)
   - [site_preprocessing.py](#site_preprocessingpy)
   - [content_extraction.py](#content_extractionpy)
   - [header_extraction.py](#header_extractionpy)
   - [subtitle_validation.py](#subtitle_validationpy)
   - [image_positioning.py](#image_positioningpy)
   - [logo_extraction.py](#logo_extractionpy)
   - [output_generation.py](#output_generationpy)
   - [find_first_and_last_sentences.py](#find_first_and_last_sentencespy)
   - [keyword_filtering.py](#keyword_filteringpy)
   - [url_utils.py](#url_utilspy)
   - [image_utils.py](#image_utilspy)
   - [network_utils.py](#network_utilspy)
   - [dom_utils.py](#dom_utilspy)
   - [constants.py](#constantspy)
   - [logger.py](#loggerpy)
   - [config.py](#configpy)

---

## Overview & Architecture

Clipt uses a **hybrid approach** combining traditional web scraping with AI-powered content boundary detection. The system is designed to gracefully degrade: if AI services are unavailable, it falls back to heuristic-based extraction.

### Key Design Principles

1. **Ad-Free Scraping**: Uses Selenium with uBlock Origin to block ads and trackers
2. **AI-Guided Extraction**: Uses Firecrawl + OpenAI to identify precise content boundaries
3. **Graceful Degradation**: Falls back to heuristics if AI services unavailable
4. **Security First**: SSRF protection, URL validation, secure file handling

---

## Web Scraping Architecture

### Primary Tool: Selenium WebDriver

**Technology**: Selenium 4.38.0 with Chrome/Chromium WebDriver

**Location**: `site_preprocessing.py`

**How It Works**:

1. **Browser Initialization**:

   ```python
   chrome_options = Options()
   chrome_options.add_argument('--headless=new')
   chrome_options.add_argument('--disable-blink-features=AutomationControlled')
   ```

2. **Ad-Blocking Integration**:

   - Loads uBlock Origin extension from `backend/uBlock0.chromium/uBlock0.chromium/`
   - Extension blocks ads, trackers, and unwanted content before page load
   - Falls back gracefully if extension not found (continues without ad-blocking)

3. **Page Rendering**:
   - Waits for JavaScript to fully render (configurable wait time, default: 1 second)
   - Uses `WebDriverWait` to ensure `<body>` element is present
   - Extracts complete HTML after full page load

**Key Functions**:

- `scrape_page(url, wait_time, timeout)`: Main scraping function
- `create_chrome_options()`: Configures Chrome with uBlock Origin
- `chrome_driver_context()`: Context manager for proper resource cleanup

**Advantages**:

- Handles JavaScript-heavy sites
- Blocks ads automatically via uBlock Origin
- Waits for dynamic content to load
- Returns fully rendered HTML

**Limitations**:

- Slower than static HTML parsing
- Requires Chromium browser installed
- Higher resource usage

### Security Features

- **URL Validation**: Prevents SSRF attacks by validating URLs before requests
- **Private IP Blocking**: Blocks access to localhost and private IP ranges
- **Path Validation**: Validates uBlock extension path, prevents symlink attacks

---

## AI-Powered Content Extraction

Clipt uses a **two-stage AI pipeline** to identify precise content boundaries:

1. **Firecrawl**: Converts web pages to clean markdown
2. **OpenAI GPT**: Analyzes markdown to identify first and last contentful sentences

### Why AI-Guided Extraction?

**Problem**: Heuristic extraction (using CSS selectors) often includes:

- Navigation menus
- Sidebars
- Author bios
- Related articles
- Footer content
- Advertisements

**Solution**: Use AI to identify the actual article boundaries by finding the first and last meaningful sentences, then extract the smallest DOM container containing both.

### Firecrawl Integration

**Technology**: Firecrawl Python SDK (`firecrawl-py==4.9.0`)

**Location**: `find_first_and_last_sentences.py` → `scrape_url_to_markdown()`

**Purpose**: Converts web pages to clean, structured markdown format

**How It Works**:

```python
from firecrawl import FirecrawlApp

firecrawl = FirecrawlApp(api_key=Config.get_firecrawl_key())
result = firecrawl.scrape(url, formats=["markdown"])
```

**Process**:

1. **API Key Validation**: Checks for `FIRECRAWL_API_KEY` in environment
2. **URL Scraping**: Calls Firecrawl API with URL and markdown format request
3. **Response Handling**: Extracts markdown content from response (handles both object and dict formats)
4. **Validation**: Ensures markdown content is not empty

**Why Firecrawl?**

**Advantages**:

- **Clean Output**: Removes ads, navigation, and clutter automatically
- **Markdown Format**: Structured, easy-to-parse format for AI analysis
- **Reliability**: Handles complex sites, JavaScript rendering, and anti-bot measures
- **Consistency**: Standardized output format regardless of source site structure

**Use Case in Clipt**:

Firecrawl's markdown output is fed to OpenAI for sentence boundary detection. The markdown format is ideal because:

- It's text-focused (no HTML noise)
- It preserves content structure
- It's easier for LLMs to analyze

**Configuration**:

- **Required**: `FIRECRAWL_API_KEY` in `.env` file (optional - feature degrades gracefully if missing)
- **API Endpoint**: Firecrawl cloud service (no local installation required)

### OpenAI Integration

**Technology**: OpenAI Python SDK (`openai==2.8.1`)

**Model**: `gpt-5-mini` (or latest available)

**Location**: `find_first_and_last_sentences.py` → `extract_first_and_last_sentences()`

**Purpose**: Intelligently identifies first and last contentful sentences from article markdown

**How It Works**:

```python
from openai import OpenAI

client = OpenAI(api_key=Config.get_openai_key())
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    response_format={"type": "json_object"}
)
```

**Process**:

1. **Input**: Markdown content from Firecrawl
2. **Prompt Engineering**: Detailed instructions to identify:
   - First sentence: Directly below article title, within main body
   - Last sentence: From main content only, **BEFORE** author bios/sections
3. **JSON Response**: Returns structured JSON with `first_sentence` and `last_sentence`
4. **Validation**: Ensures both sentences are extracted

**Prompt Strategy**:

The prompt includes specific guidelines:

- ✅ First sentence should be directly below article title
- ✅ Last sentence MUST be from main content, NOT author bio
- ✅ Stop BEFORE reaching author information sections
- ✅ Exclude navigation, ads, external links
- ✅ Handle listicle formats (brief list items)

**Why OpenAI?**

**Advantages**:

- **Semantic Understanding**: Understands context, not just pattern matching
- **Handles Edge Cases**: Works with various article formats (listicles, interviews, etc.)
- **Author Bio Detection**: Intelligently stops before author sections
- **Consistent Output**: JSON format ensures reliable parsing

**Limitations**:

- Requires API key and credits
- Network dependency
- Cost per request

**Configuration**:

- **Required**: `OPENAI_API_KEY` in `.env` file (optional - feature degrades gracefully if missing)

---

## Technology Stack

### Core Web Scraping

| Tool              | Version      | Purpose                                  |
| ----------------- | ------------ | ---------------------------------------- |
| **Selenium**      | 4.38.0       | Browser automation, JavaScript rendering |
| **ChromeDriver**  | Auto-managed | Chrome/Chromium WebDriver                |
| **uBlock Origin** | Latest       | Ad-blocking extension                    |

### AI Services

| Tool          | Version | Purpose                                   |
| ------------- | ------- | ----------------------------------------- |
| **Firecrawl** | 4.9.0   | Web scraping API, markdown conversion     |
| **OpenAI**    | 2.8.1   | GPT model for sentence boundary detection |

### HTML Processing

| Tool               | Version | Purpose                           |
| ------------------ | ------- | --------------------------------- |
| **BeautifulSoup4** | 4.14.2  | HTML parsing and DOM manipulation |
| **lxml**           | 6.0.2   | Fast XML/HTML parser backend      |

### Image Processing

| Tool             | Version | Purpose                                        |
| ---------------- | ------- | ---------------------------------------------- |
| **Pillow (PIL)** | 12.0.0  | Image downloading, resizing, format conversion |

### Output Generation

| Tool            | Version | Purpose                     |
| --------------- | ------- | --------------------------- |
| **WeasyPrint**  | 66.0    | HTML to PDF conversion      |
| **python-docx** | 1.2.0   | DOCX document generation    |
| **htmldocx**    | 0.0.5   | HTML to DOCX conversion     |
| **markdownify** | 1.2.2   | HTML to Markdown conversion |

### Network & Utilities

| Tool              | Version | Purpose                         |
| ----------------- | ------- | ------------------------------- |
| **requests**      | 2.32.5  | HTTP requests with retry logic  |
| **urllib3**       | 2.5.0   | URL handling and validation     |
| **python-dotenv** | 1.2.1   | Environment variable management |

### Methodology Summary

1. **Dual Scraping Approach**

   - **Selenium**: For JavaScript-heavy sites, full page rendering
   - **Firecrawl**: For clean markdown conversion (AI preprocessing)

2. **Hybrid Content Extraction**

   - **AI-Guided** (when available): Precise boundaries via Firecrawl + OpenAI
   - **Heuristic Fallback**: CSS selectors, semantic HTML parsing

3. **Progressive Enhancement**

   - Core functionality works without AI
   - AI enhances precision when available
   - Graceful degradation ensures reliability

4. **Security-First Design**
   - URL validation prevents SSRF
   - Path validation prevents symlink attacks
   - Size limits prevent memory exhaustion
   - Input sanitization prevents XSS

### Configuration Requirements

**Required (Core Functionality)**:

- None - Core scraping works without API keys

**Optional (AI Enhancement)**:

- `FIRECRAWL_API_KEY`: Enables AI-guided content boundary detection
- `OPENAI_API_KEY`: Required for sentence extraction (works with Firecrawl)

**System Requirements**:

- Python 3.8+
- Chromium browser installed
- ChromeDriver (auto-managed by Selenium 4.x)
- uBlock Origin extension (download separately)

### Performance Characteristics

**Scraping Speed**:

- **Selenium**: ~2-5 seconds per page (includes JavaScript rendering)
- **Firecrawl**: ~1-3 seconds per page (cloud service)
- **OpenAI**: ~1-2 seconds per request

**Resource Usage**:

- **Memory**: Moderate (image processing can be memory-intensive)
- **CPU**: Low (mostly I/O bound)
- **Network**: Moderate (multiple HTTP requests per page)

**Reliability**:

- **Selenium**: High (handles most sites)
- **Firecrawl**: High (handles anti-bot measures)
- **OpenAI**: High (consistent API)

### Best Practices

1. **Always validate URLs** before scraping
2. **Use context managers** for resource cleanup (Selenium drivers)
3. **Implement retry logic** for network requests
4. **Set size limits** to prevent memory exhaustion
5. **Log all operations** for debugging
6. **Graceful degradation** - never fail completely if optional services unavailable

---

## Complete Processing Pipeline

### Step-by-Step Flow

```
1. URL Input
   ↓
2. Selenium Scraping (with uBlock Origin)
   ├─ Validates URL (SSRF protection)
   ├─ Loads Chromium with uBlock extension
   ├─ Waits for JavaScript rendering
   └─ Returns full HTML
   ↓
3. Logo Extraction
   ├─ Searches for logo in DOM
   ├─ Checks structured data (JSON-LD)
   └─ Returns logo URL and metadata
   ↓
4. Header Extraction
   ├─ Extracts title (h1, meta tags, structured data)
   ├─ Extracts subtitle (near title, meta description)
   └─ Returns formatted headers
   ↓
5. AI Content Boundary Detection (Optional)
   ├─ Firecrawl: URL → Clean Markdown
   ├─ OpenAI: Markdown → First/Last Sentences
   └─ Returns sentence boundaries
   ↓
6. Content Extraction
   ├─ If AI boundaries available:
   │  └─ Finds smallest DOM container with both sentences
   └─ If not available:
      └─ Uses heuristic selectors (main, article, etc.)
   ↓
7. Keyword Filtering (Optional)
   ├─ Filters paragraphs by keywords
   ├─ Optionally preserves first paragraph
   └─ Removes non-matching content
   ↓
8. Image Processing
   ├─ Finds images near paragraphs
   ├─ Downloads and resizes images
   ├─ Converts to data URIs
   └─ Positions images in content
   ↓
9. Subtitle Validation
   ├─ Verifies subtitle is between title and first paragraph
   └─ Adjusts if needed
   ↓
10. Output Generation
    ├─ Builds final HTML document
    ├─ Converts to requested format (DOCX, PDF, Markdown)
    └─ Returns file path or bytes
```

### AI Integration Points

**Primary Integration**: `clipping_logic.py` → `process_url_to_file()`

```python
# Step 3.75: AI Content Boundary Detection
if use_ai_extraction:
    sentence_result = find_first_and_last_sentences.find_first_and_last_sentences_from_url(
        url,
        use_firecrawl=True
    )

    if sentence_result['success']:
        first_sentence = sentence_result['first_sentence']
        last_sentence = sentence_result['last_sentence']
    else:
        # Graceful degradation: use heuristics
        first_sentence = None
        last_sentence = None

# Step 4: Content Extraction (uses AI boundaries if available)
extracted_content_html = content_extraction.extract_main_content(
    html_content,
    first_sentence=first_sentence,  # AI-identified boundary
    last_sentence=last_sentence      # AI-identified boundary
)
```

**Fallback Behavior**:

- If Firecrawl fails → Falls back to heuristic extraction
- If OpenAI fails → Falls back to heuristic extraction
- If API keys missing → Falls back to heuristic extraction
- System always produces output, even without AI

---

## Module Documentation

## site_preprocessing.py

**Purpose**: Web scraping with Selenium and uBlock Origin ad-blocking.

### `scrape_page(url, wait_time=None, timeout=None) -> Optional[str]`

**What it does**: Scrapes a webpage using Selenium with Chrome in headless mode, loads uBlock Origin extension to block ads, waits for page to render, and returns the HTML content.

**How it works**:

1. Validates the URL using `validate_url()` to prevent SSRF attacks
2. Creates Chrome options with headless mode and uBlock Origin extension
3. Uses a context manager to ensure browser cleanup
4. Loads the URL with Selenium WebDriver
5. Waits for specified time (default 1 second) for JavaScript rendering
6. Waits for `<body>` element to be present
7. Returns the page source HTML

**Parameters**:

- `url`: The URL to scrape
- `wait_time`: Time to wait for page rendering (default: `PageConfig.LOAD_WAIT_TIME`)
- `timeout`: Maximum time to wait for page load (default: `PageConfig.PAGE_TIMEOUT`)

**Returns**: HTML content as string, or `None` if scraping fails

**Security**: Validates URLs to prevent SSRF attacks, blocks access to localhost and private IPs

---

### `create_chrome_options() -> Options`

**What it does**: Creates Chrome browser options with headless mode and uBlock Origin extension.

**How it works**:

1. Creates Chrome options object
2. Adds headless mode arguments (`--headless=new`, `--disable-blink-features=AutomationControlled`, etc.)
3. Attempts to load uBlock Origin extension from `./uBlock0.chromium/uBlock0.chromium`
4. Validates extension path exists and is not a symlink (security check)
5. Returns configured options

**Returns**: Configured Chrome Options object

---

### `chrome_driver_context(options) -> ContextManager`

**What it does**: Context manager for Chrome WebDriver that ensures proper cleanup.

**How it works**:

1. Creates Chrome WebDriver instance
2. Yields driver for use
3. Always calls `driver.quit()` in finally block to clean up resources

**Returns**: Context manager yielding Chrome WebDriver

---

## content_extraction.py

**Purpose**: Extracts main content from HTML, optionally using AI-identified sentence boundaries.

### `extract_main_content(html_content, first_sentence=None, last_sentence=None) -> str`

**What it does**: Extracts the main content body from HTML. If first and last sentences are provided, finds the smallest container containing both. Otherwise, uses heuristic selectors.

**How it works**:

1. **If both sentences provided** (AI-guided extraction):

   - Calls `extract_content_between_sentences()` to find smallest container
   - Returns extracted HTML if successful
   - Falls back to heuristic if sentence extraction fails

2. **Heuristic fallback**:
   - Parses HTML with BeautifulSoup
   - Tries common main content selectors in priority order:
     - `main`, `article`, `[role="main"]`
     - `.main-content`, `.article-content`, `.post-content`, `.entry-content`
     - `#main-content`, `#content`, `.content`
   - If no selector matches, uses `<body>` element
   - If no body, uses entire document

**Parameters**:

- `html_content`: Full HTML content as string
- `first_sentence`: Optional first sentence to find (from AI extraction)
- `last_sentence`: Optional last sentence to find (from AI extraction)

**Returns**: Extracted HTML string (preserves all attributes: styles, classes, IDs)

---

### `extract_content_between_sentences(html_content, first_sentence, last_sentence) -> Tuple[Optional[str], Optional[Tag]]`

**What it does**: Finds the smallest HTML container that contains both the first and last sentences.

**How it works**:

1. Parses HTML with BeautifulSoup
2. Finds element containing first sentence using `find_element_containing_sentence()`
3. Finds element containing last sentence using `find_element_containing_sentence()`
4. Finds common container using `find_common_container()` (walks up DOM tree)
5. Returns container as HTML string and Tag object

**Parameters**:

- `html_content`: Full HTML content
- `first_sentence`: First sentence text to find
- `last_sentence`: Last sentence text to find

**Returns**: Tuple of (extracted HTML string, container Tag) or (None, None) if not found

---

### `find_element_containing_sentence(soup, sentence) -> Optional[Tag]`

**What it does**: Finds the deepest element that contains a given sentence.

**How it works**:

1. Normalizes sentence text (lowercase, collapse whitespace)
2. Iterates through all elements in soup
3. Checks if normalized sentence appears in element's text content
4. Collects all candidate elements
5. Sorts candidates by depth (number of ancestors)
6. Returns the deepest element (most specific)

**Parameters**:

- `soup`: BeautifulSoup object to search
- `sentence`: Sentence text to find

**Returns**: Deepest Tag containing the sentence, or None

---

### `find_common_container(element1, element2) -> Optional[Tag]`

**What it does**: Finds the smallest container that contains both elements.

**How it works**:

1. If elements are the same, return that element
2. If one contains the other, return the containing element
3. Walk up the DOM tree from element1's parent
4. At each level, check if that parent contains element2
5. Return first parent that contains both

**Parameters**:

- `element1`: First element
- `element2`: Second element

**Returns**: Smallest common container Tag, or None

---

### `normalize_text(text) -> str`

**What it does**: Normalizes text for comparison by collapsing whitespace and lowercasing.

**How it works**:

1. Strips leading/trailing whitespace
2. Converts to lowercase
3. Replaces all whitespace sequences with single space

**Returns**: Normalized text string

---

## header_extraction.py

**Purpose**: Extracts article title and subtitle from HTML with formatting information.

### `extract_headers(html_content) -> dict`

**What it does**: Extracts title and subtitle using multiple strategies: DOM elements, meta tags, and structured data.

**How it works**:

1. **Title extraction** (tries in order):

   - DOM elements: `_find_title_in_dom()` - searches for h1 tags in article/main areas, or elements with "title"/"headline" in class/id
   - Meta tags: `_find_title_in_meta()` - checks og:title, twitter:title, or `<title>` tag
   - Structured data: `_find_title_in_structured_data()` - extracts from JSON-LD schema.org data

2. **Subtitle extraction** (tries in order):

   - DOM elements: `_find_subtitle_in_dom()` - searches near title, or elements with "subtitle"/"dek"/"deck" in class/id
   - Meta tags: `_find_subtitle_in_meta()` - checks og:description, meta description
   - Structured data: `_find_subtitle_in_structured_data()` - extracts alternativeHeadline or description

3. For each found element, extracts formatting info using `_extract_formatting_info()`

**Returns**: Dictionary with:

- `'title'`: dict with `text`, `element`, `tag`, `classes`, `id`, `style`, `formatted_html` (or None)
- `'subtitle'`: same structure (or None)

---

### `_extract_formatting_info(element) -> dict`

**What it does**: Extracts formatting information from a BeautifulSoup element.

**How it works**:

1. Gets text content (stripped)
2. Gets tag name
3. Gets CSS classes (as list)
4. Gets ID attribute
5. Gets inline style attribute
6. Gets formatted HTML string representation

**Returns**: Dictionary with formatting information

---

### `_find_title_in_dom(soup) -> Optional[Tag]`

**What it does**: Finds title in DOM using semantic HTML tags and class/id selectors.

**How it works**:

1. Strategy 1: Look for h1 tags in article/main content areas (`article h1`, `main h1`, `[role="main"] h1`, `body h1`)
2. Strategy 2: Search all elements for "title"/"headline" in class/id attributes
3. Strategy 3: Find first h1 in body
4. Validates that text is not empty and length > 5 characters

**Returns**: BeautifulSoup element or None

---

### `_find_subtitle_in_dom(soup, title_element) -> Optional[Tag]`

**What it does**: Finds subtitle in DOM, preferably near the title element.

**How it works**:

1. If title_element provided:
   - Checks next sibling of title
   - Checks parent's next sibling
   - Looks for subtitle patterns in nearby elements
2. Searches for h2 tags in article/main areas
3. Searches all elements for "subtitle"/"dek"/"deck"/"lead"/"summary" in class/id
4. Validates text length > 10 characters

**Returns**: BeautifulSoup element or None

---

### `_find_title_in_meta(soup) -> Optional[str]`

**What it does**: Extracts title from meta tags.

**How it works**:

1. Checks `<meta property="og:title">`
2. Checks `<meta name="twitter:title">`
3. Checks `<title>` tag, removes site name suffix (e.g., " | Vogue")

**Returns**: Title text string or None

---

### `_find_subtitle_in_meta(soup) -> Optional[str]`

**What it does**: Extracts subtitle from meta description tags.

**How it works**:

1. Checks `<meta property="og:description">`
2. Checks `<meta name="description">`
3. Checks `<meta name="twitter:description">`

**Returns**: Subtitle text string or None

---

### `_find_title_in_structured_data(soup) -> Optional[str]`

**What it does**: Extracts title from JSON-LD structured data.

**How it works**:

1. Finds all `<script type="application/ld+json">` tags
2. Parses JSON content
3. Looks for `headline` or `name` fields in NewsArticle, Article, Organization, etc.
4. Handles both single objects and arrays

**Returns**: Title text string or None

---

### `_find_subtitle_in_structured_data(soup) -> Optional[str]`

**What it does**: Extracts subtitle from JSON-LD structured data.

**How it works**:

1. Finds all JSON-LD script tags
2. Parses JSON content
3. Looks for `alternativeHeadline` or `description` fields

**Returns**: Subtitle text string or None

---

## subtitle_validation.py

**Purpose**: Validates that subtitle is correctly positioned between title and first paragraph.

### `validate_subtitle_position(original_html, headers, extracted_content_html) -> dict`

**What it does**: Validates subtitle position and returns detailed results.

**How it works**:

1. Checks if title and subtitle exist in headers
2. Verifies both have DOM elements (not from meta/structured data)
3. Finds first paragraph in extracted content using `find_first_paragraph_in_extracted_content()`
4. Finds matching paragraph in original HTML using `find_matching_paragraph_in_original()`
5. Gets all elements in document order using `get_all_elements_in_order()`
6. Gets DOM positions for title, subtitle, and first paragraph
7. Verifies order: `title_position < subtitle_position < first_paragraph_position`

**Returns**: Dictionary with:

- `'is_valid'`: bool - Whether subtitle is correctly positioned
- `'reason'`: str - Reason for validation result
- `'title_position'`: int or None - DOM position of title
- `'subtitle_position'`: int or None - DOM position of subtitle
- `'first_paragraph_position'`: int or None - DOM position of first paragraph

---

### `is_subtitle_correctly_positioned(original_html, headers, extracted_content_html) -> bool`

**What it does**: Simplified boolean check for subtitle position.

**How it works**: Same as `validate_subtitle_position()` but returns only boolean result.

**Returns**: True if subtitle is correctly positioned, False otherwise

---

## image_positioning.py

**Purpose**: Finds images around paragraphs and below titles in HTML documents.

### `find_image_below_title(original_html, headers, base_url=None, max_distance=5) -> Optional[Dict]`

**What it does**: Finds the image element immediately below the title.

**How it works**:

1. Gets title element from headers
2. Verifies title has DOM element (not from meta/structured data)
3. Parses original HTML
4. Calls `find_nearest_image_below()` to find image
5. Extracts image URL using `_extract_image_info()` (wrapper around `image_utils.extract_image_info()`)
6. Returns image URL as unique identifier

**Parameters**:

- `original_html`: Full original HTML content
- `headers`: Dictionary from `header_extraction.extract_headers()`
- `base_url`: Base URL for converting relative paths
- `max_distance`: Maximum number of sibling elements to search

**Returns**: Image URL string or None

---

### `find_nearest_image_below(paragraph_element, original_soup, max_distance=5) -> Optional[Tag]`

**What it does**: Finds the nearest image element below a paragraph in the DOM.

**How it works**:

1. **Strategy 1**: Check next siblings (up to max_distance)

   - Iterates through next siblings
   - Checks if element is an image using `is_image_element()`
   - Checks if element contains an img tag

2. **Strategy 2**: Check parent's next siblings

   - Gets paragraph's parent
   - Checks parent's next siblings for images

3. **Strategy 3**: Check all next elements in document order
   - Gets all elements in document order
   - Finds paragraph position
   - Searches forward up to `max_distance * 10` elements
   - Returns first image found

**Returns**: BeautifulSoup image element or None

---

### `is_image_element(element) -> bool`

**What it does**: Checks if an element is an image (img tag, picture tag, or figure with img).

**How it works**:

1. Checks if element is `img` tag
2. Checks if element is `picture` tag
3. Checks if element is `figure` tag with img inside
4. Checks if element contains img and has image-related classes/IDs (image, img, photo, picture, figure, media)
5. Checks if img is a direct child (likely image wrapper)

**Returns**: True if element is or contains an image

---

### `get_image_container(img_element) -> Optional[Tag]`

**What it does**: Gets the best container element for an image (figure, picture, or direct parent).

**How it works**:

1. If element is already `figure` or `picture`, return it
2. If element is `img`, find parent `figure` or `picture`
3. If no figure/picture, find parent div/section/article with image-related classes
4. Return the img itself if no container found

**Returns**: Best container element or the img itself

---

## logo_extraction.py

**Purpose**: Extracts website logo from HTML content.

### `extract_logo(html_content, root_domain, base_url=None) -> dict`

**What it does**: Extracts the website's logo using multiple strategies.

**How it works**:

1. **Strategy 1: Image/SVG tags with "logo" keyword**:

   - Finds all `<img>` and `<svg>` tags
   - Checks if "logo" appears in element attributes (class, id, src, alt, title, name, aria-label, data-\*)
   - Checks parent `<a>` tag attributes
   - Checks parent containers (up to 5 levels) for "logo" in class/id/data-_/aria-_
   - Verifies image is inside a link pointing to root domain
   - Verifies it's an actual image file (svg, png, jpg, etc.)
   - Converts relative URLs to absolute

2. **Strategy 2: JSON-LD structured data**:

   - Finds all `<script type="application/ld+json">` tags
   - Parses JSON content
   - Extracts publisher logo from NewsArticle, Article, Organization, etc.
   - Validates logo URL is from same domain or subdomain

3. **Selection**:
   - Collects all candidates
   - Sorts by size (width \* height, largest first)
   - Returns the largest logo

**Parameters**:

- `html_content`: HTML content as string
- `root_domain`: Root domain to match (e.g., "example.com")
- `base_url`: Base URL for converting relative paths

**Returns**: Dictionary with:

- `'element'`: BeautifulSoup element (or None)
- `'src'`: Original image source
- `'url'`: Absolute URL (or None)
- `'alt'`: Alt text (or None)
- `'width'`: Width attribute (or None)
- `'height'`: Height attribute (or None)

---

### `get_root_domain(url) -> str`

**What it does**: Extracts the root domain from a URL.

**How it works**:

1. Parses URL using `urlparse()`
2. Gets netloc (hostname)
3. Removes "www." prefix
4. Removes port if present

**Returns**: Root domain string (e.g., "example.com")

---

## output_generation.py

**Purpose**: Converts HTML to various file formats (DOCX, PDF, Markdown).

### `convert_html(html_content, filetype) -> Union[bytes, str]`

**What it does**: Converts HTML content to specified file format.

**How it works**:

1. Normalizes filetype (case-insensitive)
2. Routes to appropriate conversion function:
   - `'docx'` or `'doc'` → `html_to_docx()`
   - `'pdf'` → `html_to_pdf()`
   - `'md'` or `'markdown'` → `html_to_markdown()`

**Returns**: bytes for binary formats, str for text formats

---

### `html_to_docx(html_content) -> bytes`

**What it does**: Converts HTML to DOCX document.

**How it works**:

1. Processes images: deduplicates, downloads, resizes using `_process_images_in_html()`
2. Parses HTML with BeautifulSoup
3. Preprocesses subtitle elements: converts h2/h3 subtitles to styled paragraphs (italic, centered)
4. Converts data URI images to temporary files (htmldocx works better with file paths)
5. Uses `htmldocx.HtmlToDocx` to convert HTML to DOCX
6. Saves to BytesIO and returns bytes
7. Cleans up temporary files

**Returns**: DOCX document as bytes

---

### `html_to_pdf(html_content) -> bytes`

**What it does**: Converts HTML to PDF document.

**How it works**:

1. Processes images using `_process_images_in_html()`
2. Uses WeasyPrint `HTML()` to convert HTML to PDF
3. Returns PDF bytes

**Returns**: PDF document as bytes

---

### `html_to_markdown(html_content) -> str`

**What it does**: Converts HTML to Markdown document.

**How it works**:

1. Processes images using `_process_images_in_html()`
2. Parses HTML with BeautifulSoup
3. Preserves image dimensions in markdown (as HTML img tags if dimensions available)
4. Uses `markdownify.markdownify()` to convert HTML to Markdown
5. Strips script and style tags

**Returns**: Markdown content as string

---

### `_process_images_in_html(html_content, target_width=800) -> str`

**What it does**: Processes all images in HTML: deduplicates by URL, downloads, and resizes.

**How it works**:

1. Parses HTML with BeautifulSoup
2. Finds all `<img>` tags
3. Collects unique image URLs (normalized for deduplication)
4. Downloads and processes each unique image in parallel (max 5 concurrent):
   - Downloads image using `download_image()`
   - Resizes to target_width using `resize_image()`
   - Converts to data URI (base64)
5. Replaces all image tags with processed versions (data URIs)
6. Updates width/height attributes

**Returns**: HTML content with processed images

---

## find_first_and_last_sentences.py

**Purpose**: Extracts first and last contentful sentences from web articles using Firecrawl and OpenAI.

### `find_first_and_last_sentences_from_url(url, use_firecrawl=True) -> Dict[str, Optional[str]]`

**What it does**: Complete integration function to extract first and last contentful sentences from a URL.

**How it works**:

1. Scrapes URL with Firecrawl using `scrape_url_to_markdown()` to get clean markdown
2. Extracts sentences using `extract_first_and_last_sentences()` with OpenAI
3. Returns sentences for use in content extraction

**Parameters**:

- `url`: The URL to process
- `use_firecrawl`: If True (default), use Firecrawl. If False, returns empty sentences.

**Returns**: Dictionary with:

- `'first_sentence'`: First contentful sentence (or None)
- `'last_sentence'`: Last contentful sentence (or None)
- `'success'`: Boolean indicating success
- `'error'`: Error message if failed (None otherwise)

---

### `scrape_url_to_markdown(url) -> Dict[str, str]`

**What it does**: Scrapes a URL using Firecrawl and converts it to markdown.

**How it works**:

1. Gets Firecrawl API key from config
2. Initializes FirecrawlApp
3. Calls `firecrawl.scrape(url, formats=["markdown"])`
4. Handles response (SDK may return object with attributes or dict)
5. Validates markdown content is not empty

**Returns**: Dictionary with:

- `'markdown'`: Markdown content
- `'url'`: Original URL
- `'title'`: Page title (if available)

**Raises**: ValueError if FIRECRAWL_API_KEY not set

---

### `extract_first_and_last_sentences(markdown_content) -> Dict[str, str]`

**What it does**: Extracts first and last contentful sentences using OpenAI.

**How it works**:

1. Gets OpenAI API key from config
2. Constructs prompt with guidelines:
   - First sentence should be directly below article title
   - Last sentence MUST be from main content, NOT from author bio
   - Stop before reaching author information sections
   - Exclude ads, navigation, external links
3. Calls OpenAI API (gpt-5-mini) with JSON response format
4. Parses JSON response
5. Returns first and last sentences

**Returns**: Dictionary with:

- `'first_sentence'`: First contentful sentence
- `'last_sentence'`: Last contentful sentence

**Raises**: ValueError if OPENAI_API_KEY not set

---

## keyword_filtering.py

**Purpose**: Filters HTML content by keywords, keeping only paragraphs/lists that contain keywords.

### `filter_content_by_keywords(html_content, keywords=None, include_first_paragraph=False) -> str`

**What it does**: Filters HTML content, keeping only text objects (paragraphs, lists, etc.) that contain at least one keyword.

**How it works**:

1. If no keywords provided, returns original content
2. Normalizes keywords for comparison
3. Parses HTML with BeautifulSoup
4. Preserves all `<style>` tags
5. Finds all discrete content units: `<p>`, `<div>`, `<li>`, `<ul>`, `<ol>`, `<article>`, `<section>`, `<blockquote>`
6. Filters to top-level units only (not nested within another content unit)
7. For each content unit:
   - Normalizes text content
   - Checks if it contains any keyword
   - If `include_first_paragraph=True`, always includes first unit
   - If unit matches, finds adjacent images using `find_adjacent_images()`
8. Removes content units that don't match
9. Removes images that are not adjacent to kept units and not inside kept units
10. Returns filtered HTML (preserves styles, classes, IDs, inline styles)

**Parameters**:

- `html_content`: HTML content string to filter
- `keywords`: Optional list of keywords to filter by
- `include_first_paragraph`: If True, always include first content unit

**Returns**: Filtered HTML string

---

### `find_adjacent_images(element, container) -> List[Tag]`

**What it does**: Finds images that are immediately before or after an element within the container.

**How it works**:

1. Gets all direct children of container in document order
2. Finds index of element's parent (or element itself if direct child)
3. Checks previous sibling for images
4. Checks next sibling for images
5. Checks direct siblings of element
6. Falls back to `find_adjacent_images_by_descendants()` if index not found

**Returns**: List of image elements (img, picture, figure)

---

### `normalize_text(text) -> str`

**What it does**: Normalizes text for comparison (same as in content_extraction.py).

**How it works**: Collapses whitespace and lowercases text.

**Returns**: Normalized text string

---

## url_utils.py

**Purpose**: URL normalization and validation utilities.

### `normalize_image_url(url) -> str`

**What it does**: Normalizes an image URL for duplicate detection.

**How it works**:

1. Parses URL using `urlparse()`
2. Reconstructs URL without query parameters and fragments
3. Returns normalized URL

**Example**: `"https://example.com/img.jpg?size=large#top"` → `"https://example.com/img.jpg"`

**Returns**: Normalized URL string

---

### `validate_url(url, allow_private=None) -> tuple[bool, Optional[str]]`

**What it does**: Validates a URL for security (SSRF protection).

**How it works**:

1. Parses URL
2. Checks scheme is HTTP or HTTPS
3. Checks hostname exists
4. Checks hostname is not in blocked hosts (localhost, 127.0.0.1, cloud metadata endpoints)
5. If `allow_private=False`, checks hostname is not a private IP address
6. Returns validation result

**Parameters**:

- `url`: URL to validate
- `allow_private`: Override for allowing private IPs (defaults to `SecurityConfig.ALLOW_PRIVATE_IPS`)

**Returns**: Tuple of (is_valid: bool, error_message: Optional[str])

---

### `is_valid_http_url(url) -> bool`

**What it does**: Quick check if URL is valid HTTP/HTTPS.

**How it works**: Parses URL and checks scheme is HTTP/HTTPS and netloc exists.

**Returns**: True if valid HTTP/HTTPS URL

---

## image_utils.py

**Purpose**: Image utility functions for downloading, parsing, and extracting image information.

### `extract_image_info(img_element, base_url=None, fetch_dimensions=True, fetch_content=False) -> Dict`

**What it does**: Extracts comprehensive information from an image element.

**How it works**:

1. Handles different element types:

   - If `picture` element, finds `<img>` inside and checks `<source>` elements for srcset
   - If `figure` element, finds `<img>` inside
   - Otherwise uses element as-is

2. **Priority order for getting highest quality image**:

   - `picture` source srcset (responsive images - gets highest resolution)
   - `img` srcset (responsive images - gets highest resolution)
   - `data-srcset` (lazy-loaded responsive)
   - `data-src` (lazy-loaded single)
   - `data-lazy-src` (alternative lazy-load)
   - `data-original` (original quality lazy-load)
   - `src` (fallback)

3. Parses srcset using `parse_srcset()` to get best quality URL
4. Converts relative URLs to absolute using `base_url`
5. Gets HTML attributes (alt, width, height)
6. If `fetch_dimensions=True`, downloads image using `download_image()` to get actual dimensions
7. If `fetch_content=True`, downloads and stores image bytes

**Returns**: Dictionary with:

- `'element'`: BeautifulSoup element
- `'src'`: Image source URL
- `'url'`: Absolute URL
- `'alt'`: Alt text
- `'width'`: Width (from attribute or actual)
- `'height'`: Height (from attribute or actual)
- `'actual_width'`: Actual width from file
- `'actual_height'`: Actual height from file
- `'type'`: Element type ('img', 'picture', 'figure')
- `'content'`: Image bytes (only if fetch_content=True)

---

### `download_image(url) -> Tuple[Optional[bytes], Optional[int], Optional[int]]`

**What it does**: Downloads image and gets its dimensions with memory safety.

**How it works**:

1. Calls `download_with_size_limit()` to download with size limit (prevents memory exhaustion)
2. Gets dimensions using PIL if available
3. Falls back to `_get_dimensions_from_headers()` if PIL not available
4. Returns image bytes, width, and height

**Returns**: Tuple of (image_bytes, width, height) or (None, None, None) if failed

---

### `resize_image(image_bytes, target_width) -> Tuple[bytes, Optional[int], Optional[int]]`

**What it does**: Resizes an image to target width while maintaining aspect ratio.

**How it works**:

1. Opens image with PIL
2. Gets original dimensions
3. Calculates new height maintaining aspect ratio
4. Resizes using LANCZOS resampling
5. Saves to bytes preserving original format
6. Returns resized bytes and dimensions

**Returns**: Tuple of (resized_image_bytes, width, height)

---

### `parse_srcset(srcset_str) -> List[Tuple[str, Optional[float]]]`

**What it does**: Parses a srcset string and returns list of (url, descriptor_value) tuples.

**How it works**:

1. Limits srcset length to prevent DoS (max 10000 chars)
2. Splits by comma (handles commas in URLs by tracking parentheses)
3. For each part:
   - Extracts descriptor using regex (e.g., "1920w" or "2x")
   - Parses descriptor value (width in pixels for 'w', density for 'x')
   - Extracts URL
4. Sorts by descriptor value (highest first)

**Returns**: List of (url, descriptor_value) tuples, sorted by descriptor (highest first)

---

### `get_best_image_from_srcset(srcset_str, base_url=None) -> Optional[str]`

**What it does**: Extracts the highest quality image URL from a srcset string.

**How it works**:

1. Parses srcset using `parse_srcset()`
2. Gets first (highest quality) source
3. Converts to absolute URL if base_url provided

**Returns**: Best quality image URL (absolute if base_url provided) or None

---

### `_get_dimensions_from_headers(image_bytes) -> Tuple[Optional[int], Optional[int]]`

**What it does**: Fallback method to get image dimensions from image file headers (when PIL unavailable).

**How it works**:

1. Checks image signature:
   - PNG: width/height at bytes 16-23
   - JPEG: parses SOF markers to find dimensions
   - GIF: width/height at bytes 6-9
   - WebP: parses VP8/VP8L chunks

**Returns**: Tuple of (width, height) or (None, None)

---

## network_utils.py

**Purpose**: Network utilities with retry logic and connection pooling.

### `download_with_size_limit(url, max_size, timeout=30, chunk_size=8192) -> bytes`

**What it does**: Downloads content with size limit to prevent memory exhaustion.

**How it works**:

1. Gets session using `get_session()` (with retry logic and connection pooling)
2. Makes GET request with streaming enabled
3. Checks Content-Length header - raises error if exceeds max_size
4. Streams download in chunks
5. Tracks total size - raises error if exceeds max_size during download
6. Returns downloaded content

**Parameters**:

- `url`: URL to download
- `max_size`: Maximum size in bytes
- `timeout`: Request timeout in seconds
- `chunk_size`: Size of chunks to download

**Returns**: Downloaded content as bytes

**Raises**: ValueError if content exceeds max_size

---

### `get_session() -> requests.Session`

**What it does**: Gets a requests session with connection pooling and retry logic (singleton pattern).

**How it works**:

1. Checks if global session exists
2. If not, creates session using `create_session_with_retries()`
3. Returns session

**Returns**: Configured requests.Session instance

---

### `create_session_with_retries(total_retries=3, backoff_factor=1.0, status_forcelist=(429, 500, 502, 503, 504)) -> requests.Session`

**What it does**: Creates a requests session with retry strategy and connection pooling.

**How it works**:

1. Creates requests.Session
2. Configures Retry strategy:
   - Total retries
   - Exponential backoff
   - Status codes to retry on (429, 500, 502, 503, 504)
3. Configures HTTPAdapter with:
   - Retry strategy
   - Connection pooling (pool_connections, pool_maxsize)
4. Mounts adapter for HTTP and HTTPS

**Returns**: Configured requests.Session

---

## dom_utils.py

**Purpose**: DOM manipulation utilities for BeautifulSoup elements.

### `get_all_elements_in_order(soup) -> list`

**What it does**: Gets all elements in document order.

**How it works**: Uses `soup.find_all(True)` to find all tags in document order.

**Returns**: List of all elements in document order

---

### `get_element_position(element, all_elements) -> Optional[int]`

**What it does**: Gets the position of an element in the DOM tree.

**How it works**:

1. Checks if element is None
2. Finds index of element in all_elements list
3. Returns index or None if not found

**Returns**: Position index (0-based) or None

---

### `find_first_paragraph_in_extracted_content(extracted_html) -> Optional[Tag]`

**What it does**: Finds the first paragraph element in extracted content HTML.

**How it works**:

1. Parses extracted HTML with BeautifulSoup
2. Finds first `<p>` tag
3. Returns element or None

**Returns**: BeautifulSoup paragraph element or None

---

### `find_matching_paragraph_in_original(original_soup, extracted_paragraph) -> Optional[Tag]`

**What it does**: Finds the matching paragraph in original HTML by matching text content.

**How it works**:

1. Gets text content of extracted paragraph (normalized)
2. Searches all paragraphs in original HTML
3. Tries exact text match first
4. If exact match fails, tries partial match (first 50 chars)

**Returns**: Matching BeautifulSoup paragraph element or None

---

## constants.py

**Purpose**: Centralized constants and configuration values.

### Configuration Classes

- **ImageConfig**: Image processing constants (MAX_SEARCH_DISTANCE, TARGET_WIDTH, MAX_SIZE, TIMEOUT, etc.)
- **PageConfig**: Web scraping constants (LOAD_WAIT_TIME, PAGE_TIMEOUT, MAX_RETRIES, etc.)
- **DocumentConfig**: Document output constants (PAGE_WIDTH_INCHES, LOGO_WIDTH_PERCENT, etc.)
- **FileConfig**: File handling constants (TEMP_DIR_NAME, MAX_FILENAME_LENGTH, etc.)
- **NetworkConfig**: Network request constants (DEFAULT_TIMEOUT, MAX_RETRIES, MAX_SRCSET_LENGTH, etc.)
- **ContentConfig**: Content extraction constants (MIN_PARAGRAPH_LENGTH, MAIN_CONTENT_SELECTORS, etc.)
- **LogoConfig**: Logo extraction constants (MIN_LOGO_SIZE, MAX_LOGO_SIZE, etc.)
- **SecurityConfig**: Security-related constants (ALLOWED_URL_SCHEMES, BLOCKED_HOSTS, ALLOW_PRIVATE_IPS, etc.)
- **CacheConfig**: Caching constants (IMAGE_CACHE_SIZE, IMAGE_CACHE_TTL, etc.)

---

## logger.py

**Purpose**: Logging configuration for Clipt backend.

### `get_logger(name) -> logging.Logger`

**What it does**: Gets an existing logger or creates a new one with default settings.

**How it works**:

1. Gets logger by name
2. If logger has no handlers, calls `setup_logger()` to create one
3. Returns logger

**Returns**: Logger instance

---

### `setup_logger(name, level='INFO', log_file=None) -> logging.Logger`

**What it does**: Sets up a logger with consistent formatting.

**How it works**:

1. Gets or creates logger by name
2. Sets log level
3. Avoids duplicate handlers
4. Creates formatter with timestamp, name, level, message
5. Adds console handler (stdout)
6. Optionally adds file handler if log_file provided
7. Returns logger

**Returns**: Configured logger instance

---

## config.py

**Purpose**: Configuration management for Clipt backend.

### `Config` class

**Methods**:

- **`get(key, default=None)`**: Gets configuration value from environment
- **`validate(strict=False)`**: Validates required configuration at startup
- **`has_firecrawl()`**: Checks if Firecrawl API key is configured
- **`has_openai()`**: Checks if OpenAI API key is configured
- **`get_firecrawl_key()`**: Gets Firecrawl API key
- **`get_openai_key()`**: Gets OpenAI API key

**How it works**:

- Loads environment variables from `.env` file using `dotenv`
- Validates required vs optional API keys
- Provides helper methods to check and get API keys
- Logs warnings for missing optional keys

---

## Data Flow in clipping_logic.py

The main function `process_url_to_file()` orchestrates all these modules:

1. **Scraping**: `site_preprocessing.scrape_page()` - Gets HTML with ad-blocking
2. **Logo Extraction**: `logo_extraction.extract_logo()` - Finds website logo
3. **Header Extraction**: `header_extraction.extract_headers()` - Finds title and subtitle
4. **Title Image**: `image_positioning.find_image_below_title()` - Finds image below title
5. **AI Extraction** (optional): `find_first_and_last_sentences.find_first_and_last_sentences_from_url()` - Gets content boundaries
6. **Content Extraction**: `content_extraction.extract_main_content()` - Extracts main content
7. **Keyword Filtering** (optional): `keyword_filtering.filter_content_by_keywords()` - Filters by keywords
8. **Subtitle Validation**: `subtitle_validation.validate_subtitle_position()` - Validates subtitle position
9. **Image Processing**: Extracts images from content, downloads, resizes, converts to data URIs
10. **CSS Extraction**: `extract_css_styles()` - Extracts CSS from original HTML
11. **Output Generation**: `build_final_html()` - Builds final HTML document

Each step uses utility functions from `url_utils`, `image_utils`, `network_utils`, `dom_utils`, `constants`, `logger`, and `config` modules.
