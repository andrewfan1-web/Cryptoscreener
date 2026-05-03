import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestHardening")

def test_config_validation():
    logger.info("Testing Config validation with missing tokens...")
    
    # Backup
    original_token = Config.TELEGRAM_BOT_TOKEN
    
    # Test failure
    Config.TELEGRAM_BOT_TOKEN = None
    try:
        Config.validate()
        logger.error("Validation failed to block missing token!")
        assert False, "Validation should have failed"
    except ValueError as e:
        logger.info(f"Validation correctly blocked startup: {e}")
        assert "TELEGRAM_BOT_TOKEN" in str(e)
    
    # Restore
    Config.TELEGRAM_BOT_TOKEN = original_token
    logger.info("Config validation hardening test passed.")

def test_cache_safety():
    logger.info("Verifying cg_cache.json safety...")
    cache_path = "logs/cg_cache.json"
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            content = f.read()
            # Ensure no tokens or secrets are leaked into cache
            if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_BOT_TOKEN in content:
                logger.error("SECRET LEAKED INTO CACHE!")
                assert False
            else:
                logger.info("Cache safety verified.")
    else:
        logger.info("Cache file doesn't exist yet, safety test skipped.")

if __name__ == "__main__":
    test_config_validation()
    test_cache_safety()
    print("Hardening Tests Passed!")
