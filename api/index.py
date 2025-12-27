from flask import Flask, request, jsonify, make_response
import requests
import json
import os
from functools import wraps
from .lib.scraper import fetch_winning_numbers_cached, check_number_against_data, init_all_prize_caches
from .lib.cache import get_cached_data

app = Flask(__name__)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_token = os.environ.get('ADMIN_SECRET_TOKEN')
        if not auth_token:
            # If no token is configured, we might want to allow it for now or block it.
            # Usually, if we want protection, we should have a token.
            # But let's assume if it's not set, we might be in dev.
            # For security, better to require it if we are explicitly adding protection.
            return jsonify({'error': 'Authentication not configured'}), 500
        
        provided_token = request.headers.get('X-API-KEY') or request.args.get('token')
        if provided_token != auth_token:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

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
@require_auth
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

@app.route('/api/init-cache')
@require_auth
def init_cache():
    result = fetch_winning_numbers_cached(force_refresh=True)
    if result:
        return jsonify({
            'status': 'Cache initialized',
            'cachedAt': result.get('cached_at'),
            'daysFetched': len(result.get('days_info', {})),
            'winnersFetched': len(result.get('winning_numbers', []))
        })
    return jsonify({'error': 'Failed to initialize cache'}), 500

@app.route('/api/init-prize-cache')
@require_auth
def init_prize_cache():
    result = init_all_prize_caches()
    if result is not None:
        return jsonify({
            'status': 'Prize cache initialized',
            'daysProcessed': len(result),
            'details': result
        })
    return jsonify({'error': 'Failed to initialize prize cache'}), 500

# This is for Vercel
app = app
