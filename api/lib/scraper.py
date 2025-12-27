import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
from .cache import get_cached_data, set_cached_data

BASE_URL = "https://adventskalender-vs.de/"
AJAX_URL = f"{BASE_URL}wp-admin/admin-ajax.php"

def fetch_winning_numbers_from_origin():
    """Fetch winning numbers directly from the website"""
    try:
        response = requests.get(BASE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        unlocked_windows = soup.find_all('div', class_='unlocked-window')
        winning_numbers = []
        days_info = {}

        for window in unlocked_windows:
            window_classes = window.get('class', [])
            day_number = None
            for cls in window_classes:
                if cls.startswith('window-'):
                    day_number = cls.replace('window-', '')
                    break

            day_elem = window.find('p', class_='single-number')
            display_day = day_elem.get_text(strip=True) if day_elem else day_number

            number_elements = window.find_all('p', class_='numbers')
            day_numbers = [num.get_text(strip=True) for num in number_elements]

            if day_numbers:
                days_info[display_day] = {
                    'numbers': day_numbers,
                    'window_class': f'window-{day_number}' if day_number else None
                }
                winning_numbers.extend(day_numbers)

        return winning_numbers, days_info
    except Exception as e:
        print(f"Origin fetch error: {e}")
        return None, None

def fetch_winning_numbers_cached():
    """Fetch winning numbers with caching"""
    cache_key = "advent_data"
    
    cached = get_cached_data(cache_key)
    if cached:
        print("✅ Cache HIT for numbers")
        return cached

    print("❌ Cache MISS for numbers - fetching from origin")
    winning_numbers, days_info = fetch_winning_numbers_from_origin()

    if winning_numbers is None:
        return None

    cache_data = {
        'winning_numbers': winning_numbers,
        'days_info': days_info,
        'cached_at': datetime.now(timezone.utc).isoformat()
    }

    set_cached_data(cache_key, cache_data)
    return cache_data

def get_prize_info_from_origin(window_class, session=None):
    """Fetch prize information from origin via AJAX"""
    if session is None:
        session = requests.Session()
        
    body = f"action=check_access&target={window_class}"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL.rstrip('/'),
        "Referer": BASE_URL,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = session.post(AJAX_URL, data=body, headers=headers, timeout=10)

        if response.status_code != 200 or not response.text:
            return None

        text = response.text.strip()
        if text == "false":
            return None

        if (text.startswith('"') and text.endswith('"')) or ("\\/" in text):
            try:
                text = json.loads(text)
            except:
                text = text.strip('"').replace("\\/", "/")

        html = f"<table>{text}</table>"
        soup = BeautifulSoup(html, "html.parser")

        prizes = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            prizes.append({
                "number": cols[0].get_text(" ", strip=True),
                "prize": cols[1].get_text(" ", strip=True),
                "value": cols[2].get_text(" ", strip=True),
                "sponsor": cols[3].get_text(" ", strip=True),
            })

        return prizes or None
    except Exception as e:
        print(f"Prize fetch error: {e}")
        return None

def get_prize_info_cached(window_class, session=None):
    """Fetch prize info with caching"""
    cache_key = f"prices_{window_class}"
    
    cached = get_cached_data(cache_key)
    if cached:
        print(f"✅ Cache HIT for prices_{window_class}")
        return cached

    prizes = get_prize_info_from_origin(window_class, session)
    print(f"❌ Cache MISS for prices_{window_class} - fetching from origin")

    if prizes:
        set_cached_data(cache_key, prizes, ex=None) # Use default TTL or specify
        
    return prizes

def check_number_against_data(number, days_info):
    """
    Checks a number against the days_info and returns winning days and prize details.
    """
    winning_days = []
    for day, info in days_info.items():
        if number in info['numbers']:
            winning_days.append({
                'day': day,
                'window_class': info['window_class']
            })

    prize_details = []
    if winning_days:
        session = requests.Session()
        for win in winning_days:
            if win['window_class']:
                prizes = get_prize_info_cached(win['window_class'], session)
                if prizes:
                    for prize in prizes:
                        if prize['number'] == number:
                            prize_details.append({
                                'day': win['day'],
                                'prize': prize['prize'],
                                'value': prize['value'],
                                'sponsor': prize['sponsor']
                            })
    
    return winning_days, prize_details
