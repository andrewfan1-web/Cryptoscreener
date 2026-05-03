import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.config import Config
from src.engine.orchestrator import Orchestrator

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

async def main():
    print("--- CRYPTOSCREENER V6.3 ---")
    try:
        # 1. Validate Config
        Config.validate()
        
        # 2. Initialize Orchestrator
        orchestrator = Orchestrator()
        
        # 3. Start Loop
        logger.info("Application starting...")
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
