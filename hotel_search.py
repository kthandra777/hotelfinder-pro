import os
import logging
import requests
import random
import re
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from kayak import kayak_hotels, _generate_kayak_url

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _generate_booking_url(location_query: str, check_in_date: str, check_out_date: str, num_adults: int = 2) -> str:
    """Generate a URL for Booking.com hotel search"""
    formatted_location = location_query.lower().replace(" ", "-")
    return f"https://www.booking.com/searchresults.html?ss={formatted_location}&checkin_year_month_monthday={check_in_date}&checkout_year_month_monthday={check_out_date}&group_adults={num_adults}"

def booking_com_search(location: str, check_in_date: str, check_out_date: str, num_adults: int = 2):
    """
    Use Selenium WebDriver to scrape hotel data from Booking.com.
    """
    url = _generate_booking_url(location, check_in_date, check_out_date, num_adults)
    logging.info(f"Searching hotels on Booking.com using URL: {url}")

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Add headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')

        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        # Set longer timeout and get the page
        driver.set_page_load_timeout(30)
        driver.get(url)
        
        # Longer wait time for prices to load
        sleep(random.uniform(5, 7))

        # Scroll slowly with random pauses
        for i in range(4):
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 400)})")
            sleep(random.uniform(1.5, 2.5))

        # Wait for hotel elements to load
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="property-card"]')))
            # Additional wait for prices
            sleep(random.uniform(2, 3))
        except:
            logging.warning("Timeout waiting for property cards to load")

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        hotels = []

        # Updated selectors for Booking.com's current structure
        property_cards = soup.select('div[data-testid="property-card"]')
        if not property_cards:
            property_cards = soup.select('.sr_property_block')  # Fallback selector

        for item in property_cards:
            try:
                hotel_data = {}
                
                # Try multiple possible selectors for each field
                name_element = (
                    item.select_one('div[data-testid="title"]') or 
                    item.select_one('.sr-hotel__name') or
                    item.select_one('span[data-testid="title"]')
                )

                # Updated price selectors
                price_element = (
                    item.select_one('[data-testid="price-and-discounted-price"]') or
                    item.select_one('[data-testid="price"]') or
                    item.select_one('.bui-price-display__value') or
                    item.select_one('.prco-valign-middle-helper') or
                    item.select_one('[data-testid="price-primary"]') or
                    item.select_one('.bui-f-color-constructive') or
                    item.select_one('.prco-inline-block-maker-helper') or
                    item.select_one('div[data-testid="price-per-night"]')
                )

                rating_element = (
                    item.select_one('div[data-testid="review-score"]') or
                    item.select_one('div[data-testid="rating"]') or
                    item.select_one('div[aria-label*="Scored"]') or
                    item.select_one('.bui-review-score__badge') or
                    item.select_one('.review-score-badge')
                )

                if name_element:
                    hotel_data['name'] = name_element.text.strip()

                if price_element:
                    price_text = price_element.text.strip()
                    # Extract price value more flexibly
                    price_match = re.search(r'[\d,]+', price_text)
                    if price_match:
                        price_digits = price_match.group().replace(',', '')
                        try:
                            price_num = float(price_digits)
                            price_text = f"₹{price_num:,.0f}"
                            hotel_data['price'] = price_text
                        except:
                            hotel_data['price'] = price_text

                if rating_element:
                    rating_text = rating_element.text.strip()
                    if rating_text:
                        try:
                            # Extract numeric rating more flexibly
                            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                            if rating_match:
                                rating_num = float(rating_match.group(1))
                                rating_text = f"Scored {rating_num}"
                            hotel_data['rating'] = rating_text
                        except:
                            hotel_data['rating'] = rating_text

                hotel_data['source'] = 'Booking.com'
                hotel_data['booking_link'] = url

                if hotel_data.get('name') and (hotel_data.get('price') or hotel_data.get('rating')):
                    hotels.append(hotel_data)

            except Exception as e:
                logging.warning(f"Error processing hotel item: {str(e)}")
                continue

        if hotels:
            logging.info(f"Found {len(hotels)} hotels on Booking.com")
            logging.debug(f"Sample hotel data: {hotels[0] if hotels else None}")
        else:
            logging.warning("No hotels found on Booking.com.")

        return hotels

    except Exception as e:
        logging.error(f"Booking.com search error: {str(e)}", exc_info=True)
        return []

