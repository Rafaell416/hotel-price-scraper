"""
Date calculation utilities for hotel price scraper
"""

from datetime import datetime, timedelta


def calculate_dates(days=2):
    """
    Calculate check-in and check-out date pairs for the next N days
    
    Args:
        days (int): Number of days to calculate from today (default: 2 for testing, 30 for production)
    
    Returns:
        list: List of (checkin_date, checkout_date) tuples
    """
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        checkin_date = current_date
        checkout_date = current_date + timedelta(days=1)
        dates.append((checkin_date, checkout_date))
        current_date += timedelta(days=1)
    
    return dates 