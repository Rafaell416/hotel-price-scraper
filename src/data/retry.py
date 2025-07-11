"""
Retry functionality for failed hotel price searches
"""

import os
import json
from datetime import datetime

from ..scraper.core import scrape_single_hotel


def load_failed_searches_from_json(json_file_path):
    """
    Load failed searches from existing JSON file
    
    Args:
        json_file_path (str): Path to the JSON file
        
    Returns:
        tuple: (original_json_data, failed_searches)
    """
    try:
        if not os.path.exists(json_file_path):
            print(f'❌ JSON file not found: {json_file_path}')
            return None, []
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        failed_searches = []
        hotel_name = None
        
        # Check if it's single hotel or multiple hotels structure
        if 'hotel_name' in data:
            # Single hotel structure
            hotel_name = data['hotel_name']
            searches = data.get('searches', [])
            
            for search in searches:
                if _is_search_failed(search):
                    failed_searches.append({
                        'hotel_name': hotel_name,
                        'checkin_date': search['checkin_date'],
                        'checkout_date': search['checkout_date'],
                        'original_error': search.get('error'),
                        'original_availability': search.get('availability')
                    })
        
        elif 'hotels' in data:
            # Multiple hotels structure
            hotels = data.get('hotels', {})
            
            for hotel_key, hotel_data in hotels.items():
                hotel_name = hotel_data.get('hotel_name', hotel_key)
                searches = hotel_data.get('searches', [])
                
                for search in searches:
                    if _is_search_failed(search):
                        failed_searches.append({
                            'hotel_name': hotel_name,
                            'checkin_date': search['checkin_date'],
                            'checkout_date': search['checkout_date'],
                            'original_error': search.get('error'),
                            'original_availability': search.get('availability')
                        })
        
        print(f'📖 Loaded JSON file: {json_file_path}')
        print(f'🔍 Found {len(failed_searches)} failed searches to retry')
        
        if failed_searches:
            print(f'\n📋 Failed searches to retry:')
            for i, search in enumerate(failed_searches, 1):
                print(f'   {i}. {search["hotel_name"]} - {search["checkin_date"]} → {search["checkout_date"]} '
                      f'(was: {search["original_availability"]})')
        
        return data, failed_searches
        
    except Exception as e:
        print(f'❌ Error loading JSON file: {str(e)}')
        return None, []


def _is_search_failed(search):
    """
    Determine if a search is considered failed and should be retried
    
    Args:
        search (dict): Search result dictionary
        
    Returns:
        bool: True if search failed, False otherwise
    """
    # Consider a search failed if:
    # 1. It has an error (technical failure)
    # 2. Price is None and availability indicates failure (not just "Not available")
    return (
        search.get('error') is not None or
        (search.get('price') is None and 
         search.get('availability') in ['Search failed', 'Date selection failed', 'Price extraction failed', 'Error'])
    )


