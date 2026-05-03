import logging
import re
from typing import List, Dict  # Added List here
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from src.config import Config
import asyncio

logger = logging.getLogger("TelegramClient")

class TelegramClient:
    """
    Telegram Bot Client for alert delivery and interaction.
    Uses python-telegram-bot v20+ patterns.
    """

    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.application = None
        # Auto-activate if chat_id is present
        self.is_active = True if self.chat_id else False
        self.orchestrator = None # Will be set by Orchestrator

    def escape_markdown(self, text: str) -> str:
        """
        Escapes reserved characters for Telegram MarkdownV2.
        Reserved: _ * [ ] ( ) ~ ` > # + - = | { } . !
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    async def initialize(self):
        """Initializes the Telegram application instance."""
        if self.application:
            return

        if not self.token or not self.chat_id:
            logger.error("Telegram credentials missing in Config.")
            return

        self.application = ApplicationBuilder().token(self.token).build()
        
        # Add Command Handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("stop", self.handle_stop))
        self.application.add_handler(CommandHandler("hard_stop", self.handle_hard_stop))
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("help", self.handle_help))
        self.application.add_handler(CommandHandler("top", self.handle_top))
        
        # Add Callback Handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("Telegram Bot application built with command handlers.")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /start command."""
        self.is_active = True
        heartbeat_mins = Config.HEARTBEAT_INTERVAL // 60
        msg = (
            "🚀 *Cryptoscreener V6 Activated*\n\n"
            "Reporting is now **ON**\\. I will alert you to anomalous OI buildup "
            f"and send a heartbeat every {heartbeat_mins} minutes\\.\n\n"
            "Use `/status` to see current market stats\\."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

    async def handle_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /stop command (Pause reporting)."""
        self.is_active = False
        await update.message.reply_text("⏸ *Reporting Paused*\nData logging continues in the background\\.", parse_mode=ParseMode.MARKDOWN_V2)

    async def handle_hard_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /hard_stop command."""
        await update.message.reply_text("🛑 *Hard Stop Initiated*\nShutting down system\\.\\.\\.", parse_mode=ParseMode.MARKDOWN_V2)
        if self.orchestrator:
            await self.orchestrator.stop()

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /status command."""
        status = "🟢 Running" if self.is_active else "⏸ Paused"
        history_size = 0
        if self.orchestrator and self.orchestrator.state_manager:
            history_size = len(self.orchestrator.state_manager.get_history_df())
        
        # Escaping dynamic values
        status_esc = self.escape_markdown(status)
        
        msg = (
            f"📊 *System Status*\n"
            f"• *State:* `{status_esc}`\n"
            f"• *History Size:* `{history_size} entries`\n"
            f"• *Reporting:* `{'Active' if self.is_active else 'Muted'}`\n\n"
            f"Waiting for next scan cycle\\.\\.\\."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /help command."""
        help_text = (
            "🛠 *Available Commands*\n\n"
            "🚀 `/start` \\- Resume reporting and heartbeats\n"
            "⏸ `/stop` \\- Pause reporting \\(logging continues\\)\n"
            "📊 `/status` \\- System health and stats\n"
            "🏆 `/top` \\- Show top 5 anomaly candidates\n"
            "🛑 `/hard_stop` \\- Kill the bot completely\n"
            "❓ `/help` \\- Show this menu"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)

    async def handle_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /top command."""
        if not self.orchestrator or not self.orchestrator.state_manager:
            await update.message.reply_text("No data available yet\\.")
            return

        df = self.orchestrator.state_manager.get_history_df()
        if df.empty:
            await update.message.reply_text("History is currently empty\\.")
            return

        # Get top 5 from latest timestamp
        latest_ts = df['timestamp'].max()
        top_5 = df[df['timestamp'] == latest_ts].sort_values('score', ascending=False).head(5)
        
        latest_ts_esc = self.escape_markdown(str(latest_ts))
        lines = [f"🏆 *Top 5 Candidates ({latest_ts_esc})*"]
        for _, row in top_5.iterrows():
            sym = self.escape_markdown(row['symbol'])
            label = self.escape_markdown(row['label'])
            lines.append(f"• `{sym}`: Score `{row['score']:.1f}` \\| `{label}`")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2)

    async def send_heartbeat(self):
        """Sends a heartbeat message if active."""
        if not self.is_active:
            return
        
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text="💓 *Heartbeat:* System is running\\. Monitoring for signals\\.\\.\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    async def stop(self):
        """Stops the Telegram application."""
        if self.application:
            if self.application.updater and self.application.updater.running:
                await self.application.updater.stop()
            if self.application.running:
                await self.application.stop()
            
            try:
                await self.application.shutdown()
            except RuntimeError:
                pass
            
            self.application = None
            logger.info("Telegram Bot stopped.")

    async def send_alert(self, asset: Dict):
        """
        Sends a formatted alert for an anomalous asset.
        """
        if not self.application:
            await self.initialize()

        symbol = asset["symbol"]
        score = asset["score"]
        label = asset["label"].replace("_", " ")
        price = asset.get("last_price", asset.get("cg_price", 0))
        oi_z = asset.get("oi_zscore_30d", 0)
        vol_oi_z = asset.get("vol_oi_zscore_30d", 0)
        
        risk = asset.get("risk_context")
        sl_text = f"{risk['stop_loss']:.4f}" if risk else "N/A"
        tp1_text = f"{risk['tp1']:.4f}" if risk else "N/A"

        # Escape all dynamic fields
        symbol_esc = self.escape_markdown(symbol)
        label_esc = self.escape_markdown(label)
        sl_text_esc = self.escape_markdown(sl_text)
        tp1_text_esc = self.escape_markdown(tp1_text)
        
        message = (
            f"🚨 *ANOMALY DETECTED: {symbol_esc}*\n\n"
            f"🏷 *Label:* `{label_esc}`\n"
            f"🎯 *Score:* `{score:.1f}/100`\n\n"
            f"💰 *Price:* `{price:.4f}`\n"
            f"📊 *OI Z\\-Score:* `{oi_z:.2f}`\n"
            f"📈 *Vol/OI Z\\-Score:* `{vol_oi_z:.2f}`\n\n"
            f"🛡 *SL:* `{sl_text_esc}`\n"
            f"🏁 *TP1:* `{tp1_text_esc}`\n"
        )

        # Buttons
        tv_url = f"https://www.tradingview.com/chart/?symbol=BYBIT:{symbol}.P"
        keyboard = [
            [
                InlineKeyboardButton("📊 Quick Analysis", callback_data=f"qa_{symbol}"),
                InlineKeyboardButton("🔗 TradingView", url=tv_url)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
            logger.info(f"Alert sent for {symbol}")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert for {symbol}: {e}")

    async def send_cycle_summary(self, top_assets: List[Dict], regime: str):
        """
        Sends a summary of the current scan cycle to Telegram.
        """
        if not self.is_active:
            return

        regime_esc = self.escape_markdown(regime)
        lines = [
            f"📊 *Scan Cycle Summary*",
            f"• *BTC Regime:* `{regime_esc}`",
            ""
        ]

        if not top_assets:
            lines.append("No candidates found in this cycle\\.")
        else:
            lines.append("🏆 *Top Candidates & Watchlist:*")
            for asset in top_assets[:5]: # Top 5
                symbol = self.escape_markdown(asset["symbol"])
                score = asset["score"]
                label = self.escape_markdown(asset["label"].replace("_", " "))
                lines.append(f"• `{symbol}`: `{score:.1f}` \\| `{label}`")

        message = "\n".join(lines)
        
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"Failed to send cycle summary: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data.startswith("qa_"):
            symbol = data.split("_")[1]
            symbol_esc = self.escape_markdown(symbol)
            # In Phase 11, the orchestrator will provide the full analysis.
            # For now, we return a compact placeholder summary.
            summary = (
                f"📝 *Quick Analysis: {symbol_esc}*\n\n"
                f"• *1h Regime:* Bullish\n"
                f"• *15m Structure:* Expansion\n"
                f"• *Context:* Anomalous OI buildup supported by volume\\."
            )
            
            # query.message.text contains the plain text version of the message.
            # To re-send it with MARKDOWN_V2, we must escape the entire original text.
            original_text_escaped = self.escape_markdown(query.message.text)
            
            await query.edit_message_text(
                text=original_text_escaped + f"\n\n{summary}",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=query.message.reply_markup
            )

