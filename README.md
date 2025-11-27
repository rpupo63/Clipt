# Clipt - Web Content Extraction and Clipping Tool

> **Transform web articles into clean, formatted documents** - Extract articles from any website, remove ads and clutter, and save them in multiple formats (HTML, DOCX, PDF, Markdown).

Clipt is an intelligent web scraping and content extraction tool that converts messy web pages into clean, readable documents. Whether you're archiving articles, creating research documents, or building a content processing pipeline, Clipt handles the heavy lifting of extracting, cleaning, and formatting web content.

## 🎯 What Can Clipt Do?

- **Extract Articles**: Pull main content from any web page, automatically removing navigation, ads, and clutter
- **Multiple Formats**: Export to HTML, DOCX (Word), PDF, or Markdown
- **AI-Powered Precision**: Uses Firecrawl and OpenAI to identify exact article boundaries (optional)
- **Smart Image Handling**: Automatically finds, downloads, and embeds relevant images
- **Keyword Filtering**: Extract only sections containing specific keywords
- **REST API**: Integrate into your applications with a simple API

## 🌟 What Makes Clipt Different?

Unlike simple web scrapers, Clipt is designed specifically for **article extraction**:

- **🎯 Intelligent Content Detection**: Uses AI (optional) to identify exact article boundaries, avoiding author bios, related articles, and navigation
- **🛡️ Ad-Free by Default**: Built-in uBlock Origin integration ensures clean content without ads or trackers
- **📐 Precise Extraction**: Finds the smallest DOM container containing the article, not just the entire page
- **🔄 Graceful Degradation**: Works perfectly without AI services - falls back to smart heuristics
- **🔒 Security First**: Built-in SSRF protection, URL validation, and secure file handling
- **🎨 Format Preservation**: Maintains styling, images, and structure in output documents

## 🚀 Quick Start

### For Users: Extract Your First Article

```bash
# 1. Set up environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Extract an article (no API keys needed!)
python clipping_logic.py "https://example.com/article" pdf
```

That's it! The article will be saved as a clean PDF. See [Installation](#installation) for full setup including Chromium and uBlock Origin.

### For Developers: API Integration

```bash
# Start the API server
cd backend
python main.py

# Use the API (in another terminal)
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "filetype": "pdf", "return_file": true}' \
  --output article.pdf
```

