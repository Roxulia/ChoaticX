from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
from functools import wraps

class TelegramBot:
    def __init__(self, service : SignalService):
        load_dotenv()
        self.CAPITAL_UPDATE = 1
        self.TELEGRAM_TOKEN = os.getenv("TEST_BOT_API")
        self.btcservice = SignalService("BTCUSDT",300)
        self.bnbservice = SignalService("BNBUSDT",threshold=3)
        self.app = Application.builder().token(self.TELEGRAM_TOKEN).post_init(self.post_init).build()
        self.redis = redis.Redis(host = '127.0.0.1',port = 6379,db=0)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("signals_channel")
        
    def restricted(min_tier=1, admin_only=False,for_starter = False):
        def decorator(func):
            @wraps(func)
            async def wrapper(self,update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_id = update.effective_user.id
                user = Subscribers.getByChatID(user_id)
                if not for_starter:
                    
                    if not user:
                        await update.message.reply_text("❌ You are not registered.")
                        return

                    if admin_only and not user['is_admin']:
                        await update.message.reply_text("🚫 Admins only.")
                        return

                    if not user['is_admin'] and user['tier'] < min_tier:
                        await update.message.reply_text(
                            f"⚠️ This command requires *Tier {min_tier}* or higher. Please upgrade your subscription.",
                            parse_mode="Markdown"
                        )
                        return
                return await func(self,update, context,user, *args, **kwargs)
            return wrapper
        return decorator
    
    async def post_init(self, app: Application):
        # Start Redis listener as background task once loop is running
        app.create_task(self.listener())
        
    # ---------------- Handlers ----------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    @restricted(for_starter=True)  # all registered users can use help
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user):
        keyboard = [
            [InlineKeyboardButton("📊 BTCUSDT Zones", callback_data="btc_zones")],
            [InlineKeyboardButton("🔔 Subscribe", callback_data="subscribe")],
            [InlineKeyboardButton("💰 Update Capital", callback_data="update_capital")] if user is not None and (user['tier']>1 or user['is_admin']) else None,
        ]
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

        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")

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

    @restricted(for_starter=True)
    async def get_btc_zones(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            zones = self.btcservice.get_untouched_zones(limit= 5)
            sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
            msg = "Recent BTC Zones\n"
            for zz in sorted_zones:
                msg = msg +  f"Zone Type : {zz['zone_type']},Zone High: {zz['zone_high']}, Low: {zz['zone_low']}, Time: {zz['timestamp']}\n"
            
            await update.message.reply_text(msg)
        except NoUntouchedZone as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    @restricted(for_starter=True)
    async def get_given_btc_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            signals = self.btcservice.get_given_signals()
            msg = "Recent BTCUSDT Signals\n"
            if user is not None and (user['tier'] > 1 or user['is_admin']):
                for s in signals:
                    porfolio = Portfolio(starting_balance= user['capital'])
                    lot_size = porfolio.risk_position_size(s['entry_price'],s['sl'],s['risk_size'])
                    msg = msg +  f"Signal Side: {s['position']} | Symbol: {s['symbol']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']} | Lot Size: {lot_size}\n"
            else:
                for s in signals:
                    msg = msg +  f"Signal Side: {s['position']} | Symbol: {s['symbol']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']}\n"
            await update.message.reply_text(msg)
        except EmptySignalException as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    @restricted(min_tier=2)
    async def get_bnb_zones(self,update:Update,context:ContextTypes.DEFAULT_TYPE):
        try:
            zones = self.bnbservice.get_untouched_zones(limit= 5)
            sorted_zones = sorted(zones, key=lambda x: x.get("timestamp"),reverse= True)[:4]
            msg = "Recent BNBUSDT Zones\n"
            for zz in sorted_zones:
                msg = msg +  f"Zone Type : {zz['zone_type']},Zone High: {zz['zone_high']}, Low: {zz['zone_low']}, Time: {zz['timestamp']}\n"
            
            await update.message.reply_text(msg)
        except NoUntouchedZone as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    @restricted(min_tier=2)
    async def get_given_bnb_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE,user):
        try:
            signals = self.bnbservice.get_given_signals()
            msg = "Recent BNBUSDT Signals\n"
            for s in signals:
                porfolio = Portfolio(starting_balance= user['capital'])
                lot_size = porfolio.risk_position_size(s['entry_price'],s['sl'],s['risk_size'])
                msg = msg +  f"Signal Side: {s['position']} | Symbol: {s['symbol']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']} | Lot Size: {lot_size}\n"
            await update.message.reply_text(msg)
        except EmptySignalException as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    @restricted(min_tier=2)  # only Tier ≥2 or admins
    async def update_subscriber_capital(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.reply_text(
                "💰 Please enter your new capital size in *USDT* or type 'cancel' to stop:",
                parse_mode="Markdown"
            )
            return self.CAPITAL_UPDATE
        except Exception as e:
            await update.message.reply_text("⚠️ An error occurred while starting update.")
            return ConversationHandler.END

    @restricted(min_tier=2)  # only Tier ≥2 or admins
    async def set_capital(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            capital = float(update.message.text)
            if capital <= 0:
                await update.message.reply_text("⚠️ Capital must be greater than 0. Try again:")
                return self.CAPITAL_UPDATE

            # ✅ Update in DB
            user_id = update.effective_user.id
            user = Subscribers.getByChatID(user_id)
            Subscribers.update(user['id'], {"capital": capital})

            await update.message.reply_text(f"✅ Your capital has been updated to *{capital} USDT*.", parse_mode="Markdown")
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number:")
            return self.CAPITAL_UPDATE

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Capital update canceled.")
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
        entry_points=[CommandHandler("update_capital", self.update_subscriber_capital)],
        states={
            self.CAPITAL_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_capital)],
        },
        fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("btc_zones", self.get_btc_zones))
        self.app.add_handler(CommandHandler("btc_signals", self.get_given_btc_signals))
        self.app.add_handler(CommandHandler("bnb_zones", self.get_bnb_zones))
        self.app.add_handler(CommandHandler("bnb_signals", self.get_given_bnb_signals))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(capital_update_handler)
        self.app.run_polling()

