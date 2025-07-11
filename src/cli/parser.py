"""
Command line argument parsing for hotel price scraper
"""

import argparse


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
  
  # Retry failed searches from existing JSON
  python main.py --retry outputs/hotel_dann_carlton_bogota_20241220_143022.json
        """
    )
    
    # Create mutually exclusive group for the main operation modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    # Scraping mode - hotel name
    mode_group.add_argument(
        '--hotel',
        type=str,
        help='Single hotel name to scrape (exact name as it appears on Booking.com)'
    )
    
    # Scraping mode - file with hotels
    mode_group.add_argument(
        '--file', '-f',
        type=str,
        help='Path to text file containing hotel names (one per line)'
    )
    
    # Retry mode
    mode_group.add_argument(
        '--retry', '-r',
        type=str,
        help='Path to existing JSON output file to retry failed searches'
    )
    
    return parser.parse_args() 