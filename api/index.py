from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

def fetch_winning_numbers():
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
    except Exception:
        return None, None


def get_prize_info(window_class, session):
    """Fetch prize information for a specific day via AJAX"""
    url = "https://adventskalender-vs.de/wp-admin/admin-ajax.php"

    body = f"action=check_access&target={window_class}"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://adventskalender-vs.de",
        "Referer": "https://adventskalender-vs.de/",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        response = session.post(url, data=body, headers=headers, timeout=10)

        if response.status_code != 200 or not response.text:
            return None

        text = response.text.strip()
        if text == "false":
            return None

        # Response is often a JSON/PHP-escaped string containing <tr>...</tr> fragments
        if (text.startswith('"') and text.endswith('"')) or ("\\/" in text) or ("\\u" in text):
            try:
                text = json.loads(text)
            except Exception:
                text = text.strip('"').replace("\\/", "/")

        # Wrap fragments so BeautifulSoup parses consistently
        html = f"<table>{text}</table>"
        soup = BeautifulSoup(html, "html.parser")

        prizes = []
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            number = cols[0].get_text(" ", strip=True)
            prize_name = cols[1].get_text(" ", strip=True)
            prize_value = cols[2].get_text(" ", strip=True)
            sponsor = cols[3].get_text(" ", strip=True)

            prizes.append({
                "number": number,
                "prize": prize_name,
                "value": prize_value,
                "sponsor": sponsor,
            })

        return prizes or None

    except Exception:
        return None


@app.route('/api/check')
def check():
    number = request.args.get('number')

    if not number or not number.isdigit():
        return jsonify({'error': 'Invalid number'}), 400

    winning_numbers, days_info = fetch_winning_numbers()

    if winning_numbers is None:
        return jsonify({'error': 'Could not fetch data'}), 500

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
                prizes = get_prize_info(win['window_class'], session)
                if prizes:
                    # Find prizes for this specific number
                    for prize in prizes:
                        if prize['number'] == number:
                            prize_details.append({
                                'day': win['day'],
                                'prize': prize['prize'],
                                'value': prize['value'],
                                'sponsor': prize['sponsor']
                            })

    return jsonify({
        'number': number,
        'isWinner': len(winning_days) > 0,
        'winningDays': [w['day'] for w in winning_days],
        'prizeDetails': prize_details,
        'totalDaysDrawn': len(days_info),
        'totalWinners': len(winning_numbers),
        'allResults': days_info
    })


# Required for Vercel
app = app
