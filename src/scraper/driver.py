"""
WebDriver management for hotel price scraper
"""

import time
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..utils.config import get_webdriver_url, get_scraper_settings


def create_driver_session():
    """
    Create a new WebDriver session with Bright Data proxy
    
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    settings = get_scraper_settings()
    
    options = ChromeOptions()
    options.set_capability('brd:options', {
        'country': settings['country'],
        'session_id': f'booking_com_{time.time()}',
        'browser_type': 'chrome',
        'keep_alive': True,
        'timeout': 60000
    })

    options.add_argument(f"--lang={settings['language']}")
    options.add_argument(f"--accept-language={settings['language']},es,en")
    
    sbr_webdriver = get_webdriver_url()
    sbr_connection = ChromiumRemoteConnection(
        sbr_webdriver,
        'sbr:browser',
        'goog',
        'chrome'
    )
    
    driver = Remote(sbr_connection, options=options)
    driver.set_page_load_timeout(settings['page_load_timeout'])
    driver.implicitly_wait(settings['implicit_wait'])
    return driver


def wait_for_page_load(driver, timeout=30):
    """
    Wait for page to load completely
    
    Args:
        driver: WebDriver instance
        timeout (int): Maximum wait time in seconds
        
    Returns:
        bool: True if page loaded successfully, False otherwise
    """
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
    """
    Single attempt to close modal
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if modal was closed successfully, False otherwise
    """
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


def ensure_no_blocking_modals(driver):
    """
    Ensure no blocking modals are present
    
    Args:
        driver: WebDriver instance
    """
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