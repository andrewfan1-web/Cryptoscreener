import logging
import asyncio
from typing import Dict, List, Optional
from src.clients.bybit import BybitClient
from src.clients.coingecko import CoinGeckoClient

logger = logging.getLogger("SymbolMapper")

class SymbolMapper:
    """
    Handles mapping between Bybit symbols and CoinGecko metadata.
    Creates a merged market snapshot for the screener.
    """

    def __init__(self, bybit_client: BybitClient, cg_client: CoinGeckoClient):
        self.bybit = bybit_client
        self.cg = cg_client

    async def get_merged_snapshot(self) -> List[Dict]:
        """
        Fetches data from both Bybit and CoinGecko and merges them (Async).
        Primary key for Bybit is 'symbol' (e.g., BTCUSDT).
        Primary key for CoinGecko is 'symbol' (e.g., btc).
        """
        logger.info("Fetching market data from Bybit and CoinGecko...")
        # Fetch both concurrently
        bybit_tickers, cg_markets = await asyncio.gather(
            self.bybit.get_tickers(),
            self.cg.get_markets()
        )

        if not bybit_tickers:
            logger.error("No Bybit tickers fetched. Snapshot cannot be created.")
            return []

        # Create a mapping dictionary from CoinGecko: symbol (lowercase) -> metadata
        cg_map = {m["symbol"].lower(): m for m in cg_markets}

        merged_data = []
        for ticker in bybit_tickers:
            symbol = ticker["symbol"]
            
            # We assume Bybit USDT perpetuals end with 'USDT'
            # Extract the base symbol (e.g., BTC from BTCUSDT)
            if not symbol.endswith("USDT"):
                continue
            
            base_symbol = symbol.replace("USDT", "").lower()
            
            # Find matching CoinGecko data
            cg_metadata = cg_map.get(base_symbol)
            
            # Assemble the normalized snapshot entry
            # Fields required by Phase 3 & 4
            entry = {
                "symbol": symbol,  # Bybit full symbol
                "base_symbol": base_symbol.upper(),
                "last_price": float(ticker.get("lastPrice", 0)),
                "mark_price": float(ticker.get("markPrice", 0)),
                "index_price": float(ticker.get("indexPrice", 0)),
                "open_interest": float(ticker.get("openInterest", 0)),
                "open_interest_value": float(ticker.get("openInterestValue", 0)),
                "turnover_24h": float(ticker.get("turnover24h", 0)),
                "volume_24h": float(ticker.get("volume24h", 0)),
                "funding_rate": float(ticker.get("fundingRate", 0)),
                "price_24h_pcnt": float(ticker.get("price24hPcnt", 0)),
                # CoinGecko fields (optional if no match found)
                "market_cap": cg_metadata.get("market_cap") if cg_metadata else None,
                "market_cap_rank": cg_metadata.get("market_cap_rank") if cg_metadata else None,
                "cg_id": cg_metadata.get("id") if cg_metadata else None,
                "cg_name": cg_metadata.get("name") if cg_metadata else None,
                "cg_price": cg_metadata.get("current_price") if cg_metadata else None,
                "cg_volume_24h": cg_metadata.get("total_volume") if cg_metadata else None,
                "cg_price_change_24h": cg_metadata.get("price_change_percentage_24h") if cg_metadata else None
            }
            merged_data.append(entry)

        logger.info(f"Merged snapshot created with {len(merged_data)} symbols.")
        return merged_data
