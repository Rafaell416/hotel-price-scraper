from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import csv

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
                return True
        except:
            return True
            
    except Exception as e:
        print(f'⚠️ Modal close attempt failed: {str(e)}')
        return False

def search_and_click_on_hotel(driver, hotel_name):
    try:
        ensure_no_blocking_modals(driver)

        print('🔍 Looking for search input...')
        wait = WebDriverWait(driver, 15)

        # Find the search input
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='ss']"))
        )
        
        print('✨ Found search input, entering text...')
        search_text = hotel_name
        
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
        
        # Find all autocomplete options using stable selectors
        autocomplete_options = autocomplete_list.find_elements(
            By.CSS_SELECTOR, 
            "li[role='option']"
        )
        
        print(f'🔍 Found {len(autocomplete_options)} autocomplete options')
        
        # Look for exact match by checking the hotel name text
        for i, option in enumerate(autocomplete_options):
            try:
                # Use data-testid to find the autocomplete result container
                result_container = option.find_element(By.CSS_SELECTOR, "[data-testid='autocomplete-result']")
                
                # Get all text content from the result container
                option_text = result_container.text.strip()
                
                # Split by lines to get hotel name (first line) and location (second line)
                text_lines = [line.strip() for line in option_text.split('\n') if line.strip()]
                
                if text_lines:
                    hotel_text = text_lines[0]  # First line should be the hotel name
                    location_text = text_lines[1] if len(text_lines) > 1 else ""
                    
                    print(f'🔍 Option {i+1}: Hotel="{hotel_text}", Location="{location_text}"')
                    
                    # Check for exact match with the hotel name
                    if hotel_text == hotel_name:
                        print(f'🎯 Found exact match: {hotel_text}')
                        
                        # Click on the clickable button element using role attribute
                        clickable_button = option.find_element(By.CSS_SELECTOR, "div[role='button']")
                        clickable_button.click()
                        
                        print('🏨 Selected hotel from autocomplete')
                        return True
                        
            except Exception as e:
                print(f'⚠️ Error checking autocomplete option {i+1}: {e}')
                continue
        
        # If exact match not found, try partial matching
        print('🔍 Exact match not found, checking for partial matches...')
        for i, option in enumerate(autocomplete_options):
            try:
                result_container = option.find_element(By.CSS_SELECTOR, "[data-testid='autocomplete-result']")
                option_text = result_container.text.strip()
                text_lines = [line.strip() for line in option_text.split('\n') if line.strip()]
                
                if text_lines:
                    hotel_text = text_lines[0]
                    
                    # Check if the hotel name is contained within the option text (case-insensitive)
                    if hotel_name.lower() in hotel_text.lower() or hotel_text.lower() in hotel_name.lower():
                        print(f'🎯 Found partial match: {hotel_text}')
                        
                        clickable_button = option.find_element(By.CSS_SELECTOR, "div[role='button']")
                        clickable_button.click()
                        
                        print('🏨 Selected hotel from autocomplete (partial match)')
                        return True
                        
            except Exception as e:
                print(f'⚠️ Error checking autocomplete option {i+1} for partial match: {e}')
                continue
        
        print('❌ Hotel not found in autocomplete results')
        
        # Debug: Print all available options for troubleshooting
        print('🔍 All available autocomplete options:')
        for i, option in enumerate(autocomplete_options):
            try:
                result_container = option.find_element(By.CSS_SELECTOR, "[data-testid='autocomplete-result']")
                option_text = result_container.text.strip()
                text_lines = [line.strip() for line in option_text.split('\n') if line.strip()]
                hotel_text = text_lines[0] if text_lines else "Unknown"
                location_text = text_lines[1] if len(text_lines) > 1 else "Unknown location"
                print(f'  {i+1}. Hotel: "{hotel_text}" | Location: "{location_text}"')
            except Exception as e:
                print(f'  {i+1}. (Unable to read text: {e})')
        
        return False
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def calculate_dates():
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=30) #30
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
            print('👍🏾 Date picker is open')
            return True
        else:
            print('❌ Date picker is not visible')
            return False
            
    except:
        return False

