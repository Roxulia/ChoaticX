from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
import os
from dotenv import load_dotenv
from Exceptions.ServiceExceptions import *
from Services.signalService import SignalService
import redis,json,threading,time
import asyncio
import logging,traceback
from logging.handlers import RotatingFileHandler
from Database.DataModels.Subscribers import Subscribers
from Backtest.Portfolio import *
from functools import wraps
from Utility.UtilityClass import UtilityFunctions as utility

class TelegramBot:
    def __init__(self, service : SignalService):
        load_dotenv()
        self.CAPITAL_UPDATE = 1
        self.TELEGRAM_TOKEN = os.getenv("BOT_API")
        self.btcservice = SignalService("BTCUSDT",300)
        self.bnbservice = SignalService("BNBUSDT",threshold=3)
        self.paxgservice = SignalService("PAXGUSDT",10)
        self.app = Application.builder().token(self.TELEGRAM_TOKEN).post_init(self.post_init).post_stop(self.stop).build()
        self.redis = redis.Redis(host = '127.0.0.1',port = 6379,db=0)
        self.pubsub = self.redis.pubsub()
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
        self.stop_event = asyncio.Event()

    def restricted(min_tier=1, admin_only=False,for_starter = False):
        def decorator(func):
            @wraps(func)
            async def wrapper(self,update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                try:
                    message = self.get_message(update)
                    user_id = update.effective_user.id
                    user = Subscribers.getByChatID(user_id)

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
                    print(f'{str(e)}')
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
            print(f'{str(e)}')

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
            print(f'{str(e)}')

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            try:
                existed = Subscribers.getByChatID(chat_id)
                if existed:
                    Subscribers.update(existed['id'],{"is_active":True})
                else:
                    Subscribers.create({"chat_id":chat_id})
                await message.reply_text("✅ Subscribed for auto broadcasts!")
            except Exception as e:
                print("Error in Database")
                await message.reply_text("Unknown Error Occur !! Pls Contact Us for Support")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')


    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            try:
                existed = Subscribers.getByChatID(chat_id)
                if existed:
                    Subscribers.update(existed['id'],{"is_active":False})
                    await message.reply_text("❌ Unsubscribed.")
                else:
                    Subscribers.create({"chat_id":chat_id,"is_active":False})
                    await message.reply_text("U Haven't Subcribed to this Channel")
            except Exception as e:
                print("Error in Database")
                await message.reply_text("Unknown Error Occur !! Pls Contact Us for Support")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')

    @restricted(for_starter=True)
    async def get_btc_zones(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = self.btcservice.get_untouched_zones(limit= 5)
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
            print(f'{str(e)}')

    @restricted(for_starter=True)
    async def get_given_btc_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.btcservice.get_given_signals()
                msg = f"📊 *Recent BTCUSDT Signals*\n\n"
                if user is not None and (user['tier'] > 1 or user['is_admin']):
                    for i,s in enumerate(signals,start=1):
                        porfolio = Portfolio(starting_balance= user['capital'])
                        lot_size = porfolio.risk_position_size(s['entry_price'],s['sl'],user['risk_size'])
                        side = s["position"].upper()
                        emoji = "🟩" if side == "LONG" else "🟥"
                        rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                        msg += (
                            f"{emoji} *Signal {i}*\n"
                            f"• *Side:* {side}\n"
                            f"• *Symbol:* `{s['symbol']}`\n"
                            f"• *Entry:* `{s['entry_price']}`\n"
                            f"• *TP:* `{s['tp']}`\n"
                            f"• *SL:* `{s['sl']}`\n"
                            f"• *Lot Size:* `{lot_size}`\n"
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
                            f"• *Entry:* `{s['entry_price']}`\n"
                            f"• *TP:* `{s['tp']}`\n"
                            f"• *SL:* `{s['sl']}`\n"
                            f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                        )
                await message.reply_text(msg,parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')

    @restricted(min_tier=2)
    async def get_bnb_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = self.bnbservice.get_untouched_zones(limit= 5)
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
            print(f'{str(e)}')

    @restricted(min_tier=2)
    async def get_given_bnb_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.bnbservice.get_given_signals()
                msg = f"📊 *Recent BNBUSDT Signals*\n\n"

                for i, s in enumerate(signals, start=1):
                    portfolio = Portfolio(starting_balance=user["capital"])
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{s['entry_price']}`\n"
                        f"• *TP:* `{s['tp']}`\n"
                        f"• *SL:* `{s['sl']}`\n"
                        f"• *Lot Size:* `{lot_size}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')

    @restricted(min_tier=3)
    async def get_paxg_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                zones = self.paxgservice.get_untouched_zones(limit= 5)
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
            print(f'{str(e)}')

    @restricted(min_tier=3)
    async def get_given_paxg_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                signals = self.paxgservice.get_given_signals()
                msg = f"📊 *Recent PAXGUSDT Signals*\n\n"

                for i, s in enumerate(signals, start=1):
                    portfolio = Portfolio(starting_balance=user["capital"])
                    lot_size = portfolio.risk_position_size(s["entry_price"], s["sl"], user["risk_size"])

                    side = s["position"].upper()
                    emoji = "🟩" if side == "LONG" else "🟥"
                    rr_ratio = round(abs((s["tp"] - s["entry_price"]) / (s["entry_price"] - s["sl"])), 2) if s["entry_price"] != s["sl"] else "N/A"

                    msg += (
                        f"{emoji} *Signal {i}*\n"
                        f"• *Side:* {side}\n"
                        f"• *Symbol:* `{s['symbol']}`\n"
                        f"• *Entry:* `{s['entry_price']}`\n"
                        f"• *TP:* `{s['tp']}`\n"
                        f"• *SL:* `{s['sl']}`\n"
                        f"• *Lot Size:* `{lot_size}`\n"
                        f"• *R/R Ratio:* `{rr_ratio}`\n\n"
                    )

                await message.reply_text(msg, parse_mode="MarkdownV2")
            except EmptySignalException as e:
                await message.reply_text(str(e))
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')

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
            print(f'{str(e)}')
            return ConversationHandler.END

    @restricted(min_tier=2)  # only Tier ≥2 or admins
    async def set_capital(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            message = self.get_message(update)
            try:
                capital = float(message.text)
                if capital <= 0:
                    await message.reply_text("⚠️ Capital must be greater than 0. Try again:")
                    return self.CAPITAL_UPDATE

                Subscribers.update(user['id'], {"capital": capital})

                await message.reply_text(f"✅ Your capital has been updated to *{capital} USDT*.", parse_mode="Markdown")
                return ConversationHandler.END

            except ValueError:
                await message.reply_text("❌ Please enter a valid number:")
                return self.CAPITAL_UPDATE
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = self.get_message(update)
            await message.reply_text("❌ Capital update canceled.")
        except EmptyTelegramMessage as e:
            print(f'{str(e)}')
        return ConversationHandler.END


    # ---------------- Broadcast ----------------
    async def broadcast_signals(self, signal):
        """This is called by the service when a new signal is generated."""
        if not isinstance(signal, dict):
            print("Invalid signal format:", signal)
            return
        text = (
        f"📢 New Signal! Side: {signal['position']} | Token: {signal['symbol']} "
        f"| Entry: {signal['entry_price']} | TP: {signal['tp']} | SL: {signal['sl']}"
        )
        if signal['symbol'] == "BTCUSDT":
            subscribers = Subscribers.getActiveSubscribers()
            for s in subscribers:
                if s['is_admin'] == True or s['tier'] > 1:
                    porfolio = Portfolio(starting_balance= s['capital'])
                    lot_size = porfolio.risk_position_size(signal['entry_price'],signal['sl'],s['risk_size'])
                    temp_text = text + f"| Lot Size: {lot_size}"
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=temp_text)
                else:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
        elif signal['symbol'] == "BNBUSDT" :
            subscribers = Subscribers.getActiveSubscriberWithTier(2)
            for s in subscribers:
                porfolio = Portfolio(starting_balance= s['capital'])
                lot_size = porfolio.risk_position_size(signal['entry_price'],signal['sl'],s['risk_size'])
                temp_text = text + f"| Lot Size: {lot_size}"
                await self.app.bot.send_message(chat_id=s['chat_id'], text=temp_text)
        elif signal['symbol'] == "PAXGUSDT" :
            subscribers = Subscribers.getActiveSubscriberWithTier(3)
            for s in subscribers:
                porfolio = Portfolio(starting_balance= s['capital'])
                lot_size = porfolio.risk_position_size(signal['entry_price'],signal['sl'],s['risk_size'])
                temp_text = text + f"| Lot Size: {lot_size}"
                await self.app.bot.send_message(chat_id=s['chat_id'], text=temp_text)

    async def broadcast_ath(self,data):
        if not isinstance(data, dict):
            print("Invalid signal format:", data)
            return
        text = (
        f"📢 New ATH! in Token: {data['symbol']} "
        f"with Price {data['zone_high']}"
        )
        if data['symbol'] == "BTCUSDT":
            subscribers = Subscribers.getActiveSubscribers()
            for s in subscribers:
                    await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
        elif data['symbol'] == "BNBUSDT" :
            subscribers = Subscribers.getActiveSubscriberWithTier(2)
            for s in subscribers:
                await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
        elif data['symbol'] == "PAXGUSDT" :
            subscribers = Subscribers.getActiveSubscriberWithTier(3)
            for s in subscribers:
                await self.app.bot.send_message(chat_id=s['chat_id'], text=text)

    async def broadcast_error(self,data):
        subscribers = Subscribers.getAdmin()
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
                    print("⚠️ Redis connection lost inside blocking loop.")
                    raise
                except Exception as e:
                    print(f"❌ Blocking listener error: {e}")
                    traceback.print_exc()
                    time.sleep(2)
            return None, None

        while not self.stop_event.is_set():
            try:
                print("🚀 Starting Redis listener...")
                # Keep reading messages until stopped
                while not self.stop_event.is_set():
                    channel, data = await asyncio.to_thread(blocking_listen)
                    if not channel or not data or self.stop_event.is_set():
                        continue

                    try:
                        if channel == "signals_channel":
                            await self.broadcast_signals(data)
                        elif channel == "ath_channel":
                            await self.broadcast_ath(data)
                        elif channel == "service_error":
                            await self.broadcast_error(data)
                    except Exception as inner_e:
                        print(f"❌ Error processing message from {channel}: {inner_e}")
                        traceback.print_exc()

            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                if self.stop_event.is_set():
                    break
                print("🔌 Redis disconnected. Attempting to reconnect in 5s...")
                await asyncio.sleep(5)
                try:
                    self.redis = redis.Redis(host="127.0.0.1", port=6379, db=0)
                    self.pubsub = self.redis.pubsub()
                    self.pubsub.subscribe("signals_channel", "ath_channel", "service_error")
                    print("✅ Reconnected to Redis.")
                except Exception as reconnect_err:
                    print(f"❗ Failed to reconnect to Redis: {reconnect_err}")
                    await asyncio.sleep(10)

            except asyncio.CancelledError:
                print("🛑 Listener task cancelled — shutting down cleanly.")
                break

            except Exception as e:
                print(f"⚠️ Listener crashed: {e}")
                traceback.print_exc()
                if not self.stop_event.is_set():
                    print("🔁 Restarting listener in 5 seconds...")
                    await asyncio.sleep(5)

        print("👋 Listener exited.")
                
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
        user = Subscribers.getByChatID(user_id)
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
        self.app.add_handler(CommandHandler("bnb_zones", self.get_bnb_zones))
        self.app.add_handler(CommandHandler("bnb_signals", self.get_given_bnb_signals))
        self.app.add_handler(CommandHandler("paxg_zones", self.get_paxg_zones))
        self.app.add_handler(CommandHandler("paxg_signals", self.get_given_paxg_signals))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(capital_update_handler)
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        self.app.run_polling()

    async def startMessage(self):
        subscribers = Subscribers.getActiveSubscribers()
        text = (f'✅ We’re back online!'
                'ChaoticX has completed its latest update — new optimizations, smoother signals, and improved stability are now live.'

                '📊 Start receiving signals again and let’s get back to trading smarter!'

                '💥 Welcome back to the chaos!')
        for s in subscribers:
            await self.app.bot.send_message(chat_id=s['chat_id'], text=text)

    async def stop(self):
        """Gracefully stop listener and app"""
        print("⚙️ Stopping TelegramBot tasks...")
        self.stop_event.set()
        if self.listener_task:
            self.listener_task.cancel()
            subscribers = Subscribers.getActiveSubscribers()
            text = (f'🚧 ChaoticX is going offline for a quick update!'
                'We’re upgrading systems and polishing things up to make your trading insights even sharper.'
                'The bot will be temporarily unavailable during this maintenance period.'

                '⏳ Don’t worry — we’ll be back soon, faster and smarter than ever!'

                '💬 Stay tuned for the comeback notification 👇')
            for s in subscribers:
                await self.app.bot.send_message(chat_id=s['chat_id'], text=text)
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        if self.pubsub:
            try:
                self.pubsub.close()
            except Exception:
                pass
        print("✅ TelegramBot stopped.")