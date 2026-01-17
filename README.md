# Gemini HFT System

A microservices-based High-Frequency Trading bot with AI-powered risk management.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DASHBOARD                                 │
│                 (Command Center - Ctrl+C to stop)               │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────────┐
│ Market Feeder │    │ Quant Engine  │    │ Execution Engine  │
│   (60s loop)  │    │   (60s loop)  │    │    (10s loop)     │
└───────┬───────┘    └───────┬───────┘    └─────────┬─────────┘
        │                    │                      │
        └────────────────────┼──────────────────────┘
                             ▼
                    ┌───────────────┐
                    │   TURSO DB    │
                    │  (LibSQL)     │
                    └───────────────┘
                             ▲
                    ┌────────┴────────┐
                    │ Gemini Manager  │
                    │  (5min loop)    │
                    │ PAUSE/CONTINUE  │
                    └─────────────────┘
```

## Services

| Service | File | Role | Interval |
|---------|------|------|----------|
| Market Feeder | `services/market_feeder.py` | Fetches live prices from yfinance | 60s |
| Quant Engine | `services/quant_engine.py` | XGBoost ML model for BUY/SELL signals | 60s |
| Execution Engine | `services/execution_engine.py` | Paper trading execution | 10s |
| Gemini Manager | `services/gemini_manager.py` | AI risk controller (Gemini API) | 5min |
| Dashboard | `services/dashboard.py` | Command center (launches all) | 2s |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (edit .env if needed)
python config.py

# 3. Run everything
python services/dashboard.py
```

## Project Structure

```
Gemini_HFT_System/
├── .env                    # Environment configuration
├── config.py               # Configuration loader
├── db_client.py            # Turso database client
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── trade_signal.json       # Real-time signal (high-speed)
└── services/
    ├── market_feeder.py    # Service 1: Data pipeline
    ├── quant_engine.py     # Service 2: ML predictions
    ├── execution_engine.py # Service 3: Trade execution
    ├── gemini_manager.py   # Service 4: AI risk control
    └── dashboard.py        # Command center
```

## Database Tables

| Table | Purpose |
|-------|---------|
| `market_data` | Historical price data |
| `trade_logs` | All executed trades |
| `portfolio` | Current balance & positions |
| `manager_status` | Gemini AI control state |

## Configuration

All settings are in `.env`:

```env
# Trading
TRADING_SYMBOL=TATASTEEL.NS
INITIAL_BALANCE=100000

# Database
TURSO_URL=libsql://...
TURSO_TOKEN=...

# AI
GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...

# Risk Management
MAX_CAPITAL_LOSS_PERCENT=2
MAX_TRADES_PER_10_MIN=5
```

## Running Individual Services

```bash
# Just the data feeder
python services/market_feeder.py

# Just the ML engine
python services/quant_engine.py

# Just execution
python services/execution_engine.py

# Just risk manager
python services/gemini_manager.py
```

## License

Private - Hardik Rawat
