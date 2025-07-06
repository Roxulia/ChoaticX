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

    def getTimeFrame(self,interval):
        return self.tf[interval]
    
    def getTFOrder(self,interval):
        return self.tfOrder.index(interval)
    
    def getBasedZone(self,all_df):
        if not all_df:
            return []

        # Get the minimum order value (i.e. smallest timeframe)
        min_order = min(self.getTFOrder(z['time_frame']) for z in all_df if 'time_frame' in z)

        # Filter only zones with that smallest timeframe
        smallest_zones = [z for z in all_df if self.getTFOrder(z['time_frame']) == min_order]
        return smallest_zones