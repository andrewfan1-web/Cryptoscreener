import sys
import os
import logging
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.getcwd())

from src.engine.features import FeatureEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase6")

def test_feature_engine():
    engine = FeatureEngine()

    # 1. Test basic calculations (no history)
    logger.info("Testing basic feature calculations...")
    asset = {
        "symbol": "BTCUSDT",
        "open_interest": "1000",
        "prior_open_interest": "900",
        "open_interest_value": "50000000",
        "turnover_24h": "100000000"
    }
    
    enriched = engine.calculate_features(asset)
    
    # Expected OI Change: ((1000-900)/900)*100 = 11.1111
    assert abs(enriched["oi_change_pct_15m"] - 11.1111) < 0.001
    # Expected Vol/OI Ratio: 100M / 50M = 2.0
    assert enriched["vol_oi_ratio"] == 2.0
    # Expected Flags
    assert enriched["insufficient_history"] is True
    assert enriched["oi_zscore_30d"] == 0.0

    # 2. Test Z-Score calculations with mock history
    logger.info("Testing Z-Score calculations with mock history...")
    
    # Generate 50 rows of history for BTCUSDT
    history_data = {
        "symbol": ["BTCUSDT"] * 50,
        "oi_change_pct_15m": np.random.normal(0, 1, 50), # Mean 0, Std 1
        "vol_oi_ratio": np.random.normal(1.5, 0.2, 50)   # Mean 1.5, Std 0.2
    }
    history_df = pd.DataFrame(history_data)
    
    # Set a high OI change and high volume to see positive Z-Scores
    asset_anomaly = {
        "symbol": "BTCUSDT",
        "open_interest": "1200", # +20% from 1000
        "prior_open_interest": "1000",
        "open_interest_value": "50000000",
        "turnover_24h": "150000000" # Vol/OI = 3.0
    }
    
    enriched_anomaly = engine.calculate_features(asset_anomaly, history_df)
    
    logger.info(f"OI Change Pct: {enriched_anomaly['oi_change_pct_15m']}")
    logger.info(f"OI Z-Score: {enriched_anomaly['oi_zscore_30d']}")
    logger.info(f"Vol/OI Ratio: {enriched_anomaly['vol_oi_ratio']}")
    logger.info(f"Vol/OI Z-Score: {enriched_anomaly['vol_oi_zscore_30d']}")
    
    assert enriched_anomaly["insufficient_history"] is False
    assert enriched_anomaly["oi_zscore_30d"] > 0
    assert enriched_anomaly["vol_oi_zscore_30d"] > 0

    logger.info("Phase 6 Test Passed!")

if __name__ == "__main__":
    test_feature_engine()
