from binance.client import Client
class timeFrame:
    def __init__(self):
        self.tf = {
            '1min' : Client.KLINE_INTERVAL_1MINUTE,
            '3min' :Client.KLINE_INTERVAL_3MINUTE,
            '5min' : Client.KLINE_INTERVAL_5MINUTE,
            '15min' : Client.KLINE_INTERVAL_15MINUTE,
            '1h' : Client.KLINE_INTERVAL_1HOUR,
            '4h' : Client.KLINE_INTERVAL_4HOUR,
            '1D' : Client.KLINE_INTERVAL_1DAY
        }
        self.tfOrder = ['1min','3min','5min','15min','1h','4h','1D']
        self.multiplier = {
            '1min' : {
                '1min' : 1,
                '3min': 3,
                '5min' : 5,
                '15min' : 15,
                '1h' : 60,
                '4h' : 240,
                '1D' : 1440
            },
            '3min':{
                '3min' : 1,
                '5min' : 2,
                '15min' : 5,
                '1h' : 15,
                '4h' : 60,
                '1D' : 240
            },
            '5min' : {
                '5min' : 1,
                '15min' : 3,
                '1h' : 12,
                '4h' : 48,
                '1D' : 288
            },
            '1h' : {
                '1h' : 1,
                '4h' : 4,
                '1D' : 24
            },
            '4h' : {
                '4h' : 1,
                '1D' : 6
            },
            '1D' : {
                '1D' : 1
            }
        }

    def getTimeFrame(self,interval):
        return self.tf[interval]
    
    def getTFOrder(self,interval):
        return self.tfOrder.index(interval)
    
    def getSmallestTF(self,all_df):
        if not all_df:
            return []

        # Get the minimum order value (i.e. smallest timeframe)
        min_order = min(self.getTFOrder(z['time_frame']) for z in all_df if 'time_frame' in z)
        return self.tfOrder[min_order]
    
    def getBasedZone(self,all_df):
        if not all_df:
            return []
        min_order = min(self.getTFOrder(z['time_frame']) for z in all_df if 'time_frame' in z)
        # Filter only zones with that smallest timeframe
        smallest_zones = [z for z in all_df if self.getTFOrder(z['time_frame']) == min_order]
        return smallest_zones
    
    def getMultiplier(self,smallest,current):
        return self.multiplier[smallest][current]
    
