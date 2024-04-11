from selenium import webdriver
from bs4 import BeautifulSoup

def fetch_with_selenium(url):
    # Specify the path to the WebDriver you downloaded
    driver_path = '/path/to/your/webdriver'

    # Initialize the WebDriver (the example below uses Chrome; adjust if using Firefox or another browser)
    driver = webdriver.Chrome(executable_path=driver_path)

    # Load the webpage
    driver.get(url)

    # Wait for the desired content to load. You can adjust the sleep time as necessary or use more sophisticated waits.
    driver.implicitly_wait(10)  # Waits for 10 seconds

    # Now that the page is loaded, you can parse the HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Close the WebDriver
    driver.quit()

    # Here, you would use your image finding logic on 'soup'
    # For example:
    images = soup.find_all('img')
    for img in images:
        print(img.get('src'))

# Example URL
url = "https://www.forbes.com/sites/forbes-personal-shopper/article/mother-of-the-bride-gifts/?sh=26cda2942b94"

fetch_with_selenium(url)
