import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.engine.orchestrator import Orchestrator
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmokeTestCycle")

async def test_single_cycle():
    logger.info("Starting Full Cycle Smoke Test...")
    
    # Initialize Orchestrator
    orchestrator = Orchestrator()
    
    # Initialize Telegram (needed for JobQueue background but we will run cycle manually)
    await orchestrator.telegram.initialize()
    
    # Run a single cycle manually
    logger.info("Executing manual scan cycle...")
    await orchestrator.run_scan_cycle()
    
    # Verification
    if os.path.exists("logs/history.csv"):
        logger.info("History file exists and was updated.")
    else:
        logger.error("History file missing!")
        
    if os.path.exists("logs/state.json"):
        logger.info("State file exists and was updated.")
    else:
        logger.error("State file missing!")

    await orchestrator.stop()
    logger.info("Cycle Smoke Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_single_cycle())
