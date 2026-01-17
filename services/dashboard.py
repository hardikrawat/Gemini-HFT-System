#!/usr/bin/env python3
"""
Dashboard - Command Center
==========================
Launches all services and displays real-time status.
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from db_client import TradingDB


# Service configurations
SERVICES = [
    ("Market Feeder", "services/market_feeder.py"),
    ("Quant Engine", "services/quant_engine.py"),
    ("Execution Engine", "services/execution_engine.py"),
    ("Gemini Manager", "services/gemini_manager.py"),
]

REFRESH_INTERVAL = 2


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def start_services():
    """Launch all services as background processes."""
    processes = []
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("  GEMINI HFT - Starting Services")
    print("=" * 60)
    
    for name, script in SERVICES:
        try:
            script_path = project_root / script
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(project_root)
            )
            processes.append((name, process))
            print(f"  [✓] {name} (PID: {process.pid})")
        except Exception as e:
            print(f"  [✗] {name}: {e}")
    
    time.sleep(2)
    return processes


def stop_services(processes):
    """Stop all services."""
    print("\n" + "=" * 60)
    print("  Shutting down...")
    print("=" * 60)
    
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"  [✓] {name} stopped")
        except:
            proc.kill()
            print(f"  [!] {name} killed")
    
    print("\nSystem Shutdown Complete")


def display_dashboard(processes, db):
    """Display real-time dashboard."""
    clear_screen()
    
    # Get data
    prices = db.get_latest_prices(limit=1)
    portfolio = db.get_portfolio()
    manager = db.get_manager_status_full()
    
    price = float(prices.iloc[-1]['price']) if not prices.empty else 0
    balance = portfolio['balance']
    positions = portfolio['positions']
    total_value = balance + (positions * price)
    
    active = sum(1 for _, p in processes if p.poll() is None)
    
    # Display
    print()
    print("=" * 60)
    print("           GEMINI HFT COMMAND CENTER")
    print("=" * 60)
    print(f"  Status:  Active ({active}/{len(processes)} services)")
    print(f"  Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(f"  Symbol:  {config.SYMBOL}")
    print(f"  Price:   ₹{price:,.2f}")
    print("-" * 60)
    print(f"  Balance:    ₹{balance:,.2f}")
    print(f"  Positions:  {positions}")
    print(f"  Net Worth:  ₹{total_value:,.2f}")
    print("-" * 60)
    print(f"  Manager:    {manager['action']}")
    if manager.get('reason'):
        print(f"  Reason:     {manager['reason']}")
    print("=" * 60)
    print("\n  [Press Ctrl+C to Stop]")


def run():
    """Main dashboard loop."""
    config.print_config()
    
    if not config.validate():
        print("\n[FATAL] Configuration invalid. Check .env file.")
        return
    
    db = TradingDB()
    db.init_db()
    
    processes = start_services()
    
    try:
        while True:
            display_dashboard(processes, db)
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        stop_services(processes)


if __name__ == "__main__":
    run()
