"""
Core scraping orchestration for hotel price scraper
"""

import time

from .driver import create_driver_session, wait_for_page_load, ensure_no_blocking_modals
from .booking import (
    search_and_click_on_hotel, 
    select_checkin_and_checkout_dates, 
    click_on_search_button,
    extract_price, 
    check_hotel_availability
)
from ..utils.config import get_scraper_settings
from ..utils.dates import calculate_dates
from ..utils.files import load_hotel_names_from_args


def scrape_single_hotel(hotel_name, dates_list):
    """
    Scrape prices for a single hotel across all provided dates
    
    Args:
        hotel_name (str): Name of the hotel to scrape
        dates_list (list): List of (checkin_date, checkout_date) tuples
        
    Returns:
        list: List of result dictionaries
    """
    print(f'🚀 Starting hotel: {hotel_name} with {len(dates_list)} dates')
    
    settings = get_scraper_settings()
    hotel_results = []
    driver = None
    search_count = 0
    
    try:
        # Process each date for this hotel
        for date_idx, (checkin_date, checkout_date) in enumerate(dates_list):
            try:
                # Create new session if needed
                if search_count % settings['max_searches_per_session'] == 0 or driver is None:
                    if driver:
                        print(f'🔄 [{hotel_name}] Restarting browser session...')
                        try:
                            driver.quit()
                        except:
                            pass
                        time.sleep(settings['session_restart_delay'])
                    
                    print(f'🚀 [{hotel_name}] Starting new browser session...')
                    driver = create_driver_session()
                    print(f'🔗 [{hotel_name}] Connected to Bright Data')
                    
                    # Load Booking.com
                    print(f'🌐 [{hotel_name}] Loading Booking.com...')
                    driver.get(f'https://www.booking.com/?cc1={settings["country"]}&selected_currency={settings["currency"]}')
                    
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
                        'error': None,  # No error - just unavailable
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
                            'error': 'Price extraction failed',
                            'availability': 'Price extraction failed'
                        })
                
                search_count += 1
                
                # Wait between searches
                if date_idx < len(dates_list) - 1:
                    print('⏸️ Waiting...')
                    print('\n')
                    time.sleep(settings['search_delay'])
            
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
                    'error': f'Exception: {error_msg}',
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
    """
    Main scraping function that uses command line arguments
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        list: List of all scraping results
    """
    settings = get_scraper_settings()
    
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
        
        hotel_results = scrape_single_hotel(hotel_name, dates_list)
        all_results.extend(hotel_results)
        
        # Wait between hotels (if multiple)
        if hotel_idx < len(hotel_names) - 1:
            print(f'\n⏸️ Waiting before next hotel...')
            time.sleep(settings['hotel_delay'])
    
    return all_results 