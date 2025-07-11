"""
Data storage operations for hotel price scraper
"""

import os
import json
from datetime import datetime

from ..utils.files import clean_filename


def save_results_to_json(results, hotel_name=None):
    """
    Save results to JSON file with simplified structure inside outputs folder
    
    Args:
        results (list): List of scraping results
        hotel_name (str, optional): Hotel name for single hotel mode
        
    Returns:
        str or None: Path to saved JSON file or None if failed
    """
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
            json_data = _create_single_hotel_json(results, unique_hotels[0])
        else:
            json_data = _create_multiple_hotels_json(results)
        
        # Save JSON file
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f'💾 JSON saved: {json_filename}')
        
        # Print JSON summary
        _print_json_summary(json_data, is_single_hotel)
        
        return json_filename
        
    except Exception as e:
        print(f'❌ Error saving JSON: {str(e)}')
        return None


def _create_single_hotel_json(results, hotel_name_key):
    """Create JSON structure for single hotel"""
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
    return {
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


def _create_multiple_hotels_json(results):
    """Create JSON structure for multiple hotels"""
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
    return {
        'metadata': {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_hotels': len(hotels_data),
            'total_searches': len(results),
            'total_successful': sum(h['summary']['successful_prices'] for h in hotels_data.values()),
            'overall_success_rate': (sum(h['summary']['successful_prices'] for h in hotels_data.values()) / len(results)) * 100 if results else 0
        },
        'hotels': hotels_data
    }


def _print_json_summary(json_data, is_single_hotel):
    """Print summary of saved JSON data"""
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