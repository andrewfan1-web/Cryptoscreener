import sys
import os
import logging
import asyncio

# Add src to path
sys.path.append(os.getcwd())

from src.clients.telegram import TelegramClient
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmokeTestTelegram")

async def smoke_test_telegram():
    # Only run if credentials are present
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing. Skipping smoke test.")
        return

    client = TelegramClient()
    
    # Mock alertable asset
    asset = {
        "symbol": "BTC-USDT",
        "score": 85.5,
        "label": "ANOMALOUS_LONG_BUILDUP",
        "last_price": 50000.1234,
        "oi_zscore_30d": 3.2,
        "vol_oi_zscore_30d": 2.1,
        "risk_context": {
            "stop_loss": 48000.0,
            "tp1": 53000.0
        }
    }

    logger.info("Sending mock Telegram alert...")
    await client.initialize()
    await client.send_alert(asset)
    
    logger.info("Alert sent. Please check your Telegram chat.")
    logger.info("Wait 10 seconds for interaction testing (Quick Analysis button)...")
    await asyncio.sleep(10)
    
    await client.stop()
    logger.info("Telegram Smoke Test Complete.")

if __name__ == "__main__":
    asyncio.run(smoke_test_telegram())
