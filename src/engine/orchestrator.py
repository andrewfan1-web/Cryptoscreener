import logging
import asyncio
from typing import List, Dict
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.config import Config
from src.clients.bybit import BybitClient
from src.clients.coingecko import CoinGeckoClient
from src.clients.telegram import TelegramClient
from src.engine.mapping import SymbolMapper
from src.engine.universe import UniverseFilter
from src.engine.regime import RegimeEngine
from src.engine.features import FeatureEngine
from src.engine.scoring import ScoringEngine
from src.engine.risk import RiskEngine
from src.utils.state import StateManager

logger = logging.getLogger("Orchestrator")

class Orchestrator:
    """
    Main Orchestration Loop for Cryptoscreener.
    Ties together all engines and clients into a scheduled cycle.
    """

    def __init__(self):
        self.bybit = BybitClient()
        self.cg = CoinGeckoClient()
        self.telegram = TelegramClient()
        self.telegram.orchestrator = self # Link back for commands
        
        self.mapper = SymbolMapper(self.bybit, self.cg)
        self.universe_filter = UniverseFilter()
        self.regime_engine = RegimeEngine()
        self.feature_engine = FeatureEngine()
        self.scoring_engine = ScoringEngine()
        self.risk_engine = RiskEngine()
        self.state_manager = StateManager()
        
        self.is_running = False
        self._is_scanning = False

    async def run_scan_cycle(self, context: ContextTypes.DEFAULT_TYPE = None):
        """
        Executes a single scan cycle.
        """
        if self._is_scanning:
            logger.warning("Previous scan cycle still in progress. Skipping this iteration.")
            return
            
        self._is_scanning = True
        logger.info("--- Starting Scan Cycle ---")
        try:
            # 1. Market Regime
            logger.info("Step 1: Calculating Market Regime...")
            btc_klines = await self.bybit.get_klines("BTCUSDT", "60", limit=100)
            regime = self.regime_engine.calculate_regime(btc_klines)
            transition = self.regime_engine.get_transition_state(regime)
            
            # Apply Cooldown Reset if transition occurred
            self.state_manager.apply_cooldown_rules(transition, regime)

            # 2. Merged Snapshot
            logger.info("Step 2: Generating Merged Snapshot...")
            snapshot = await self.mapper.get_merged_snapshot()
            if not snapshot:
                logger.warning("Empty snapshot. Skipping cycle.")
                return

            # 3. Universe Filtering
            logger.info("Step 3: Filtering Universe...")
            included, _ = self.universe_filter.filter_assets(snapshot)
            if not included:
                logger.info("No assets passed universe filters. Updating history and ending cycle.")
                self.state_manager.update_history(snapshot, regime)
                return

            # 4. Feature Enrichment
            logger.info("Step 4: Calculating Features...")
            history_df = self.state_manager.get_history_df()
            
            import time
            current_time_ms = int(time.time() * 1000)
            max_age_ms = Config.SCAN_INTERVAL * 2 * 1000 # Allow up to 2 intervals old
            
            # Inject prior_oi from history into included assets
            for asset in included:
                symbol = asset["symbol"]
                if not history_df.empty:
                    symbol_hist = history_df[history_df["symbol"] == symbol]
                    if not symbol_hist.empty:
                        # Last entry in history is the prior cycle
                        last_entry = symbol_hist.iloc[-1]
                        if current_time_ms - last_entry["timestamp"] <= max_age_ms:
                            asset["prior_open_interest"] = last_entry["open_interest"]
                        else:
                            logger.debug(f"Stale history for {symbol}, ignoring prior_open_interest.")
            
            enriched = self.feature_engine.process_universe(included, history_df)

            # 5. Scoring & Labeling
            logger.info("Step 5: Scoring Assets...")
            scored = self.scoring_engine.process_universe(enriched, regime)

            # 6. Risk Context (for alert candidates)
            logger.info("Step 6: Calculating Risk Levels...")
            # Note: risk_engine.process_universe needs a kline fetching function
            with_risk = await self.risk_engine.process_universe(scored, lambda s, i: self.bybit.get_klines(s, i, limit=50))

            # 7. Alerting
            logger.info("Step 7: Processing Alerts...")
            alert_candidates = []
            watchlist_candidates = []

            for asset in with_risk:
                symbol = asset["symbol"]
                if asset.get("is_alertable"):
                    alert_candidates.append(asset)
                    # Only alert if Telegram is active (/start command received)
                    if self.telegram.is_active:
                        if not self.state_manager.is_on_cooldown(symbol):
                            logger.info(f"ALERTTING: {symbol} with score {asset['score']}")
                            await self.telegram.send_alert(asset)
                            self.state_manager.set_cooldown(symbol)
                        else:
                            logger.debug(f"Skipping {symbol} (on cooldown)")
                    else:
                        logger.debug(f"Skipping {symbol} alert (Bot inactive)")
                
                if asset.get("is_watchlist"):
                    watchlist_candidates.append(asset)

            # Send Cycle Summary to Telegram
            if self.telegram.is_active:
                # Combine alert and watchlist candidates for the summary, sorted by score
                summary_assets = sorted(
                    alert_candidates + [a for a in watchlist_candidates if a not in alert_candidates],
                    key=lambda x: x["score"],
                    reverse=True
                )
                await self.telegram.send_cycle_summary(summary_assets, regime)

            # 8. State & History Persistence
            logger.info("Step 8: Persisting State & History...")
            # Update snapshot with enriched metrics before saving history
            enriched_map = {a["symbol"]: a for a in with_risk}
            for asset in snapshot:
                if asset["symbol"] in enriched_map:
                    asset.update(enriched_map[asset["symbol"]])
            
            self.state_manager.update_history(snapshot, regime)
            self.state_manager.save_state()
            
            logger.info("="*50)
            logger.info("SCAN CYCLE COMPLETE")
            logger.info(f"Next scan scheduled in {Config.SCAN_INTERVAL/60:.1f} minutes.")
            logger.info("="*50)

        except Exception as e:
            logger.error(f"Error in scan cycle: {e}", exc_info=True)

    async def send_heartbeat_job(self, context: ContextTypes.DEFAULT_TYPE):
        """JobQueue wrapper for heartbeat."""
        await self.telegram.send_heartbeat()

    async def start(self):
        """
        Starts the orchestrator with JobQueue.
        """
        if self.is_running:
            return
        
        logger.info("Starting Orchestrator...")
        await self.telegram.initialize()
        
        self.is_running = True
        try:
            async with self.telegram.application as application:
                try:
                    await application.start()
                    
                    # Notify user that bot is up
                    status_text = "Active" if self.telegram.is_active else "Muted"
                    start_hint = "" if self.telegram.is_active else "\n\nUse `/start` to begin reporting and heartbeats\\."
                    
                    await application.bot.send_message(
                        chat_id=self.telegram.chat_id,
                        text=f"🤖 *Cryptoscreener V6 is ONLINE*\nStatus: `{status_text}`\n\nMonitoring for anomalous market activity\\.{start_hint}",
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    
                    # Schedule Scan Cycle
                    application.job_queue.run_repeating(
                        self.run_scan_cycle, 
                        interval=Config.SCAN_INTERVAL, 
                        first=Config.SCAN_INTERVAL 
                    )
                    
                    # Schedule Heartbeat
                    application.job_queue.run_repeating(
                        self.send_heartbeat_job,
                        interval=Config.HEARTBEAT_INTERVAL,
                        first=Config.HEARTBEAT_INTERVAL
                    )
                    
                    await application.updater.start_polling(drop_pending_updates=True)
                    logger.info(f"Orchestrator started. Scan: {Config.SCAN_INTERVAL}s, Heartbeat: {Config.HEARTBEAT_INTERVAL}s")
                    
                    # Execute first scan manually (logging starts immediately)
                    await self.run_scan_cycle()
                    
                    # This loop keeps the script from exiting
                    while self.is_running:
                        await asyncio.sleep(1)
                finally:
                    if application.running:
                        await application.updater.stop()
                        await application.stop()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Orchestrator shutdown requested.")
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
        finally:
            self.is_running = False

    async def stop(self):
        """Stops the orchestrator."""
        if not self.is_running:
            return
        logger.info("Stopping Orchestrator...")
        self.is_running = False
