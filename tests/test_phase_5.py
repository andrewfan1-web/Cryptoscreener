import sys
import os
import logging
import pandas as pd

# Add src to path
sys.path.append(os.getcwd())

from src.engine.regime import RegimeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase5")

def generate_mock_klines(price_start, price_end, n=100):
    """Generates mock klines in Bybit format (newest first)."""
    prices = [price_start + (price_end - price_start) * i / (n-1) for i in range(n)]
    klines = []
    # Bybit: [startTime, open, high, low, close, volume, turnover]
    for i in range(n):
        timestamp = 1700000000000 + (i * 3600000)
        close = prices[i]
        klines.append([str(timestamp), str(close), str(close+10), str(close-10), str(close), "100", "1000000"])
    
    # Reverse to newest first as Bybit does
    return klines[::-1]

def test_regime_engine():
    engine = RegimeEngine()

    # 1. Test Bullish: Price trending up, current price > EMA
    logger.info("Testing Bullish Regime...")
    bullish_klines = generate_mock_klines(100, 200, n=100)
    regime = engine.calculate_regime(bullish_klines)
    logger.info(f"Regime: {regime}")
    assert regime == RegimeEngine.BULLISH
    
    # Initial state transition (none yet because it's first call)
    # Wait, the first call should set self.last_regime
    transition = engine.get_transition_state(regime)
    assert transition is False 

    # 2. Test Bearish: Price trending down, current price < EMA
    logger.info("Testing Bearish Regime...")
    bearish_klines = generate_mock_klines(200, 100, n=100)
    regime = engine.calculate_regime(bearish_klines)
    logger.info(f"Regime: {regime}")
    assert regime == RegimeEngine.BEARISH
    
    # Transition should be True: BULLISH -> BEARISH
    transition = engine.get_transition_state(regime)
    logger.info(f"Transition: {transition}")
    assert transition is True

    # 3. Test No Transition: Bearish -> Bearish
    logger.info("Testing No Transition...")
    regime = engine.calculate_regime(bearish_klines)
    transition = engine.get_transition_state(regime)
    logger.info(f"Transition: {transition}")
    assert transition is False

    # 4. Test Insufficient Data
    logger.info("Testing Insufficient Data...")
    short_klines = generate_mock_klines(100, 110, n=5)
    regime = engine.calculate_regime(short_klines)
    assert regime == RegimeEngine.BEARISH

    logger.info("Phase 5 Test Passed!")

if __name__ == "__main__":
    test_regime_engine()
