#!/usr/bin/env python3
"""
Flask API for the Clipt web clipping service.
Exposes the URL processing logic as a REST API endpoint.
"""

from flask import Flask, request, jsonify, send_file
import os
import sys
import traceback
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse
from clipping_logic import process_url_to_html, process_url_to_file, build_final_html
import output_generation

# Import utilities
from config import Config
from constants import FileConfig
from logger import get_logger

# Try to import CORS, but continue if not available
try:
    from flask_cors import CORS
    cors_available = True
except ImportError:
    cors_available = False

# Set up logging
logger = get_logger(__name__)

# SECURITY: Validate configuration at startup
try:
    # Validate configuration (optional keys)
    # Set strict=True if you want to require all API keys at startup
    Config.validate(strict=False)
    logger.info("Configuration validated successfully")
except EnvironmentError as e:
    logger.error(f"Configuration validation failed: {e}")
    logger.error("Application may have limited functionality")
    # Don't exit - allow app to run with degraded functionality
    # If you want strict validation, uncomment the next line:
    # sys.exit(1)

app = Flask(__name__)

# Enable CORS if available (useful for frontend integration)
if cors_available:
    CORS(app)
    logger.info("CORS enabled")
else:
    logger.warning("CORS not available - install flask-cors for frontend integration")

@app.route('/api/process', methods=['POST'])
def process():
    """
    Process a URL and generate output in the specified format.

    Request JSON:
    {
        "url": "https://example.com/article",
        "filetype": "html",  // optional, defaults to "html". Options: html, docx, pdf, md, markdown
        "keywords": ["keyword1", "keyword2"],  // optional, filter paragraphs by keywords
        "include_first_paragraph": false,  // optional, always include first paragraph even if no keyword match
        "output_file": "output.html",  // optional, custom output filename
        "return_file": false,  // optional, if true returns file directly instead of JSON
        "image_width": 33.333,  // optional, width as percentage of container (default: 33.333 for 1/3 width)
        "image_position": "center"  // optional, image position: "center", "left", or "right" (default: "center")
    }

    Response JSON (if return_file=false):
    {
        "success": true,
        "output_path": "path/to/output/file.html",
        "message": "Processing completed successfully"
    }

    Or returns the file directly if return_file=true
    """
    try:
        # Get JSON data from request
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON'
            }), 400

        # Validate required parameters
        url = data.get('url')
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400

        # Get optional parameters with defaults
        filetype = data.get('filetype', 'html')
        keywords = data.get('keywords', None)
        include_first_paragraph = data.get('include_first_paragraph', False)
        output_file = data.get('output_file', None)
        return_file = data.get('return_file', False)
        image_width = data.get('image_width', 33.333)
        image_position = data.get('image_position', 'center')
        
        # Validate image_width
        if not isinstance(image_width, (int, float)) or image_width <= 0 or image_width > 100:
            return jsonify({
                'success': False,
                'error': 'image_width must be a number between 0 and 100'
            }), 400
        
        # Validate image_position
        valid_positions = ['center', 'left', 'right']
        if image_position not in valid_positions:
            return jsonify({
                'success': False,
                'error': f'image_position must be one of: {", ".join(valid_positions)}'
            }), 400

        # Validate filetype
        valid_filetypes = ['html', 'docx', 'pdf', 'md', 'markdown']
        if filetype.lower() not in valid_filetypes:
            return jsonify({
                'success': False,
                'error': f'Invalid filetype. Must be one of: {", ".join(valid_filetypes)}'
            }), 400

        # Validate keywords is a list if provided
        if keywords is not None and not isinstance(keywords, list):
            return jsonify({
                'success': False,
                'error': 'Keywords must be a list of strings'
            }), 400

        # Process the URL
        if filetype.lower() == 'html':
            # For HTML, use the new function that returns formatted HTML directly
            final_html = process_url_to_html(
                url=url,
                keywords=keywords,
                include_first_paragraph=include_first_paragraph,
                image_width=image_width,
                image_position=image_position
            )
            
            # Save to file if output_file is specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                output_path = output_file
            else:
                # Save to temp file
                temp_dir = Path(tempfile.gettempdir()) / FileConfig.TEMP_DIR_NAME
                temp_dir.mkdir(exist_ok=True, parents=True)
                output_path = temp_dir / f"output_{uuid.uuid4().hex[:8]}.html"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                output_path = str(output_path)
            
            # Return file directly if requested
            if return_file:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=os.path.basename(output_path)
                )
            
            # Otherwise return JSON with file path
            return jsonify({
                'success': True,
                'output_path': output_path,
                'message': 'Processing completed successfully'
            }), 200
        else:
            # For other formats, get structured content, build HTML, then convert
            content_dict = process_url_to_file(
                url=url,
                keywords=keywords,
                include_first_paragraph=include_first_paragraph,
                image_width=image_width,
                image_position=image_position
            )
            
            # Build HTML from structured content
            final_html = build_final_html(content_dict, image_width=image_width, image_position=image_position)
            
            # Convert to requested format
            converted_content = output_generation.convert_html(final_html, filetype)
            
            # Determine output filename
            if output_file is None:
                parsed_url = urlparse(url)
                base_name = Path(parsed_url.path).stem or "output"
                if not base_name or base_name == "/":
                    base_name = "output"
                
                # Get appropriate extension
                ext_map = {
                    'docx': '.docx',
                    'doc': '.docx',
                    'pdf': '.pdf',
                    'md': '.md',
                    'markdown': '.md'
                }
                ext = ext_map.get(filetype.lower(), '.txt')
                output_file = f"{base_name}{ext}"
            
            # Save the content to file
            if filetype.lower() in ['docx', 'doc', 'pdf']:
                # Binary format
                with open(output_file, 'wb') as f:
                    f.write(converted_content)
            else:
                # Text format (markdown)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(converted_content)
            
            output_path = output_file
            
            # Return file directly if requested
            if return_file:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=os.path.basename(output_path)
                )
            
            # Otherwise return JSON with file path
            return jsonify({
                'success': True,
                'output_path': output_path,
                'message': 'Processing completed successfully'
            }), 200

    except Exception as e:
        # SECURITY: Log full error server-side, send generic message to client
        error_trace = traceback.format_exc()
        logger.error(f"Error processing request: {error_trace}")

        # Don't expose internal details to client in production
        # Only send generic error message
        return jsonify({
            'success': False,
            'error': 'An error occurred processing your request. Please check your input and try again.',
            'error_type': type(e).__name__  # Only expose error type, not details
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Clipt API',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation"""
    return jsonify({
        'service': 'Clipt API',
        'version': '1.0.0',
        'endpoints': {
            '/api/process': {
                'method': 'POST',
                'description': 'Process a URL and extract content',
                'parameters': {
                    'url': 'string (required) - URL to process',
                    'filetype': 'string (optional) - Output format: html, docx, pdf, md, markdown. Default: html',
                    'keywords': 'array (optional) - List of keywords to filter paragraphs',
                    'include_first_paragraph': 'boolean (optional) - Always include first paragraph. Default: false',
                    'output_file': 'string (optional) - Custom output filename',
                    'return_file': 'boolean (optional) - Return file directly. Default: false',
                    'image_width': 'number (optional) - Width as percentage of container (0-100). Default: 33.333',
                    'image_position': 'string (optional) - Image position: "center", "left", or "right". Default: "center"'
                }
            },
            '/api/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            }
        }
    }), 200


if __name__ == '__main__':
    # Run the Flask app
    # In production, use a proper WSGI server like gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
