import sys
import os
import logging
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.getcwd())

from src.engine.risk import RiskEngine
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase8")

def generate_mock_klines(base_price, volatility=0.01, n=30):
    """Generates mock klines in Bybit format (newest first)."""
    klines = []
    current_price = base_price
    for i in range(n):
        timestamp = 1700000000000 + (i * 900000) # 15m intervals
        change = current_price * np.random.uniform(-volatility, volatility)
        open_p = current_price
        close_p = current_price + change
        high_p = max(open_p, close_p) + (abs(change) * 0.1)
        low_p = min(open_p, close_p) - (abs(change) * 0.1)
        
        # Bybit: [startTime, open, high, low, close, volume, turnover]
        klines.append([str(timestamp), str(open_p), str(high_p), str(low_p), str(close_p), "100", "1000"])
        current_price = close_p
    
    return klines[::-1]

def test_risk_engine():
    engine = RiskEngine()
    
    # Mock asset
    asset = {
        "symbol": "BTCUSDT",
        "last_price": 50000,
        "is_alertable": True
    }
    
    # 1. Test standard calculation
    logger.info("Testing standard risk calculation...")
    klines = generate_mock_klines(50000, volatility=0.02, n=30)
    enriched = engine.calculate_levels(asset, klines)
    
    context = enriched["risk_context"]
    assert context is not None
    logger.info(f"Entry: {context['entry']}")
    logger.info(f"SL: {context['stop_loss']}")
    logger.info(f"TP1: {context['tp1']}")
    logger.info(f"TP2: {context['tp2']}")
    
    assert context["stop_loss"] < context["entry"]
    assert context["tp1"] > context["entry"]
    assert context["tp2"] > context["tp1"]
    
    # 2. Test insufficient data
    logger.info("Testing insufficient data...")
    short_klines = generate_mock_klines(50000, n=5)
    enriched_short = engine.calculate_levels(asset, short_klines)
    assert enriched_short["risk_context"] is None

    # 3. Test non-alertable asset (process_universe)
    logger.info("Testing process_universe skip logic...")
    asset_not_alertable = asset.copy()
    asset_not_alertable["is_alertable"] = False
    
    def mock_get_klines(symbol, interval):
        return klines

    universe = [asset, asset_not_alertable]
    processed = engine.process_universe(universe, mock_get_klines)
    
    assert processed[0]["risk_context"] is not None
    assert processed[1]["risk_context"] is None

    logger.info("Phase 8 Test Passed!")

if __name__ == "__main__":
    test_risk_engine()
