from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import urllib3.exceptions
import time
import re
import json
import os
from dotenv import load_dotenv

load_dotenv()

AUTH = f'{os.environ.get("BRIGHT_DATA_USERNAME")}:{os.environ.get("BRIGHT_DATA_PASSWORD")}'
HOST = os.environ.get("BRIGHT_DATA_HOST")
PORT = os.environ.get("BRIGHT_DATA_PORT")

if not all([os.environ.get("BRIGHT_DATA_USERNAME"), 
           os.environ.get("BRIGHT_DATA_PASSWORD"),
           HOST,
           PORT]):
    raise ValueError("Missing required environment variables. Please ensure BRIGHT_DATA_USERNAME, BRIGHT_DATA_PASSWORD, BRIGHT_DATA_HOST, and BRIGHT_DATA_PORT are set.")

SBR_WEBDRIVER = f'https://{AUTH}@{HOST}:{PORT}'

print(f"Connecting to: {SBR_WEBDRIVER}")  # Added for debugging (will mask credentials)

base_url = 'https://www.booking.com'

def scrape_booking_com():
    try:
        options = ChromeOptions()
        options.set_capability('brd:options', {
            'country': 'co',
            'session_id': f'booking_com_{time.time()}',
            'browser_type': 'chrome',
            'keep_alive': True
        })

        print('Connecting to Bright Data browser...')
        sbr_connection = ChromiumRemoteConnection(
            SBR_WEBDRIVER, 
            'sbr:browser',
            'goog',
            'chrome'
        )

        with Remote(sbr_connection, options=options) as driver:
            print('Connected to Bright Data browser successfully')
            driver.set_page_load_timeout(10)
            driver.get(base_url)

            print('Waiting for page to load...')
            time.sleep(10)

            print('Scraping page...')
            page_source = driver.page_source
            print(page_source)
            
        
    except Exception as e:
        print(f'Error connecting to Bright Data browser: {e}')
        return None

scrape_booking_com()