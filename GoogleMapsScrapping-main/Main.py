from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(filename='scraping.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s: %(message)s')

filename = "data.csv"

# Get user input for search query and location
search_query = input("Enter what you want to search: ")
location = input("Enter location: ")

link = f"https://www.google.com/maps/search/{search_query}+in+{location}"

# Check if the file exists
if os.path.exists(filename):
    df = pd.read_csv(filename)
else:
    df = pd.DataFrame(columns=['Name', 'Phone', 'Address', 'Website', 'Email']) 

# Function to extract email from a page
def extract_email_from_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    email_element = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    if email_element:
        return email_element['href'].split(':')[1]
    return None

# Function to extract emails from the entire website
def extract_email_from_website(url):
    try:
        # Check if the URL has a scheme, if not, add 'https://' as the default scheme
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)  # Set a timeout of 10 seconds
        response.raise_for_status()  # Raise an exception for any non-200 status code

        soup = BeautifulSoup(response.content, 'html.parser')
        email = extract_email_from_page(response.content)
        if email:
            return email

        # If no email found, crawl the website
        links_to_visit = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if urlparse(href).netloc:  # If the link has a netloc, it's an absolute URL
                full_url = href
            else:
                full_url = urljoin(url, href)
            if urlparse(full_url).netloc == urlparse(url).netloc:  # Only visit links within the same domain
                links_to_visit.add(full_url)

        for link in links_to_visit:
            try:
                response = requests.get(link, headers=headers, timeout=10)
                response.raise_for_status()
                email = extract_email_from_page(response.content)
                if email:
                    return email
            except requests.RequestException as e:
                logging.error(f"Error fetching content from {link}: {e}")
                continue

        return "Email not found"
    except requests.RequestException as e:
        logging.error(f"Error fetching website content for {url}: {e}")
        return None

# Function to scroll through Google Maps search results and extract data
def scroll_and_extract_data():
    global df
    action = ActionChains(browser)
    WebDriverWait(browser, 90).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hfpxzc")))

    records = []  # List to store records as dictionaries
    scraped_elements = set()  # Set to store already scraped elements to avoid duplicates

    while True:
        elements = browser.find_elements(By.CLASS_NAME, "hfpxzc")
        
        # Filter out already scraped elements
        elements = [el for el in elements if el not in scraped_elements]
        
        # If no new elements are found, break the loop
        if not elements:
            break
        
        for element in elements:
            try:
                scroll_origin = ScrollOrigin.from_element(element)
                action.scroll_from_origin(scroll_origin, 0, 200).perform()
                action.move_to_element(element).perform()

                WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "hfpxzc")))
                browser.execute_script("arguments[0].click();", element)
                WebDriverWait(browser, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Io6YTe")))

                source = browser.page_source
                soup = BeautifulSoup(source, 'html.parser')

                name_html = soup.find('h1', {"class": "DUwDvf lfPIob"})
                name = name_html.text.strip() if name_html else "Not available"

                divs = soup.findAll('div', {"class": "Io6YTe"})
                phone = next((div.text for div in divs if div.text.startswith(("+", "03"))), "Not available")
                address = next((div.text for div in divs if re.search(r'\d{1,4}\s[\w\s]+\s(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Square|Sq|Place|Pl|Court|Ct),?\s[\w\s]+,\s[A-Z]{2}\s\d{5}', div.text)), "Not available")
                website = next((div.text for div in divs if re.search(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', div.text)), "Not available")

                if website != "Not available":
                    # Extract email from the website
                    email = extract_email_from_website(website)
                else:
                    email = "Not available"

                print([name, phone, address, website, email])

                # Append the new record to the list of dictionaries
                records.append({'Name': name, 'Phone': phone, 'Address': address, 'Website': website, 'Email': email})

                # Add the element to the set of scraped elements
                scraped_elements.add(element)

            except (TimeoutException, StaleElementReferenceException) as e:
                logging.error(f"Error: {e}. Retrying...")
                continue
            except Exception as e:
                logging.error(f"Error: {e}. Skipping element.")
                continue

        # Scroll down to load more results
        try:
            scroll_origin = ScrollOrigin.from_element(elements[-1])
            action.scroll_from_origin(scroll_origin, 0, 8000).perform()  # Increased scrolling distance
            time.sleep(2)  # Wait for new results to load
        except (IndexError, StaleElementReferenceException) as e:
            logging.error(f"Error scrolling: {e}. Exiting...")
            break

    # Convert the list of dictionaries to a DataFrame
    new_df = pd.DataFrame(records)

    # Remove duplicates
    df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()

    # Save data to a DataFrame
    df.to_csv(filename, index=False)

# Set up Selenium Chrome WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--log-level=3")  # Suppress most log messages

browser = webdriver.Chrome(options=chrome_options)

try:
    browser.get(str(link))
    scroll_and_extract_data()

finally:
    browser.quit()
