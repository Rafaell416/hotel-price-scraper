"""
Booking.com specific interactions for hotel price scraper
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .driver import ensure_no_blocking_modals


def search_and_click_on_hotel(driver, hotel_name):
    """
    Search for a hotel and click on it from autocomplete results
    
    Args:
        driver: WebDriver instance
        hotel_name (str): Name of the hotel to search for
        
    Returns:
        bool: True if hotel was found and selected, False otherwise
    """
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


def open_date_picker(driver):
    """
    Open the date picker
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if date picker opened successfully, False otherwise
    """
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
    """
    Check if the date picker is open and visible
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if date picker is open, False otherwise
    """
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
    """
    Select check-in and check-out dates
    
    Args:
        driver: WebDriver instance
        checkin_date: Check-in date
        checkout_date: Check-out date
        
    Returns:
        bool: True if dates selected successfully, False otherwise
    """
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
    """
    Click on the search button
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if search button clicked successfully, False otherwise
    """
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
    """
    Enhanced price extraction with availability check
    
    Args:
        driver: WebDriver instance
        
    Returns:
        str or None: Extracted price string or None if not found
    """
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
    """
    Separate function to explicitly check hotel availability
    
    Args:
        driver: WebDriver instance
        
    Returns:
        tuple: (is_available: bool, message: str)
    """
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