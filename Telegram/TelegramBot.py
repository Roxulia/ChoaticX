from telegram import Update
from telegram.ext import *
import os
from dotenv import load_dotenv
from Exceptions.ServiceExceptions import *
from Services.signalService import SignalService
import redis,json,threading
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from Database.DataModels.Subscribers import Subscribers
from Backtest.Portfolio import *

class TelegramBot:
    def __init__(self, service : SignalService):
        load_dotenv()
        self.CAPITAL_UPDATE = 1
        self.TELEGRAM_TOKEN = os.getenv("BOT_API")
        self.btcservice = SignalService("BTCUSDT",300)
        self.app = Application.builder().token(self.TELEGRAM_TOKEN).post_init(self.post_init).build()
        self.redis = redis.Redis(host = '127.0.0.1',port = 6379,db=0)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("signals_channel")
        
    async def post_init(self, app: Application):
        # Start Redis listener as background task once loop is running
        app.create_task(self.listener())
        
    # ---------------- Handlers ----------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hey! I’m your ChaoticX bot. Try /zones to see latest zone formation.\n Type /subscribe to enable bot to send u signal everytime it finds a signal")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        try:
            existed = Subscribers.getByChatID(chat_id)
            if existed:
                Subscribers.update(existed['id'],{"is_active":True})
            else:
                Subscribers.create({"chat_id":chat_id})
            await update.message.reply_text("✅ Subscribed for auto broadcasts!")
        except Exception as e:
            print("Error in Database")
            await update.message.reply_text("Unknown Error Occur !! Pls Contact Us for Support")
        

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        try:
            existed = Subscribers.getByChatID(chat_id)
            if existed:
                Subscribers.update(existed['id'],{"is_active":False})
                await update.message.reply_text("❌ Unsubscribed.")
            else:
                Subscribers.create({"chat_id":chat_id,"is_active":False})
                await update.message.reply_text("U Haven't Subcribed to this Channel")
        except Exception as e:
            print("Error in Database")
            await update.message.reply_text("Unknown Error Occur !! Pls Contact Us for Support")

    async def get_zones(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            zones = self.btcservice.get_untouched_zones(limit= 5)
            sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
            msg = "Recent Zones\n"
            for zz in sorted_zones:
                msg = msg +  f"Zone Type : {zz['zone_type']},Zone High: {zz['zone_high']}, Low: {zz['zone_low']}, Time: {zz['timestamp']}\n"
            
            await update.message.reply_text(msg)
        except NoUntouchedZone as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def get_running_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            signals = self.btcservice.get_running_signals()
            msg = "Recent Running Signals\n"
            for s in signals:
                msg = msg +  f"Signal Side: {s['position']} | Symbol: {s['symbol']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']}\n"
            await update.message.reply_text(msg)
        except EmptySignalException as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def update_subscriber_capital(self,update:Update,context:ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            user = Subscribers.getByChatID(user_id)
            if user['tier'] > 1 or user['is_admin'] :
                await update.message.reply_text("Please enter your new capital size in USDT or 'cancel' to cancel updating")
                return self.CAPITAL_UPDATE
            else:
                await update.message.reply_text(f"❌ Your Account Tier Too Low to Update Capital")
                return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text("Error Occured")

    async def set_capital(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            capital = float(update.message.text)
            if capital <= 0:
                await update.message.reply_text("Capital must be greater than 0. Try again:")
                return self.CAPITAL_UPDATE

            # Example: update in DB
            user_id = update.effective_user.id
            user = Subscribers.getByChatID(user_id)
            if user['tier'] > 1 or user['is_admin'] :
                Subscribers.update(user['id'],{"capital":capital})
                await update.message.reply_text(f"✅ Your capital has been updated to {capital} USDT.")
            else:
                await update.message.reply_text(f"❌ Your Account Tier Too Low to Update Capital")
            
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number:")
            return self.CAPITAL_UPDATE

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Capital update canceled.")
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

    async def listener(self):
        def blocking():
            for message in self.pubsub.listen():
                if message["type"] == "message":
                    return json.loads(message["data"])

        while True:
            data = await asyncio.to_thread(blocking)
            await self.broadcast_signals(data)


    def run(self):
        # Register bot handlers
        capital_update_handler = ConversationHandler(
        entry_points=[CommandHandler("update-capital", self.update_subscriber_capital)],
        states={
            self.CAPITAL_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_capital)],
        },
        fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("zones", self.get_zones))
        self.app.add_handler(CommandHandler("signals", self.get_running_signals))
        self.app.add_handler(capital_update_handler)
        self.app.run_polling()

