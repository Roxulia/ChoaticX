
    def getSmallestTF(self,all_df):
        if not all_df:
            return []

        # Get the minimum order value (i.e. smallest timeframe)
        min_order = min(self.getTFOrder(z['time_frame']) for z in all_df if 'time_frame' in z)
        return min_order
    
    def getBasedZone(self,all_df):
        if not all_df:
            return []

        # Filter only zones with that smallest timeframe
        smallest_zones = [z for z in all_df if self.getTFOrder(z['time_frame']) == self.getSmallestTF(all_df)]
        return smallest_zones
    
