#!/usr/bin/env python3
"""
Reset Database CLI
==================
Command-line tool to reset the database to initial state.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from db_client import TradingDB


def main():
    print("=" * 50)
    print("  DATABASE RESET UTILITY")
    print("=" * 50)
    print()
    print("WARNING: This will DELETE ALL DATA including:")
    print("  - Market data history")
    print("  - Trade logs")
    print("  - Portfolio state")
    print("  - Manager status")
    print()
    
    # Check for --force flag
    if "--force" in sys.argv:
        confirm = True
    else:
        response = input("Type 'RESET' to confirm: ").strip()
        confirm = response == "RESET"
    
    if not confirm:
        print("\n[CANCELLED] Database reset aborted.")
        return
    
    print()
    db = TradingDB()
    db.init_db()
    
    success = db.reset_db(confirm=True)
    
    if success:
        # Verify reset
        print()
        print("-" * 50)
        print("Verification:")
        portfolio = db.get_portfolio()
        print(f"  Balance:   ₹{portfolio['balance']:,.2f}")
        print(f"  Positions: {portfolio['positions']}")
        print(f"  Manager:   {db.get_manager_status()}")
        print("-" * 50)
        print("\n[SUCCESS] Database has been reset!")
    else:
        print("\n[FAILED] Database reset failed.")


if __name__ == "__main__":
    main()
