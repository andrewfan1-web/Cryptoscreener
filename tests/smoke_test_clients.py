import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.clients.bybit import BybitClient
from src.clients.coingecko import CoinGeckoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmokeTest")

def test_bybit():
    client = BybitClient()
    logger.info("Testing Bybit get_tickers...")
    tickers = client.get_tickers()
    if tickers:
        logger.info(f"Successfully fetched {len(tickers)} tickers from Bybit.")
        # Check first ticker
        t = tickers[0]
        logger.info(f"Sample ticker: {t.get('symbol')} - Price: {t.get('lastPrice')}")
    else:
        logger.error("Failed to fetch tickers from Bybit.")

    logger.info("Testing Bybit get_klines for BTCUSDT...")
    klines = client.get_klines("BTCUSDT", "60", limit=5)
    if klines:
        logger.info(f"Successfully fetched {len(klines)} klines for BTCUSDT.")
    else:
        logger.error("Failed to fetch klines from Bybit.")

    logger.info("Testing Bybit get_open_interest for BTCUSDT...")
    oi = client.get_open_interest("BTCUSDT", "15min", limit=5)
    if oi:
        logger.info(f"Successfully fetched {len(oi)} OI records for BTCUSDT.")
    else:
        logger.error("Failed to fetch OI from Bybit.")

def test_coingecko():
    client = CoinGeckoClient()
    logger.info("Testing CoinGecko get_markets...")
    markets = client.get_markets()
    if markets:
        logger.info(f"Successfully fetched {len(markets)} markets from CoinGecko.")
        # Check first market
        m = markets[0]
        logger.info(f"Sample market: {m.get('name')} ({m.get('symbol')}) - Rank: {m.get('market_cap_rank')}")
    else:
        logger.error("Failed to fetch markets from CoinGecko.")
    
    # Test cache
    logger.info("Testing CoinGecko cache (should be hit)...")
    markets_cached = client.get_markets()
    if markets_cached:
        logger.info("Cache test successful.")

if __name__ == "__main__":
    test_bybit()
    print("-" * 30)
    test_coingecko()