def update_json_with_results(original_json_data, retry_results, json_file_path):
    """
    Update the original JSON file with retry results
    
    Args:
        original_json_data (dict): Original JSON data
        retry_results (list): List of retry results
        json_file_path (str): Path to the JSON file
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        if not retry_results:
            print('❌ No retry results to update')
            return False
        
        # Create a lookup dictionary for quick access to retry results
        retry_lookup = {}
        for result in retry_results:
            key = f"{result['hotel_name']}_{result['checkin']}_{result['checkout']}"
            retry_lookup[key] = result
        
        updated_count = 0
        
        # Update the JSON data structure
        if 'hotel_name' in original_json_data:
            updated_count = _update_single_hotel_json(original_json_data, retry_lookup)
        elif 'hotels' in original_json_data:
            updated_count = _update_multiple_hotels_json(original_json_data, retry_lookup)
        
        # Save the updated JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(original_json_data, f, indent=2, ensure_ascii=False)
        
        print(f'✅ Updated {updated_count} searches in {json_file_path}')
        return True
        
    except Exception as e:
        print(f'❌ Error updating JSON file: {str(e)}')
        return False


def _update_single_hotel_json(json_data, retry_lookup):
    """Update single hotel JSON structure with retry results"""
    updated_count = 0
    searches = json_data.get('searches', [])
    
    for search in searches:
        key = f"{json_data['hotel_name']}_{search['checkin_date']}_{search['checkout_date']}"
        
        if key in retry_lookup:
            retry_result = retry_lookup[key]
            # Update the search entry
            search['price'] = retry_result['price']
            search['availability'] = retry_result['availability']
            search['error'] = retry_result['error']
            search['timestamp'] = datetime.now().isoformat()
            updated_count += 1
    
    # Recalculate summary statistics
    _recalculate_summary_stats(json_data, searches)
    
    return updated_count


def _update_multiple_hotels_json(json_data, retry_lookup):
    """Update multiple hotels JSON structure with retry results"""
    updated_count = 0
    hotels = json_data.get('hotels', {})
    
    for hotel_key, hotel_data in hotels.items():
        searches = hotel_data.get('searches', [])
        
        for search in searches:
            key = f"{hotel_data['hotel_name']}_{search['checkin_date']}_{search['checkout_date']}"
            
            if key in retry_lookup:
                retry_result = retry_lookup[key]
                # Update the search entry
                search['price'] = retry_result['price']
                search['availability'] = retry_result['availability']
                search['error'] = retry_result['error']
                search['timestamp'] = datetime.now().isoformat()
                updated_count += 1
        
        # Recalculate summary for this hotel
        _recalculate_summary_stats(hotel_data, searches)
    
    # Update overall metadata
    total_successful = sum(h['summary']['successful_prices'] for h in hotels.values())
    total_searches = json_data['metadata']['total_searches']
    json_data['metadata']['total_successful'] = total_successful
    json_data['metadata']['overall_success_rate'] = (total_successful / total_searches * 100) if total_searches > 0 else 0
    json_data['metadata']['last_updated'] = datetime.now().isoformat()
    
    return updated_count


def _recalculate_summary_stats(data_container, searches):
    """Recalculate summary statistics for a hotel"""
    summary = data_container.get('summary', {})
    summary['successful_prices'] = len([s for s in searches if s.get('price') and 'Not available' not in str(s.get('price'))])
    summary['not_available'] = len([s for s in searches if s.get('availability') == 'Not available'])
    summary['errors'] = len([s for s in searches if s.get('error') is not None])
    
    if summary.get('total_searches', 0) > 0:
        summary['success_rate'] = (summary['successful_prices'] / summary['total_searches']) * 100
    
    # Recalculate price statistics
    prices = []
    for search in searches:
        if search.get('price') and 'Not available' not in str(search.get('price')):
            try:
                price_str = str(search['price']).replace('COP', '').replace(',', '').strip()
                price_num = float(''.join(filter(str.isdigit, price_str)))
                prices.append(price_num)
            except:
                pass
    
    summary['prices'] = prices
    if prices:
        summary['min_price'] = min(prices)
        summary['max_price'] = max(prices)
        summary['avg_price'] = sum(prices) / len(prices)
    
    # Update metadata if it exists
    if 'metadata' in data_container:
        data_container['metadata']['total_successful'] = summary['successful_prices']
        data_container['metadata']['overall_success_rate'] = summary['success_rate']
        data_container['metadata']['last_updated'] = datetime.now().isoformat()


def scrape_specific_dates(hotel_name, failed_searches):
    """
    Scrape specific hotel and date combinations for retry
    
    Args:
        hotel_name (str): Name of the hotel
        failed_searches (list): List of failed search dictionaries
        
    Returns:
        list: List of retry results
    """
    if not failed_searches:
        return []
    
    # Filter failed searches for this hotel
    hotel_failed = [fs for fs in failed_searches if fs['hotel_name'] == hotel_name]
    
    if not hotel_failed:
        return []
    
    print(f'🚀 Retrying {len(hotel_failed)} failed searches for {hotel_name}')
    
    # Convert failed searches to date tuples
    dates_list = []
    for failed_search in hotel_failed:
        try:
            checkin_date = datetime.strptime(failed_search['checkin_date'], '%Y-%m-%d').date()
            checkout_date = datetime.strptime(failed_search['checkout_date'], '%Y-%m-%d').date()
            dates_list.append((checkin_date, checkout_date))
        except Exception as e:
            print(f'❌ Error parsing dates for {failed_search}: {e}')
            continue
    
    if not dates_list:
        print(f'❌ No valid dates found for {hotel_name}')
        return []
    
    # Use the existing single hotel scraper
    return scrape_single_hotel(hotel_name, dates_list) 