import pandas as pd
import logging
from typing import List, Optional

logger = logging.getLogger("RegimeEngine")

class RegimeEngine:
    """
    BTC 1h Market Regime Engine.
    Determines if the market is BULLISH or BEARISH based on BTCUSDT 1h klines.
    
    Formula: 
        - BULLISH: BTC 1h Close > 20-period EMA
        - BEARISH: BTC 1h Close <= 20-period EMA
    Lookback Window: 20 periods (requires at least 20 klines, 100 recommended for EMA stability).
    Units: Categorical (BULLISH, BEARISH).
    Null Behavior: Defaults to BEARISH if insufficient data.
    Rounding Policy: None (direct comparison).
    """
    
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

    def __init__(self):
        self.last_regime = None

    def calculate_regime(self, btc_klines: List[List]) -> str:
        """
        Calculates the current regime based on BTC 1h klines.
        Expects klines in Bybit format: [startTime, open, high, low, close, volume, turnover]
        (Bybit returns newest first).
        """
        if not btc_klines or len(btc_klines) < 20:
            logger.warning("Insufficient BTC klines for regime calculation. Defaulting to BEARISH.")
            return self.BEARISH

        try:
            # Load into DataFrame and sort oldest first
            df = pd.DataFrame(btc_klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['close'] = df['close'].astype(float)
            df['timestamp'] = df['timestamp'].astype(int)
            df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
            
            # Calculate EMA(20)
            df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
            
            current_close = df['close'].iloc[-1]
            current_ema = df['ema_20'].iloc[-1]
            
            new_regime = self.BULLISH if current_close > current_ema else self.BEARISH
            
            logger.info(f"BTC Regime Calculation: Close={current_close:.2f}, EMA20={current_ema:.2f} -> {new_regime}")
            return new_regime
            
        except Exception as e:
            logger.error(f"Error calculating regime: {e}")
            return self.BEARISH

    def get_transition_state(self, current_regime: str) -> bool:
        """
        Returns True if a regime transition occurred since the last call.
        Updates internal state.
        
        This output will later support cooldown reset logic in Phase 9.
        """
        transition = False
        if self.last_regime is not None and self.last_regime != current_regime:
            transition = True
            logger.info(f"Regime transition detected: {self.last_regime} -> {current_regime}")
        
        self.last_regime = current_regime
        return transition
