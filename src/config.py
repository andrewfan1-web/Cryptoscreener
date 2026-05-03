import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Config")

# Suppress noisy library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class Config:
    """
    Project configuration and validation.
    As per Phase 1 requirements, this provides explicit startup validation.
    """
    # Secrets
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    COINALYZE_API_KEY = os.getenv("COINALYZE_API_KEY")

    # App Settings
    COOLDOWN_REGIME_RESET = os.getenv("COOLDOWN_REGIME_RESET", "True").lower() == "true"
    UNIVERSE_HARD_EXCLUDE_OVEREXTENDED = os.getenv("UNIVERSE_HARD_EXCLUDE_OVEREXTENDED", "False").lower() == "true"
    SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 900))
    HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 1800))
    
    # Universe Filters
    MIN_MARKET_CAP = float(os.getenv("MIN_MARKET_CAP", 10_000_000))
    MIN_VOLUME_24H = float(os.getenv("MIN_VOLUME_24H", 5_000_000))
    MIN_OI_VALUE = float(os.getenv("MIN_OI_VALUE", 1_000_000))

    # Scoring Thresholds
    OI_ZSCORE_THRESHOLD = float(os.getenv("OI_ZSCORE_THRESHOLD", 2.0))
    VOL_OI_ZSCORE_THRESHOLD = float(os.getenv("VOL_OI_ZSCORE_THRESHOLD", 1.0))

    # Risk Settings
    ATR_LOOKBACK = int(os.getenv("ATR_LOOKBACK", 14))
    ATR_SL_MULTIPLIER = float(os.getenv("ATR_SL_MULTIPLIER", 2.0))
    TP1_RR = float(os.getenv("TP1_RR", 1.5))
    TP2_RR = float(os.getenv("TP2_RR", 3.0))
    
    ENABLE_COINALYZE_ENRICHMENT = os.getenv("ENABLE_COINALYZE_ENRICHMENT", "False").lower() == "true"
    ENABLE_BINANCE_FALLBACK = os.getenv("ENABLE_BINANCE_FALLBACK", "False").lower() == "true"
    COINGECKO_CACHE_TTL_SECONDS = int(os.getenv("COINGECKO_CACHE_TTL_SECONDS", 300))
    COINGECKO_CACHE_PATH = "logs/cg_cache.json"
    LONG_ONLY_MODE = os.getenv("LONG_ONLY_MODE", "True").lower() == "true"

    @classmethod
    def validate(cls):
        """Validates critical configuration on startup."""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        
        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validated successfully.")

if __name__ == "__main__":
    # Test validation
    try:
        Config.validate()
    except ValueError as e:
        print(f"Validation Error: {e}")
