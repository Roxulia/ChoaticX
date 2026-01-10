from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from Exceptions.ServiceExceptions import EmptyTelegramMessage
from Services.subscriptionService import SubscriptionService
from Utility.Logger import Logger

class BaseHandler:
    def __init__(self, subscriptionService :SubscriptionService, logger:Logger):
        self.subscriptionService = subscriptionService
        self.logger = logger

    def get_message(self, update: Update):
        if update.message:
            return update.message
        if update.callback_query:
            return update.callback_query.message
        raise EmptyTelegramMessage()

    def restricted(self, min_tier=1, admin_only=False, for_starter=False):
        def decorator(func):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args):
                try:
                    message = self.get_message(update)
                    user_id = update.effective_user.id
                    user = self.subscriptionService.getByChatID(user_id)

                    if not for_starter:
                        if not user:
                            await message.reply_text("❌ You are not registered.")
                            return
                        if admin_only and not user["is_admin"]:
                            await message.reply_text("🚫 Admins only.")
                            return
                        if not user["is_admin"] and user["tier"] < min_tier:
                            await message.reply_text(
                                f"⚠️ Requires *Tier {min_tier}* or higher.",
                                parse_mode="Markdown"
                            )
                            return

                    return await func(update, context, user)
                except EmptyTelegramMessage as e:
                    self.logger.error(str(e))
            return wrapper
        return decorator
