import pandas as pd
import numpy as np
import logging
import asyncio
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger("RiskEngine")

class RiskEngine:
    """
    Risk Context Engine for anomalous leverage setups.
    Provides human-readable execution levels (SL, TP1, TP2, Invalidation) 
    for long-only candidates.
    
    Formulae:
    - ATR: Average True Range (Wilder's or Simple) over configured lookback.
    - SL: max(Local Swing Low, Entry - (ATR * ATR_SL_MULTIPLIER))
    - TP1: Entry + (Entry - SL) * TP1_RR
    - TP2: Entry + (Entry - SL) * TP2_RR
    - Invalidation: Price closing below SL or breaking local structure.
    """

    def calculate_levels(self, asset: Dict, klines_15m: List[List]) -> Dict:
        """
        Calculates risk levels for a single asset based on 15m klines.
        Expects klines in Bybit format: [startTime, open, high, low, close, volume, turnover]
        (Bybit returns newest first).
        """
        symbol = asset.get("symbol")
        current_price = float(asset.get("last_price", asset.get("cg_price", 0)))
        
        if not klines_15m or len(klines_15m) < Config.ATR_LOOKBACK + 1:
            logger.warning(f"Insufficient klines for risk levels for {symbol}. Returning partial context.")
            return self._empty_levels(asset)

        try:
            # Load into DataFrame and sort oldest first
            df = pd.DataFrame(klines_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            df['timestamp'] = df['timestamp'].astype(int)
            df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)

            # Calculate ATR
            df['prev_close'] = df['close'].shift(1)
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['prev_close']),
                    abs(df['low'] - df['prev_close'])
                )
            )
            atr = df['tr'].rolling(window=Config.ATR_LOOKBACK).mean().iloc[-1]
            
            # Local Swing Low (lowest low in lookback)
            swing_low = df['low'].tail(Config.ATR_LOOKBACK).min()
            
            # Entry Price (current price)
            entry = current_price
            
            # SL Calculation
            atr_sl = entry - (atr * Config.ATR_SL_MULTIPLIER)
            # Use the more conservative of the two or prioritize structure
            stop_loss = min(swing_low, atr_sl) if swing_low > 0 else atr_sl
            
            # Ensure SL is below entry
            if stop_loss >= entry:
                stop_loss = entry * 0.98 # Fallback 2% SL if calculation fails sanity
            
            # Risk Amount
            risk = entry - stop_loss
            
            # TP Calculations
            tp1 = entry + (risk * Config.TP1_RR)
            tp2 = entry + (risk * Config.TP2_RR)
            
            # Invalidation context
            invalidation = stop_loss
            
            risk_context = {
                "entry": round(entry, 6),
                "stop_loss": round(stop_loss, 6),
                "tp1": round(tp1, 6),
                "tp2": round(tp2, 6),
                "invalidation": round(invalidation, 6),
                "atr": round(atr, 6),
                "swing_low": round(swing_low, 6),
                "risk_reward_tp1": Config.TP1_RR,
                "risk_reward_tp2": Config.TP2_RR
            }
            
            updated_asset = asset.copy()
            updated_asset["risk_context"] = risk_context
            return updated_asset

        except Exception as e:
            logger.error(f"Error calculating risk levels for {symbol}: {e}")
            return self._empty_levels(asset)

    def _empty_levels(self, asset: Dict) -> Dict:
        updated_asset = asset.copy()
        updated_asset["risk_context"] = None
        return updated_asset

    async def process_universe(self, scored_assets: List[Dict], get_klines_func) -> List[Dict]:
        """
        Enriches alertable assets with risk context (Async).
        Note: Only processes assets that are 'is_alertable' to save API calls.
        
        get_klines_func: async function(symbol, interval) -> List[List]
        """
        tasks = []
        alertable_indices = []

        for i, asset in enumerate(scored_assets):
            if asset.get("is_alertable"):
                symbol = asset["symbol"]
                tasks.append(get_klines_func(symbol, "15"))
                alertable_indices.append(i)

        if not tasks:
            return [self._empty_levels(asset) for asset in scored_assets]

        # Fetch all klines concurrently
        all_klines = await asyncio.gather(*tasks)

        enriched_assets = []
        kline_idx = 0
        for i, asset in enumerate(scored_assets):
            if i in alertable_indices:
                klines = all_klines[kline_idx]
                enriched_assets.append(self.calculate_levels(asset, klines))
                kline_idx += 1
            else:
                enriched_assets.append(self._empty_levels(asset))
        
        return enriched_assets
