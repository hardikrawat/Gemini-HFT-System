#!/usr/bin/env python3
"""
Configuration Manager
=====================
Centralized configuration loading from .env file.
All services import settings from this module.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / '.env')


class Config:
    """Application configuration loaded from environment variables."""
    
    # ----- Database -----
    TURSO_URL: str = os.getenv('TURSO_URL', '')
    TURSO_TOKEN: str = os.getenv('TURSO_TOKEN', '')
    
    # ----- Gemini AI -----
    GEMINI_API_KEYS: list = [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
    ]
    GEMINI_MODELS: list = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]
    
    # ----- Trading -----
    SYMBOL: str = os.getenv('TRADING_SYMBOL', 'TATASTEEL.NS')
    INITIAL_BALANCE: float = float(os.getenv('INITIAL_BALANCE', '100000'))
    
    # ----- Service Intervals -----
    MARKET_FEEDER_INTERVAL: int = int(os.getenv('MARKET_FEEDER_INTERVAL', '60'))
    QUANT_ENGINE_INTERVAL: int = int(os.getenv('QUANT_ENGINE_INTERVAL', '60'))
    EXECUTION_ENGINE_INTERVAL: int = int(os.getenv('EXECUTION_ENGINE_INTERVAL', '10'))
    GEMINI_MANAGER_INTERVAL: int = int(os.getenv('GEMINI_MANAGER_INTERVAL', '300'))
    
    # ----- Model Parameters -----
    RSI_WINDOW: int = int(os.getenv('RSI_WINDOW', '14'))
    SMA_WINDOW: int = int(os.getenv('SMA_WINDOW', '20'))
    MIN_TRAINING_ROWS: int = int(os.getenv('MIN_TRAINING_ROWS', '200'))
    XGBOOST_ESTIMATORS: int = int(os.getenv('XGBOOST_ESTIMATORS', '100'))
    XGBOOST_MAX_DEPTH: int = int(os.getenv('XGBOOST_MAX_DEPTH', '3'))
    XGBOOST_LEARNING_RATE: float = float(os.getenv('XGBOOST_LEARNING_RATE', '0.1'))
    
    # ----- Risk Management -----
    MAX_CAPITAL_LOSS_PERCENT: float = float(os.getenv('MAX_CAPITAL_LOSS_PERCENT', '2'))
    MAX_TRADES_PER_10_MIN: int = int(os.getenv('MAX_TRADES_PER_10_MIN', '5'))
    
    # ----- File Paths -----
    SIGNAL_FILE: str = str(PROJECT_ROOT / 'trade_signal.json')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration is present."""
        errors = []
        
        if not cls.TURSO_URL:
            errors.append("TURSO_URL is not set")
        if not cls.TURSO_TOKEN:
            errors.append("TURSO_TOKEN is not set")
        if not any(cls.GEMINI_API_KEYS):
            errors.append("No GEMINI_API_KEY is set")
        
        if errors:
            print("[CONFIG ERROR] Missing required configuration:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (redacted secrets)."""
        print("=" * 50)
        print("  GEMINI HFT SYSTEM - Configuration")
        print("=" * 50)
        print(f"  Symbol:         {cls.SYMBOL}")
        print(f"  Initial Balance: ₹{cls.INITIAL_BALANCE:,.2f}")
        print(f"  Database:       {'Connected' if cls.TURSO_URL else 'Not Set'}")
        print(f"  Gemini APIs:    {sum(1 for k in cls.GEMINI_API_KEYS if k)} configured")
        print("-" * 50)
        print(f"  Market Feeder:  {cls.MARKET_FEEDER_INTERVAL}s interval")
        print(f"  Quant Engine:   {cls.QUANT_ENGINE_INTERVAL}s interval")
        print(f"  Execution:      {cls.EXECUTION_ENGINE_INTERVAL}s interval")
        print(f"  Gemini Manager: {cls.GEMINI_MANAGER_INTERVAL}s interval")
        print("-" * 50)
        print(f"  RSI Window:     {cls.RSI_WINDOW}")
        print(f"  SMA Window:     {cls.SMA_WINDOW}")
        print(f"  XGBoost Trees:  {cls.XGBOOST_ESTIMATORS}")
        print("=" * 50)


# Singleton config instance
config = Config()


if __name__ == "__main__":
    config.print_config()
    print()
    if config.validate():
        print("[OK] Configuration is valid")
    else:
        print("[FAIL] Configuration has errors")
