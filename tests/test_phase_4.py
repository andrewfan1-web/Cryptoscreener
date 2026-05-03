import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.engine.universe import UniverseFilter
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase4")

def test_universe_filter():
    # Mock data
    snapshot = [
        {
            "symbol": "BTCUSDT",
            "market_cap": 1_000_000_000_000,
            "turnover_24h": 50_000_000_000,
            "open_interest_value": 20_000_000_000,
            "is_overextended": False
        },
        {
            "symbol": "SMALLCAPUSDT",
            "market_cap": 1_000_000,  # Below 10M
            "turnover_24h": 10_000_000,
            "open_interest_value": 5_000_000,
            "is_overextended": False
        },
        {
            "symbol": "LOWVOLUSDT",
            "market_cap": 100_000_000,
            "turnover_24h": 1_000_000,  # Below 5M
            "open_interest_value": 2_000_000,
            "is_overextended": False
        },
        {
            "symbol": "LOWOIUSDT",
            "market_cap": 100_000_000,
            "turnover_24h": 10_000_000,
            "open_interest_value": 100_000,  # Below 1M
            "is_overextended": False
        },
        {
            "symbol": "OVEREXTENDEDUSDT",
            "market_cap": 100_000_000,
            "turnover_24h": 10_000_000,
            "open_interest_value": 5_000_000,
            "is_overextended": True
        }
    ]

    filter_engine = UniverseFilter()

    logger.info("Testing with UNIVERSE_HARD_EXCLUDE_OVEREXTENDED = False")
    Config.UNIVERSE_HARD_EXCLUDE_OVEREXTENDED = False
    included, excluded = filter_engine.filter_assets(snapshot)

    logger.info(f"Included: {[a['symbol'] for a in included]}")
    logger.info(f"Excluded: {[(a['symbol'], a['exclusion_reasons']) for a in excluded]}")

    assert "BTCUSDT" in [a["symbol"] for a in included]
    assert "OVEREXTENDEDUSDT" in [a["symbol"] for a in included]
    assert "SMALLCAPUSDT" in [a["symbol"] for a in excluded]
    assert "LOWVOLUSDT" in [a["symbol"] for a in excluded]
    assert "LOWOIUSDT" in [a["symbol"] for a in excluded]

    logger.info("-" * 30)
    logger.info("Testing with UNIVERSE_HARD_EXCLUDE_OVEREXTENDED = True")
    Config.UNIVERSE_HARD_EXCLUDE_OVEREXTENDED = True
    included, excluded = filter_engine.filter_assets(snapshot)

    logger.info(f"Included: {[a['symbol'] for a in included]}")
    logger.info(f"Excluded: {[(a['symbol'], a['exclusion_reasons']) for a in excluded]}")

    assert "OVEREXTENDEDUSDT" in [a["symbol"] for a in excluded]
    
    logger.info("Phase 4 Test Passed!")

if __name__ == "__main__":
    test_universe_filter()
