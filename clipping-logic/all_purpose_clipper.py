from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotVisibleException, NoSuchElementException, ElementNotSelectableException
from bs4 import BeautifulSoup
from weasyprint import HTML
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
import requests
from PIL import Image
from io import BytesIO
import base64
import xml.etree.ElementTree as ET


# Get desirable page elements
def find_and_edit_logo(soup, url):
    logo_image = None
    for element in soup.find_all(class_=lambda x: x and 'logo' in x.lower()):
        logo_image = element.find('img')
        if logo_image:
            break
    
    if logo_image and 'src' in logo_image.attrs:
        src = logo_image['src']
        if not src.startswith(('http://', 'https://')):
            src = urljoin(url, src)

        new_tag = soup.new_tag("img")  # Create a new tag to replace the old one

        if src.endswith('.svg'):
            try:
                response = requests.get(src)
                response.raise_for_status()
                modified_svg = add_background_to_svg(response.text)
                svg_base64 = base64.b64encode(modified_svg.encode('utf-8')).decode('utf-8')
                new_tag['src'] = f"data:image/svg+xml;base64,{svg_base64}"
            except Exception as e:
                print(f"Error processing SVG {src}: {e}")
                new_tag['src'] = src
        else:
            try:
                response = requests.get(src)
                img = Image.open(BytesIO(response.content))
                
                if img.mode in ['RGBA', 'P'] and 'transparency' in img.info:
                    is_mostly_white = all(pixel[:3] == (255, 255, 255) for pixel in img.getdata())
                    background_color = 'black' if is_mostly_white else 'white'
                else:
                    background_color = 'white'
                    
                new_tag['src'] = src
                new_tag['alt'] = f"logo on {background_color} background"
            except Exception as e:
                print(f"Error processing raster image {src}: {e}")
                new_tag['src'] = src
    else:
        new_tag = None

    return new_tag

def add_background_to_svg(svg_content):
    tree = ET.ElementTree(ET.fromstring(svg_content))
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'} if 'svg' not in root.tag else {'svg': ''}
    rect = ET.Element('{http://www.w3.org/2000/svg}rect', attrib={'width': '100%', 'height': '100%', 'fill': 'black'})
    root.insert(0, rect)
    return ET.tostring(root, encoding='unicode', method='xml')

def get_header(soup):
    h1_tag = soup.find('h1')
    return h1_tag if h1_tag else None

def find_paragraph_with_two_sentences_and_image(soup):
    paragraphs = soup.find_all('p')

    for paragraph in paragraphs:
        sentences = [sentence.strip() for sentence in paragraph.text.split('.') if sentence.strip()]
        if len(sentences) >= 2:
            image = None
            previous_elements = paragraph.find_all_previous()
            for elem in previous_elements:
                if elem.name == 'img':
                    image = elem  # Return the element itself
                    break

            return paragraph, image

    return None, None

# Apply filters
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

# Get webpage using selenium
def get_webpage_info(url):
    options = Options()
    prefs = {
        "download.default_directory": "./",
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--disable-popup-blocking')  # Explicitly allow popups to manage them
    options.add_argument('--headless')  # Run in headless mode (no UI)
    options.add_argument('--no-sandbox')  # For certain environments like CI
    options.add_argument('--disable-dev-shm-usage')  # Helps with resource issues
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    #service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com/")
    chrome_driver = webdriver.Chrome(options=options)

    chrome_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)  # Increase timeout if necessary

        # Attempt to close any popups
        try:
            popup_selector = "div[class^='popupClass']"
            close_button_selector = "button[class^='closeButtonClass']"
            popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, popup_selector)))
            close_button = driver.find_element(By.CSS_SELECTOR, close_button_selector)
            close_button.click()
        except TimeoutException:
            print("No popup appeared within the timeout period.")
        except ElementClickInterceptedException:
            print("Popup close button was not clickable.")

        # Wait for specific elements to load
        try:
            elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^='someclass']")))
        except TimeoutException:
            print("Specified elements did not appear within the timeout period.")
            elements = []  # Assign an empty list if elements are not found

        html_content = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    return soup


# Save webpage using weasyprint
def save_document_to_pdf(clean_html, output_name):
    HTML(string=clean_html).write_pdf(f'{output_name}.pdf')
    print("PDF has been created successfully!")

def primary_func(url, keyword, output_type, output_name):
    soup = get_webpage_info(url)

    logo = find_and_edit_logo(soup, url)
    article_title = get_header(soup)
    first_paragraph, first_image = find_paragraph_with_two_sentences_and_image(soup)

    soup = filter_paragraphs(soup=soup, keyword=keyword, first_paragraph=first_paragraph)
    soup = filter_images(soup)

    # Clean up HTML
    for element in soup.find_all(['nav', 'header', 'footer', 'title']):
        element.decompose()
    for element in soup.find_all(class_=["nav", "menu", "header", "footer"]):
        element.decompose()
    #for script in soup(["script", "style"]):
    #    script.decompose()

    clean_html = str('')

    if logo:
        clean_html += logo.text if logo else ''
    if article_title:
        clean_html += article_title.text if article_title else ''
    if first_image:
        clean_html += first_image.text if first_image else ''
    if first_paragraph:
        clean_html += first_paragraph.text if first_paragraph else ''

    clean_html += str(soup)

    save_document_to_pdf(clean_html=clean_html, output_name=output_name)

    return soup


# Implementation (change this for stremamline)
if __name__ == "__main__":
    url = input("Enter the URL to clip: ")
    url = url if url else "https://thedieline.com/blog/2024/3/13/knesko-skin-green-jade"
    keyword = input("Enter the keyword: ")
    keyword = keyword if keyword else ''
    output_type = input("Enter the type of file: ")
    output_type = output_type if output_type else 'pdf'
    output_filename = input("Enter the output file name (default 'output.pdf'): ")
    output_filename = output_filename if output_filename else 'output'
    primary_func(url=url, keyword=keyword, output_name=output_filename, output_type=output_type)
