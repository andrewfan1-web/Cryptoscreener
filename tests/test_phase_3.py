import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.clients.bybit import BybitClient
from src.clients.coingecko import CoinGeckoClient
from src.engine.mapping import SymbolMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPhase3")

def test_mapping():
    bybit = BybitClient()
    cg = CoinGeckoClient()
    mapper = SymbolMapper(bybit, cg)

    logger.info("Generating merged market snapshot...")
    snapshot = mapper.get_merged_snapshot()

    if snapshot:
        logger.info(f"Successfully generated snapshot with {len(snapshot)} symbols.")
        
        # Validate structure of the first entry
        sample = snapshot[0]
        required_keys = [
            "symbol", "base_symbol", "last_price", "mark_price", "index_price",
            "open_interest", "open_interest_value", "turnover_24h", "volume_24h",
            "funding_rate", "price_24h_pcnt", "cg_name", "cg_price", "cg_volume_24h"
        ]
        
        missing_keys = [k for k in required_keys if k not in sample]
        if missing_keys:
            logger.error(f"Snapshot entry missing keys: {missing_keys}")
        else:
            logger.info("Snapshot entry structure validated.")
        
        # Look for BTCUSDT to verify mapping
        btc_entry = next((item for item in snapshot if item["symbol"] == "BTCUSDT"), None)
        if btc_entry:
            logger.info("BTCUSDT found in snapshot.")
            logger.info(f"BTC Name: {btc_entry.get('cg_name')} | Price: {btc_entry.get('cg_price')}")
            if btc_entry.get("cg_id"):
                logger.info("CoinGecko mapping successful for BTC.")
            else:
                logger.warning("CoinGecko mapping failed for BTC.")
        else:
            logger.warning("BTCUSDT not found in snapshot.")
    else:
        logger.error("Failed to generate merged snapshot.")

if __name__ == "__main__":
    test_mapping()
