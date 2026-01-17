#!/usr/bin/env python3
"""
Main Entry Point
================
Launches the dashboard which starts all services.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.dashboard import run

if __name__ == "__main__":
    run()
