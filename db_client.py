#!/usr/bin/env python3
"""
Database Client - Turso DB Integration
=======================================
Handles all database interactions for the HFT system using Turso (libSQL).
Provides persistent storage for market data, trades, portfolio, and manager status.

Part of the HFT Microservices Trading Bot.
"""

from datetime import datetime
from typing import Dict, Optional

import libsql_experimental as libsql
import pandas as pd

from config import config


class TradingDB:
    """Production-ready database client for trading system using Turso DB."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern for database connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize database connection."""
        if self._initialized:
            return
        
        self.url = config.TURSO_URL
        self.token = config.TURSO_TOKEN
        
        if not self.url or not self.token:
            raise ValueError("TURSO_URL and TURSO_TOKEN must be configured in .env")
        
        self.conn = libsql.connect(database=self.url, auth_token=self.token)
        self._initialized = True
        print(f"[DB] Connected to Turso database")
    
    def init_db(self):
        """Create all required tables if they don't exist."""
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL DEFAULT 0
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                balance REAL NOT NULL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance REAL NOT NULL DEFAULT 100000,
                positions INTEGER NOT NULL DEFAULT 0,
                last_trade_time TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS manager_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                action TEXT NOT NULL DEFAULT 'CONTINUE',
                reason TEXT,
                timestamp TEXT
            )
        """)
        
        # Initialize portfolio
        result = self.conn.execute("SELECT COUNT(*) FROM portfolio").fetchone()
        if result[0] == 0:
            self.conn.execute(
                "INSERT INTO portfolio (id, balance, positions) VALUES (1, ?, 0)",
                (config.INITIAL_BALANCE,)
            )
        
        # Initialize manager status
        result = self.conn.execute("SELECT COUNT(*) FROM manager_status").fetchone()
        if result[0] == 0:
            self.conn.execute(
                "INSERT INTO manager_status (id, action, timestamp) VALUES (1, 'CONTINUE', ?)",
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)
            )
        
        self.conn.commit()
        print("[DB] Tables initialized")
    
    # ==================== MARKET DATA ====================
    
    def log_price(self, symbol: str, price: float, volume: float = 0) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.conn.execute(
                "INSERT INTO market_data (timestamp, symbol, price, volume) VALUES (?, ?, ?, ?)",
                (timestamp, symbol, price, volume)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB ERROR] log_price: {e}")
            return False
    
    def get_latest_prices(self, limit: int = 500, symbol: str = None) -> pd.DataFrame:
        try:
            if symbol:
                query = "SELECT timestamp, symbol, price, volume FROM market_data WHERE symbol = ? ORDER BY id DESC LIMIT ?"
                result = self.conn.execute(query, (symbol, limit)).fetchall()
            else:
                query = "SELECT timestamp, symbol, price, volume FROM market_data ORDER BY id DESC LIMIT ?"
                result = self.conn.execute(query, (limit,)).fetchall()
            
            df = pd.DataFrame(result, columns=['timestamp', 'symbol', 'price', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.iloc[::-1].reset_index(drop=True)
        except Exception as e:
            print(f"[DB ERROR] get_latest_prices: {e}")
            return pd.DataFrame(columns=['timestamp', 'symbol', 'price', 'volume'])
    
    # ==================== PORTFOLIO ====================
    
    def get_portfolio(self) -> Dict:
        try:
            result = self.conn.execute(
                "SELECT balance, positions, last_trade_time FROM portfolio WHERE id = 1"
            ).fetchone()
            if result:
                return {'balance': result[0], 'positions': result[1], 'last_trade_time': result[2]}
            return {'balance': config.INITIAL_BALANCE, 'positions': 0, 'last_trade_time': None}
        except Exception as e:
            print(f"[DB ERROR] get_portfolio: {e}")
            return {'balance': config.INITIAL_BALANCE, 'positions': 0, 'last_trade_time': None}
    
    def update_portfolio(self, balance: float, positions: int, last_trade_time: str = None) -> bool:
        try:
            self.conn.execute(
                "UPDATE portfolio SET balance = ?, positions = ?, last_trade_time = ? WHERE id = 1",
                (balance, positions, last_trade_time)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB ERROR] update_portfolio: {e}")
            return False
    
    # ==================== TRADE LOGS ====================
    
    def log_trade(self, action: str, price: float, quantity: int, balance: float) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.conn.execute(
                "INSERT INTO trade_logs (timestamp, action, price, quantity, balance) VALUES (?, ?, ?, ?, ?)",
                (timestamp, action, price, quantity, balance)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB ERROR] log_trade: {e}")
            return False
    
    def get_recent_trades(self, limit: int = 10) -> pd.DataFrame:
        try:
            query = "SELECT timestamp, action, price, quantity, balance FROM trade_logs ORDER BY id DESC LIMIT ?"
            result = self.conn.execute(query, (limit,)).fetchall()
            df = pd.DataFrame(result, columns=['timestamp', 'action', 'price', 'quantity', 'balance'])
            return df.iloc[::-1].reset_index(drop=True)
        except Exception as e:
            print(f"[DB ERROR] get_recent_trades: {e}")
            return pd.DataFrame(columns=['timestamp', 'action', 'price', 'quantity', 'balance'])
    
    # ==================== MANAGER STATUS ====================
    
    def get_manager_status(self) -> str:
        try:
            result = self.conn.execute("SELECT action FROM manager_status WHERE id = 1").fetchone()
            return result[0].upper() if result else 'CONTINUE'
        except Exception as e:
            print(f"[DB ERROR] get_manager_status: {e}")
            return 'CONTINUE'
    
    def get_manager_status_full(self) -> Dict:
        try:
            result = self.conn.execute(
                "SELECT action, reason, timestamp FROM manager_status WHERE id = 1"
            ).fetchone()
            if result:
                return {'action': result[0].upper(), 'reason': result[1], 'timestamp': result[2]}
            return {'action': 'CONTINUE', 'reason': None, 'timestamp': None}
        except Exception as e:
            print(f"[DB ERROR] get_manager_status_full: {e}")
            return {'action': 'CONTINUE', 'reason': None, 'timestamp': None}
    
    def set_manager_status(self, action: str, reason: str = None) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.conn.execute(
                "UPDATE manager_status SET action = ?, reason = ?, timestamp = ? WHERE id = 1",
                (action.upper(), reason, timestamp)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB ERROR] set_manager_status: {e}")
            return False
    
    def close(self):
        if self.conn:
            self.conn.close()
            TradingDB._instance = None
            print("[DB] Connection closed")


def get_db() -> TradingDB:
    """Get TradingDB singleton instance."""
    return TradingDB()


if __name__ == "__main__":
    print("Testing database connection...")
    db = TradingDB()
    db.init_db()
    
    portfolio = db.get_portfolio()
    print(f"Portfolio: {portfolio}")
    
    status = db.get_manager_status()
    print(f"Manager Status: {status}")
    
    print("\n[OK] Database connection test passed!")
