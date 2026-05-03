import os
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger("StateManager")

class StateManager:
    """
    Handles persistence for circular memory and application state.
    
    Files:
    - logs/history.csv: 30-day circular market metrics.
    - logs/state.json: App state including cooldowns and last alerts.
    """
    
    HISTORY_PATH = "logs/history.csv"
    STATE_PATH = "logs/state.json"
    
    HISTORY_COLUMNS = [
        "timestamp", "symbol", "price", "turnover24h", "volume24h",
        "open_interest", "open_interest_value", "funding_rate",
        "price_change_15m", "price_change_1h", "oi_change_15m",
        "oi_change_1h", "oi_change_pct_15m", "vol_oi_ratio", "regime",
        "score", "label"
    ]

    def __init__(self):
        self._ensure_logs_dir()
        self.state = self._load_state()

    def _ensure_logs_dir(self):
        os.makedirs("logs", exist_ok=True)

    def _load_state(self) -> Dict:
        if os.path.exists(self.STATE_PATH):
            try:
                with open(self.STATE_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading state.json: {e}")
        return {"cooldowns": {}, "last_alerts": {}, "last_regime": None}

    def save_state(self):
        try:
            with open(self.STATE_PATH, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving state.json: {e}")

    def update_history(self, snapshot: List[Dict], regime: str):
        """
        Appends current metrics to history.csv and prunes rows older than 30 days.
        """
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        new_rows = []
        
        for asset in snapshot:
            row = {
                "timestamp": timestamp,
                "symbol": asset.get("symbol"),
                "price": asset.get("last_price", asset.get("cg_price")),
                "turnover24h": asset.get("turnover_24h"),
                "volume24h": asset.get("volume_24h"),
                "open_interest": asset.get("open_interest"),
                "open_interest_value": asset.get("open_interest_value"),
                "funding_rate": asset.get("funding_rate"),
                "price_change_15m": asset.get("price_change_15m", 0),
                "price_change_1h": asset.get("price_change_1h", 0),
                "oi_change_15m": asset.get("oi_change_15m", 0),
                "oi_change_1h": asset.get("oi_change_1h", 0),
                "oi_change_pct_15m": asset.get("oi_change_pct_15m", 0),
                "vol_oi_ratio": asset.get("vol_oi_ratio", 0),
                "regime": regime,
                "score": asset.get("score", 0.0),
                "label": asset.get("label", "NO_SIGNAL")
            }
            new_rows.append(row)

        new_df = pd.DataFrame(new_rows)
        
        if os.path.exists(self.HISTORY_PATH):
            try:
                history_df = pd.read_csv(self.HISTORY_PATH)
                combined_df = pd.concat([history_df, new_df], ignore_index=True)
            except Exception as e:
                logger.error(f"Error reading history.csv: {e}")
                combined_df = new_df
        else:
            combined_df = new_df

        # Pruning: Retain only most recent 30 days
        cutoff = timestamp - (30 * 24 * 60 * 60 * 1000)
        combined_df = combined_df[combined_df['timestamp'] >= cutoff]
        
        try:
            combined_df.to_csv(self.HISTORY_PATH, index=False)
            logger.info(f"History updated: {len(new_rows)} rows added, total {len(combined_df)} rows.")
        except Exception as e:
            logger.error(f"Error saving history.csv: {e}")

    def get_history_df(self) -> pd.DataFrame:
        """Returns the current history as a DataFrame."""
        if os.path.exists(self.HISTORY_PATH):
            try:
                return pd.read_csv(self.HISTORY_PATH)
            except Exception as e:
                logger.error(f"Error reading history.csv: {e}")
        return pd.DataFrame(columns=self.HISTORY_COLUMNS)

    def apply_cooldown_rules(self, regime_transition: bool, current_regime: str = None):
        """
        Resets cooldowns if a favorable regime transition occurred.
        (BEARISH -> BULLISH)
        """
        if Config.COOLDOWN_REGIME_RESET and regime_transition:
            # We check if it was BEARISH -> BULLISH
            if current_regime == "BULLISH":
                logger.info("Favorable regime transition detected (BEARISH -> BULLISH). Resetting cooldowns.")
                self.state["cooldowns"] = {}
                self.save_state()

    def set_cooldown(self, symbol: str, duration_minutes: int = 240):
        """Sets an alert cooldown for a symbol."""
        expiry = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.state["cooldowns"][symbol] = expiry.isoformat()
        self.save_state()

    def is_on_cooldown(self, symbol: str) -> bool:
        """Checks if a symbol is currently on alert cooldown."""
        cooldown_expiry = self.state["cooldowns"].get(symbol)
        if not cooldown_expiry:
            return False
        
        try:
            expiry_dt = datetime.fromisoformat(cooldown_expiry)
            if datetime.utcnow() < expiry_dt:
                return True
            else:
                # Clean up expired cooldown
                del self.state["cooldowns"][symbol]
                self.save_state()
                return False
        except Exception:
            return False