def select_checkin_and_checkout_dates(driver, checkin_date, checkout_date):
    """Select check-in and check-out dates"""
    try:
        print(f'📅 Selecting dates: {checkin_date} to {checkout_date}')
        # check if date picker is open
        if not is_date_picker_open(driver):
            print('👎🏾 Date picker is not open')
            if not open_date_picker(driver):
                print('👎🏾 Could not open date picker')
                return False
            else:
                print('👍🏾 Date picker opened')
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
    """Enhanced price extraction with availability check"""
    try:
        print('🔍 Extracting price...')
        
        # First, check if the hotel is available for the selected dates
        try:
            # Look for the property card and check if it's sold out
            property_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='property-card']")
            soldout_status = property_card.get_attribute('data-soldout')
            
            if soldout_status == "1":
                print('❌ Hotel not available for this date')
                
                # Try to extract the specific unavailability message
                try:
                    unavailable_message = driver.find_element(
                        By.CSS_SELECTOR, 
                        "p.b99b6ef58f.c8075b5e6a"
                    ).text
                    print(f'📋 Availability message: {unavailable_message}')
                    return f"Not available - {unavailable_message}"
                except:
                    return "Not available for selected dates"
            
        except:
            # If we can't find the property card or soldout attribute, continue with price extraction
            pass
        
        # Try multiple price selectors as Booking.com uses different ones
        price_selectors = [
            "span[data-testid='price-and-discounted-price']",
            "[data-testid='price-and-discounted-price']",
            ".prco-valign-middle-helper",
            "[data-testid='price']",
            ".bui-price-display__value",
            ".prco-text-nowrap-helper",
            "span[aria-label*='COP']",
            # New selectors for available properties
            ".bui-price-display__value .sr-only",
            "[data-testid='price-availability-row'] span"
        ]
        
        for selector in price_selectors:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, selector)
                if price_element and price_element.text.strip():
                    price_text = price_element.text.strip()
                    # Filter out non-price text
                    if 'COP' in price_text and any(char.isdigit() for char in price_text):
                        print(f"💰 Price found: {price_text}")
                        return price_text
            except:
                continue
        
        # If no price found with standard selectors, try to find any element containing "COP"
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'COP')]")
            for element in elements:
                text = element.text.strip()
                if 'COP' in text and any(char.isdigit() for char in text):
                    # Avoid alternative date suggestions
                    if 'From' not in text and 'night' not in text:
                        print(f"💰 Price found via COP search: {text}")
                        return text
        except:
            pass
        
        # Check if we're on a page showing alternative dates instead of no availability
        try:
            alternative_dates = driver.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='next-available-dates-carousel']"
            )
            if alternative_dates:
                print('📅 Hotel showing alternative dates - not available for selected dates')
                return "Not available for selected dates - alternative dates suggested"
        except:
            pass
            
        print("❌ No price found with any method")
        return None
        
    except Exception as e:
        print(f"❌ Error during price extraction: {e}")
        return None

def check_hotel_availability(driver):
    """Separate function to explicitly check hotel availability"""
    try:
        # Check for soldout attribute
        property_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='property-card']")
        soldout_status = property_card.get_attribute('data-soldout')
        
        if soldout_status == "1":
            return False, "Hotel not available for selected dates"
        
        # Check for availability message
        try:
            unavailable_message = driver.find_element(
                By.CSS_SELECTOR, 
                "p.b99b6ef58f.c8075b5e6a"
            )
            if "no availability" in unavailable_message.text.lower():
                return False, unavailable_message.text
        except:
            pass
        
        # Check for alternative dates carousel (indicates unavailability)
        try:
            alternative_dates = driver.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='next-available-dates-carousel']"
            )
            if alternative_dates:
                return False, "Not available for selected dates - alternative dates suggested"
        except:
            pass
        
        return True, "Available"
        
    except Exception as e:
        print(f"⚠️ Error checking availability: {e}")
        return True, "Could not determine availability"

