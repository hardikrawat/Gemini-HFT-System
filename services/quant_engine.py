#!/usr/bin/env python3
"""
Quant Engine - Service 2: AI Brain
===================================
XGBoost model for price prediction with RSI/SMA features.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from datetime import datetime

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from xgboost import XGBClassifier

from config import config
from db_client import TradingDB


def load_market_data(db):
    """Load market data from database."""
    df = db.get_latest_prices(limit=500, symbol=config.SYMBOL)
    if df.empty:
        return None
    
    df = df.rename(columns={'timestamp': 'Datetime', 'price': 'Close', 'volume': 'Volume'})
    df['Open'] = df['High'] = df['Low'] = df['Close']
    return df


def warmup_data(df):
    """Fetch historical data if needed."""
    current_len = len(df) if df is not None else 0
    
    if current_len >= config.MIN_TRAINING_ROWS:
        return df
    
    print(f"[WARMUP] Fetching historical data...")
    try:
        ticker = yf.Ticker(config.SYMBOL)
        hist = ticker.history(period="7d", interval="1m")
        
        if hist.empty:
            return df
        
        hist = hist.reset_index()
        if 'Date' in hist.columns:
            hist = hist.rename(columns={'Date': 'Datetime'})
        elif 'index' in hist.columns:
            hist = hist.rename(columns={'index': 'Datetime'})
        
        hist['Datetime'] = pd.to_datetime(hist['Datetime'], utc=True)
        hist = hist[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        if df is not None and not df.empty:
            df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
            combined = pd.concat([hist, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=['Datetime'], keep='last')
            return combined.sort_values('Datetime').reset_index(drop=True)
        return hist
    except Exception as e:
        print(f"[WARMUP ERROR] {e}")
        return df


def engineer_features(df):
    """Calculate technical indicators."""
    df = df.copy()
    df['RSI'] = RSIIndicator(close=df['Close'], window=config.RSI_WINDOW).rsi()
    df['SMA'] = SMAIndicator(close=df['Close'], window=config.SMA_WINDOW).sma_indicator()
    return df.dropna().reset_index(drop=True)


def train_and_predict(df):
    """Train model and predict signal."""
    feature_cols = ['RSI', 'SMA', 'Close', 'High', 'Low', 'Volume']
    
    # Create target
    df_train = df.copy()
    df_train['Target'] = (df_train['Close'].shift(-1) > df_train['Close']).astype(int)
    df_train = df_train[:-1]
    
    if len(df_train) < 50:
        return None
    
    X, y = df_train[feature_cols], df_train['Target']
    
    model = XGBClassifier(
        n_estimators=config.XGBOOST_ESTIMATORS,
        max_depth=config.XGBOOST_MAX_DEPTH,
        learning_rate=config.XGBOOST_LEARNING_RATE,
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        verbosity=0,
        random_state=42
    )
    model.fit(X, y)
    
    # Predict on latest
    latest = df.iloc[-1:][feature_cols]
    pred = model.predict(latest)[0]
    proba = model.predict_proba(latest)[0]
    
    timestamp = df.iloc[-1]['Datetime']
    if isinstance(timestamp, pd.Timestamp):
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        "timestamp": str(timestamp),
        "signal": "BUY" if pred == 1 else "SELL",
        "confidence": round(float(proba[pred]), 4),
        "rsi": round(float(df.iloc[-1]['RSI']), 2)
    }


def save_signal(signal):
    """Save signal to JSON file."""
    with open(config.SIGNAL_FILE, 'w') as f:
        json.dump(signal, f, indent=2)
    print(f"[SIGNAL] {signal['signal']} ({signal['confidence']:.1%})")


def run():
    """Main service loop."""
    print("=" * 60)
    print("  SERVICE 2: QUANT ENGINE")
    print(f"  Model: XGBoost | RSI({config.RSI_WINDOW}) SMA({config.SMA_WINDOW})")
    print("=" * 60)
    
    db = TradingDB()
    
    while True:
        try:
            print(f"\n[CYCLE] {datetime.now().strftime('%H:%M:%S')}")
            
            df = load_market_data(db)
            if df is None or df.empty:
                print("[WAIT] No data")
                time.sleep(config.QUANT_ENGINE_INTERVAL)
                continue
            
            df = warmup_data(df)
            if df is None or len(df) < 50:
                time.sleep(config.QUANT_ENGINE_INTERVAL)
                continue
            
            df = engineer_features(df)
            if len(df) < 50:
                time.sleep(config.QUANT_ENGINE_INTERVAL)
                continue
            
            signal = train_and_predict(df)
            if signal:
                save_signal(signal)
            
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(config.QUANT_ENGINE_INTERVAL)


if __name__ == "__main__":
    run()
