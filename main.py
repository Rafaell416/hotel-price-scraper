from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import time
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import urllib3.exceptions

load_dotenv()

AUTH = f'{os.environ.get("BRIGHT_DATA_USERNAME")}:{os.environ.get("BRIGHT_DATA_PASSWORD")}'
HOST = os.environ.get("BRIGHT_DATA_HOST")
PORT = os.environ.get("BRIGHT_DATA_PORT")

if not all([os.environ.get("BRIGHT_DATA_USERNAME"), 
           os.environ.get("BRIGHT_DATA_PASSWORD"),
           HOST,
           PORT]):
    raise ValueError("❌ Missing required environment variables")

SBR_WEBDRIVER = f'https://{AUTH}@{HOST}:{PORT}'

def create_driver_session():
    options = ChromeOptions()
    options.set_capability('brd:options', {
        'country': 'co',
        'session_id': f'booking_com_{time.time()}',
        'browser_type': 'chrome',
        'keep_alive': True,
        'timeout': 60000
    })

    options.add_argument("--lang=es-CO")
    options.add_argument("--accept-language=es-CO,es,en")
    
    sbr_connection = ChromiumRemoteConnection(
        SBR_WEBDRIVER,
        'sbr:browser',
        'goog',
        'chrome'
    )
    
    driver = Remote(sbr_connection, options=options)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(20)
    return driver

def wait_for_page_load(driver, timeout=30):
    """Wait for page to load completely"""
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return True
    except Exception as e:
        print(f'⚠️ Page load wait error: {str(e)}')
        return False

def close_modal(driver):
    """Single attempt to close modal"""
    try:
        print('🔍 Looking for modal...')
        wait = WebDriverWait(driver, 10)
        
        # Check if modal exists and is visible
        modal = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']"))
        )
        
        print('🎯 Modal found, attempting to close...')
        driver.execute_script("arguments[0].click();", modal)
        time.sleep(2)
        
        # Verify modal is closed
        try:
            modal = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']")
            if not modal.is_displayed():
                print('✅ Modal closed successfully')
                return True
        except:
            print('✅ Modal closed successfully')
            return True
            
    except Exception as e:
        print(f'⚠️ Modal close attempt failed: {str(e)}')
        return False

def search_and_click_on_hotel(driver):
    try:
        print('🔍 Looking for search input...')
        wait = WebDriverWait(driver, 15)
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='ss']"))
        )
        
        print('✨ Found search input, entering text...')
        search_text = "Loft 32 Medellin Living"
        
        # Clear and enter text
        search_input.clear()
        search_input.send_keys(search_text)
        
        # Verify text entry
        actual_value = search_input.get_attribute('value')
        print(f'📝 Text in input field: {actual_value}')
        
        print('🔄 Waiting for autocomplete results...')
        # Wait for autocomplete list to appear
        autocomplete_list = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='group']"))
        )
        
        # Give a short time for the list to populate
        time.sleep(2)
        
        # Re-find the list to avoid stale element
        autocomplete_list = driver.find_element(By.CSS_SELECTOR, "ul[role='group']")
        
        # Find the specific hotel option
        hotel_options = autocomplete_list.find_elements(
            By.CSS_SELECTOR, 
            "li[role='option'] div.b08850ce41"
        )
        
        # Look for exact match
        for option in hotel_options:
            if option.text.strip() == "Loft 32 Medellín Living":
                print(f'🎯 Found exact match: {option.text}')
                option.click()
                print('✅ Selected hotel from autocomplete')
                # driver.save_screenshot("selected_hotel.png")
                return True
        
        print('⚠️ Hotel not found in autocomplete results')
        return False
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def calculate_dates():
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=30)
    dates = []
    current_date = start_date
    while current_date <= end_date:
        checkin_date = current_date
        checkout_date = current_date + timedelta(days=1)
        dates.append((checkin_date, checkout_date))
        current_date += timedelta(days=1)
    return dates

