from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
from telegram.helpers import escape_markdown
import os
from dotenv import load_dotenv
from Exceptions.ServiceExceptions import *
from Services.signalService import SignalService
from Services.subscriptionService import SubscriptionService
from Services.DailyAnalysisService import DailyAnalysisService
import redis,json,threading,time
import asyncio
import logging,traceback
from logging.handlers import RotatingFileHandler
from Database.DataModels.Subscribers import Subscribers
from Backtest.Portfolio import *
from functools import wraps
from Utility.UtilityClass import UtilityFunctions as utility
from Utility.ImageGeneration import ImageGenerator as imagegen
from Utility.Logger import Logger

class TelegramBot:
    def __init__(self,testing=False):
        load_dotenv()
        self.CAPITAL_UPDATE = 1
        self.TELEGRAM_TOKEN = os.getenv("BOT_API")
        self.image_path = os.getenv("IMAGE_PATH")
        self.btcservice = SignalService("BTCUSDT",500)
        self.bnbservice = SignalService("BNBUSDT",threshold=5)
        self.paxgservice = SignalService("PAXGUSDT",10)
        self.ethservice = SignalService("ETHUSDT",10)
        self.solservice = SignalService("SOLUSDT",2)
        self.subscriptionService = SubscriptionService()
        self.app = Application.builder().token(self.TELEGRAM_TOKEN).post_init(self.post_init).post_stop(self.stop).build()
        self.redis = redis.Redis(host = '127.0.0.1',port = 6379,db=0)
        self.pubsub = self.redis.pubsub()
        if testing:
            self.pubsub.subscribe("test_signals_channel")
        self.pubsub.subscribe("signals_channel")
        self.pubsub.subscribe("ath_channel")
        self.pubsub.subscribe("service_error")
        self.CALLBACK_MAP = {
            "btc_zones" : "get_btc_zones",
            "subscribe" : "subscribe",
            "help" : "help",
            "btc_signals" : "get_given_btc_signals",
            "update_capital" : "update_subscriber_capital"
        }
        self.listener_task = None
        self.logger = Logger()
        self.stop_event = asyncio.Event()

    def restricted(min_tier=1, admin_only=False,for_starter = False):
        def decorator(func):
            @wraps(func)
            async def wrapper(self,update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                try:
                    message = self.get_message(update)
                    user_id = update.effective_user.id
                    user = self.subscriptionService.getByChatID(user_id)

                    if not for_starter:

                        if not user:
                            await message.reply_text("❌ You are not registered.")
                            return

                        if admin_only and not user['is_admin']:
                            await message.reply_text("🚫 Admins only.")
                            return

                        if not user['is_admin'] and user['tier'] < min_tier:
                            await message.reply_text(
                                f"⚠️ This command requires *Tier {min_tier}* or higher. Please upgrade your subscription.",
                                parse_mode="Markdown"
                            )
                            return
                    return await func(self,update, context,user, *args, **kwargs)
                except EmptyTelegramMessage as e:
                    self.logger.error(f'{str(e)}')
                    return
            return wrapper
        return decorator

    async def post_init(self, app: Application):
        await self.startMessage()
        # Start Redis listener as background task once loop is running
        self.listener_task=app.create_task(self.listener())

    # ---------------- Handlers ----------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            keyboard = [
                [InlineKeyboardButton("📊 View BTCUSDT Zones", callback_data="btc_zones")],
                [InlineKeyboardButton("📈 View BTCUSDT Signals", callback_data="btc_signals")],
                [InlineKeyboardButton("🔔 Subscribe for Signals", callback_data="subscribe")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                "👋 *Welcome to ChaoticX Bot!*\n\n"
                "I’m your trading assistant for detecting smart money concepts 📈.\n\n"
                "✨ What I can do for you:\n"
                "• `/btc_zones` → Show latest zone formations (FVGs, OBs, Liquidity)\n"
                "• `/btc_signals` → Show latest BTC signal informations\n"
                "• `/subscribe` → Get real-time signals when new setups appear\n"
                "• `/help` → Learn how to use me\n\n"
                "⚡ Let’s start trading smarter!"
            )

            await message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(for_starter=True)  # all registered users can use help
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user):
        try:
            message = self.get_message(update)
            keyboard = [
                [InlineKeyboardButton("📊 BTCUSDT Zones", callback_data="btc_zones")],
                [InlineKeyboardButton("🔔 Subscribe", callback_data="subscribe")],

            ]
            if user is not None and (user['tier']>1 or user['is_admin']):
                keyboard.append([InlineKeyboardButton("💰 Update Capital", callback_data="update_capital")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            if user is None:
                tier = 0
            else:
                tier = user['tier']
            help_text = (
                "🤖 *ChaoticX Bot Help*\n\n"
                "Here’s what I can do for you:\n\n"
                "• `/btc_zones` → Show the latest zone formations (FVGs, OBs, Liquidity).\n"
                "• `/subscribe` → Subscribe to real-time signals when setups appear and increase ur tier to 1.\n"
                "• `/update_capital` → Update your portfolio capital size.\n"
                "• `/cancel` → Cancel an ongoing action (like capital update).\n\n"
                "⚡ *Your Tier:* {tier}\n"
                "Use the buttons below for quick access 👇"
            ).format(tier=tier)

            await message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            text = self.subscriptionService.subscribeUsingTelegram(chat_id)
            await message.reply_text(text=text)
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')


    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            text = self.subscriptionService.unsubscribeUsingTelegram(chat_id)
            await message.reply_text(text=text)
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(for_starter=True)
    async def get_btc_zones(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = await self.btcservice.zoneHandler.get_untouched_zones(limit= 5)
                sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
                msg = f"📊 *Recent BTCUSDT Zones*\n\n"
                for i, zz in enumerate(sorted_zones, start=1):
                    zone_type = zz["zone_type"]
                    zone_high = zz["zone_high"]
                    zone_low = zz["zone_low"]
                    zone_time = zz["timestamp"]

                    emoji = "🟩" if ("Bullish" in zone_type or "Buy-Side" in zone_type) else "🟥" if ("Bearish" in zone_type or "Sell-Side" in zone_type) else "⚪"

                    msg += (
                        f"{emoji} *Zone {i}*\n"
                        f"• *Type:* {utility.escape_md(zone_type)}\n"
                        f"• *High:* `{utility.escape_md(zone_high)}`\n"
                        f"• *Low:* `{utility.escape_md(zone_low)}`\n"
                        f"• *Time:* `{utility.escape_md(zone_time)}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except NoUntouchedZone as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(for_starter=True)
    async def get_given_btc_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.btcservice.get_given_signals()
                msg = f"📊 *Recent BTCUSDT Signals*\n\n"
                if user is not None and (user['tier'] > 1 or user['is_admin']):
                    porfolio = Portfolio(starting_balance= user['capital'])
                    for i,s in enumerate(signals,start=1):
                        
                        lot_size = porfolio.risk_position_size(s['entry_price'],s['sl'],user['risk_size'])
                        side = s["position"].upper()
                        emoji = "🟩" if side == "LONG" else "🟥"
                        rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                        msg += (
                            f"{emoji} *Signal {i}*\n"
                            f"• *Side:* {side}\n"
                            f"• *Symbol:* `{s['symbol']}`\n"
                            f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                            f"• *TP:* `{float(s['tp']):,.2f}`\n"
                            f"• *SL:* `{float(s['sl']):,.2f}`\n"
                            f"• *Lot Size:* `{float(lot_size):,.4f}`\n"
                            f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                        )
                else:
                    for i,s in enumerate(signals,start=1):
                        side = s["position"].upper()
                        emoji = "🟩" if side == "LONG" else "🟥"
                        rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                        msg += (
                            f"{emoji} *Signal {i}*\n"
                            f"• *Side:* {side}\n"
                            f"• *Symbol:* `{s['symbol']}`\n"
                            f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                            f"• *TP:* `{float(s['tp']):,.2f}`\n"
                            f"• *SL:* `{float(s['sl']):,.2f}`\n"
                            f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                        )
                await message.reply_text(msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(for_starter=True)
    async def get_btc_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                msg = DailyAnalysisService("BTCUSDT").get_daily_report()
                safe_msg = escape_markdown(msg, version=2)
                await message.reply_text(safe_msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=2)
    async def get_bnb_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = await self.bnbservice.zoneHandler.get_untouched_zones(limit= 5)
                sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
                msg = f"📊 *Recent BNBUSDT Zones*\n\n"
                for i, zz in enumerate(sorted_zones, start=1):
                    zone_type = zz["zone_type"]
                    zone_high = zz["zone_high"]
                    zone_low = zz["zone_low"]
                    zone_time = zz["timestamp"]

                    emoji = "🟩" if ("Bullish" in zone_type or "Buy-Side" in zone_type) else "🟥" if ("Bearish" in zone_type or "Sell-Side" in zone_type) else "⚪"

                    msg += (
                        f"{emoji} *Zone {i}*\n"
                        f"• *Type:* {utility.escape_md(zone_type)}\n"
                        f"• *High:* `{utility.escape_md(zone_high)}`\n"
                        f"• *Low:* `{utility.escape_md(zone_low)}`\n"
                        f"• *Time:* `{utility.escape_md(zone_time)}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except NoUntouchedZone as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=2)
    async def get_given_bnb_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.bnbservice.get_given_signals()
                msg = f"📊 *Recent BNBUSDT Signals*\n\n"
                portfolio = Portfolio(starting_balance=user["capital"])
                for i, s in enumerate(signals, start=1):
                    
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                        f"• *TP:* `{float(s['tp']):,.2f}`\n"
                        f"• *SL:* `{float(s['sl']):,.2f}`\n"
                        f"• *Lot Size:* `{float(lot_size):,.4f}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=2)
    async def get_bnb_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                msg = DailyAnalysisService("BNBUSDT").get_daily_report()
                safe_msg = escape_markdown(msg, version=2)
                await message.reply_text(safe_msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_paxg_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = await self.paxgservice.zoneHandler.get_untouched_zones(limit= 5)
                sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
                msg = f"📊 *Recent PAXGUSDT Zones*\n\n"
                for i, zz in enumerate(sorted_zones, start=1):
                    zone_type = zz["zone_type"]
                    zone_high = zz["zone_high"]
                    zone_low = zz["zone_low"]
                    zone_time = zz["timestamp"]

                    emoji = "🟩" if ("Bullish" in zone_type or "Buy-Side" in zone_type) else "🟥" if ("Bearish" in zone_type or "Sell-Side" in zone_type) else "⚪"

                    msg += (
                        f"{emoji} *Zone {i}*\n"
                        f"• *Type:* {utility.escape_md(zone_type)}\n"
                        f"• *High:* `{utility.escape_md(zone_high)}`\n"
                        f"• *Low:* `{utility.escape_md(zone_low)}`\n"
                        f"• *Time:* `{utility.escape_md(zone_time)}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except NoUntouchedZone as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_given_paxg_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.paxgservice.get_given_signals()
                msg = f"📊 *Recent PAXGUSDT Signals*\n\n"
                portfolio = Portfolio(starting_balance=user["capital"])
                for i, s in enumerate(signals, start=1):
                    
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                        f"• *TP:* `{float(s['tp']):,.2f}`\n"
                        f"• *SL:* `{float(s['sl']):,.2f}`\n"
                        f"• *Lot Size:* `{float(lot_size):,.4f}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_paxg_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                msg = DailyAnalysisService("PAXGUSDT").get_daily_report()
                safe_msg = escape_markdown(msg, version=2)
                await message.reply_text(safe_msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_eth_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = await self.ethservice.zoneHandler.get_untouched_zones(limit= 5)
                sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
                msg = f"📊 *Recent ETHUSDT Zones*\n\n"
                for i, zz in enumerate(sorted_zones, start=1):
                    zone_type = zz["zone_type"]
                    zone_high = zz["zone_high"]
                    zone_low = zz["zone_low"]
                    zone_time = zz["timestamp"]

                    emoji = "🟩" if ("Bullish" in zone_type or "Buy-Side" in zone_type) else "🟥" if ("Bearish" in zone_type or "Sell-Side" in zone_type) else "⚪"

                    msg += (
                        f"{emoji} *Zone {i}*\n"
                        f"• *Type:* {utility.escape_md(zone_type)}\n"
                        f"• *High:* `{utility.escape_md(zone_high)}`\n"
                        f"• *Low:* `{utility.escape_md(zone_low)}`\n"
                        f"• *Time:* `{utility.escape_md(zone_time)}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except NoUntouchedZone as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_given_eth_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.ethservice.get_given_signals()
                msg = f"📊 *Recent ETHUSDT Signals*\n\n"
                portfolio = Portfolio(starting_balance=user["capital"])
                for i, s in enumerate(signals, start=1):
                    
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                        f"• *TP:* `{float(s['tp']):,.2f}`\n"
                        f"• *SL:* `{float(s['sl']):,.2f}`\n"
                        f"• *Lot Size:* `{float(lot_size):,.4f}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_eth_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                msg = DailyAnalysisService("ETHUSDT").get_daily_report()
                safe_msg = escape_markdown(msg, version=2)
                await message.reply_text(safe_msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_sol_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = await self.solservice.zoneHandler.get_untouched_zones(limit= 5)
                sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
                msg = f"📊 *Recent SOLUSDT Zones*\n\n"
                for i, zz in enumerate(sorted_zones, start=1):
                    zone_type = zz["zone_type"]
                    zone_high = zz["zone_high"]
                    zone_low = zz["zone_low"]
                    zone_time = zz["timestamp"]

                    emoji = "🟩" if ("Bullish" in zone_type or "Buy-Side" in zone_type) else "🟥" if ("Bearish" in zone_type or "Sell-Side" in zone_type) else "⚪"

                    msg += (
                        f"{emoji} *Zone {i}*\n"
                        f"• *Type:* {utility.escape_md(zone_type)}\n"
                        f"• *High:* `{utility.escape_md(zone_high)}`\n"
                        f"• *Low:* `{utility.escape_md(zone_low)}`\n"
                        f"• *Time:* `{utility.escape_md(zone_time)}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except NoUntouchedZone as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_given_sol_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.solservice.get_given_signals()
                msg = f"📊 *Recent SOLUSDT Signals*\n\n"
                portfolio = Portfolio(starting_balance=user["capital"])
                for i, s in enumerate(signals, start=1):
                    
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{float(s['entry_price']):,.2f}`\n"
                        f"• *TP:* `{float(s['tp']):,.2f}`\n"
                        f"• *SL:* `{float(s['sl']):,.2f}`\n"
                        f"• *Lot Size:* `{float(lot_size):,.4f}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=3)
    async def get_sol_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                msg = DailyAnalysisService("SOLUSDT").get_daily_report()
                safe_msg = escape_markdown(msg, version=2)
                await message.reply_text(safe_msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    @restricted(min_tier=2)  # only Tier ≥2 or admins
    async def update_subscriber_capital(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                await message.reply_text(
                    "💰 Please enter your new capital size in *USDT* or type 'cancel' to stop:",
                    parse_mode="Markdown"
                )
                return self.CAPITAL_UPDATE
            except Exception as e:
                await message.reply_text("⚠️ An error occurred while starting update.")
                return ConversationHandler.END
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')
            return ConversationHandler.END

    @restricted(min_tier=2)  # only Tier ≥2 or admins
    async def set_capital(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                capital = float(message.text)
                self.subscriptionService.updateCapital(user['id'],capital)
                await message.reply_text(f"✅ Your capital has been updated to *{capital} USDT*.", parse_mode="Markdown")
                return ConversationHandler.END
            except ValueError:
                await message.reply_text("❌ Please enter a valid number:")
                return self.CAPITAL_UPDATE
            except ValueLessThanZero:
                await message.reply_text("⚠️ Capital must be greater than 0. Try again:")
                return self.CAPITAL_UPDATE
            except Exception as e:
                await message.reply_text("❌ Error Occur during updating!!")
                return ConversationHandler.END
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            await message.reply_text("❌ Capital update canceled.")
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')
        return ConversationHandler.END


    # ---------------- Broadcast ----------------
    async def broadcast_signals(self, signal):
        """This is called by the service when a new signal is generated."""
        if not isinstance(signal, dict):
            self.logger.error(f'{self.__class__}:Error:Invalid signal format:{signal}')
            return
        text = (
        f"📢 New Signal! Side: {signal['position']} | Token: {signal['symbol']} "
        f"| Entry: {float(signal['entry_price']):,.2f} | TP: {float(signal['tp']):,.2f} | SL: {float(signal['sl']):,.2f}"
        )
        symbol = signal['symbol']
        position = signal['position']
        path = imagegen.create_signal_card(signal,template=f'{self.image_path}/{symbol}_{position}_template.jpg',output_path=f'{self.image_path}/{symbol}_signal.jpg')
        try:
            if signal['symbol'] == "BTCUSDT":
                subscribers = self.subscriptionService.getActiveSubscribers()
                for s in subscribers:
                    if s['is_admin'] == True or s['tier'] > 1:
                        porfolio = Portfolio(starting_balance= s['capital'])
                        lot_size = porfolio.risk_position_size(float(signal['entry_price']),float(signal['sl']),s['risk_size'])
                        temp_text = text + f"| Lot Size: {float(lot_size):,.4f}"
                        
                        await self.app.bot.send_photo(chat_id=s['chat_id'], photo=open(path, 'rb'),caption=temp_text, parse_mode="Markdown")
                        
                    else:
                        
                        await self.app.bot.send_photo(chat_id=s['chat_id'], photo=open(path, 'rb'),caption=text, parse_mode="Markdown")
                    
            elif signal['symbol'] == "BNBUSDT" :
                subscribers = self.subscriptionService.getActiveSubscribers(tier=2)
                for s in subscribers:
                    porfolio = Portfolio(starting_balance= s['capital'])
                    lot_size = porfolio.risk_position_size(float(signal['entry_price']),float(signal['sl']),s['risk_size'])
                    temp_text = text + f"| Lot Size: {float(lot_size):,.4f}"
                    await self.app.bot.send_photo(chat_id=s['chat_id'], photo=open(path, 'rb'),caption=temp_text, parse_mode="Markdown")
            elif signal['symbol'] in ["PAXGUSDT","ETHUSDT","SOLUSDT"] :
                subscribers = self.subscriptionService.getActiveSubscribers(tier=3)
                for s in subscribers:
                    porfolio = Portfolio(starting_balance= s['capital'])
                    lot_size = porfolio.risk_position_size(float(signal['entry_price']),float(signal['sl']),s['risk_size'])
                    temp_text = text + f"| Lot Size: {float(lot_size):,.4f}"
                    await self.app.bot.send_photo(chat_id=s['chat_id'], photo=open(path, 'rb'),caption=temp_text, parse_mode="Markdown")
        except Forbidden:
            print(f"Cannot send message to {s['chat_id']}: bot was blocked.")

    async def broadcast_ath(self,data):
        if not isinstance(data, dict):
            self.logger.error(f'{self.__class__}:Error:Invalid data format:{data}')
            return
        text = (
        f"📢 New ATH! in Token: {data['symbol']} "
        f"with Price {data['zone_high']}"
        )
        try:
            if data['symbol'] == "BTCUSDT":
                subscribers = self.subscriptionService.getActiveSubscribers()
                for s in subscribers:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
            elif data['symbol'] == "BNBUSDT" :
                subscribers = self.subscriptionService.getActiveSubscribers(tier=2)
                for s in subscribers:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
            elif data['symbol'] in ["PAXGUSDT","ETHUSDT","SOLUSDT"] :
                subscribers = self.subscriptionService.getActiveSubscribers(tier=3)
                for s in subscribers:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
        except Forbidden:
            print(f"Cannot send message to {s['chat_id']}: bot was blocked.")
        
    async def broadcast_error(self,data):
        subscribers = self.subscriptionService.getActiveSubscribers(admin_only=True)
        for s in subscribers:
                await self.app.bot.send_message(chat_id=s['chat_id'], text=f"{data}")

    async def listener(self):
        """Redis listener that auto-reconnects and supports graceful shutdown."""
        def blocking_listen():
            """Blocking loop wrapped in thread — respects stop_event."""
            while not self.stop_event.is_set():
                try:
                    for message in self.pubsub.listen():
                        if self.stop_event.is_set():
                            break
                        if message["type"] != "message":
                            continue
                        data = json.loads(message["data"])
                        channel = message["channel"].decode()
                        return channel, data
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                    self.logger.error(f"{self.__class__}:⚠️ Redis connection lost inside blocking loop.")
                    raise
                except Exception as e:
                    self.logger.error(f"{self.__class__}:❌ Blocking listener error: {e}",True)
                    traceback.print_exc()
                    time.sleep(2)
            return None, None

        while not self.stop_event.is_set():
            try:
                self.logger.info("🚀 Starting Redis listener...")
                # Keep reading messages until stopped
                while not self.stop_event.is_set():
                    channel, data = await asyncio.to_thread(blocking_listen)
                    if not channel or not data or self.stop_event.is_set():
                        continue

                    try:
                        if channel == "signals_channel" or channel == "test_signals_channel":
                            await self.broadcast_signals(data)
                        elif channel == "ath_channel":
                            await self.broadcast_ath(data)
                        elif channel == "service_error":
                            await self.broadcast_error(data)
                    except Exception as inner_e:
                        self.logger.error(f"{self.__class__}:❌ Error processing message from {channel}: {inner_e}",True)
                        traceback.print_exc()

            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                if self.stop_event.is_set():
                    break
                self.logger.info("🔌 Redis disconnected. Attempting to reconnect in 5s...")
                await asyncio.sleep(5)
                try:
                    self.redis = redis.Redis(host="127.0.0.1", port=6379, db=0)
                    self.pubsub = self.redis.pubsub()
                    self.pubsub.subscribe("signals_channel", "ath_channel", "service_error")
                    self.logger.info("✅ Reconnected to Redis.")
                except Exception as reconnect_err:
                    self.logger.error(f"❗ Failed to reconnect to Redis: {reconnect_err}")
                    await asyncio.sleep(10)

            except asyncio.CancelledError:
                self.logger.info("🛑 Listener task cancelled — shutting down cleanly.")
                break

            except Exception as e:
                self.logger.error(f"⚠️ Listener crashed: {e}")
                traceback.print_exc()
                if not self.stop_event.is_set():
                    self.logger.info("🔁 Restarting listener in 5 seconds...")
                    await asyncio.sleep(5)

        self.logger.info("👋 Listener exited.")
                
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        action = self.CALLBACK_MAP.get(query.data)
        if not action:
            await query.edit_message_text("❌ Unknown action.")
            return

        func = getattr(self, action, None)
        if func is None:
            await query.edit_message_text("⚠️ Handler not implemented yet.")
            return
        user_id = update.effective_user.id
        user = self.subscriptionService.getByChatID(user_id)
        if action == "update_subscriber_capital" :
            await query.answer()
            return
        # ✅ Try calling function normally (decorator handles user check)
        try:
            return await func(update, context)
        except TypeError as e:
            # If function explicitly expects user, resolve it manually
            if "missing 1 required positional argument: 'user'" in str(e):

                return await func(update, context, user)
            else:
                raise e
        
    def get_message(self,update: Update):
        if update.message:
            return update.message
        elif update.callback_query:
            return update.callback_query.message
        else:
            raise EmptyTelegramMessage

    def run(self):
        # Register bot handlers
        capital_update_handler = ConversationHandler(
        entry_points=[CommandHandler("update_capital", self.update_subscriber_capital),
                CallbackQueryHandler(self.update_subscriber_capital, pattern="^update_capital$")],
        states={
            self.CAPITAL_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_capital)],
        },
        fallbacks=[CommandHandler("cancel", self.cancel)],per_chat =  True
        )
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("btc_zones", self.get_btc_zones))
        self.app.add_handler(CommandHandler("btc_signals", self.get_given_btc_signals))
        self.app.add_handler(CommandHandler("btc_analysis", self.get_btc_analysis))
        self.app.add_handler(CommandHandler("bnb_zones", self.get_bnb_zones))
        self.app.add_handler(CommandHandler("bnb_signals", self.get_given_bnb_signals))
        self.app.add_handler(CommandHandler("bnb_analysis", self.get_bnb_analysis))
        self.app.add_handler(CommandHandler("paxg_zones", self.get_paxg_zones))
        self.app.add_handler(CommandHandler("paxg_signals", self.get_given_paxg_signals))
        self.app.add_handler(CommandHandler("paxg_analysis", self.get_paxg_analysis))
        self.app.add_handler(CommandHandler("eth_zones", self.get_eth_zones))
        self.app.add_handler(CommandHandler("eth_signals", self.get_given_eth_signals))
        self.app.add_handler(CommandHandler("eth_analysis", self.get_eth_analysis))
        self.app.add_handler(CommandHandler("sol_zones", self.get_sol_zones))
        self.app.add_handler(CommandHandler("sol_signals", self.get_given_sol_signals))
        self.app.add_handler(CommandHandler("sol_analysis", self.get_sol_analysis))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(capital_update_handler)
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        self.app.run_polling()

    async def startMessage(self):
        subscribers = self.subscriptionService.getActiveSubscribers()
        text = (f'✅ We’re back online!\n'
                'ChaoticX has completed its latest update — new optimizations, smoother signals, and improved stability are now live.\n\n'

                '📊 Start receiving signals again and let’s get back to trading smarter!\n\n'

                '💥 Welcome back to the chaos!')
        for s in subscribers:
            try:
                await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
            except Forbidden:
                print(f"Cannot send message to {s['chat_id']}: bot was blocked.")

    async def stop(self,app = None):
        """Gracefully stop listener and app"""
        self.logger.info("⚙️ Stopping TelegramBot tasks...")
        self.stop_event.set()
        if self.listener_task:
            self.listener_task.cancel()
            subscribers = self.subscriptionService.getActiveSubscribers()
            text = (f'🚧 ChaoticX is going offline for a quick update!\n'
                'We’re upgrading systems and polishing things up to make your trading insights even sharper.\n'
                'The bot will be temporarily unavailable during this maintenance period.\n\n'

                '⏳ Don’t worry — we’ll be back soon, faster and smarter than ever!\n\n'

                '💬 Stay tuned for the comeback notification 👇')
            for s in subscribers:
                try:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
                except Forbidden:
                    print(f"Cannot send message to {s['chat_id']}: bot was blocked.")
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        if self.pubsub:
            try:
                self.pubsub.close()
            except Exception:
                pass

        self.logger.info("✅ TelegramBot stopped.")
