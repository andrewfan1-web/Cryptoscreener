import logging
import numpy as np
from typing import List, Dict, Optional

logger = logging.getLogger("FeatureEngine")

class FeatureEngine:
    """
    Core Feature Engine for anomalous leverage detection.
    Calculates technical features and statistical anomalies for individual assets.
    
    Required Anomaly Fields:
    - oi_change_pct_15m: ((current_oi - prior_oi) / prior_oi) * 100
    - vol_oi_ratio: volume24h / open_interest_value
    - oi_zscore_30d: Normalization of oi_change_pct_15m against 30d history.
    - vol_oi_zscore_30d: Normalization of vol_oi_ratio against 30d history.
    """

    def __init__(self):
        # Memory for 30-day Z-Scores will be integrated in Phase 9 (persistence).
        # For Phase 6, we provide the calculation logic and use a passed-in history context.
        pass

    def calculate_features(self, asset: Dict, history_df: Optional[any] = None) -> Dict:
        """
        Calculates features for a single asset.
        
        Formulae:
        - oi_change_pct_15m: Percentage change in OI over the last 15m cycle.
        - vol_oi_ratio: 24h Volume divided by current Open Interest Value (USDT).
        
        Null Behavior:
        - Returns 0.0 or None for missing data.
        - Surfaces 'insufficient_history' flag if 30d context is missing.
        """
        symbol = asset.get("symbol")
        current_oi = float(asset.get("open_interest", 0))
        prior_oi = float(asset.get("prior_open_interest", current_oi)) # Fallback to current if unknown
        oi_value = float(asset.get("open_interest_value", 0))
        volume_24h = float(asset.get("turnover_24h", 0))

        # 1. OI Change Pct 15m
        # Formula: ((current - prior) / prior) * 100
        oi_change_pct_15m = 0.0
        if prior_oi > 0:
            oi_change_pct_15m = ((current_oi - prior_oi) / prior_oi) * 100
        
        # 2. Vol / OI Ratio
        # Formula: volume24h / open_interest_value
        vol_oi_ratio = 0.0
        if oi_value > 0:
            vol_oi_ratio = volume_24h / oi_value

        # 3. Z-Score Calculations (Stat Anomaly)
        # In this phase, we look for history in the provided history_df.
        # If no history, we flag it.
        oi_zscore = 0.0
        vol_oi_zscore = 0.0
        insufficient_history = True

        if history_df is not None and not history_df.empty:
            # Filter history for this specific symbol
            symbol_history = history_df[history_df['symbol'] == symbol]
            
            if len(symbol_history) >= 20: # Arbitrary minimum for "some" stats
                insufficient_history = False
                
                # OI Change Z-Score
                oi_history = symbol_history['oi_change_pct_15m'].values
                oi_mean = np.mean(oi_history)
                oi_std = np.std(oi_history)
                if oi_std > 0:
                    oi_zscore = (oi_change_pct_15m - oi_mean) / oi_std
                
                # Vol/OI Z-Score
                ratio_history = symbol_history['vol_oi_ratio'].values
                ratio_mean = np.mean(ratio_history)
                ratio_std = np.std(ratio_history)
                if ratio_std > 0:
                    vol_oi_zscore = (vol_oi_ratio - ratio_mean) / ratio_std

        # 4. Overextended Logic
        # Flag if the asset is highly overextended in the short term.
        # In the absence of an RSI calculation in this phase, we use 24h price change as a proxy.
        price_24h_pcnt = float(asset.get("price_24h_pcnt", asset.get("price_change_percentage_24h", 0.0)))
        is_overextended = price_24h_pcnt > 15.0

        # Update asset with calculated features
        updated_asset = asset.copy()
        updated_asset.update({
            "oi_change_pct_15m": round(oi_change_pct_15m, 4),
            "vol_oi_ratio": round(vol_oi_ratio, 4),
            "oi_zscore_30d": round(oi_zscore, 4),
            "vol_oi_zscore_30d": round(vol_oi_zscore, 4),
            "insufficient_history": insufficient_history,
            "is_overextended": is_overextended,
            "price_24h_pcnt": price_24h_pcnt
        })

        return updated_asset

    def process_universe(self, included_assets: List[Dict], history_df: Optional[any] = None) -> List[Dict]:
        """Processes all assets in the included universe."""
        enriched_assets = []
        for asset in included_assets:
            enriched_assets.append(self.calculate_features(asset, history_df))
        
        logger.info(f"Feature Engine processed {len(enriched_assets)} assets.")
        return enriched_assets
