import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.engine.scoring import ScoringEngine
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase7")

def test_scoring_engine():
    engine = ScoringEngine()

    # Mock Config thresholds
    Config.OI_ZSCORE_THRESHOLD = 2.0
    Config.VOL_OI_ZSCORE_THRESHOLD = 1.0

    # 1. Ideal Case: High OI Anomaly + Vol Confirmation + Bullish Regime
    logger.info("Testing Ideal Case...")
    asset1 = {
        "symbol": "BTCUSDT",
        "oi_zscore_30d": 3.5,
        "vol_oi_zscore_30d": 1.5,
        "is_overextended": False,
        "insufficient_history": False
    }
    scored1 = engine.score_asset(asset1, "BULLISH")
    logger.info(f"Score: {scored1['score']} | Label: {scored1['label']}")
    assert scored1["score"] == 80.0
    assert scored1["label"] == ScoringEngine.LABEL_ANOMALOUS_LONG
    assert scored1["is_alertable"] is True

    # 2. High OI Anomaly but NO Vol Confirmation
    logger.info("Testing High OI No Vol...")
    asset2 = {
        "symbol": "ETHUSDT",
        "oi_zscore_30d": 3.0,
        "vol_oi_zscore_30d": 0.5,
        "is_overextended": False,
        "insufficient_history": False
    }
    scored2 = engine.score_asset(asset2, "BULLISH")
    logger.info(f"Score: {scored2['score']} | Label: {scored2['label']}")
    assert scored2["score"] == 50.0
    assert scored2["label"] == ScoringEngine.LABEL_HIGH_OI_LOW_VOL
    assert scored2["is_alertable"] is False

    # 3. Ideal Case but Overextended
    logger.info("Testing Overextended Anomaly...")
    asset3 = asset1.copy()
    asset3["is_overextended"] = True
    scored3 = engine.score_asset(asset3, "BULLISH")
    logger.info(f"Score: {scored3['score']} | Label: {scored3['label']}")
    assert scored3["score"] == 60.0
    assert scored3["label"] == ScoringEngine.LABEL_OVEREXTENDED

    # 4. Ideal Case but Bearish Regime
    logger.info("Testing Bearish Regime Suppression...")
    scored4 = engine.score_asset(asset1, "BEARISH")
    logger.info(f"Score: {scored4['score']} | Label: {scored4['label']}")
    assert scored4["score"] == 50.0
    assert scored4["label"] == ScoringEngine.LABEL_LOW_CONFIDENCE

    # 5. Insufficient History
    logger.info("Testing Insufficient History...")
    asset5 = asset1.copy()
    asset5["insufficient_history"] = True
    scored5 = engine.score_asset(asset5, "BULLISH")
    logger.info(f"Score: {scored5['score']} | Label: {scored5['label']}")
    assert scored5["score"] == 40.0
    assert scored5["label"] == ScoringEngine.LABEL_INSUFFICIENT_HISTORY

    logger.info("Phase 7 Test Passed!")

if __name__ == "__main__":
    test_scoring_engine()
