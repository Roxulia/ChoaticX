import os
import asyncio
import websockets
from binance import AsyncClient, BinanceSocketManager
from dotenv import load_dotenv
from Exceptions.ServiceExceptions import *
from Utility.Logger import Logger

class BinanceWebSocket:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        self.logger = Logger()

    async def connect(self):
        """Initialize async client + socket manager."""
        try:
            self.broadcast_client= await AsyncClient.create(self.api_key, self.api_secret)
            self.bm = BinanceSocketManager(self.broadcast_client)
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    async def close(self):
        """Close connection gracefully."""
        try:
            if self.broadcast_client:
                await self.broadcast_client.close_connection()
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    async def listen_kline(self, symbols, intervals, callback):
        """
        Subscribe to Binance kline broadcasts.
        - symbols: list of trading pairs, e.g. ["BTCUSDT"]
        - intervals: list of intervals, e.g. ["1h", "4h"]
        - callback: function to call when candle closes
        """
        if not self.bm:
            raise RuntimeError("Call connect() before listen_kline()")
        try:
            streams = []
            for sym in symbols:
                for itv in intervals:
                    streams.append(f"{sym.lower()}@kline_{itv}")

            ms = self.bm.multiplex_socket(streams)

            async with ms as stream:
                while True:
                    msg = await stream.recv()
                    data = msg.get("data", {})
                    kline = data.get("k", {})

                    if kline.get("x"):  # ✅ candle closed
                        await callback(kline)
        except websockets.exceptions.ConnectionClosedOK as e:
            # graceful disconnect
            self.logger.info("⚠️ Binance WebSocket closed normally (1001 Going Away).")
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e
        except asyncio.CancelledError as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise 
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    
        
    
    
    
    
            
                
            

    




