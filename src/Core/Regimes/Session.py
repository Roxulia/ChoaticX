import pandas as pd
from Core.Regimes.registry import register_regime

@register_regime
class Session:
    def __init__(self, timezone="UTC"):
        self.timezone = timezone

    async def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        temp = pd.DataFrame()

        # Ensure timestamp is timezone-aware
        temp["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        temp["weekday"] = temp["timestamp"].dt.weekday  # 0=Mon, 6=Sun
        temp["hour"] = temp["timestamp"].dt.hour

        temp["session_regime"] = temp.apply(self.classify, axis=1)
        temp["session_conf"] = 1.0

        return df.join(temp[["session_conf", "session_regime"]])
    
    def classify(self,row):
        if row["weekday"] >= 5:
            return "WEEKEND"

        hour = row["hour"]

        if 0 <= hour < 7:
            return "ASIA"
        elif 7 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 17:
            return "OVERLAP_LONDON_NY"
        elif 17 <= hour < 21:
            return "NEW_YORK"
        else:
            return "ASIA"  # late NY → Asia drift
