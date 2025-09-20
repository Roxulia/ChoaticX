from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from Exceptions.ServiceExceptions import *
from Services.signalService import SignalService
import redis,json,threading
import asyncio
import logging
from logging.handlers import RotatingFileHandler

class TelegramBot:
    def __init__(self, service : SignalService):
        load_dotenv()
        self.TELEGRAM_TOKEN = os.getenv("BOT_API")
        self.subscribers = set()
        self.service = service
        self.app = Application.builder().token(self.TELEGRAM_TOKEN).build()
        self.redis = redis.Redis(host = '127.0.0.1',port = 6379,db=0)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("signals_channel")

    # ---------------- Handlers ----------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hey! I’m your ChaoticX bot. Try /zones to see latest zone formation.\n Type /subscribe to enable bot to send u signal everytime it finds a signal")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.subscribers.add(chat_id)
        await update.message.reply_text("✅ Subscribed for auto broadcasts!")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.subscribers.discard(chat_id)
        await update.message.reply_text("❌ Unsubscribed.")

    async def get_zones(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            zones = self.service.get_untouched_zones()
            sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
            msg = "Recent Zones\n"
            for zz in sorted_zones:
                msg = msg +  f"Zone Type : {zz['type']},Zone High: {zz['zone_high']}, Low: {zz['zone_low']}, Time: {zz['timestamp']}\n"
            
            await update.message.reply_text(msg)
        except NoUntouchedZone as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def get_running_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            signals = self.service.get_running_signals()
            sorted_signals = sorted(signals, key=lambda x: x.get("timestamp"))[-5:]
            msg = "Recent Running Signals\n"
            for s in sorted_signals:
                msg = msg +  f"Signal Side: {s['side']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']}\n"
            await update.message.reply_text(msg)
        except EmptySignalException as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    # ---------------- Broadcast ----------------
    def broadcast_signals(self, signal):
        """This is called by the service when a new signal is generated."""
        if not isinstance(signal, dict):
            print("Invalid signal format:", signal)
            return
        text = f"📢 New Signal! Side: {signal['side']} | Entry: {signal['entry_price']} | TP: {signal['tp']} | SL: {signal['sl']}"
        loop = asyncio.get_event_loop()
        for chat_id in self.subscribers:
            asyncio.run_coroutine_threadsafe(
                self.app.bot.send_message(chat_id=chat_id, text=text),
                loop
            )

    def listener(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                self.broadcast_signals(data)

    def run(self):
        # Register bot handlers
        threading.Thread(target=self.listener, daemon=True).start()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("zones", self.get_zones))
        self.app.add_handler(CommandHandler("signals", self.get_running_signals))
        self.app.run_polling()
