from Services.signalService import SignalService
from Telegram.TelegramBot import TelegramBot
from Database.DB import MySQLDB as DB
from Database.Cache import Cache
from Utility.Logger import Logger
import time,signal,sys
import argparse
Cache.init()
Logger.set_context("telegram_bot_service")

if __name__ == "__main__":
    DB.init_logger("bot_db.log")
    parser = argparse.ArgumentParser(description="run training program")
    parser.add_argument("option",help="'test' to enable testing\n'prod' to production",default='prod')
    args = parser.parse_args()
    if args.option == "test":
        bot = TelegramBot(testing=True)
    else:
        bot = TelegramBot()
    bot.run()
    
    
    
