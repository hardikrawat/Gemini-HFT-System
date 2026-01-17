#!/usr/bin/env python3
"""
Execution Engine - Service 3: Trade Executor
=============================================
Paper trading execution with portfolio management.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
import os
from datetime import datetime

from config import config
from db_client import TradingDB


def load_signal():
    """Load trade signal from JSON."""
    if not os.path.exists(config.SIGNAL_FILE):
        return None
    with open(config.SIGNAL_FILE, 'r') as f:
        return json.load(f)


def get_current_price(db):
    """Get latest price from database."""
    prices = db.get_latest_prices(limit=1)
    return float(prices.iloc[-1]['price']) if not prices.empty else None


def execute_buy(db, balance, positions, price, timestamp):
    """Execute BUY order."""
    if balance <= price:
        return balance, positions, False
    
    qty = int(balance // price)
    cost = qty * price
    new_balance = balance - cost
    new_positions = positions + qty
    
    db.log_trade('BUY', price, qty, new_balance)
    db.update_portfolio(new_balance, new_positions, timestamp)
    
    print(f"[BUY] {qty} @ {price:.2f} | Cost: {cost:.2f}")
    return new_balance, new_positions, True


def execute_sell(db, balance, positions, price, timestamp):
    """Execute SELL order."""
    if positions <= 0:
        return balance, positions, False
    
    revenue = positions * price
    new_balance = balance + revenue
    
    db.log_trade('SELL', price, positions, new_balance)
    db.update_portfolio(new_balance, 0, timestamp)
    
    print(f"[SELL] {positions} @ {price:.2f} | Revenue: {revenue:.2f}")
    return new_balance, 0, True


def run():
    """Main service loop."""
    print("=" * 60)
    print("  SERVICE 3: EXECUTION ENGINE")
    print(f"  Interval: {config.EXECUTION_ENGINE_INTERVAL}s")
    print("=" * 60)
    
    db = TradingDB()
    db.init_db()
    
    portfolio = db.get_portfolio()
    print(f"[INIT] Balance: {portfolio['balance']:.2f} | Positions: {portfolio['positions']}")
    
    while True:
        try:
            portfolio = db.get_portfolio()
            balance = portfolio['balance']
            positions = portfolio['positions']
            last_trade = portfolio['last_trade_time']
            
            signal = load_signal()
            price = get_current_price(db)
            
            if not signal or not price:
                time.sleep(config.EXECUTION_ENGINE_INTERVAL)
                continue
            
            sig_type = signal.get('signal')
            sig_time = signal.get('timestamp')
            confidence = signal.get('confidence', 0)
            
            # Anti-spam
            if sig_time == last_trade:
                print(f"Balance: {balance:.2f} | Pos: {positions} | {sig_type} (traded)")
                time.sleep(config.EXECUTION_ENGINE_INTERVAL)
                continue
            
            # Manager check
            manager_action = db.get_manager_status()
            if manager_action == 'PAUSE':
                status = db.get_manager_status_full()
                print(f"[BLOCKED] {status.get('reason', 'Paused')}")
                time.sleep(config.EXECUTION_ENGINE_INTERVAL)
                continue
            
            # Execute trades
            if sig_type == 'BUY' and balance > price:
                balance, positions, _ = execute_buy(db, balance, positions, price, sig_time)
            elif sig_type == 'SELL' and positions > 0:
                balance, positions, _ = execute_sell(db, balance, positions, price, sig_time)
            
            total = balance + (positions * price)
            print(f"Balance: {balance:.2f} | Pos: {positions} | Value: {total:.2f} | {sig_type} ({confidence:.1%})")
            
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(config.EXECUTION_ENGINE_INTERVAL)


if __name__ == "__main__":
    run()
