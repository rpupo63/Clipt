import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as md
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO
import base64
import streamlit as st
import io
from weasyprint import HTML
import markdown2

# Header Getting Stuff
def get_header(soup):
    h1_tags = soup.find_all('h1')

    h1_texts = [tag.text.strip() for tag in h1_tags]
    if h1_texts:
        article_title = h1_texts[0]
        return f"# {article_title}\n\n"
    else:
        return None

# Filter Stuff
def filter_paragraphs(soup, keyword, first_paragraph):
    first_paragraph_text = first_paragraph.text if first_paragraph else None
    paragraphs = soup.find_all('p')

    for paragraph in paragraphs:
        is_different = paragraph.text != first_paragraph_text
        if keyword.lower() not in paragraph.text.lower() and is_different:
            paragraph.decompose()

    return soup

def filter_images(soup):    
    # Get all <p> elements
    paragraphs = soup.find_all('p')
    
    # To handle images before the first <p> and after the last <p>
    first_p = soup.new_tag('p')
    last_p = soup.new_tag('p')
    if paragraphs:
        soup.body.insert(0, first_p)
        soup.body.append(last_p)
    else:
        # If no <p> tags are present, simply return the original content
        return str(soup)
    
    # Refresh the list of paragraphs to include the new dummy tags
    paragraphs = soup.find_all('p')
    
    # Iterate over each pair of consecutive <p> elements
    for i in range(len(paragraphs) - 1):
        current_p = paragraphs[i]
        next_p = paragraphs[i + 1]
        
        # Find all <img> tags between the current <p> and the next <p>
        images = []
        element = current_p.next_sibling
        while element and element != next_p:
            if isinstance(element, Tag) and element.name == 'img':
                images.append(element)
            element = element.next_sibling
        
        # Remove all but the last image in the found list
        for img in images[:-1]:
            img.decompose()

    # Remove the dummy <p> tags
    first_p.decompose()
    last_p.decompose()

    return soup


# First paragraph stuff
def find_paragraph_with_two_sentences_and_image(soup):
    paragraphs = soup.find_all('p')

    for paragraph in paragraphs:
        sentences = [sentence.strip() for sentence in paragraph.text.split('.') if sentence.strip()]
        if len(sentences) >= 2:
            soupy_text = paragraph
            markdown_text = md(str(paragraph))
            image = None
            previous_elements = paragraph.find_all_previous()
            for elem in previous_elements:
                if elem.name == 'img':
                    image = elem['src']
                    break

            return markdown_text, image, soupy_text

    return None, None, None


# Logo Getting Stuff
def find_and_edit_logo(soup):
    logo_image = None
    for element in soup.find_all(class_=lambda x: x and 'logo' in x.lower()):
        logo_image = element.find('img')
        if logo_image:
            break
    if logo_image and 'src' in logo_image.attrs:
        src = logo_image['src']
        if not src.startswith(('http://', 'https://')):
            src = urljoin(url, src)

        if src.endswith('.svg'):
            try:
                response = requests.get(src)
                response.raise_for_status()
                modified_svg = add_background_to_svg(response.text)
                import base64
                svg_base64 = base64.b64encode(modified_svg.encode('utf-8')).decode('utf-8')
                logo_markdown = f"![logo](data:image/svg+xml;base64,{svg_base64})\n"
            except Exception as e:
                print(f"Error processing SVG {src}: {e}")
                logo_markdown = f"![logo]({src})\n"
        else:
            try:
                response = requests.get(src)
                img = Image.open(BytesIO(response.content))
                
                if img.mode in ['RGBA', 'P'] and 'transparency' in img.info:
                    is_mostly_white = all(pixel[:3] == (255, 255, 255) for pixel in img.getdata())
                    background_color = 'black' if is_mostly_white else 'white'
                else:
                    background_color = 'white'
                    
                logo_markdown = f"![logo on {background_color} background]({src})\n"
            except Exception as e:
                print(f"Error processing raster image {src}: {e}")
                logo_markdown = f"![logo]({src})\n"
    else:
        logo_markdown = "Logo not found\n"

    return logo_markdown

def add_background_to_svg(svg_content):
    tree = ET.ElementTree(ET.fromstring(svg_content))
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'} if 'svg' not in root.tag else {'svg': ''}
    rect = ET.Element('{http://www.w3.org/2000/svg}rect', attrib={'width': '100%', 'height': '100%', 'fill': 'black'})
    root.insert(0, rect)
    return ET.tostring(root, encoding='unicode', method='xml')

# Main Function
def url_to_markdown(url, keyword='', output_file='output.md'):
    try:
        # Fetch the content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Will raise an exception for bad responses
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    target_height = '100px'

    logo_markdown = find_and_edit_logo(soup)
    article_title = get_header(soup)
    first_paragraph, first_image, soupy_paragraph = find_paragraph_with_two_sentences_and_image(soup)
    
    # Create an image tag in Markdown with an HTML 'div' for centering
    first_image_md = f'<img src="{first_image}" style="display: block; margin: auto; height: {target_height}; width: auto;">\n' if first_image else ""
    
    soup = filter_paragraphs(soup, keyword, soupy_paragraph)
    soup = filter_images(soup)

    # Clean up HTML
    for element in soup.find_all(['nav', 'header', 'footer', 'title']):
        element.decompose()
    for element in soup.find_all(class_=["nav", "menu", "header", "footer"]):
        element.decompose()

    remaining_text = md(str(soup))

    # Remove all text up to and including first_paragraph
    idx = remaining_text.find(first_paragraph)
    print("here bubsy")
    print(idx)
    if idx != -1:
        remaining_text = remaining_text[idx + len(first_paragraph):]

    # Convert remaining HTML to Markdown, assuming other functions return processed soup
    markdown_text = logo_markdown + article_title + first_image_md + first_paragraph + remaining_text

    return markdown_text


def save_output(text, file_name, output_format='markdown'):
    print(output_format)
    if not text:
        print("No content to save.")
        return

    if output_format == 'markdown':
        with open(file_name + '.md', 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"Markdown saved to {file_name}.md")
    elif output_format == 'pdf':
        # Use the markdown2 library to convert markdown to HTML
        html_text = markdown2.markdown(text)
        # HTML content with CSS for centering images and controlling max size
        html_content = f'''
        <html>
        <head>
            <style>
                img {{
                    max-height: 300px;
                    max-width: 100%;
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                }}
                div.align {{
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
        </html>'''
        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(file_name + '.pdf')
        print(f"PDF saved to {file_name}.pdf")

# Implementation (change this for streamline)
if __name__ == "__main__":
    url = input("Enter the URL to convert to Markdown: ")
    url = url if url else "https://thedieline.com/blog/2024/3/13/knesko-skin-green-jade"
    keyword = input("Enter the keyword: ")
    keyword = keyword if keyword else ''
    output_type = input("Enter the type of file (markdown or pdf): ")
    output_type = output_type if output_type else 'markdown'
    output_filename = input("Enter the output Markdown file name (default 'output.md'): ")
    output_filename = output_filename if output_filename else 'output' #changed
    markdown_text = url_to_markdown(url=url, keyword=keyword, output_file=output_filename)
    if markdown_text is not None:
        save_output(text=markdown_text, file_name=output_filename, output_format=output_type)
