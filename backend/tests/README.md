# Backend Unit Tests

This directory contains comprehensive unit tests for all functions in the backend modules.

## Test Structure

Each test file corresponds to a module in the backend:
- `test_logger.py` - Tests for `logger.py`
- `test_config.py` - Tests for `config.py`
- `test_url_utils.py` - Tests for `url_utils.py`
- `test_dom_utils.py` - Tests for `dom_utils.py`
- `test_network_utils.py` - Tests for `network_utils.py`
- `test_keyword_filtering.py` - Tests for `keyword_filtering.py`
- `test_content_extraction.py` - Tests for `content_extraction.py`
- `test_image_utils.py` - Tests for `image_utils.py`
- `test_image_positioning.py` - Tests for `image_positioning.py`
- `test_subtitle_validation.py` - Tests for `subtitle_validation.py`
- `test_site_preprocessing.py` - Tests for `site_preprocessing.py`
- `test_logo_extraction.py` - Tests for `logo_extraction.py`
- `test_header_extraction.py` - Tests for `header_extraction.py`
- `test_find_first_and_last_sentences.py` - Tests for `find_first_and_last_sentences.py`
- `test_output_generation.py` - Tests for `output_generation.py`
- `test_clipping_logic.py` - Tests for `clipping_logic.py`
- `test_analyze_codebase.py` - Tests for `analyze_codebase.py`

## Running Tests

### Run all tests:
```bash
cd backend
python -m pytest tests/
```

Or using the test runner:
```bash
cd backend
python tests/run_tests.py
```

### Run a specific test file:
```bash
cd backend
python -m pytest tests/test_logger.py
```

### Run a specific test class:
```bash
cd backend
python -m pytest tests/test_logger.py::TestLogger
```

### Run a specific test method:
```bash
cd backend
python -m pytest tests/test_logger.py::TestLogger::test_setup_logger
```

### Run with verbose output:
```bash
cd backend
python -m pytest tests/ -v
```

## Test Coverage

All functions in the backend have been tested with:
- Normal operation cases
- Edge cases (empty inputs, None values, etc.)
- Error handling
- Mocked external dependencies (APIs, file I/O, network calls)

## Dependencies

Tests use the following libraries:
- `unittest` - Python's built-in testing framework
- `unittest.mock` - For mocking external dependencies
- `pytest` (optional) - Alternative test runner with more features

## Notes

- Some tests require mocking external services (Firecrawl, OpenAI) since they require API keys
- Network-related tests mock HTTP requests to avoid actual network calls
- File I/O tests use temporary files that are cleaned up automatically
- Tests are designed to be independent and can run in any order

