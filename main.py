#!/usr/bin/env python3
"""
Hotel Price Scraper - Main Entry Point

A command-line tool for scraping hotel prices from Booking.com with retry functionality.
"""

import sys
import time

from src.cli import parse_arguments
from src.scraper import scrape_hotels_with_args
from src.data import (
    save_results_to_json,
    load_failed_searches_from_json,
    update_json_with_results,
    scrape_specific_dates
)


def handle_retry_mode(args):
    """
    Handle retry mode for failed searches
    
    Args:
        args: Parsed command line arguments with retry file path
    """
    print(f'🔄 RETRY MODE')
    print(f'   📁 JSON file: {args.retry}')
    
    # Load failed searches from JSON
    original_json_data, failed_searches = load_failed_searches_from_json(args.retry)
    
    if not original_json_data:
        print('❌ Could not load JSON file')
        return
    
    if not failed_searches:
        print('✅ No failed searches found - all searches were successful!')
        return
    
    # Group failed searches by hotel
    hotels_to_retry = {}
    for search in failed_searches:
        hotel_name = search['hotel_name']
        if hotel_name not in hotels_to_retry:
            hotels_to_retry[hotel_name] = []
        hotels_to_retry[hotel_name].append(search)
    
    print(f'\n🎯 Will retry {len(failed_searches)} searches across {len(hotels_to_retry)} hotels')
    
    all_retry_results = []
    
    # Process each hotel
    for hotel_idx, (hotel_name, hotel_failed) in enumerate(hotels_to_retry.items()):
        print(f'\n{"="*60}')
        print(f'🔄 RETRY HOTEL {hotel_idx + 1}/{len(hotels_to_retry)}: {hotel_name}')
        print(f'🔄 Retrying {len(hotel_failed)} failed searches')
        print(f'{"="*60}')
        
        retry_results = scrape_specific_dates(hotel_name, hotel_failed)
        all_retry_results.extend(retry_results)
        
        # Wait between hotels
        if hotel_idx < len(hotels_to_retry) - 1:
            print(f'\n⏸️ Waiting before next hotel...')
            time.sleep(10)
    
    # Update the original JSON file with retry results
    if all_retry_results:
        success = update_json_with_results(original_json_data, all_retry_results, args.retry)
        
        if success:
            # Print retry summary
            successful_retries = len([r for r in all_retry_results 
                                    if r['price'] is not None and 'Not available' not in str(r['price'])])
            
            print(f'\n🎉 RETRY SUMMARY:')
            print(f'📊 Total retry attempts: {len(all_retry_results)}')
            print(f'✅ Successful: {successful_retries}')
            print(f'❌ Still failed: {len(all_retry_results) - successful_retries}')
            print(f'📈 Retry success rate: {(successful_retries/len(all_retry_results)*100):.1f}%')
            print(f'💾 Updated file: {args.retry}')
            print('\n✅ Retry completed!')
        else:
            print('\n❌ Failed to update JSON file')
    else:
        print('\n❌ No retry results to save')


def handle_normal_mode(args):
    """
    Handle normal scraping mode
    
    Args:
        args: Parsed command line arguments
    """
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


def main():
    """
    Main entry point for the hotel price scraper
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Handle different modes
        if args.retry:
            handle_retry_mode(args)
        else:
            handle_normal_mode(args)
            
    except KeyboardInterrupt:
        print('\n\n⚠️ Scraping interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Unexpected error: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    main() 