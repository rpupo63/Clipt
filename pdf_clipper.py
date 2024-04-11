import requests
from bs4 import BeautifulSoup
import pdfkit

# Function to download the HTML content of a webpage
def download_html(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print("Error fetching the page. Status Code:", response.status_code)
            return None
    except Exception as e:
        print("An error occurred:", str(e))
        return None

# Function to convert HTML to PDF
def html_to_pdf(html_content, output_filename):
    try:
        pdfkit.from_string(html_content, output_filename)
        print(f"PDF saved as {output_filename}")
    except Exception as e:
        print("An error occurred while converting HTML to PDF:", str(e))

# Example usage
url = "https://www.forbes.com/sites/forbes-personal-shopper/article/best-gifts-for-husband/?sh=6af878a1bde2"
html_content = download_html(url)

if html_content:
    output_filename = "downloaded_webpage.pdf"
    html_to_pdf(html_content, output_filename)
else:
    print("Failed to download HTML content.")