def save_results_to_csv(results, filename='hotel_prices.csv'):
    """Save all results to a single CSV file with hotels as columns and dates as rows"""
    try:
        if not results:
            print('❌ No results to save')
            return
        
        # Get all unique hotels and dates
        hotels = sorted(list(set([r['hotel_name'] for r in results])))
        all_dates = sorted(list(set([(r['checkin'], r['checkout']) for r in results])))
        
        print(f'📊 Creating CSV with {len(hotels)} hotels and {len(all_dates)} date ranges')
        
        # Create CSV filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'hotel_prices_{timestamp}.csv'
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Create CSV writer
            writer = csv.writer(csvfile)
            
            # Write header row
            header = ['Check-in Date', 'Check-out Date', 'Date Range'] + hotels
            writer.writerow(header)
            
            # Write data rows
            for checkin_date, checkout_date in all_dates:
                # Create date range string for better readability
                date_range = f"{checkin_date} → {checkout_date}"
                row = [checkin_date, checkout_date, date_range]
                
                # Add price for each hotel for this date range
                for hotel in hotels:
                    # Find the result for this hotel and date combination
                    hotel_result = next(
                        (r for r in results 
                         if r['hotel_name'] == hotel 
                         and r['checkin'] == checkin_date 
                         and r['checkout'] == checkout_date), 
                        None
                    )
                    
                    if hotel_result:
                        if hotel_result['price'] and hotel_result['price'] != 'None':
                            # Clean price text (remove extra spaces, normalize format)
                            price = str(hotel_result['price']).strip()
                            if 'Not available' in price:
                                row.append('N/A')
                            else:
                                row.append(price)
                        else:
                            # Determine the reason for no price
                            if hotel_result['availability'] == 'Not available':
                                row.append('N/A')
                            elif hotel_result['error']:
                                row.append('ERROR')
                            else:
                                row.append('N/A')
                    else:
                        row.append('NO DATA')
                
                writer.writerow(row)
        
        print(f'💾 CSV saved: {csv_filename}')
        
        # Also create a detailed CSV with error information
        detailed_filename = f'hotel_prices_detailed_{timestamp}.csv'
        
        with open(detailed_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Detailed CSV header
            detailed_header = [
                'Hotel Name', 'Check-in Date', 'Check-out Date', 'Date Range',
                'Price', 'Availability', 'Error', 'Status'
            ]
            writer.writerow(detailed_header)
            
            # Write detailed data
            for result in results:
                date_range = f"{result['checkin']} → {result['checkout']}"
                
                # Determine status
                if result['price'] and 'Not available' not in str(result['price']):
                    status = 'SUCCESS'
                    price = result['price']
                elif result['availability'] == 'Not available':
                    status = 'NOT_AVAILABLE'
                    price = 'N/A'
                elif result['error']:
                    status = 'ERROR'
                    price = 'ERROR'
                else:
                    status = 'NO_DATA'
                    price = 'N/A'
                
                detailed_row = [
                    result['hotel_name'],
                    result['checkin'],
                    result['checkout'],
                    date_range,
                    price,
                    result.get('availability', 'Unknown'),
                    result.get('error', ''),
                    status
                ]
                writer.writerow(detailed_row)
        
        print(f'💾 Detailed CSV saved: {detailed_filename}')
        
        # Print summary statistics
        total_combinations = len(hotels) * len(all_dates)
        successful_prices = len([r for r in results if r['price'] and 'Not available' not in str(r['price'])])
        not_available = len([r for r in results if r['availability'] == 'Not available'])
        errors = len([r for r in results if r['error']])
        
        print(f'\n📊 CSV SUMMARY:')
        print(f'   🏨 Hotels: {len(hotels)}')
        print(f'   📅 Date ranges: {len(all_dates)}')
        print(f'   📊 Total combinations: {total_combinations}')
        print(f'   ✅ Successful prices: {successful_prices}')
        print(f'   ❌ Not available: {not_available}')
        print(f'   🔧 Errors: {errors}')
        print(f'   📈 Success rate: {(successful_prices/len(results)*100):.1f}%')
        
        # Print hotel list for reference
        print(f'\n🏨 Hotels in CSV (columns):')
        for i, hotel in enumerate(hotels, 1):
            print(f'   {i}. {hotel}')
            
        return csv_filename, detailed_filename
        
    except Exception as e:
        print(f'❌ Error saving CSV: {str(e)}')
        return None, None

def create_price_summary_csv(results, filename_prefix='hotel_summary'):
    """Create a summary CSV with aggregated statistics per hotel"""
    try:
        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f'{filename_prefix}_{timestamp}.csv'
        
        # Group results by hotel
        hotel_stats = {}
        
        for result in results:
            hotel = result['hotel_name']
            if hotel not in hotel_stats:
                hotel_stats[hotel] = {
                    'total_searches': 0,
                    'successful_prices': 0,
                    'not_available': 0,
                    'errors': 0,
                    'prices': [],
                    'min_price': None,
                    'max_price': None,
                    'avg_price': None
                }
            
            stats = hotel_stats[hotel]
            stats['total_searches'] += 1
            
            if result['price'] and 'Not available' not in str(result['price']):
                stats['successful_prices'] += 1
                # Extract numeric value from price string
                price_str = str(result['price']).replace('COP', '').replace(',', '').strip()
                try:
                    price_num = float(''.join(filter(str.isdigit, price_str)))
                    stats['prices'].append(price_num)
                except:
                    pass
            elif result['availability'] == 'Not available':
                stats['not_available'] += 1
            else:
                stats['errors'] += 1
        
        # Calculate price statistics
        for hotel, stats in hotel_stats.items():
            if stats['prices']:
                stats['min_price'] = min(stats['prices'])
                stats['max_price'] = max(stats['prices'])
                stats['avg_price'] = sum(stats['prices']) / len(stats['prices'])
        
        # Write summary CSV
        with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            header = [
                'Hotel Name', 'Total Searches', 'Successful Prices', 'Not Available', 
                'Errors', 'Success Rate (%)', 'Min Price (COP)', 'Max Price (COP)', 
                'Avg Price (COP)', 'Price Range'
            ]
            writer.writerow(header)
            
            # Data rows
            for hotel, stats in hotel_stats.items():
                success_rate = (stats['successful_prices'] / stats['total_searches'] * 100) if stats['total_searches'] > 0 else 0
                
                min_price_str = f"{stats['min_price']:,.0f}" if stats['min_price'] else 'N/A'
                max_price_str = f"{stats['max_price']:,.0f}" if stats['max_price'] else 'N/A'
                avg_price_str = f"{stats['avg_price']:,.0f}" if stats['avg_price'] else 'N/A'
                
                price_range = f"{min_price_str} - {max_price_str}" if stats['min_price'] and stats['max_price'] else 'N/A'
                
                row = [
                    hotel,
                    stats['total_searches'],
                    stats['successful_prices'],
                    stats['not_available'],
                    stats['errors'],
                    f"{success_rate:.1f}%",
                    min_price_str,
                    max_price_str,
                    avg_price_str,
                    price_range
                ]
                writer.writerow(row)
        
        print(f'📊 Summary CSV saved: {summary_filename}')
        return summary_filename
        
    except Exception as e:
        print(f'❌ Error creating summary CSV: {str(e)}')
        return None

def load_hotel_names(filename='hotel_names.txt'):
    """Load hotel names from text file (one hotel per line)"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Clean and filter hotel names
        valid_hotels = []
        for line_num, line in enumerate(lines, 1):
            hotel_name = line.strip()
            if hotel_name:  # Skip empty lines
                valid_hotels.append(hotel_name)
            else:
                print(f'⚠️ Skipping empty line {line_num}')
        
        print(f'📋 Loaded {len(valid_hotels)} hotels from {filename}')
        for i, hotel in enumerate(valid_hotels, 1):
            print(f'   {i}. {hotel}')
        
        return valid_hotels
        
    except FileNotFoundError:
        print(f'❌ File {filename} not found')
        return []
    except Exception as e:
        print(f'❌ Error loading hotels: {e}')
        return []

def ensure_no_blocking_modals(driver):
    """Ensure no blocking modals are present"""
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
        print('👍🏾 No modal present, continuing...')

def scrape_hotel_prices_from_booking_com():
    """Main function to scrape prices for multiple hotels and dates"""
    
    # Load hotels and dates
    hotel_names = load_hotel_names()
    if not hotel_names:
        print('❌ No hotels to process')
        return []
    
    dates_list = calculate_dates()
    if not dates_list:
        print('❌ No dates to process')
        return []
    
    all_results = []
    max_searches_per_session = 6
    
    print(f'\n🚀 Starting scraper for {len(hotel_names)} hotels × {len(dates_list)} dates = {len(hotel_names) * len(dates_list)} total searches')
    
    # Process each hotel
    for hotel_idx, hotel_name in enumerate(hotel_names):
        print(f'\n{"="*60}')
        print(f'🏨 HOTEL {hotel_idx + 1}/{len(hotel_names)}: {hotel_name}')
        print(f'{"="*60}')
        
        hotel_results = []
        driver = None
        search_count = 0
        
        try:
            # Process each date for this hotel
            for date_idx, (checkin_date, checkout_date) in enumerate(dates_list):
                try:
                    # Create new session if needed
                    if search_count % max_searches_per_session == 0 or driver is None:
                        if driver:
                            print(f'🔄 Restarting browser session...')
                            try:
                                driver.quit()
                            except:
                                pass
                            time.sleep(5)
                        
                        print(f'🚀 Starting new browser session...')
                        driver = create_driver_session()
                        print('🔗 Connected to Bright Data')
                        
                        # Load Booking.com
                        print('🌐 Loading Booking.com...')
                        driver.get('https://www.booking.com/?cc1=co&selected_currency=COP')
                        
                        if not wait_for_page_load(driver):
                            raise Exception("Page failed to load")
                        
                        time.sleep(5)
                        ensure_no_blocking_modals(driver)
                        print('✅ Page ready')
                    
                    print(f'\n📅 Date {date_idx + 1}/{len(dates_list)}: {checkin_date} → {checkout_date}')
                    
                    # Check WebSocket connection
                    try:
                        driver.current_url
                    except Exception as e:
                        if "cdp_ws_error" in str(e) or "WebSocket" in str(e):
                            print('🔌 WebSocket lost, restarting...')
                            driver = None
                            continue
                        else:
                            raise e
                                        
                    # Step 1: Search for hotel
                    if not search_and_click_on_hotel(driver, hotel_name):
                        print(f'❌ Hotel search failed')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': None,
                            'error': 'Hotel search failed',
                            'availability': 'Search failed'
                        })
                        continue
                    
                    # Step 2: Select dates
                    if not select_checkin_and_checkout_dates(driver, checkin_date, checkout_date):
                        print(f'❌ Date selection failed')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': None,
                            'error': 'Date selection failed',
                            'availability': 'Date selection failed'
                        })
                        continue
                    
                    # Step 3: Click search
                    if not click_on_search_button(driver):
                        print(f'❌ Search execution failed')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': None,
                            'error': 'Search execution failed',
                            'availability': 'Search failed'
                        })
                        continue
                    
                    # Step 4: Check availability and extract price
                    is_available, availability_message = check_hotel_availability(driver)
                    
                    if not is_available:
                        print(f'❌ Not available: {availability_message}')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': None,
                            'error': f'Not available: {availability_message}',
                            'availability': 'Not available'
                        })
                    else:
                        # Extract price
                        price = extract_price(driver)
                        if price and 'Not available' not in str(price):
                            print(f'✅ Completed: {price}')
                            hotel_results.append({
                                'hotel_name': hotel_name,
                                'checkin': str(checkin_date),
                                'checkout': str(checkout_date),
                                'price': price,
                                'error': None,
                                'availability': 'Available'
                            })
                        else:
                            print(f'❌ Price extraction failed')
                            hotel_results.append({
                                'hotel_name': hotel_name,
                                'checkin': str(checkin_date),
                                'checkout': str(checkout_date),
                                'price': None,
                                'error': 'Price extraction failed',
                                'availability': 'Price extraction failed'
                            })
                    
                    search_count += 1
                    
                    # Wait between searches
                    if date_idx < len(dates_list) - 1:
                        print('⏸️ Waiting...')
                        time.sleep(3)
                
                except Exception as e:
                    error_msg = str(e)
                    print(f'❌ Error: {error_msg}')
                    
                    if "cdp_ws_error" in error_msg or "WebSocket" in error_msg:
                        driver = None
                    
                    hotel_results.append({
                        'hotel_name': hotel_name,
                        'checkin': str(checkin_date),
                        'checkout': str(checkout_date),
                        'price': None,
                        'error': f'Exception: {error_msg}',
                        'availability': 'Error'
                    })
            
            # Add this hotel's results to all results
            all_results.extend(hotel_results)
            
            # Print summary for this hotel
            successful = len([r for r in hotel_results if r['price'] is not None])
            print(f'\n📊 Summary for {hotel_name}:')
            print(f'   ✅ Successful: {successful}/{len(hotel_results)}')
            print(f'   ❌ Failed: {len(hotel_results) - successful}/{len(hotel_results)}')
            
        except Exception as e:
            print(f'❌ Critical error for {hotel_name}: {str(e)}')
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
        
        # Wait between hotels
        if hotel_idx < len(hotel_names) - 1:
            print(f'\n⏸️ Waiting before next hotel...')
            time.sleep(10)
    
    return all_results

if __name__ == "__main__":
    results = scrape_hotel_prices_from_booking_com()
    if results:
        # Save to CSV instead of JSON
        main_csv, detailed_csv = save_results_to_csv(results)
        summary_csv = create_price_summary_csv(results)
        
        # Print final summary
        hotels = list(set([r['hotel_name'] for r in results]))
        total_searches = len(results)
        successful = len([r for r in results if r['price'] is not None and 'Not available' not in str(r['price'])])
        
        print(f'\n🎉 FINAL SUMMARY:')
        print(f'📊 Hotels processed: {len(hotels)}')
        print(f'📊 Total searches: {total_searches}')
        print(f'📊 Successful: {successful}')
        print(f'📊 Failed: {total_searches - successful}')
        print(f'📊 Success rate: {(successful/total_searches*100):.1f}%')
        
        print(f'\n📋 Results by hotel:')
        for hotel in hotels:
            hotel_results = [r for r in results if r['hotel_name'] == hotel]
            hotel_successful = len([r for r in hotel_results if r['price'] is not None and 'Not available' not in str(r['price'])])
            print(f'   🏨 {hotel}: {hotel_successful}/{len(hotel_results)} successful')
        
        print(f'\n📁 FILES CREATED:')
        if main_csv:
            print(f'   📊 Main CSV (matrix format): {main_csv}')
        if detailed_csv:
            print(f'   📋 Detailed CSV (row format): {detailed_csv}')
        if summary_csv:
            print(f'   📈 Summary CSV (statistics): {summary_csv}')
        
        print('\n✅ Scraping completed!')
    else:
        print('\n❌ No results to save')