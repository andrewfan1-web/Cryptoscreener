import logging
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger("ScoringEngine")

class ScoringEngine:
    """
    Scoring and Labeling Engine for anomalous leverage detection.
    Evaluates assets based on features and assigns long-only labels.
    """

    # Labels
    LABEL_ANOMALOUS_LONG = "ANOMALOUS_LONG_BUILDUP"
    LABEL_HIGH_OI_LOW_VOL = "HIGH_OI_LOW_CONFIRMATION"
    LABEL_OVEREXTENDED = "OVEREXTENDED_ANOMALY"
    LABEL_LOW_CONFIDENCE = "LOW_CONFIDENCE_REGIME"
    LABEL_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    LABEL_PROVISIONAL_SIGNAL = "PROVISIONAL_SIGNAL"
    LABEL_NO_SIGNAL = "NO_SIGNAL"

    def score_asset(self, asset: Dict, regime: str) -> Dict:
        """
        Scores a single asset and assigns a long-only label.
        
        Rules:
        - A bearish regime may downgrade or suppress long candidates, 
          but must never produce a short trade label.
        - Overextended setups may be downgraded or suppressed according to config.
        """
        oi_zscore = asset.get("oi_zscore_30d", 0.0)
        vol_oi_zscore = asset.get("vol_oi_zscore_30d", 0.0)
        is_overextended = asset.get("is_overextended", False)
        insufficient_history = asset.get("insufficient_history", False)
        funding_rate = asset.get("funding_rate", 0.0)
        price_24h = asset.get("price_24h_pcnt", 0.0)
        
        score = 0.0
        label = self.LABEL_NO_SIGNAL
        
        # 1. Base Anomaly Detection
        # The core signal is anomalous OI expansion.
        is_oi_anomalous = oi_zscore >= Config.OI_ZSCORE_THRESHOLD
        
        # Warm-up Override: Use raw % change if history is missing
        if insufficient_history and not is_oi_anomalous:
            oi_change_pct = asset.get("oi_change_pct_15m", 0.0)
            if oi_change_pct >= 1.5: # 1.5% OI build in 15m is significant during warm-up
                is_oi_anomalous = True

        is_vol_confirming = vol_oi_zscore >= Config.VOL_OI_ZSCORE_THRESHOLD

        if is_oi_anomalous:
            score += 50.0 # Base score for OI anomaly
            
            if is_vol_confirming:
                score += 30.0 # Bonus for volume confirmation
                label = self.LABEL_ANOMALOUS_LONG
            else:
                label = self.LABEL_HIGH_OI_LOW_VOL
        
        # 2. Overextension & Price Handling
        if is_overextended:
            score -= 20.0 # Penalty for overextension
            if label == self.LABEL_ANOMALOUS_LONG:
                label = self.LABEL_OVEREXTENDED
        
        if price_24h > 15.0: # Very aggressive 24h move
            score -= 10.0 # Slight caution on vertical moves
        elif price_24h < -5.0: # Recovering from dip
            score += 5.0 # Bonus for "spring" setups

        # 3. Funding Rate Handling (Long-Only)
        # High positive funding means longs are paying shorts significantly.
        # This often precedes a "long squeeze".
        if funding_rate > 0.0005: # > 0.05% per 8h
            score -= 15.0
            if label == self.LABEL_ANOMALOUS_LONG:
                label = self.LABEL_LOW_CONFIDENCE
        elif funding_rate < 0: # Negative funding (shorts paying longs)
            score += 10.0 # Stronger bullish case for long-only

        # 4. Regime Handling
        # If regime is BEARISH, we downgrade confidence.
        if regime == "BEARISH":
            score -= 30.0
            if label in [self.LABEL_ANOMALOUS_LONG, self.LABEL_OVEREXTENDED, self.LABEL_HIGH_OI_LOW_VOL]:
                label = self.LABEL_LOW_CONFIDENCE

        # 4. History Check
        # If history is insufficient, we label as provisional if it would have been a signal
        if insufficient_history:
            if label in [self.LABEL_ANOMALOUS_LONG, self.LABEL_OVEREXTENDED]:
                label = self.LABEL_PROVISIONAL_SIGNAL
            else:
                label = self.LABEL_INSUFFICIENT_HISTORY
            score = min(score, 60.0) # Cap score higher to allow watchlist visibility

        # Final score clamping
        score = max(0.0, min(100.0, score))

        # Update asset
        updated_asset = asset.copy()
        
        # Thresholds
        is_alertable = score >= 70.0 and label == self.LABEL_ANOMALOUS_LONG
        is_watchlist = score >= 40.0 and label != self.LABEL_NO_SIGNAL

        updated_asset.update({
            "score": round(score, 2),
            "label": label,
            "is_alertable": is_alertable,
            "is_watchlist": is_watchlist
        })

        return updated_asset

    def process_universe(self, enriched_assets: List[Dict], regime: str) -> List[Dict]:
        """Scores and labels all assets in the enriched universe."""
        scored_assets = []
        for asset in enriched_assets:
            scored_assets.append(self.score_asset(asset, regime))
        
        # Sort by score descending
        scored_assets.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Scoring Engine processed {len(scored_assets)} assets. Top score: {scored_assets[0]['score'] if scored_assets else 0}")
        return scored_assets
