from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotVisibleException, NoSuchElementException, ElementNotSelectableException
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
import requests
from PIL import Image
from io import BytesIO, StringIO
import base64
import re
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pdfkit
import subprocess
import streamlit as st
import tempfile

def log_time(message):
    print(f"{message}: {time.time()}")

#region Find Core Div Box
def find_first_paragraphs(soup, title_tag, n):
    log_time("Start find_first_paragraphs")
    header_section = title_tag.parent
    last_element_of_header = header_section.find_all(['p', 'div', 'span'])[-1]
    paragraphs = last_element_of_header.find_all_next('p')
    found_paragraphs = []

    for paragraph in paragraphs:
        sentences = [sentence.strip() for sentence in re.split(r'(?<=[.!?]) +', paragraph.text) if sentence.strip()]

        if len(sentences) >= 2:
            image = None
            previous_elements = paragraph.find_all_previous()
            for elem in previous_elements:
                if elem.name == 'img':
                    image = elem
                    break

            if image:
                found_paragraphs.append((paragraph, image))
                
                if len(found_paragraphs) == n:
                    print(f"{n} paragraphs with images found, stopping search")
                    break

    if len(found_paragraphs) > 0:
        print("At least one paragraph with two sentences and an image found")
    else:
        print("No paragraph meeting criteria found")
    
    paragraphs = [found_paragraphs[i] if len(found_paragraphs) > i else None for i in range(n)]

    log_time("End find_first_paragraphs")
    print(paragraphs)
    return paragraphs


def find_common_container(soup, title, n):
    log_time("Start find_common_container")
    paragraphs = find_first_paragraphs(soup, title, n)
    if all(paragraphs):
        paragraph_elements = [p[0] for p in paragraphs]

        if any(isinstance(paragraph, str) for paragraph in paragraph_elements):
            print("Error: Expected tag objects, received strings.")
            return None

        parents_lists = [list(paragraph.parents) for paragraph in paragraph_elements]

        common_parent = None
        for parent in parents_lists[0]:
            if all(parent in parents_list for parents_list in parents_lists[1:]):
                common_parent = parent
                break
        
        while common_parent and common_parent.name != 'div':
            common_parent = common_parent.parent
        
        log_time("End find_common_container")
        return common_parent
        
    log_time("End find_common_container (no common parent found)")
    return None
#endregion

#region Selenium Shit
def get_webpage_info(url):
    log_time("Start get_webpage_info")
    options = Options()
    prefs = {
        "download.default_directory": "./",
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com/")
    chrome_driver = webdriver.Chrome(options=options)

    chrome_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 3)

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

        try:
            elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^='someclass']")))
        except TimeoutException:
            print("Specified elements did not appear within the timeout period.")
            elements = []

        html_content = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    log_time("End get_webpage_info")
    return soup
#endregion

#region Get Desirable Elements
def find_logo(soup, link):
    log_time("Start find_logo")
    pos = link.find('.com')
    if pos != -1:
        main_site = link[:pos+4]
    else:
        main_site = link

    main_site = main_site.rstrip('/') + '/'

    for element in soup.find_all(class_=True):
        if any('logo' in class_name.lower() for class_name in element['class']):
            href = element.get('href', '').strip().rstrip('/') + '/'
            if element.name == 'a' and href == main_site:
                logo_child = element.find(['img', 'svg'])
                if logo_child:
                    log_time("End find_logo")
                    return logo_child
            nested_logo = element.find('a', href=lambda x: (x.rstrip('/') + '/') == main_site if x else False)
            if nested_logo:
                logo_child = nested_logo.find(['img', 'svg'])
                if logo_child:
                    log_time("End find_logo")
                    return logo_child

    log_time("End find_logo (no logo found)")
    return None


def find_header(soup):
    log_time("Start find_header")
    h1_tag = soup.find('h1')
    log_time("End find_header")
    return h1_tag if h1_tag else None

def find_first_image(soup):
    log_time("Start find_first_image")
    elements = soup.find_all(['p', 'img'])
    last_img = None
    for element in elements:
        if element.name == 'img':
            last_img = element
        elif element.name == 'p':
            sentences = re.split(r'[.!?]+', element.get_text().strip())
            sentences = [sentence for sentence in sentences if sentence.strip()]
            
            if len(sentences) >= 2:
                log_time("End find_first_image")
                return last_img
    log_time("End find_first_image (no image found)")
    return None 
#endregion

