from Services.signalService import SignalService
from Telegram.TelegramBot import TelegramBot

if __name__ == "__main__":
    service = SignalService()
    bot = TelegramBot(service)
    bot.run()
    
    
