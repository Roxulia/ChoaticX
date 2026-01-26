from tqdm import tqdm
import pandas as pd
from Utility.MemoryUsage import  MemoryUsage as mu
import os
from dotenv import load_dotenv
from Exceptions import *
class CandleReaction:
    def __init__(self):
        pass

    def get_zone_reaction(self,zone,candles_data):
        candles = candles_data.copy()
        candles['timestamp'] = pd.to_datetime(candles['timestamp'])
        
        zone_high = zone['zone_high']
        zone_low = zone['zone_low']
        end_timestamp = pd.to_datetime(zone['timestamp'])

        touch_type = None
        touch_index = None
        touch_candle = None

        # Skip zones that go beyond candles
        future_candles = candles.loc[candles['timestamp'] > end_timestamp]
        if future_candles.empty:
            return zone

        for i, row in future_candles.iterrows():
            open_, close, high, low = row['open'], row['close'], row['high'], row['low']
            if (open_ > zone_high and low < zone_high) or (open_ < zone_low and high > zone_low):
                touch_type = None
                touch_candle = row

                if zone_low <= close <= zone_high:
                    touch_type = 'body_close_inside'
                elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                    touch_type = 'engulf'
                elif close > zone_high and open_ > zone_high:
                    touch_type = 'body_close_above'
                elif close < zone_low and open_ < zone_low:
                    touch_type = 'body_close_below'
                else:
                    touch_type = 'wick_touch'
                break
        zone_copy = zone.copy()
        zone_copy['touch_type'] = touch_type
        zone_copy['touch_index'] = touch_index
        zone_copy['touch_candle'] = touch_candle
        return zone_copy
    
    def get_zones_reaction(self, zones, candles_data):
        candles_data['timestamp'] = pd.to_datetime(candles_data['timestamp'])

        for zone in tqdm(zones, desc="Getting Zone Reactions"):
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            zone_type = zone['zone_type']
            end_timestamp = pd.to_datetime(zone['timestamp'])  # use timestamp instead of index

            if zone_type in ['Buy-Side Liq', 'Sell-Side Liq']:
                touch_time = zone.get('swept_time', None)
                if touch_time is not None:
                    touch_time = pd.to_datetime(touch_time)
                    touch_from = None
                    touch_candle = candles_data.loc[candles_data['timestamp'] == touch_time]
                    if touch_candle.empty:
                        zone['touch_type'] = None
                        zone['touch_candle'] = None
                        zone['touch_from'] = touch_from
                        yield zone
                        continue

                    open_ = float(touch_candle['open'].iloc[0])
                    close = float(touch_candle['close'].iloc[0])

                    if open_ > zone_high :
                        touch_from = 'Above'
                    elif open_ < zone_low:
                        touch_from = 'Below'
                    else:
                        touch_from = 'Inside'

                    if zone_low <= close <= zone_high:
                        touch_type = 'body_close_inside'
                    elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                        touch_type = 'engulf'
                    elif close > zone_high and open_ > zone_high:
                        touch_type = 'body_close_above'
                    elif close < zone_low and open_ < zone_low:
                        touch_type = 'body_close_below'
                    else:
                        touch_type = 'wick_touch'

                    
                    zone['touch_type'] = touch_type
                    zone['touch_candle'] = touch_candle.iloc[0]
                    zone['touch_from'] = touch_from
                    yield zone
                    continue
                else:
                    
                    zone['touch_type'] = None
                    zone['touch_candle'] = None
                    zone['touch_from'] = touch_from
                    yield zone
                    continue
            else:
                touch_type = None
                touch_candle = None
                touch_from = None
                touch_time = zone.get('touch_time',None)
                if touch_time is None:
                    zone['touch_type'] = None
                    zone['touch_candle'] = None
                    zone['touch_from'] = None
                    yield zone
                    continue
                else:
                    touch_time = pd.to_datetime(touch_time)
                    touch_candle = candles_data.loc[candles_data['timestamp'] == touch_time]
                    if touch_candle.empty:
                        zone['touch_type'] = None
                        zone['touch_candle'] = None
                        zone['touch_from'] = None
                        yield zone
                        continue

                    open_ = float(touch_candle['open'].iloc[0])
                    close = float(touch_candle['close'].iloc[0])

                    if open_ > zone_high :
                        touch_from = 'Above'
                    elif open_ < zone_low:
                        touch_from = 'Below'
                    else:
                        touch_from = 'Inside'

                    if zone_low <= close <= zone_high:
                        touch_type = 'body_close_inside'
                    elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                        touch_type = 'engulf'
                    elif close > zone_high and open_ > zone_high:
                        touch_type = 'body_close_above'
                    elif close < zone_low and open_ < zone_low:
                        touch_type = 'body_close_below'
                    else:
                        touch_type = 'wick_touch'

                zone['touch_type'] = touch_type
                zone['touch_candle'] = touch_candle.iloc[0]
                zone['touch_from'] = touch_from
                yield zone

    def get_last_candle_reaction(self,zones,candle):
        high, low, close, open_ = candle['high'], candle['low'], candle['close'], candle['open']
        for zone in zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            zone_timestamp = pd.to_datetime(zone['timestamp'])
            zone_id = zone['id']
            zone_type = zone['zone_type']
            if (zone_low > open_ and zone_low <= high) or (zone_high < open_ and zone_high >= low):
                touch_from = 'Inside'
                if zone_low > open_:
                    touch_from = 'Below'
                elif zone_high < open_:
                    touch_from = 'Above'

                if zone_low <= close <= zone_high:
                    return {
                        'touch_from':touch_from,
                        'touch_type':'body_close_inside',
                        'touch_time':zone_timestamp,
                        'id': zone_id,
                        'type' : zone_type
                        }
                elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                    return {
                        'touch_from':touch_from,
                        'touch_type':'engulf',
                        'touch_time':zone_timestamp,
                        'id': zone_id,
                        'type' : zone_type
                        }
                elif close > zone_high and open_ > zone_high:
                    return {
                        'touch_from':touch_from,
                        'touch_type':'body_close_above',
                        'touch_time':zone_timestamp,
                        'id': zone_id,
                        'type' : zone_type
                        }
                elif close < zone_low and open_ < zone_low:
                    return {
                        'touch_from':touch_from,
                        'touch_type':'body_close_below',
                        'touch_time':zone_timestamp,
                        'id': zone_id,
                        'type' : zone_type
                        }
                else:
                    return {
                        'touch_from':touch_from,
                        'touch_type':'wick_touch',
                        'touch_time':zone_timestamp,
                        'id': zone_id,
                        'type' : zone_type
                        }
        raise CandleNotTouch