#region Apply Final Edits (filters & formatting)
def filter_paragraphs(soup, keyword):
    log_time("Start filter_paragraphs")
    paragraphs = soup.find_all('p')

    for paragraph in paragraphs:
        sentences = [sentence.strip() for sentence in paragraph.text.split('.') if sentence.strip()]
        if len(sentences) >= 2:
            first_paragraph = BeautifulSoup(str(paragraph), 'html.parser')

    for paragraph in paragraphs:
        is_different = paragraph.text != first_paragraph.text
        if keyword.lower() not in paragraph.text.lower() and is_different:
            paragraph.decompose()

    log_time("End filter_paragraphs")
    return soup

def filter_images(soup):
    log_time("Start filter_images")
    paragraphs = soup.find_all('p')
    
    first_p = soup.new_tag('p')
    last_p = soup.new_tag('p')
    if paragraphs:
        soup.insert(0, first_p)
        soup.append(last_p)
    else:
        log_time("End filter_images")
        return soup
    
    remove_images = False
    element = soup.find()  

    while element:
        if element == last_p:
            remove_images = True  

        if remove_images and isinstance(element, Tag) and element.name == 'img':
            element.decompose()  

        element = element.next_sibling  

    first_p.decompose()
    last_p.decompose()

    log_time("End filter_images")
    return soup

def modify_html(soup):
    log_time("Start modify_html")
    for img in soup.find_all('img'):
        img_style = 'display: block; margin: auto; max-width: 500px; max-height: 300px;'
        if img.has_attr('style'):
            img['style'] += img_style
        else:
            img['style'] = img_style

    log_time("End modify_html")
    return soup
#endregion

#region Export to Other Documents
def save_document_to_pdf(html_content, output_filename):
    log_time("Start save_document_to_pdf")
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.html') as tmp_file:
            tmp_file.write(html_content)
            tmp_file_path = tmp_file.name

        command = ['node', 'html_to_pdf.js', f'{output_filename}.pdf', tmp_file_path]
        
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("PDF generated successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to generate PDF")
        print("Error:", e.stderr)
    log_time("End save_document_to_pdf")
#endregion

def primary_func(url, keyword, output_type, output_name):
    log_time("Start primary_func")
    soup = get_webpage_info(url)

    article_title = find_header(soup)
    n = 10
    lca = find_common_container(soup, article_title, n)
    logo = find_logo(soup, url)
    first_photo = find_first_image(soup)
    
    if lca:
        first_paragraphs = find_first_paragraphs(lca, article_title, n)
        first_paragraph = first_paragraphs[0]
        lca = filter_paragraphs(soup=lca, keyword=keyword)
        new_soup = BeautifulSoup('<html><body style="padding: 25px; display: flex; flex-direction: column; justify-content: center; align-items: center;"></body></html>', 'html.parser')
        new_soup.body.append(lca)
        new_soup = filter_images(new_soup)
        if first_photo:
            new_soup.body.insert(0, first_photo)
        if article_title:
            new_soup.body.insert(0, article_title)
        if logo:
            new_soup.body.insert(0, logo)
        new_soup.html.insert(0, soup.head)
        final_soup = modify_html(new_soup)
        
        with open('doc_debug.html', 'w') as debug_file:
            debug_file.write(str(final_soup))

        save_document_to_pdf(html_content=str(final_soup), output_filename=output_name)
    else:
        print("No common div found.")
    log_time("End primary_func")

if __name__ == "__main__":
    url = input("Enter the URL to clip: ")
    url = url if url else "https://www.cntraveler.com/gallery/best-hotels-in-san-diego"
    keyword = input("Enter the keyword: ")
    keyword = keyword if keyword else ''
    output_type = input("Enter the type of file: ")
    output_type = output_type if output_type else 'pdf'
    output_filename = input("Enter the output file name (default 'output.pdf'): ")
    output_filename = output_filename if output_filename else 'output'
    primary_func(url=url, keyword=keyword, output_name=output_filename, output_type=output_type)

"""
# Streamlit web interface
st.title('Clipt')

url = st.text_input("Enter the URL to clip:", "https://thedieline.com/blog/2024/3/13/knesko-skin-green-jade")
keyword = st.text_input("Enter the keyword:")
output_type = st.selectbox("Enter the type of file:", options=['pdf', 'txt', 'docx'], index=0)
output_filename = st.text_input("Enter the output file name:", 'output')

if st.button('Process URL'):
    primary_func(url=url, keyword=keyword, output_name=output_filename, output_type=output_type)
    with open(f'{output_filename}.{output_type}', "rb") as file:
        btn = st.download_button(
            label="Download PDF",
            data=file,
            file_name=f'{output_filename}.{output_type}',
            mime="application/pdf"
        )
"""