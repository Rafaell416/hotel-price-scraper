from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

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

        # Find the search input
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='ss']"))
        )
        
        print('✨ Found search input, entering text...')
        search_text = "Loft 32 Medellin Living"
        
        # Clear the field completely using multiple methods
        search_input.clear()
        time.sleep(0.5)
        
        # Use JavaScript to clear and set the value to ensure it's completely clean
        driver.execute_script("arguments[0].value = '';", search_input)
        time.sleep(0.5)
        
        # Now enter the text
        search_input.send_keys(search_text)
        time.sleep(1)
        
        # Verify text entry
        actual_value = search_input.get_attribute('value')
        print(f'📝 Text in input field: {actual_value}')
        
        # Verify the text is exactly what we expect
        if actual_value != search_text:
            print(f'⚠️ Text mismatch! Expected: "{search_text}", Got: "{actual_value}"')
            # Try to clear and re-enter
            driver.execute_script("arguments[0].value = '';", search_input)
            time.sleep(0.5)
            search_input.send_keys(search_text)
            time.sleep(1)
            actual_value = search_input.get_attribute('value')
            print(f'📝 After retry, text in input field: {actual_value}')
        
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

def open_date_picker(driver):
    """Open the date picker"""
    try:
        print('🔍 Opening date picker...')
        date_picker_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='searchbox-dates-container']")
        date_picker_button.click()
        time.sleep(1)
        return True
    except Exception as e:  
        print(f"Error: {e}")
        return False

def is_date_picker_open(driver):
    """Check if the date picker is open and visible"""
    try:
        print('🔍 Checking if date picker is open...')
        
        date_picker = driver.find_element(By.CSS_SELECTOR, "[data-testid='searchbox-datepicker-calendar']")
        
        if date_picker.is_displayed():
            print('✅ Date picker is open')
            return True
        else:
            print('❌ Date picker is not visible')
            return False
            
    except:
        print('❌ Date picker is not open')
        return False

def select_checkin_and_checkout_dates(driver, checkin_date, checkout_date):
    """Select check-in and check-out dates"""
    try:
        print(f'📅 Selecting dates: {checkin_date} to {checkout_date}')
        # check if date picker is open
        if not is_date_picker_open(driver):
            print('❌ Date picker is not open')
            if not open_date_picker(driver):
                print('❌ Could not open date picker')
                return False
            else:
                print('✅ Date picker opened')
                time.sleep(1)
        else:
            time.sleep(1)
        # select checkin date
        checkin_date_element = driver.find_element(By.CSS_SELECTOR, f"span[data-date='{checkin_date}']")
        checkin_date_element.click()
        # select checkout date
        checkout_date_element = driver.find_element(By.CSS_SELECTOR, f"span[data-date='{checkout_date}']")
        checkout_date_element.click()
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

def save_results(results, filename='hotel_prices.json'):
    """Save results to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'💾 Results saved to {filename}')
    except Exception as e:
        print(f'❌ Error saving results: {str(e)}')

def scrape_hotel_prices_from_booking_com():
    """Main function to scrape prices for multiple dates"""

    dates_list = calculate_dates()
    results = []

    if not dates_list:
        print('❌ No dates to process')
        return results

    driver = None
    try:
        print(f'\n🚀 Starting hotel prices scraper script...')
        
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
            else:
                print('ℹ️ Modal exists but not visible, continuing...')
        except:
            print('✅ No modal present, continuing...')

        print('🎉 Page ready!')

        for i, (checkin_date, checkout_date) in enumerate(dates_list):
            try:
                print(f"Processing date {i+1}/{len(dates_list)}: {checkin_date} - {checkout_date}")

                # Step 1: search and click on hotel
                if not search_and_click_on_hotel(driver):
                    print(f'⚠️ Could not complete hotel search and selection for date {i+1}/{len(dates_list)}')
                    results.append({
                        'checkin': str(checkin_date),
                        'checkout': str(checkout_date),
                        'price': None,
                        'error': 'Failed to search for hotel'
                    })
                    driver.save_screenshot(f"hotel_search_failed_{i+1}.png")
                    continue
                else:
                    print(f'✅ Hotel search and selection completed for date {i+1}/{len(dates_list)}')

                # Step 2: select dates
                if not select_checkin_and_checkout_dates(driver, checkin_date, checkout_date):
                    print(f'⚠️ Could not complete date selection for date {i+1}/{len(dates_list)}')
                    results.append({
                        'checkin': str(checkin_date),
                        'checkout': str(checkout_date),
                        'price': None,
                        'error': 'Failed to select date'
                    })
                    continue
                else:
                    print(f'✅ Date selection completed for date {i+1}/{len(dates_list)}')

                # Step 3: click on search button
                if not click_on_search_button(driver):
                    print(f'⚠️ Could not complete search button click for date {i+1}/{len(dates_list)}')
                    results.append({
                        'checkin': str(checkin_date),
                        'checkout': str(checkout_date),
                        'price': None,
                        'error': 'Failed to click on search button'
                    })
                    continue
                else:
                    print(f'✅ Search button clicked for date {i+1}/{len(dates_list)}')

                # Step 4: extract price
                print(f'🔍 Extracting price for date {i+1}/{len(dates_list)}')
                price = extract_price(driver)
                print(f'💵 Price: {price}')
                results.append({
                    'checkin': str(checkin_date),
                    'checkout': str(checkout_date),
                    'price': price,
                    'error': None if price else 'Failed to extract price'
                })

                print(f'✅ Completed: {checkin_date} to {checkout_date} - Price: {price}')

                # Wait between searches to avoid rate limiting
                if i < len(dates_list) - 1:  # Don't wait after last iteration
                    print('⏸️ Waiting before next search...')
                    time.sleep(3)

            except Exception as e:
                print(f"Error on loop processing date {i+1}/{len(dates_list)}: {str(e)}")
            
    except Exception as e:
        print(f'❌ Error on function: {str(e)}')
        
    finally:
        if driver:
            print('👋 Closing browser session...')
            driver.quit()
    
    return results

if __name__ == "__main__":
    results = scrape_hotel_prices_from_booking_com()
    if results:
        save_results(results)
        # Print summary
        print(f'\n📊 Summary:')
        print(f'Total dates processed: {len(results)}')
        successful = len([r for r in results if r['price'] is not None])
        print(f'Successful extractions: {successful}')
        print(f'Failed extractions: {len(results) - successful}')

        # Print results
        print(f'\n📋 Results:')
        for result in results:
            status = '✅' if result['price'] else '❌'
            print(f'{status} {result["checkin"]} to {result["checkout"]}: {result["price"] or result["error"]}')

        print('\n✅ Script completed successfully')
    else:
        print('\n❌ Script failed to complete')