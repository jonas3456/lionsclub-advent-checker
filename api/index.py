from flask import Flask, request, jsonify, make_response
import requests
import json
from .lib.scraper import fetch_winning_numbers_cached, check_number_against_data
from .lib.cache import get_cached_data

app = Flask(__name__)

@app.route('/api/check')
def check():
    number = request.args.get('number')

    if not number or not number.isdigit():
        return jsonify({'error': 'Invalid number'}), 400

    number = str(int(number))

    cache_data = fetch_winning_numbers_cached()

    if cache_data is None:
        return jsonify({'error': 'Could not fetch data'}), 500

    winning_numbers = cache_data['winning_numbers']
    days_info = cache_data['days_info']

    winning_days, prize_details = check_number_against_data(number, days_info)

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

@app.route('/api/cache-status')
def cache_status():
    cached = get_cached_data("advent_data")
    if cached:
        return jsonify({
            'status': 'Cache exists',
            'cachedAt': cached.get('cached_at'),
            'daysInCache': len(cached.get('days_info', {})),
            'winnersInCache': len(cached.get('winning_numbers', []))
        })
    return jsonify({'status': 'Cache empty or Redis not connected'})

# This is for Vercel
app = app
