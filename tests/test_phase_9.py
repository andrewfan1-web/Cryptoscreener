import sys
import os
import logging
import pandas as pd
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.getcwd())

from src.utils.state import StateManager
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase9")

def test_state_manager():
    # Setup: Clear existing logs for clean test
    if os.path.exists("logs/history.csv"):
        os.remove("logs/history.csv")
    if os.path.exists("logs/state.json"):
        os.remove("logs/state.json")

    manager = StateManager()

    # 1. Test History Persistence & Pruning
    logger.info("Testing History Persistence & Pruning...")
    mock_snapshot = [
        {"symbol": "BTCUSDT", "last_price": 50000, "turnover_24h": 1000000, "open_interest": 100},
        {"symbol": "ETHUSDT", "last_price": 2500, "turnover_24h": 500000, "open_interest": 50}
    ]
    
    manager.update_history(mock_snapshot, "BULLISH")
    assert os.path.exists("logs/history.csv")
    df = manager.get_history_df()
    assert len(df) == 2
    assert "BTCUSDT" in df["symbol"].values

    # Test Pruning
    logger.info("Testing Pruning (Adding old data)...")
    old_timestamp = int((datetime.utcnow() - timedelta(days=31)).timestamp() * 1000)
    old_row = df.iloc[0:1].copy()
    old_row["timestamp"] = old_timestamp
    
    # Save manually then update to trigger pruning
    df_with_old = pd.concat([df, old_row])
    df_with_old.to_csv("logs/history.csv", index=False)
    
    manager.update_history(mock_snapshot, "BULLISH")
    df_pruned = manager.get_history_df()
    assert len(df_pruned) == 4 # 2 from previous update + 2 from this update. The 1 old one should be gone.
    # Wait, 2 (initial) + 1 (old) = 3. Then update_history adds 2 = 5. Pruning removes 1 = 4. Correct.
    assert old_timestamp not in df_pruned["timestamp"].values

    # 2. Test State Persistence (Cooldowns)
    logger.info("Testing Cooldown Persistence...")
    manager.set_cooldown("SOLUSDT", duration_minutes=10)
    assert manager.is_on_cooldown("SOLUSDT") is True
    
    # Reload manager to check persistence
    new_manager = StateManager()
    assert new_manager.is_on_cooldown("SOLUSDT") is True

    # 3. Test Cooldown Reset on Regime Transition
    logger.info("Testing Cooldown Reset...")
    Config.COOLDOWN_REGIME_RESET = True
    new_manager.apply_cooldown_rules(regime_transition=True)
    assert new_manager.is_on_cooldown("SOLUSDT") is False

    logger.info("Phase 9 Test Passed!")

if __name__ == "__main__":
    test_state_manager()
