from Database.DataModels.Subscribers import Subscribers
from Exceptions.ServiceExceptions import *
from Utility.Logger import Logger
class SubscriptionService():
    def __init__(self):
        self.logger = Logger()

    def subscribeUsingTelegram(self,chat_id):
        try:
            existed = Subscribers.getByChatID(chat_id)
            if existed:
                Subscribers.update(existed['id'],{"is_active":True})
            else:
                Subscribers.create({"chat_id":chat_id})
            return "✅ Subscribed for auto broadcasts!"
        except Exception as e:
            self.logger.error(f"{self.__class__} : Error in Database : {e}")
            return "Unknown Error Occur !! Pls Contact Us for Support"
        
    def unsubscribeUsingTelegram(self,chat_id):
        try:
            existed = Subscribers.getByChatID(chat_id)
            if existed:
                Subscribers.update(existed['id'],{"is_active":False})
                return "❌ Unsubscribed."
            else:
                Subscribers.create({"chat_id":chat_id,"is_active":False})
                return "U Haven't Subcribed to this Channel"
        except Exception as e:
            self.logger.error(f"{self.__class__} : Error in Database : {e}")
            return "Unknown Error Occur !! Pls Contact Us for Support"
        
    def getByChatID(self,chat_id):
        user = Subscribers.getByChatID(chat_id)
        return user
    
    def getActiveSubscribers(self,tier = 1,admin_only = False):
        if admin_only:
            return Subscribers.getAdmin()
        else:
            if tier < 2:
                return Subscribers.getActiveSubscribers()
            else:
                return Subscribers.getActiveSubscriberWithTier(tier)
        
    def updateCapital(self,id,capital):
        if capital <= 0:
            raise ValueLessThanZero
        try:
            Subscribers.update(id, {"capital": capital})
        except Exception as e:
            raise e