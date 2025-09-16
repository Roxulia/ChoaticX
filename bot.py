from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from dotenv import load_dotenv
import os

class TelegramBot():
    def __init__(self):
        load_dotenv()
        self.TELEGRAM_TOKEN = os.getenv(key='BOT_API')

        # Your API endpoint (Flask/FastAPI)
        self.API_URL = os.getenv(key="API_URL")

    # Command: /start
    async def start(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hey! I’m your ChaoticX bot. Try /zones")

    # Command: /zones
    async def get_zones(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = requests.get(f'{self.API_URL}/zones')
            if response.status_code == 200:
                zones = response.json()
                await update.message.reply_text(f"Zones: {zones}")
            else:
                await update.message.reply_text("API Error: Couldn’t fetch zones")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def get_running_signals(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = requests.get(f'{self.API_URL}/signals')
            if response.status_code == 200:
                zones = response.json()
                await update.message.reply_text(f"Signals: {zones}")
            else:
                await update.message.reply_text("API Error: Couldn’t fetch signals")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    def run(self):
        app = Application.builder().token(self.TELEGRAM_TOKEN).build()

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("zones", self.get_zones))
        app.add_handler(CommandHandler("signals",self.get_running_signals))

        app.run_polling()

if __name__ == "__main__":
    print('starting bot')
    TelegramBot().run()
