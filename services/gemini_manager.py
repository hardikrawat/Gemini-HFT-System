#!/usr/bin/env python3
"""
Gemini Manager - Service 4: AI Risk Controller
===============================================
Uses Gemini AI for risk analysis and trading control.
"""

import re
import json
import time
from datetime import datetime

import google.generativeai as genai

from config import config
from db_client import TradingDB


current_api_idx = 0
current_model_idx = 0


def configure_gemini():
    """Configure Gemini with current API key and model."""
    genai.configure(api_key=config.GEMINI_API_KEYS[current_api_idx])
    return genai.GenerativeModel(config.GEMINI_MODELS[current_model_idx])


def rotate_model():
    """Rotate to next model."""
    global current_model_idx
    current_model_idx = (current_model_idx + 1) % len(config.GEMINI_MODELS)


def rotate_api():
    """Rotate to next API key."""
    global current_api_idx, current_model_idx
    current_api_idx = (current_api_idx + 1) % len(config.GEMINI_API_KEYS)
    current_model_idx = 0


def is_rate_limit(msg):
    return any(k in str(msg).lower() for k in ['rate', 'quota', '429', 'exhausted'])


def is_not_found(msg):
    return '404' in str(msg).lower() or 'not found' in str(msg).lower()


def parse_response(text):
    """Extract JSON from Gemini response."""
    try:
        match = re.search(r'\{[^}]+\}', text)
        if match:
            data = json.loads(match.group().replace("'", '"'))
            if 'action' in data:
                action = data['action'].upper()
                if action in ['CONTINUE', 'PAUSE']:
                    return action, data.get('reason', '')
        return 'CONTINUE', 'Parse fallback'
    except:
        return 'CONTINUE', 'Parse error'


def get_command(trades_summary, balance, positions):
    """Get CONTINUE/PAUSE from Gemini."""
    prompt = f"""You are a Risk Manager. Review these trades:

{trades_summary}

Balance: ₹{balance:,.2f} | Positions: {positions}

RULES:
- If lost >{config.MAX_CAPITAL_LOSS_PERCENT}% capital OR >{config.MAX_TRADES_PER_10_MIN} trades in 10 min: PAUSE
- Otherwise: CONTINUE
- Return JSON only

Examples:
{{"action": "CONTINUE"}}
{{"action": "PAUSE", "reason": "High Risk"}}

Response:"""

    attempts = len(config.GEMINI_API_KEYS) * len(config.GEMINI_MODELS)
    
    for _ in range(attempts):
        try:
            model = configure_gemini()
            response = model.generate_content(prompt)
            return parse_response(response.text.strip())
        except Exception as e:
            if is_not_found(str(e)):
                rotate_model()
            elif is_rate_limit(str(e)):
                if current_model_idx < len(config.GEMINI_MODELS) - 1:
                    rotate_model()
                elif current_api_idx < len(config.GEMINI_API_KEYS) - 1:
                    rotate_api()
                else:
                    return 'CONTINUE', 'All APIs exhausted'
            else:
                rotate_model()
    
    return 'CONTINUE', 'Failed'


def run():
    """Main service loop."""
    print("=" * 60)
    print("  SERVICE 4: GEMINI MANAGER")
    print(f"  Interval: {config.GEMINI_MANAGER_INTERVAL}s")
    print("=" * 60)
    
    db = TradingDB()
    db.init_db()
    
    while True:
        try:
            print(f"\n[CYCLE] {datetime.now().strftime('%H:%M:%S')}")
            
            trades = db.get_recent_trades(10)
            if trades.empty:
                db.set_manager_status('CONTINUE', 'No trades')
                time.sleep(config.GEMINI_MANAGER_INTERVAL)
                continue
            
            trades_str = "\n".join([
                f"{r['timestamp']} - {r['action']} @ ₹{r['price']}"
                for _, r in trades.iterrows()
            ])
            
            portfolio = db.get_portfolio()
            
            action, reason = get_command(trades_str, portfolio['balance'], portfolio['positions'])
            db.set_manager_status(action, reason)
            
            print(f"[COMMAND] {action}" + (f" ({reason})" if reason else ""))
            
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(config.GEMINI_MANAGER_INTERVAL)


if __name__ == "__main__":
    run()
