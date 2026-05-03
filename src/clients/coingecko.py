import requests
import json
import os
import time
import logging
import asyncio
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger("CoinGeckoClient")

class CoinGeckoClient:
    """
    CoinGecko API Client with file-backed caching.
    Uses /api/v3/coins/markets to fetch asset metadata.
    """
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.cache_path = Config.COINGECKO_CACHE_PATH
        self.cache_ttl = Config.COINGECKO_CACHE_TTL_SECONDS
        self._ensure_logs_dir()

    def _ensure_logs_dir(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    async def _read_cache(self) -> Optional[List[Dict]]:
        """Reads data from the local file cache if it exists and is fresh (Async)."""
        return await asyncio.to_thread(self._read_cache_sync)

    def _read_cache_sync(self) -> Optional[List[Dict]]:
        if not os.path.exists(self.cache_path):
            return None
        
        try:
            with open(self.cache_path, "r") as f:
                cached_data = json.load(f)
                
            timestamp = cached_data.get("timestamp", 0)
            if time.time() - timestamp < self.cache_ttl:
                logger.info("CoinGecko cache hit.")
                return cached_data.get("data")
            else:
                logger.info("CoinGecko cache expired.")
        except Exception as e:
            logger.error(f"Error reading CoinGecko cache: {e}")
            
        return None

    async def _write_cache(self, data: List[Dict]):
        """Writes data to the local file cache (Async)."""
        await asyncio.to_thread(self._write_cache_sync, data)

    def _write_cache_sync(self, data: List[Dict]):
        try:
            cache_payload = {
                "timestamp": time.time(),
                "data": data
            }
            with open(self.cache_path, "w") as f:
                json.dump(cache_payload, f)
            logger.info("CoinGecko cache updated.")
        except Exception as e:
            logger.error(f"Error writing CoinGecko cache: {e}")

    async def get_markets(self, vs_currency: str = "usd", per_page: int = 250) -> List[Dict]:
        """
        Fetches market data from CoinGecko, using cache if available (Async).
        """
        cached_data = await self._read_cache()
        if cached_data:
            return cached_data

        return await asyncio.to_thread(self._get_markets_sync, vs_currency, per_page)

    def _get_markets_sync(self, vs_currency: str, per_page: int) -> List[Dict]:
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            self._write_cache_sync(data)
            return data
        except Exception as e:
            logger.error(f"CoinGecko get_markets request failed: {e}")
            # Fallback to expired cache if request fails
            if os.path.exists(self.cache_path):
                logger.warning("CoinGecko request failed, falling back to expired cache.")
                try:
                    with open(self.cache_path, "r") as f:
                        return json.load(f).get("data", [])
                except:
                    pass
            return []
