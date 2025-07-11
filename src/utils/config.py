"""
Configuration management for hotel price scraper
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_webdriver_url():
    """Get the Bright Data WebDriver URL from environment variables"""
    username = os.environ.get("BRIGHT_DATA_USERNAME")
    password = os.environ.get("BRIGHT_DATA_PASSWORD")
    host = os.environ.get("BRIGHT_DATA_HOST")
    port = os.environ.get("BRIGHT_DATA_PORT")
    
    if not all([username, password, host, port]):
        raise ValueError("❌ Missing required environment variables")
    
    auth = f'{username}:{password}'
    return f'https://{auth}@{host}:{port}'


def get_scraper_settings():
    """Get scraper configuration settings"""
    return {
        'max_searches_per_session': 6,
        'page_load_timeout': 60,
        'implicit_wait': 20,
        'search_delay': 3,
        'hotel_delay': 10,
        'session_restart_delay': 5,
        'country': 'co',
        'language': 'es-CO',
        'currency': 'COP'
    } 