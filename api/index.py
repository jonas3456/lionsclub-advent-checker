from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

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
            winning_days.append(day)

    return jsonify({
        'number': number,
        'isWinner': len(winning_days) > 0,
        'winningDays': winning_days,
        'totalDaysDrawn': len(days_info),
        'totalWinners': len(winning_numbers),
        'allResults': days_info
    })
