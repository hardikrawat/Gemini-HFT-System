#!/usr/bin/env python3
"""
Market Feeder - Service 1: Data Pipeline
=========================================
Fetches live market data and stores in Turso database.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime

import yfinance as yf

from config import config
from db_client import TradingDB


def fetch_latest_candle():
    """Fetch the latest 1-minute candle."""
    ticker = yf.Ticker(config.SYMBOL)
    df = ticker.history(period="1d", interval="1m")
    
    if df.empty:
        return None
    
    latest = df.iloc[-1]
    return {
        'symbol': config.SYMBOL,
        'price': round(latest['Close'], 2),
        'volume': float(latest['Volume'])
    }


def run():
    """Main service loop."""
    print("=" * 60)
    print("  SERVICE 1: MARKET FEEDER")
    print(f"  Symbol: {config.SYMBOL}")
    print(f"  Interval: {config.MARKET_FEEDER_INTERVAL}s")
    print("=" * 60)
    
    db = TradingDB()
    db.init_db()
    
    while True:
        try:
            candle = fetch_latest_candle()
            
            if candle:
                db.log_price(candle['symbol'], candle['price'], candle['volume'])
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Price: {candle['price']}")
            else:
                print("[SKIP] No data")
        
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(config.MARKET_FEEDER_INTERVAL)


if __name__ == "__main__":
    run()
