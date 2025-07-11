from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from dotenv import load_dotenv

import time
import os
import argparse
import re
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
    end_date = start_date + timedelta(days=2) #30
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

def clean_filename(text):
    """Clean text to make it safe for filenames"""
    # Replace spaces with underscores and remove special characters
    cleaned = re.sub(r'[^\w\s-]', '', text)
    cleaned = re.sub(r'[-\s]+', '_', cleaned)
    return cleaned.lower()

def save_results_to_json(results, hotel_name=None):
    """Save results to JSON file with simplified structure inside outputs folder"""
    try:
        if not results:
            print('❌ No results to save to JSON')
            return None
        
        # Create outputs folder if it doesn't exist
        output_folder = 'outputs'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f'📁 Created outputs folder: {output_folder}')
        
        # Create JSON filename with timestamp and hotel name if provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if hotel_name:
            clean_hotel_name = clean_filename(hotel_name)
            json_filename = os.path.join(output_folder, f'{clean_hotel_name}_{timestamp}.json')
        else:
            json_filename = os.path.join(output_folder, f'hotel_prices_{timestamp}.json')
        
        # Check if it's a single hotel or multiple hotels
        unique_hotels = list(set([r['hotel_name'] for r in results]))
        is_single_hotel = len(unique_hotels) == 1
        
        if is_single_hotel:
            # Simplified structure for single hotel
            hotel_name_key = unique_hotels[0]
            searches = []
            summary = {
                'total_searches': 0,
                'successful_prices': 0,
                'not_available': 0,
                'errors': 0,
                'success_rate': 0.0,
                'prices': []
            }
            
            for result in results:
                # Add search result
                search_data = {
                    'checkin_date': result['checkin'],
                    'checkout_date': result['checkout'],
                    'date_range': f"{result['checkin']} → {result['checkout']}",
                    'price': result['price'],
                    'availability': result['availability'],
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                }
                
                searches.append(search_data)
                
                # Update summary statistics
                summary['total_searches'] += 1
                
                if result['price'] and 'Not available' not in str(result['price']):
                    summary['successful_prices'] += 1
                    # Extract numeric price for statistics
                    try:
                        price_str = str(result['price']).replace('COP', '').replace(',', '').strip()
                        price_num = float(''.join(filter(str.isdigit, price_str)))
                        summary['prices'].append(price_num)
                    except:
                        pass
                elif result['availability'] == 'Not available':
                    summary['not_available'] += 1
                else:
                    summary['errors'] += 1
            
            # Calculate final statistics
            if summary['total_searches'] > 0:
                summary['success_rate'] = (summary['successful_prices'] / summary['total_searches']) * 100
            
            if summary['prices']:
                summary['min_price'] = min(summary['prices'])
                summary['max_price'] = max(summary['prices'])
                summary['avg_price'] = sum(summary['prices']) / len(summary['prices'])
            else:
                summary['min_price'] = None
                summary['max_price'] = None
                summary['avg_price'] = None
            
            # Create simplified JSON structure for single hotel
            json_data = {
                'metadata': {
                    'scrape_timestamp': datetime.now().isoformat(),
                    'hotel_name': hotel_name_key,
                    'total_searches': len(results),
                    'total_successful': summary['successful_prices'],
                    'overall_success_rate': summary['success_rate']
                },
                'hotel_name': hotel_name_key,
                'searches': searches,
                'summary': summary
            }
            
        else:
            # Keep nested structure for multiple hotels
            hotels_data = {}
            
            for result in results:
                hotel_name_key = result['hotel_name']
                if hotel_name_key not in hotels_data:
                    hotels_data[hotel_name_key] = {
                        'hotel_name': hotel_name_key,
                        'searches': [],
                        'summary': {
                            'total_searches': 0,
                            'successful_prices': 0,
                            'not_available': 0,
                            'errors': 0,
                            'success_rate': 0.0,
                            'prices': []
                        }
                    }
                
                # Add search result
                search_data = {
                    'checkin_date': result['checkin'],
                    'checkout_date': result['checkout'],
                    'date_range': f"{result['checkin']} → {result['checkout']}",
                    'price': result['price'],
                    'availability': result['availability'],
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                }
                
                hotels_data[hotel_name_key]['searches'].append(search_data)
                
                # Update summary statistics
                summary = hotels_data[hotel_name_key]['summary']
                summary['total_searches'] += 1
                
                if result['price'] and 'Not available' not in str(result['price']):
                    summary['successful_prices'] += 1
                    # Extract numeric price for statistics
                    try:
                        price_str = str(result['price']).replace('COP', '').replace(',', '').strip()
                        price_num = float(''.join(filter(str.isdigit, price_str)))
                        summary['prices'].append(price_num)
                    except:
                        pass
                elif result['availability'] == 'Not available':
                    summary['not_available'] += 1
                else:
                    summary['errors'] += 1
            
            # Calculate final statistics for each hotel
            for hotel_name_key, hotel_data in hotels_data.items():
                summary = hotel_data['summary']
                if summary['total_searches'] > 0:
                    summary['success_rate'] = (summary['successful_prices'] / summary['total_searches']) * 100
                
                if summary['prices']:
                    summary['min_price'] = min(summary['prices'])
                    summary['max_price'] = max(summary['prices'])
                    summary['avg_price'] = sum(summary['prices']) / len(summary['prices'])
                else:
                    summary['min_price'] = None
                    summary['max_price'] = None
                    summary['avg_price'] = None
            
            # Create nested JSON structure for multiple hotels
            json_data = {
                'metadata': {
                    'scrape_timestamp': datetime.now().isoformat(),
                    'total_hotels': len(hotels_data),
                    'total_searches': len(results),
                    'total_successful': sum(h['summary']['successful_prices'] for h in hotels_data.values()),
                    'overall_success_rate': (sum(h['summary']['successful_prices'] for h in hotels_data.values()) / len(results)) * 100 if results else 0
                },
                'hotels': hotels_data
            }
        
        # Save JSON file
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f'💾 JSON saved: {json_filename}')
        
        # Print JSON summary
        print(f'\n📊 JSON SUMMARY:')
        if is_single_hotel:
            print(f'   🏨 Hotel: {json_data["hotel_name"]}')
            print(f'   📊 Total searches: {json_data["metadata"]["total_searches"]}')
            print(f'   ✅ Successful: {json_data["metadata"]["total_successful"]}')
            print(f'   📈 Success rate: {json_data["metadata"]["overall_success_rate"]:.1f}%')
        else:
            print(f'   🏨 Hotels: {json_data["metadata"]["total_hotels"]}')
            print(f'   📊 Total searches: {json_data["metadata"]["total_searches"]}')
            print(f'   ✅ Successful: {json_data["metadata"]["total_successful"]}')
            print(f'   📈 Success rate: {json_data["metadata"]["overall_success_rate"]:.1f}%')
        
        return json_filename
        
    except Exception as e:
        print(f'❌ Error saving JSON: {str(e)}')
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

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Hotel Price Scraper for Booking.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single hotel
  python main.py --hotel "Hotel Dann Carlton Bogotá"
  
  # Scrape all hotels from file
  python main.py --file hotel_names.txt
  
  # Scrape all hotels from custom file
  python main.py --file my_hotels.txt
        """
    )
    
    # Hotel input options (mutually exclusive)
    hotel_group = parser.add_mutually_exclusive_group(required=True)
    hotel_group.add_argument(
        '--hotel',
        type=str,
        help='Single hotel name to scrape (exact name as it appears on Booking.com)'
    )
    hotel_group.add_argument(
        '--file', '-f',
        type=str,
        help='Path to text file containing hotel names (one per line)'
    )
    
    return parser.parse_args()

def load_hotel_names_from_args(args):
    """Load hotel names based on command line arguments"""
    if args.hotel:
        # Single hotel mode
        print(f'📋 Single hotel mode: {args.hotel}')
        return [args.hotel]
    elif args.file:
        # File mode
        return load_hotel_names(args.file)
    else:
        print('❌ No hotel input specified')
        return []

def scrape_single_hotel_with_args(hotel_name, dates_list):
    """Modified single hotel scraper for command line use"""
    print(f'🚀 Starting hotel: {hotel_name} with {len(dates_list)} dates')
    
    hotel_results = []
    driver = None
    search_count = 0
    max_searches_per_session = 6
    
    try:
        # Process each date for this hotel
        for date_idx, (checkin_date, checkout_date) in enumerate(dates_list):
            try:
                # Create new session if needed
                if search_count % max_searches_per_session == 0 or driver is None:
                    if driver:
                        print(f'🔄 [{hotel_name}] Restarting browser session...')
                        try:
                            driver.quit()
                        except:
                            pass
                        time.sleep(5)
                    
                    print(f'🚀 [{hotel_name}] Starting new browser session...')
                    driver = create_driver_session()
                    print(f'🔗 [{hotel_name}] Connected to Bright Data')
                    
                    # Load Booking.com
                    print(f'🌐 [{hotel_name}] Loading Booking.com...')
                    driver.get('https://www.booking.com/?cc1=co&selected_currency=COP')
                    
                    if not wait_for_page_load(driver):
                        raise Exception("Page failed to load")
                    
                    time.sleep(5)
                    ensure_no_blocking_modals(driver)
                    print(f'✅ [{hotel_name}] Page ready')
                
                print(f'📅 [{hotel_name}] Date {date_idx + 1}/{len(dates_list)}: {checkin_date} → {checkout_date}')
                
                # Check WebSocket connection
                try:
                    driver.current_url
                except Exception as e:
                    if "cdp_ws_error" in str(e) or "WebSocket" in str(e):
                        print(f'🔌 [{hotel_name}] WebSocket lost, restarting...')
                        driver = None
                        continue
                    else:
                        raise e
                
                # Step 1: Search for hotel
                if not search_and_click_on_hotel(driver, hotel_name):
                    print(f'❌ [{hotel_name}] Hotel search failed')
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
                    print(f'❌ [{hotel_name}] Date selection failed')
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
                    print(f'❌ [{hotel_name}] Search execution failed')
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
                    print(f'❌ [{hotel_name}] Not available: {availability_message}')
                    hotel_results.append({
                        'hotel_name': hotel_name,
                        'checkin': str(checkin_date),
                        'checkout': str(checkout_date),
                        'price': None,
                        'error': None,  # ✅ No error - just unavailable
                        'availability': 'Not available'
                    })
                else:
                    # Extract price
                    price = extract_price(driver)
                    if price and 'Not available' not in str(price):
                        print(f'✅ [{hotel_name}] Completed: {price}')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': price,
                            'error': None,
                            'availability': 'Available'
                        })
                    else:
                        print(f'❌ [{hotel_name}] Price extraction failed')
                        hotel_results.append({
                            'hotel_name': hotel_name,
                            'checkin': str(checkin_date),
                            'checkout': str(checkout_date),
                            'price': None,
                            'error': 'Price extraction failed',  # ✅ This IS an error
                            'availability': 'Price extraction failed'
                        })
                
                search_count += 1
                
                # Wait between searches
                if date_idx < len(dates_list) - 1:
                    print('⏸️ Waiting...')
                    print('\n')
                    time.sleep(3)
            
            except Exception as e:
                error_msg = str(e)
                print(f'❌ [{hotel_name}] Error: {error_msg}')
                
                if "cdp_ws_error" in error_msg or "WebSocket" in error_msg:
                    driver = None
                
                hotel_results.append({
                    'hotel_name': hotel_name,
                    'checkin': str(checkin_date),
                    'checkout': str(checkout_date),
                    'price': None,
                    'error': f'Exception: {error_msg}',  # ✅ This IS an error
                    'availability': 'Error'
                })
        
        # Print summary for this hotel
        successful = len([r for r in hotel_results if r['price'] is not None])
        print(f'\n📊 Summary for {hotel_name}:')
        print(f'   ✅ Successful: {successful}/{len(hotel_results)}')
        print(f'   ❌ Failed: {len(hotel_results) - successful}/{len(hotel_results)}')
        
        return hotel_results
        
    except Exception as e:
        print(f'❌ Critical error for {hotel_name}: {str(e)}')
        return hotel_results
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def scrape_hotels_with_args(args):
    """Main scraping function that uses command line arguments"""
    
    # Load hotels and dates
    hotel_names = load_hotel_names_from_args(args)
    if not hotel_names:
        print('❌ No hotels to process')
        return []
    
    dates_list = calculate_dates()
    if not dates_list:
        print('❌ No dates to process')
        return []
    
    print(f'\n🚀 Starting scraper for {len(hotel_names)} hotels × {len(dates_list)} dates = {len(hotel_names) * len(dates_list)} total searches')
    
    all_results = []
    
    # Sequential processing
    for hotel_idx, hotel_name in enumerate(hotel_names):
        print(f'\n{"="*60}')
        print(f'🏨 HOTEL {hotel_idx + 1}/{len(hotel_names)}: {hotel_name}')
        print(f'{"="*60}')
        
        hotel_results = scrape_single_hotel_with_args(hotel_name, dates_list)
        all_results.extend(hotel_results)
        
        # Wait between hotels (if multiple)
        if hotel_idx < len(hotel_names) - 1:
            print(f'\n⏸️ Waiting before next hotel...')
            time.sleep(10)
    
    return all_results

def main():
    """Main function with argument parsing"""
    args = parse_arguments()
    
    # Print configuration
    print(f'🔧 CONFIGURATION:')
    if args.hotel:
        print(f'   🏨 Single hotel: {args.hotel}')
    else:
        print(f'   📁 Hotel file: {args.file}')
    
    # Run the scraper
    results = scrape_hotels_with_args(args)
    
    if results:
        # Save to JSON only
        if args.hotel:
            # Single hotel mode - use hotel name in filename
            json_file = save_results_to_json(results, hotel_name=args.hotel)
        else:
            # Multiple hotels from file - use default naming
            json_file = save_results_to_json(results)
        
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
        
        print(f'\n📁 FILE CREATED:')
        if json_file:
            print(f'   📋 JSON Data: {json_file}')
        
        print('\n✅ Scraping completed!')
    else:
        print('\n❌ No results to save')

if __name__ == "__main__":
    main()