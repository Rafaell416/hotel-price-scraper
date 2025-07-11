"""
File utilities for hotel price scraper
"""

import re


def clean_filename(text):
    """
    Clean text to make it safe for filenames
    
    Args:
        text (str): Original text
        
    Returns:
        str: Cleaned filename-safe text
    """
    # Replace spaces with underscores and remove special characters
    cleaned = re.sub(r'[^\w\s-]', '', text)
    cleaned = re.sub(r'[-\s]+', '_', cleaned)
    return cleaned.lower()


def load_hotel_names(filename='hotel_names.txt'):
    """
    Load hotel names from text file (one hotel per line)
    
    Args:
        filename (str): Path to the hotel names file
        
    Returns:
        list: List of valid hotel names
    """
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


def load_hotel_names_from_args(args):
    """
    Load hotel names based on command line arguments
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        list: List of hotel names to process
    """
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