See [REST API](#rest-api) for complete API documentation.

## ✨ Key Features

- **🛡️ Ad-Free Scraping**: Uses Selenium with uBlock Origin to scrape clean content without ads
- **🤖 Intelligent Content Extraction**: AI-powered extraction using Firecrawl and OpenAI to identify article boundaries (optional, falls back to heuristics)
- **📄 Multi-Format Output**: Generate documents in HTML, DOCX, PDF, or Markdown formats
- **🎨 Logo & Header Extraction**: Automatically extracts site logos, titles, and subtitles with formatting
- **🖼️ Image Processing**: Finds and embeds relevant images from articles, resizes automatically
- **🔍 Keyword Filtering**: Filter paragraphs by keywords while optionally preserving the first paragraph
- **🌐 REST API**: Flask-based API for easy integration into your applications
- **🔒 Security Hardened**: SSRF protection, XSS prevention, secure file handling

## 📚 Documentation

- **[User Guide](#usage)**: How to use Clipt via CLI or API
- **[Developer Documentation](backend/DOCUMENTATION.md)**: Complete API reference for all modules, including tools, technologies, and methodologies

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Command Line Interface](#command-line-interface)
  - [REST API](#rest-api)
- [Architecture & Methodologies](#architecture--methodologies)
- [For Developers](#for-developers)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** (check with `python3 --version`)
- **Chromium browser** (for web scraping - see Step 4)
- **ChromeDriver** (automatically managed by Selenium 4.x, or install manually)
- **uBlock Origin extension** (optional but recommended - see Step 5)

**Note**: Clipt works without API keys, but AI-powered content extraction requires optional API keys (see [Configuration](#configuration)).

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Clipt
```

### Step 2: Set Up Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Chromium Browser

Clipt uses Chromium (or Chrome) with Selenium for web scraping. Install Chromium:

**Ubuntu/Debian:**

```bash
sudo apt-get install chromium-browser chromium-chromedriver
```

**macOS:**

```bash
brew install chromium
```

**Arch Linux:**

```bash
sudo pacman -S chromium
```

**Note:** Selenium 4.x can automatically manage ChromeDriver, but having it installed manually can help with compatibility.

### Step 5: Download uBlock Origin Extension

Clipt uses uBlock Origin to block ads and trackers during web scraping. You need to download the extension manually:

1. **Download from GitHub Releases** (recommended):

   - Visit: https://github.com/gorhill/uBlock/releases
   - Download the latest `uBlock0.chromium.zip` file
   - Extract the zip file
   - You should have a folder named `uBlock0.chromium`

2. **Place the extension in the correct location:**

   ```bash
   cd backend
   # Extract the downloaded zip file here
   # The final structure should be: backend/uBlock0.chromium/uBlock0.chromium/
   ```

   The extension should be located at: `backend/uBlock0.chromium/uBlock0.chromium/`

   **Important:** The extension directory structure must be:

   ```
   backend/
   └── uBlock0.chromium/
       └── uBlock0.chromium/
           ├── manifest.json
           ├── js/
           ├── css/
           └── ... (other extension files)
   ```

3. **Verify the installation:**
   - Check that `backend/uBlock0.chromium/uBlock0.chromium/manifest.json` exists
   - The application will automatically detect and load the extension when scraping

**Alternative:** If you don't download uBlock Origin, the application will still work but without ad-blocking capabilities. You'll see a warning message, but scraping will continue.

### Step 6: Install System Dependencies (if needed)

For PDF generation, you may need additional system libraries:

**Ubuntu/Debian:**

```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**macOS:**

```bash
brew install cairo pango gdk-pixbuf libffi
```

**Arch Linux:**

```bash
sudo pacman -S cairo pango gdk-pixbuf2 libffi
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add the following variables (optional API keys for enhanced features):

```env
# Optional: For AI-powered content extraction
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Note:** The application will work without these API keys, but AI-powered content extraction will be disabled. You can get API keys from:

- [Firecrawl](https://www.firecrawl.dev/) - For advanced web scraping
- [OpenAI](https://platform.openai.com/) - For intelligent content boundary detection

### Validate Configuration

The application validates configuration at startup. You can test it:

```bash
python -c "from config import Config; Config.validate()"
```

## Usage

Clipt can be used in three ways:

1. **Command Line Interface** - Simple scripts and one-off extractions
2. **Python Module** - Import into your Python projects
3. **REST API** - Integrate into web applications or services

### Command Line Interface

#### Basic Usage

Process a URL and generate an HTML file:

```bash
python clipping_logic.py "https://example.com/article"
```

#### Advanced Options

```bash
# Specify output format
python clipping_logic.py "https://example.com/article" pdf

# With keyword filtering
python clipping_logic.py "https://example.com/article" html technology AI "machine learning"

# Always include first paragraph
python clipping_logic.py "https://example.com/article" html technology AI --include-first
```

**Usage:**

```bash
python clipping_logic.py <url> [filetype] [keywords...] [--include-first]
```

**Parameters:**

- `url`: URL to process (required, first positional argument)
- `filetype`: Output format - `html`, `docx`, `pdf`, `md`, or `markdown` (optional, default: `html`)
- `keywords`: Space-separated keywords to filter paragraphs (optional)
- `--include-first`: Always include first paragraph even if no keyword match (optional flag)

#### Using the Python Module Directly

```python
from clipping_logic import process_url_to_file

# Basic usage
output_path = process_url_to_file(
    url="https://example.com/article",
    filetype="html"
)

# With keyword filtering
output_path = process_url_to_file(
    url="https://example.com/article",
    filetype="pdf",
    keywords=["technology", "AI"],
    include_first_paragraph=True
)
```

### REST API

#### Start the Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:5000` (default port: 5000)

#### API Endpoints

##### Process URL

**POST** `/api/process`

Process a URL and generate output in the specified format.

**Request Body:**

```json
{
  "url": "https://example.com/article",
  "filetype": "html",
  "keywords": ["keyword1", "keyword2"],
  "include_first_paragraph": false,
  "output_file": "output.html",
  "return_file": false
}
```

**Parameters:**

- `url` (required): URL to process
- `filetype` (optional): Output format - `html`, `docx`, `pdf`, `md`, `markdown` (default: `html`)
- `keywords` (optional): Array of keywords to filter paragraphs
- `include_first_paragraph` (optional): Always include first paragraph (default: `false`)
- `output_file` (optional): Custom output filename
- `return_file` (optional): If `true`, returns file directly; if `false`, returns JSON with file path (default: `false`)

**Response (JSON mode):**

```json
{
  "success": true,
  "output_path": "/path/to/output/file.html",
  "message": "Processing completed successfully"
}
```

**Response (File mode):**
Returns the file directly as a download.

##### Health Check

**GET** `/api/health`

Check if the API is running.

**Response:**

```json
{
  "status": "healthy",
  "service": "Clipt API",
  "version": "1.0.0"
}
```

##### API Documentation

**GET** `/`

Returns API documentation in JSON format.

#### Example API Calls

**Using curl:**

```bash
# Process URL and get JSON response
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "filetype": "pdf",
    "keywords": ["technology"],
    "return_file": false
  }'

# Process URL and download file directly
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "filetype": "pdf",
    "return_file": true
  }' \
  --output article.pdf
```

**Using Python requests:**

```python
import requests

response = requests.post('http://localhost:5000/api/process', json={
    'url': 'https://example.com/article',
    'filetype': 'pdf',
    'keywords': ['technology', 'AI'],
    'include_first_paragraph': True,
    'return_file': True
})

with open('article.pdf', 'wb') as f:
    f.write(response.content)
```

## Architecture & Methodologies

### Processing Pipeline

The clipping extraction process follows these steps:

1. **Web Scraping with Ad-Blocking** (`site_preprocessing.py`)

   - Uses Selenium WebDriver with Chromium browser
   - Loads uBlock Origin extension from `backend/uBlock0.chromium/uBlock0.chromium/` to block ads and trackers
   - Falls back gracefully if extension is not found (continues without ad-blocking)
   - Waits for page to fully render
   - Returns clean HTML content

2. **Logo Extraction** (`logo_extraction.py`)

   - Searches for logo using multiple heuristics:
     - Common logo selectors (`<img>` with "logo" in class/id/alt)
     - Open Graph images
     - Favicon fallback
   - Validates logo size (20-500px) and filters out decorative images
   - Returns absolute URL and element information

3. **Header Extraction** (`header_extraction.py`)

   - Extracts title using semantic HTML (`<h1>`, `<title>`, Open Graph)
   - Extracts subtitle from elements near the title
   - Validates subtitle position (must be within 5 DOM elements of title)
   - Preserves formatting information (classes, styles, HTML structure)

4. **Content Extraction** (`content_extraction.py`)

   - **AI-Powered Method** (if API keys available):
     - Uses Firecrawl to scrape and convert to markdown
     - Uses OpenAI to identify first and last contentful sentences
     - Finds the smallest DOM container containing both sentences
     - Extracts all content within that container
   - **Heuristic Fallback**:
     - Searches for main content containers (`<main>`, `<article>`, etc.)
     - Filters out navigation, headers, footers, and ads
     - Extracts paragraphs and preserves structure

5. **Image Processing** (`image_utils.py`, `image_positioning.py`)

   - Finds images near extracted paragraphs
   - Searches within 5 DOM elements of each paragraph
   - Downloads and processes images:
     - Resizes to target width (800px) while maintaining aspect ratio
     - Converts to appropriate format
     - Embeds as base64 data URIs or saves as files

6. **Output Generation** (`output_generation.py`)
   - Converts processed HTML to requested format:
     - **HTML**: Clean, formatted HTML with embedded images
     - **DOCX**: Microsoft Word document with proper formatting
     - **PDF**: PDF document using WeasyPrint
     - **Markdown**: Markdown format using markdownify

### Key Methodologies

#### 1. Ad-Free Scraping

- **Technology**: Selenium WebDriver + uBlock Origin
- **Why**: Many websites load content dynamically and contain ads/trackers
- **Method**: Loads extension before page load, waits for full render, extracts clean HTML

#### 2. AI-Powered Content Boundary Detection

- **Technology**: Firecrawl (scraping) + OpenAI GPT (analysis)
- **Why**: Heuristic extraction can include navigation, ads, or miss content boundaries
- **Method**:
  1. Firecrawl converts page to clean markdown
  2. OpenAI analyzes markdown to identify first/last contentful sentences
  3. System finds DOM elements containing these sentences
  4. Extracts smallest container containing both boundaries

#### 3. Semantic HTML Parsing

- **Technology**: BeautifulSoup4 with semantic selectors
- **Why**: Modern websites use semantic HTML (`<main>`, `<article>`, ARIA roles)
- **Method**: Prioritizes semantic containers over generic `<div>` elements

#### 4. Image-Text Association

- **Technology**: DOM traversal and positional analysis
- **Why**: Images are often near related paragraphs but not directly nested
- **Method**: Searches within 5 DOM elements of each paragraph for relevant images

#### 5. Keyword-Based Filtering

- **Technology**: Text matching with optional first-paragraph preservation
- **Why**: Users may only want specific sections of long articles
- **Method**: Filters paragraphs containing keywords, optionally preserves first paragraph for context

### Security Features

- **SSRF Protection**: Validates URLs before requests, blocks private IPs and localhost
- **XSS Prevention**: HTML escaping for user-generated content
- **Secure File Handling**: Uses temporary directories with unique filenames
- **Resource Management**: Context managers for WebDriver, connection pooling, retry logic
- **Input Validation**: Validates filetypes, keywords, and other inputs

## Troubleshooting

### Common Issues

#### 1. ChromeDriver Not Found

**Error:** `selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH`

**Solution:** Selenium 4.x should manage ChromeDriver automatically. If issues persist:

```bash
# Install ChromeDriver manually
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# macOS
brew install chromedriver

# Or download from https://chromedriver.chromium.org/
```

#### 1a. Chromium Browser Not Found

**Error:** `selenium.common.exceptions.WebDriverException: Message: unknown error: cannot find Chrome binary`

**Solution:** Install Chromium browser (see Step 4 in Installation section):

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install chromium

# Arch Linux
sudo pacman -S chromium
```

If you have Chrome installed instead of Chromium, you can specify the Chrome binary path in your code or set the `CHROME_BINARY` environment variable.

#### 1b. uBlock Origin Extension Not Found

**Error:** Warning message: `⚠ uBlock Origin not found - continuing without ad-blocker`

**Solution:** Download and install uBlock Origin extension (see Step 5 in Installation section):

1. Download `uBlock0.chromium.zip` from https://github.com/gorhill/uBlock/releases
2. Extract it to `backend/uBlock0.chromium/uBlock0.chromium/`
3. Verify `backend/uBlock0.chromium/uBlock0.chromium/manifest.json` exists

**Note:** The application will work without uBlock Origin, but ads and trackers won't be blocked during scraping.

#### 2. PIL/Pillow Import Errors

**Error:** `ImportError: cannot import name 'Image' from 'PIL'`

**Solution:**

```bash
pip install --upgrade Pillow
```

#### 3. WeasyPrint PDF Generation Fails

**Error:** PDF generation fails with system library errors

**Solution:** Install required system libraries (see Installation section)

#### 4. API Keys Not Working

**Error:** `FIRECRAWL_API_KEY not found` or `OPENAI_API_KEY not found`

**Solution:**

- Ensure `.env` file exists in `backend/` directory
- Check that keys are correctly formatted (no quotes, no extra spaces)
- Verify API keys are valid and have sufficient credits

#### 5. Memory Issues with Large Pages

**Error:** Out of memory errors when processing large pages

**Solution:**

- The system has built-in size limits (10MB for images)
- For very large pages, consider using keyword filtering to reduce content
- Monitor system resources and adjust `MAX_SIZE` in `constants.py` if needed

#### 6. Timeout Errors

**Error:** `TimeoutException` or connection timeouts

**Solution:**

- Increase timeout values in `constants.py`:
  - `PageConfig.PAGE_TIMEOUT`
  - `NetworkConfig.DEFAULT_TIMEOUT`
- Check network connectivity
- Some sites may block automated access

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Getting Help

- Check logs in the console output
- Review [Developer Documentation](backend/DOCUMENTATION.md) for detailed module information, tools, and methodologies
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## For Developers

### Understanding the Codebase

If you're contributing to Clipt or building on top of it, here's what you need to know:

#### Core Architecture

Clipt follows a modular pipeline architecture:

1. **Scraping Layer** (`site_preprocessing.py`): Selenium-based web scraping with ad-blocking
2. **Extraction Layer**: Multiple specialized extractors (logo, headers, content, images)
3. **AI Layer** (`find_first_and_last_sentences.py`): Optional AI-powered boundary detection
4. **Processing Layer**: Image processing, keyword filtering, validation
5. **Output Layer** (`output_generation.py`): Format conversion (HTML/DOCX/PDF/Markdown)

#### Key Design Principles

- **Graceful Degradation**: Core functionality works without optional dependencies (AI services, uBlock)
- **Security First**: SSRF protection, URL validation, secure file handling
- **Modular Design**: Each extraction task is a separate, testable module
- **Error Handling**: Comprehensive error handling with logging throughout

#### Documentation for Developers

- **[DOCUMENTATION.md](backend/DOCUMENTATION.md)**: Complete API reference for all modules and functions, including:
  - Web scraping architecture (Selenium + uBlock Origin)
  - AI integration (Firecrawl + OpenAI)
  - Technology stack and methodologies
  - Performance characteristics
  - Detailed function documentation

#### Adding New Features

1. **New Extractor**: Create a new module following the pattern in `logo_extraction.py` or `header_extraction.py`
2. **New Output Format**: Add conversion function to `output_generation.py`
3. **New Processing Step**: Add to the pipeline in `clipping_logic.py`

#### Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/
```

### Project Structure

```
Clipt/
├── backend/
│   ├── main.py                 # Flask API server
│   ├── clipping_logic.py       # Main processing pipeline
│   ├── site_preprocessing.py   # Selenium scraping with ad-blocking
│   ├── logo_extraction.py      # Logo detection and extraction
│   ├── header_extraction.py    # Title/subtitle extraction
│   ├── content_extraction.py   # Main content extraction
│   ├── image_positioning.py   # Image positioning logic
│   ├── find_first_and_last_sentences.py # AI-powered boundary detection
│   ├── image_utils.py          # Image processing utilities
│   ├── output_generation.py    # Format conversion (HTML/DOCX/PDF/MD)
│   ├── config.py               # Configuration management
│   ├── constants.py            # Centralized constants
│   ├── logger.py               # Logging framework
│   ├── url_utils.py            # URL validation and normalization
│   ├── network_utils.py        # HTTP session with retry logic
│   ├── requirements.txt        # Python dependencies
│   ├── DOCUMENTATION.md        # Complete API reference and technical deep-dive
│   └── uBlock0.chromium/       # uBlock Origin extension (download separately)
├── frontend/                   # React frontend (optional)
└── README.md                   # This file
```

## Use Cases & Examples

Clipt is perfect for:

- **📚 Content Archiving**: Save articles in clean, readable formats
- **📝 Research**: Extract and format content for research documents
- **🤖 Automation**: Integrate into content processing pipelines
- **📰 News Aggregation**: Extract articles from multiple sources
- **📖 E-book Creation**: Convert web articles into PDF or DOCX documents
- **🔍 Content Analysis**: Extract and filter content by keywords

### Example: Extract a Tech Article

```bash
# Extract a tech article and save as PDF
python clipping_logic.py "https://techcrunch.com/article" pdf

# Extract only sections about "AI" and "machine learning"
python clipping_logic.py "https://techcrunch.com/article" html AI "machine learning" --include-first
```

### Example: API Integration

```python
import requests

# Extract article via API
response = requests.post('http://localhost:5000/api/process', json={
    'url': 'https://example.com/article',
    'filetype': 'pdf',
    'keywords': ['technology', 'innovation'],
    'include_first_paragraph': True,
    'return_file': True
})

# Save the PDF
with open('article.pdf', 'wb') as f:
    f.write(response.content)
```

### Example: Python Module

```python
from clipping_logic import process_url_to_file

# Extract article with keyword filtering
result = process_url_to_file(
    url="https://example.com/article",
    filetype="pdf",
    keywords=["technology", "AI"],
    include_first_paragraph=True
)

print(f"Article saved to: {result['output_path']}")
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
