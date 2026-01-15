import numpy as np
import pandas as pd
from Core.Indicators.registry import get_indicator
from Core.Structures.registry import get_structure
from .registry import register_regime

@register_regime
class Trend:
    def __init__(
        self,
        ema_window=50,
        slope_lookback=5,
        structure_window=10,
        min_trend_bars=5,
        slope_threshold=0.2
    ):
        self.ema_window = ema_window
        self.slope_lookback = slope_lookback
        self.structure_window = structure_window
        self.min_trend_bars = min_trend_bars
        self.slope_threshold = slope_threshold

    async def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        temp = pd.DataFrame()
        df_swings = self.attach_swing_structure(df)
        temp["swing_type"] = df_swings["swing_type"]
        if f"ema_{self.ema_window}" not in df.columns:
            emaIndicator = get_indicator('EMA')(windows=[self.ema_window], source='close')
            temp["ema"] = emaIndicator.add(df)["ema_" + str(self.ema_window)]
        else:
            temp["ema"] = df[f"ema_{self.ema_window}"]

        if "atr" not in df.columns:
            atrIndicator = get_indicator('ATR')(window=14, source='close')
            temp["atr"] = atrIndicator.add(df)
        else:
            temp["atr"] = df["atr"]
        # Normalized slope
        temp["trend_slope"] = (
            (temp["ema"] - temp["ema"].shift(self.slope_lookback)) / temp["atr"]
        )
        
        swing_map = {
            "HH": 1,
            "HL": 1,
            "LH": -1,
            "LL": -1
        }

        temp["structure_val"] = temp["swing_type"].map(swing_map).fillna(0)


        temp["structure_score"] = (
            temp["structure_val"]
            .rolling(self.structure_window, min_periods=1)
            .sum()
            / self.structure_window
        )

        # Trend direction flags
        temp["bullish"] = (
            (temp["structure_score"] > 0.3) &
            (temp["trend_slope"] > self.slope_threshold)
        )

        temp["bearish"] = (
            (temp["structure_score"] < -0.3) &
            (temp["trend_slope"] < -self.slope_threshold)
        )

        # Persistence check
        temp["bullish_count"] = (
            temp["bullish"]
            .astype(int)
            .rolling(self.min_trend_bars)
            .sum()
        )

        temp["bearish_count"] = (
            temp["bearish"]
            .astype(int)
            .rolling(self.min_trend_bars)
            .sum()
        )

        # Regime classification
        def classify(row):
            if row["bullish_count"] >= self.min_trend_bars:
                return "UPTREND"
            if row["bearish_count"] >= self.min_trend_bars:
                return "DOWNTREND"
            if abs(row["trend_slope"]) < self.slope_threshold / 2:
                return "RANGE"
            return "TRANSITION"

        temp["trend_regime"] = temp.apply(classify, axis=1)

        # Confidence
        temp["trend_conf"] = (
            temp["structure_score"].abs().clip(0, 1) * 0.6 +
            temp["trend_slope"].abs().clip(0, 1) * 0.4
        )

        return df.join(
            temp[[
                "trend_regime",
                "structure_score",
                "trend_slope",
                "trend_conf"
            ]])
    
    def attach_swing_structure(self,df:pd.DataFrame):
        try:
            structure_cls = get_structure("Swings")
            structure = structure_cls(df=df,window=self.structure_window)
            swings = structure.label_market_structure()
            temp = df.copy()
            temp["swing_type"] = None
            swing_idx = 0
            last_type = None

            for i in range(len(temp)):
                while swing_idx < len(swings) and swings[swing_idx]["index"] <= i:
                    last_type = swings[swing_idx]["swing_type"]
                    swing_idx += 1

                temp.at[i, "swing_type"] = last_type
            return temp
        except Exception as e:
            print(f"Error in attach_swing_structure: {e}")
            raise e
        