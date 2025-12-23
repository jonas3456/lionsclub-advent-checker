# api/check.py
from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup

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
    except Exception as e:
        return None, None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        number = query.get('number', [None])[0]

        if not number or not number.isdigit():
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid number'}).encode())
            return

        winning_numbers, days_info = fetch_winning_numbers()

        if winning_numbers is None:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Could not fetch data'}).encode())
            return

        winning_days = []
        for day, info in days_info.items():
            if number in info['numbers']:
                winning_days.append(day)

        result = {
            'number': number,
            'isWinner': len(winning_days) > 0,
            'winningDays': winning_days,
            'totalDaysDrawn': len(days_info),
            'totalWinners': len(winning_numbers),
            'allResults': days_info
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
