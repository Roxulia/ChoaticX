import numpy as np
import pandas as pd
from .registry import register_regime

@register_regime
class Volatility:

    def __init__(
        self,
        ret_window=1,
        vol_window=20,
        baseline_window=100,
        slope_window=5
    ):
        self.ret_window = ret_window
        self.vol_window = vol_window
        self.baseline_window = baseline_window
        self.slope_window = slope_window


    async def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        temp = pd.DataFrame()

        # Log returns (stationary)
        temp["log_return"] = np.log(df["close"] / df["close"].shift(self.ret_window))

        # Rolling volatility
        temp["vol"] = (
            temp["log_return"]
            .rolling(self.vol_window)
            .std()
        )

        # Baseline
        temp["vol_mean"] = temp["vol"].rolling(self.baseline_window).mean()
        temp["vol_std"]  = temp["vol"].rolling(self.baseline_window).std()

        # Z-score
        temp["vol_z"] = (temp["vol"] - temp["vol_mean"]) / temp["vol_std"]

        # Volatility slope
        temp["vol_slope"] = temp["vol"] - temp["vol"].shift(self.slope_window)

        # Regime classification
        temp["vol_regime"] = temp["vol_z"].apply(self.classify)

        # Volatility trend
        temp["vol_trend"] = temp["vol_slope"].apply(self.vol_trend)

        # Confidence
        temp["vol_conf"] = temp["vol_z"].abs().clip(0, 3) / 3

        return df.join(temp[["vol_conf", "vol_regime", "vol_trend"]])

    def classify(self,z):
        if z <= -1.0:
            return "LOW"
        elif z <= 0.5:
            return "NORMAL"
        elif z <= 2.0:
            return "HIGH"
        else:
            return "EXTREME"
            
    def vol_trend(self,x):
        if x > 0:
            return "EXPANDING"
        elif x < 0:
            return "CONTRACTING"
        else:
            return "FLAT"