def select_date(driver):
    try:
        print('🔍 Selecting date...')
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30)
        dates = []

        current_date = start_date

        iterations = 0
        while current_date <= end_date:
            checkin_date = current_date
            checkout_date = current_date + timedelta(days=1)
            print(f"Checking date: {checkin_date} - Checkout date: {checkout_date}")
            dates.append((checkin_date, checkout_date))

            if iterations > 1:
                print(f"Clicking on calendar input before finding the date")
                # click on calendar input before finding the date
                pass
            
            # find the date
            checkin_date_element = driver.find_element(By.CSS_SELECTOR, f"span[data-date='{checkin_date}']")
            checkin_date_element.click()
            checkout_date_element = driver.find_element(By.CSS_SELECTOR, f"span[data-date='{checkout_date}']")
            checkout_date_element.click()

            current_date += timedelta(days=1)
            iterations += 1
            print(dates)
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def click_on_search_button(driver):
    try:
        print('🔍 Clicking on search button...')
        search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # wait for the page to load
        time.sleep(10)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def extract_price(driver):
    try:
        print('🔍 Extracting price...')
        price = driver.find_element(By.CSS_SELECTOR, "span[data-testid='price-and-discounted-price']")
        print(f"Price: {price.text}")
        return price.text
    except Exception as e:
        print(f"Error: {e}")
        return False

def scrape_booking_com(max_retries=3):
    success = False
    
    for attempt in range(max_retries):
        driver = None
        try:
            print(f'\n🚀 Starting attempt {attempt + 1}/{max_retries}')
            
            # Create new driver session
            driver = create_driver_session()
            print('🔗 Connected successfully to Bright Data')
            
            # Load Booking.com
            print('🌐 Loading Booking.com...')
            driver.get('https://www.booking.com/?cc1=co&selected_currency=COP')

            # Wait for page load
            if not wait_for_page_load(driver):
                raise Exception("Page did not load completely")
            
            print('📄 Page loaded, waiting for stability...')
            time.sleep(5)
            
            # Check if modal is present before trying to close it
            print('🔍 Checking if modal is present...')
            try:
                modal = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']")
                if modal.is_displayed():
                    print('🎯 Modal found, attempting to close...')
                    if close_modal(driver):
                        print('🎉 Modal closed successfully!')
                    else:
                        print('⚠️ Failed to close modal')
                        continue  # Try again
                else:
                    print('ℹ️ Modal exists but not visible, continuing...')
            except:
                print('✅ No modal present, continuing...')

            print('🎉 Page ready!')
            driver.save_screenshot("page_ready.png")

            # search and click on hotel
            if not search_and_click_on_hotel(driver):
                print('⚠️ Could not complete hotel search and selection')
                return False
            else:
                print('✅ Hotel search and selection completed')
                driver.save_screenshot("hotel_selected.png")
                print('📸 Screenshot saved')

            dates = calculate_dates()
            for date in dates:
                print(f"Checking date: {date[0]} - Checkout date: {date[1]}")

            # select date
            if not select_date(driver):
                print('⚠️ Could not complete date selection')
                return False
            else:
                print('✅ Date selection completed')
                driver.save_screenshot("date_selected.png")
                print('📸 Screenshot saved')

            # click on search button
            if not click_on_search_button(driver):
                print('⚠️ Could not complete search button click')
                return False
            else:
                print('✅ Search button clicked')
                driver.save_screenshot("search_results.png")

            # extract price
            if not extract_price(driver):
                print('⚠️ Could not extract price')
                return False
            else:
                print('✅ Price extracted')
                success = True
                break
                
        except Exception as e:
            print(f'❌ Error on attempt {attempt + 1}: {str(e)}')
            
        finally:
            if driver:
                print('👋 Closing browser session...')
                driver.quit()
        
        if not success and attempt < max_retries - 1:
            print(f'🔄 Retrying in 5 seconds... ({attempt + 2}/{max_retries} attempts remaining)')
            time.sleep(5)
    
    return success

if __name__ == "__main__":
    if scrape_booking_com():
        print('\n✅ Script completed successfully')
    else:
        print('\n❌ Script failed to complete')