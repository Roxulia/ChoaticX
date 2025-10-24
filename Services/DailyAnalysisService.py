import requests,os
from dotenv import load_dotenv
class DailyAnalysisService():
    def __init__(self,symbol):
        self.symbol = symbol
        self.url = os.getenv(key='ANALYSIS_LINK')
        self.url = f"{self.url}?symbol={self.symbol}"

    def get_daily_report(self):
        
        try:
            data = requests.get(self.url).json()

            # Extract key stats
            report = f"""
            📊 24H MARKET REPORT — {self.symbol}
            ---------------------------------
            💰 Last Price: {float(data['lastPrice']):,.2f} USDT
            📈 Change: {float(data['priceChange']):,.2f} USDT ({float(data['priceChangePercent']):.2f}%)
            🔼 High: {float(data['highPrice']):,.2f}
            🔽 Low: {float(data['lowPrice']):,.2f}
            📊 Volume: {float(data['volume']):,.2f} BTC
            💵 Quote Volume: {float(data['quoteVolume']):,.2f} USDT
            🕒 Open Price: {float(data['openPrice']):,.2f}
            ---------------------------------
            """

            # Optional: simple sentiment tone
            change = float(data['priceChangePercent'])
            if change > 3:
                sentiment = "🔥 Strong bullish momentum today!"
            elif change > 0:
                sentiment = "📗 Slight upward trend."
            elif change > -3:
                sentiment = "📕 Mild bearish correction."
            else:
                sentiment = "🚨 Heavy sell-off pressure."

            report += sentiment
            return report
        except Exception as e:
            raise e