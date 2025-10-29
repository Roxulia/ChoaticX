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
            base_symbol = self.symbol.replace("USDT", "").replace("BUSD", "").replace("USDC", "")
            # Extract key stats
            report = f"""
            📊 24H MARKET REPORT — {self.symbol}\n\n
            
            💰 Last Price: {float(data['lastPrice']):,.2f} USDT\n
            📈 Change: {float(data['priceChange']):,.2f} USDT ({float(data['priceChangePercent']):.2f}%)\n
            🔼 High: {float(data['highPrice']):,.2f}\n
            🔽 Low: {float(data['lowPrice']):,.2f}\n
            📊 Volume: {float(data['volume']):,.2f} {base_symbol}\n
            💵 Quote Volume: {float(data['quoteVolume']):,.2f} USDT\n
            🕒 Open Price: {float(data['openPrice']):,.2f}\n
            
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