from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseHandler
from Exceptions.ServiceExceptions import EmptyTelegramMessage

class CommonHandlers(BaseHandler):

    async def start(self, update, context):
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

    @BaseHandler.restricted(None, for_starter=True)
    async def help(self, update, context, user):
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

    async def subscribe(self, update, context):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            text = self.subscriptionService.subscribeUsingTelegram(chat_id)
            await message.reply_text(text=text)
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')

    async def unsubscribe(self, update, context):
        try:
            message = self.get_message(update)
            chat_id = update.effective_chat.id
            text = self.subscriptionService.unsubscribeUsingTelegram(chat_id)
            await message.reply_text(text=text)
        except EmptyTelegramMessage as e:
            self.logger.error(f'{self.__class__}:Error:{str(e)}')