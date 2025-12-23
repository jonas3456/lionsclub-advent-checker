from flask import Flask, request, jsonify, make_response
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

app = Flask(__name__)

# Upstash Redis client
def get_redis():
    try:
        from upstash_redis import Redis
        return Redis(
            url=os.environ.get("UPSTASH_REDIS_REST_URL"),
            token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        )
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600


def fetch_winning_numbers_cached():
    """Fetch winning numbers with Upstash Redis caching"""
    cache_key = "advent_data"
    redis = get_redis()

    # Try cache first
    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                print("✅ Cache HIT for numbers")
                # Upstash returns dict directly, no need to json.loads
                if isinstance(cached, str):
                    return json.loads(cached)
                return cached
        except Exception as e:
            print(f"Redis read error: {e}")

    # Cache miss - fetch from origin
    print("❌ Cache MISS for numbers- fetching from origin")
    winning_numbers, days_info = fetch_winning_numbers_from_origin()

    if winning_numbers is None:
        return None

    cache_data = {
        'winning_numbers': winning_numbers,
        'days_info': days_info,
        'cached_at': datetime.utcnow().isoformat()
    }

    # Store in cache
    if redis:
        try:
            redis.set(cache_key, json.dumps(cache_data), ex=CACHE_TTL)
            print(f"💾 Stored in cache (TTL={CACHE_TTL}s)")
        except Exception as e:
            print(f"Redis write error: {e}")

    return cache_data


def fetch_winning_numbers_from_origin():
    """Fetch winning numbers directly from the website"""
    url = "https://adventskalender-vs.de/"
    try:
        response = requests.get(url, timeout=10)
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


def get_prize_info_cached(window_class, session):
    """Fetch prize info with caching"""
    cache_key = f"prices_{window_class}"
    redis = get_redis()

    # Try cache first
    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                if isinstance(cached, str):
                    print(f"✅ Cache HIT for prices_{window_class}")
                    return json.loads(cached)
                return cached
        except:
            pass

    # Fetch from origin
    prizes = get_prize_info_from_origin(window_class, session)
    print(f"❌ Cache MISS for prices_{window_class} - fetching from origin")

    # Cache prizes for 1 hour (they don't change)
    if prizes and redis:
        try:
            redis.set(cache_key, json.dumps(prizes), ex=CACHE_TTL)
            print(f"💾 Stored in prices_{window_class} cache (TTL={CACHE_TTL}s)")
        except:
            pass

    return prizes


def get_prize_info_from_origin(window_class, session):
    """Fetch prize information from origin via AJAX"""
    url = "https://adventskalender-vs.de/wp-admin/admin-ajax.php"

    body = f"action=check_access&target={window_class}"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://adventskalender-vs.de",
        "Referer": "https://adventskalender-vs.de/",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = session.post(url, data=body, headers=headers, timeout=10)

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
    except:
        return None


@app.route('/api/check')
def check():
    number = request.args.get('number')

    if not number or not number.isdigit():
        return jsonify({'error': 'Invalid number'}), 400

    cache_data = fetch_winning_numbers_cached()

    if cache_data is None:
        return jsonify({'error': 'Could not fetch data'}), 500

    winning_numbers = cache_data['winning_numbers']
    days_info = cache_data['days_info']

    winning_days = []
    for day, info in days_info.items():
        if number in info['numbers']:
            winning_days.append({
                'day': day,
                'window_class': info['window_class']
            })

    # Fetch prize details if winner
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

    result = {
        'number': number,
        'isWinner': len(winning_days) > 0,
        'winningDays': [w['day'] for w in winning_days],
        'prizeDetails': prize_details,
        'totalDaysDrawn': len(days_info),
        'totalWinners': len(winning_numbers),
        'allResults': days_info,
        'cachedAt': cache_data.get('cached_at')
    }

    response = make_response(jsonify(result))
    # Also cache at edge for 1 minute
    response.headers['Cache-Control'] = 's-maxage=60, stale-while-revalidate=300'

    return response


# Debug endpoint to check cache status
@app.route('/api/cache-status')
def cache_status():
    redis = get_redis()
    if not redis:
        return jsonify({'status': 'Redis not connected'})

    try:
        cached = redis.get("advent_data")
        if cached:
            data = cached if isinstance(cached, dict) else json.loads(cached)
            return jsonify({
                'status': 'Cache exists',
                'cachedAt': data.get('cached_at'),
                'daysInCache': len(data.get('days_info', {})),
                'winnersInCache': len(data.get('winning_numbers', []))
            })
        return jsonify({'status': 'Cache empty'})
    except Exception as e:
        return jsonify({'status': 'Error', 'error': str(e)})


app = app
