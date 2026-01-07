from dataclasses import dataclass,field

@dataclass
class IgnoreColumns:
    signalGenModelV1 : list[str] = field(default_factory=lambda :['symbol','timeframe','zone_high','zone_low','below_zone_low','above_zone_low','below_zone_high','above_zone_high','candle_open','candle_close','candle_high','candle_low'] ) 
    predictionModelV1 : list[str] = field(default_factory= lambda: [
            'symbol','timeframe','avg_volume_past_5','atr_mean','above_atr','below_atr','below_conf_count_BuFVG','conf_count_BuLiq',
            'below_conf_4h_count','above_conf_count_BuLiq','conf_4h_count','wick_ratio','prev_volatility_5','below_ema_short',
            'below_prev_volatility_5','above_conf_count_BrLiq','below_equal_level_deviation','ema_short','below_ema_long','below_momentum_5',
            'above_ema_short','below_conf_count_BrOB','below_ema_short','conf_is_buy_zone','above_avg_volume_around_zone','conf_count_BrOB',
            'below_conf_1h_count','equal_level_deviation','candle_ema_long','candle_rsi','momentum_5','below_conf_is_buy_zone','above_ema_short',
            'above_rsi','above_conf_count_BrOB','conf_count_BrFVG','ema_long','above_ema_long','above_conf_count_BuFVG','conf_1h_count',
            'below_conf_count_BrLiq','below_ema_long','below_avg_volume_around_zone','below_rsi','conf_1D_count','above_equal_level_deviation',
            'below_atr_mean','avg_volume_around_zone','above_conf_1h_count','conf_count_BuOB','below_avg_volume_past_5' ,
            'below_conf_1D_count' ,'above_ema_long','below_conf_count_BuOB','rsi','ema_short','candle_atr','conf_count_BrLiq',
            'above_conf_count_BrFVG','below_conf_count_BuLiq','above_conf_1D_count','above_prev_volatility_5','candle_ema20',
            'atr','below_wick_ratio','below_conf_count_BrFVG','above_conf_is_buy_zone','above_avg_volume_past_5','above_momentum_5',
            'ema_long','above_atr_mean','above_wick_ratio','above_conf_count_BuOB','above_conf_4h_count','conf_count_BuFVG',
            'candle_atr_mean','r2','alpha','beta','gamma','bb_high','bb_mid','bb_low','above_r2',
            'above_alpha','above_beta','above_gamma','above_bb_high','above_bb_mid','above_bb_low',
            'below_r2','below_alpha','below_beta','below_gamma','below_bb_high','below_bb_mid','below_bb_low',
            'candle_r2','candle_alpha','candle_beta','candle_gamma','candle_bb_high','candle_bb_mid','candle_bb_low'
        ])