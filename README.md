Key Features:

Dynamic Web Scraping: Utilizes Selenium for scrolling and interacting with Google Maps search results to collect detailed business data.
Data Parsing: Extracts names, phone numbers, addresses, websites, and emails using BeautifulSoup and regex patterns.
Email Extraction: Crawls business websites to identify and extract email addresses.
Error Handling: Includes robust error logging and exception management for uninterrupted operation.
Data Storage: Saves data in a CSV file, ensuring records are preserved and easily accessible.
How It Works:

Input Query: User provides a search query and location (e.g., "Restaurants in New York").
Automated Browsing: The scraper navigates Google Maps, scrolls through results, and clicks on entries to access details.
Data Collection: Extracts and compiles business information into a structured CSV format.
Email Extraction: Attempts to retrieve email addresses by crawling linked websites.
Technologies Used:

Python Libraries: Selenium, BeautifulSoup, Pandas, Logging, Requests, and Re.
File Handling: CSV for data storage and management.
Web Interaction: Advanced scrolling and clicking actions using Selenium's ActionChains.
Usage:

Ideal for researchers, digital marketers, and businesses looking to compile contact information from Google Maps efficiently.
Simply run the script, provide the required inputs, and let the tool handle the rest!
