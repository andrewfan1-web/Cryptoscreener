import requests
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("BybitClient")

class BybitClient:
    """
    Bybit V5 Public API Client.
    Implements ticker, kline, and open-interest endpoints for 'linear' category.
    """
    BASE_URL = "https://api.bybit.com"

    def __init__(self):
        self.session = requests.Session()

    async def get_tickers(self, category: str = "linear") -> List[Dict]:
        """Fetch all tickers for the specified category (Async)."""
        return await asyncio.to_thread(self._get_tickers_sync, category)

    def _get_tickers_sync(self, category: str) -> List[Dict]:
        url = f"{self.BASE_URL}/v5/market/tickers"
        params = {"category": category}
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("retCode") == 0:
                return data.get("result", {}).get("list", [])
            else:
                logger.error(f"Bybit get_tickers error: {data.get('retMsg')}")
                return []
        except Exception as e:
            logger.error(f"Bybit get_tickers request failed: {e}")
            return []

    async def get_klines(self, symbol: str, interval: str, limit: int = 200, category: str = "linear") -> List[List]:
        """Fetch klines for a specific symbol (Async)."""
        return await asyncio.to_thread(self._get_klines_sync, symbol, interval, limit, category)

    def _get_klines_sync(self, symbol: str, interval: str, limit: int, category: str) -> List[List]:
        url = f"{self.BASE_URL}/v5/market/kline"
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("retCode") == 0:
                return data.get("result", {}).get("list", [])
            else:
                logger.error(f"Bybit get_klines error for {symbol}: {data.get('retMsg')}")
                return []
        except Exception as e:
            logger.error(f"Bybit get_klines request failed for {symbol}: {e}")
            return []

    async def get_open_interest(self, symbol: str, interval: str, limit: int = 50, category: str = "linear") -> List[Dict]:
        """Fetch open interest data for a specific symbol (Async)."""
        return await asyncio.to_thread(self._get_open_interest_sync, symbol, interval, limit, category)

    def _get_open_interest_sync(self, symbol: str, interval: str, limit: int, category: str) -> List[Dict]:
        url = f"{self.BASE_URL}/v5/market/open-interest"
        params = {
            "category": category,
            "symbol": symbol,
            "intervalTime": interval,
            "limit": limit
        }
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("retCode") == 0:
                return data.get("result", {}).get("list", [])
            else:
                logger.error(f"Bybit get_open_interest error for {symbol}: {data.get('retMsg')}")
                return []
        except Exception as e:
            logger.error(f"Bybit get_open_interest request failed for {symbol}: {e}")
            return []
