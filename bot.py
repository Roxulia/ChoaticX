from Services.signalService import SignalService
from Telegram.TelegramBot import TelegramBot
from Database.DB import MySQLDB as DB

if __name__ == "__main__":
    DB.init_logger("bot_db.log")
    service = SignalService()
    bot = TelegramBot(service)
    bot.run()
    
    