def search_hotels(location: str, check_in_date: Optional[str] = None, check_out_date: Optional[str] = None, num_adults: int = 2, api_keys: Optional[Dict[str, str]] = None):
    """
    Search for hotels on multiple sites and combine results.
    
    Args:
        location (str): Location to search for hotels
        check_in_date (str): Check-in date in YYYY-MM-DD format
        check_out_date (str): Check-out date in YYYY-MM-DD format
        num_adults (int): Number of adults
        api_keys (dict): Dictionary containing API keys
        
    Returns:
        list: Combined list of hotel results sorted by rating and price
    """
    # Set default dates if none provided
    if not check_in_date:
        check_in_date = datetime.now().strftime("%Y-%m-%d")
    if not check_out_date:
        # Default to check-out one day after check-in
        check_out_obj = datetime.strptime(check_in_date, "%Y-%m-%d") + timedelta(days=1)
        check_out_date = check_out_obj.strftime("%Y-%m-%d")
    
    # Set API keys if provided  
    if api_keys:
        if "BROWSERBASE_KEY" in api_keys:
            os.environ["BROWSERBASE_API_KEY"] = api_keys["BROWSERBASE_KEY"]
        if "BROWSERBASE_PROJECT_ID" in api_keys:
            os.environ["BROWSERBASE_PROJECT_ID"] = api_keys["BROWSERBASE_PROJECT_ID"]
        if "GROQ_API_KEY" in api_keys:
            os.environ["GROQ_API_KEY"] = api_keys["GROQ_API_KEY"]
            
    # Get results from both sources
    try:
        # Get Kayak results using the kayak_hotels function from kayak.py
        # This will always return mock data without requiring API keys
        kayak_results = kayak_hotels(location, check_in_date, check_out_date, num_adults)
        logging.info(f"Got {len(kayak_results)} results from Kayak")
    except Exception as e:
        logging.error(f"Error getting Kayak results: {str(e)}")
        kayak_results = []
    
    try:
        booking_results = booking_com_search(location, check_in_date, check_out_date, num_adults)
    except Exception as e:
        logging.error(f"Error getting Booking.com results: {str(e)}")
        booking_results = []

    # Normalize ratings for both sources to a 5-point scale
    for hotel in kayak_results:
        try:
            if 'rating' in hotel and not hotel.get('rating_normalized'):
                # Try to extract a numeric rating
                rating_text = str(hotel['rating'])
                match = re.search(r"(\d+\.?\d*)", rating_text)
                if match:
                    rating_num = float(match.group(1))
                    # Kayak ratings are usually out of 10 or 5
                    if rating_num > 5:  # Assume it's out of 10
                        hotel['rating_normalized'] = rating_num / 2
                    else:  # Assume it's already out of 5
                        hotel['rating_normalized'] = rating_num
                else:
                    hotel['rating_normalized'] = 3.0  # Default if we can't parse
        except (ValueError, TypeError) as e:
            logging.warning(f"Error normalizing Kayak rating: {str(e)}")
            hotel['rating_normalized'] = 3.0  # Default middle rating

    for hotel in booking_results:
        try:
            if 'rating' in hotel and not hotel.get('rating_normalized'):
                # Try to extract a numeric rating
                rating_text = str(hotel['rating'])
                match = re.search(r"(\d+\.?\d*)", rating_text)
                if match:
                    rating_num = float(match.group(1))
                    # Booking.com ratings are usually out of 10
                    if rating_num > 5:  # Assume it's out of 10
                        hotel['rating_normalized'] = rating_num / 2
                    else:  # Assume it's already out of 5
                        hotel['rating_normalized'] = rating_num
                else:
                    hotel['rating_normalized'] = 3.0  # Default if we can't parse
        except (ValueError, TypeError) as e:
            logging.warning(f"Error normalizing Booking.com rating: {str(e)}")
            hotel['rating_normalized'] = 3.0  # Default middle rating

    # Normalize prices for consistent comparison
    def normalize_price(price_str):
        if not price_str:
            return float('inf')
        try:
            # Remove currency symbols and convert to float
            price_text = str(price_str)
            price = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price)
        except (ValueError, TypeError):
            return float('inf')

    # Add source and normalize prices for both result sets
    for hotel in kayak_results:
        if not hotel.get('source'):
            hotel['source'] = 'Kayak'
        if 'price' in hotel and not hotel.get('price_value'):
            hotel['price_value'] = normalize_price(hotel['price'])

    for hotel in booking_results:
        if not hotel.get('source'):
            hotel['source'] = 'Booking.com'
        if 'price' in hotel and not hotel.get('price_value'):
            hotel['price_value'] = normalize_price(hotel['price'])

    # Combine results while preserving source information
    all_results = []
    all_results.extend([h for h in booking_results if isinstance(h, dict) and 'name' in h])
    all_results.extend([h for h in kayak_results if isinstance(h, dict) and 'name' in h])

    # Debug the results
    logging.info(f"Combined {len(all_results)} results: {len(booking_results)} from Booking.com and {len(kayak_results)} from Kayak")
    
    # Sort combined results by rating (normalized) and price
    all_results.sort(key=lambda x: (-x.get('rating_normalized', 0), x.get('price_value', float('inf'))))

    # Add rank information
    for i, hotel in enumerate(all_results, 1):
        hotel['rank'] = i

    return all_results 