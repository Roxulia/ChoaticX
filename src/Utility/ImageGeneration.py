import cv2
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import os
class ImageGenerator():
    @staticmethod
    def createWithTemplate(signal,img,rr_ratio = None,lot_size = None):
        # Image size and background color
        width, height = 562, 265
        bg_color = (15, 15, 15)  
        # Text colors
        white = (240, 240, 240)
        green = (50, 255, 50)
        red = (0, 50, 255)
        gray = (130, 130, 130)
        cyan = (255, 255, 0)

        
        # Core details
        side = signal["position"].upper()
        symbol = signal["symbol"]
        entry = signal["entry_price"]
        tp = signal["tp"]
        sl = signal["sl"]

        side_color = green if side == "LONG" else red

        lines = [
            f"Pair: {symbol}",
            f"Side: {side}",
            f"Entry: {float(entry):,.2f}",
            f"TP: {float(tp):,.2f}",
            f"SL: {float(sl):,.2f}",
        ]
        if lot_size:
            lines.append(f"Lot Size: {lot_size}")

        if rr_ratio:
            lines.append(f"R/R Ratio: {rr_ratio}")

        y = 90
        for line in lines:
            if "Side" in line:
                color = side_color
            elif "TP" in line:
                color = green
            elif "SL" in line:
                color = red
            else:
                color = white
            cv2.putText(img, line, (200, y), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1, cv2.LINE_AA)
            y += 22

        return img
    
    @staticmethod
    def createWithoutTemplate(signal,lot_size=None,rr_ratio=None):
        width, height = 600, 350
        bg_color = (15, 15, 15)  # dark background
        img = np.full((height, width, 3), bg_color, np.uint8)

        # Text colors
        white = (240, 240, 240)
        green = (50, 255, 50)
        red = (0, 50, 255)
        gray = (130, 130, 130)
        cyan = (255, 255, 0)

        # Title
        cv2.putText(img, "ChaoticX Signal Alert", (130, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, cyan, 2, cv2.LINE_AA)
        cv2.line(img, (30, 70), (width - 30, 70), (80, 80, 80), 1)

        # Core details
        side = signal["position"].upper()
        symbol = signal["symbol"]
        entry = signal["entry_price"]
        tp = signal["tp"]
        sl = signal["sl"]

        side_color = green if side == "LONG" else red

        lines = [
            f"Pair: {symbol}",
            f"Side: {side}",
            f"Entry: {float(entry):,.2f}",
            f"TP: {float(tp):,.2f}",
            f"SL: {float(sl):,.2f}",
        ]
        if lot_size:
            lines.append(f"Lot Size: {lot_size}")

        if rr_ratio:
            lines.append(f"R/R Ratio: {rr_ratio}")

        y = 100
        for line in lines:
            if "Side" in line:
                color = side_color
            elif "TP" in line:
                color = green
            elif "SL" in line:
                color = red
            else:
                color = white
            cv2.putText(img, line, (60, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
            y += 30

        # Footer
        cv2.line(img, (30, height - 60), (width - 30, height - 60), (80, 80, 80), 1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, f"{timestamp}", (60, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, gray, 1, cv2.LINE_AA)
        cv2.putText(img, "ChaoticX AI Trader", (width - 220, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cyan, 1, cv2.LINE_AA)
        return img
    
    @staticmethod
    def create_signal_card(signal, lot_size=None, rr_ratio=None, template = "",output_path = ""):
        """
        Create a compact ChaoticX signal image using OpenCV.
        """
        img = cv2.imread(template)
        if img is not None:
            img = ImageGenerator.createWithTemplate(signal,img,rr_ratio,lot_size)
        else:
            img = ImageGenerator.createWithoutTemplate(signal,lot_size=lot_size,rr_ratio=rr_ratio)
        cv2.imwrite(output_path, img)
        return output_path
    
    
if __name__ == "__main__":
    signal = {
        "symbol": "BTCUSDT",
        "position": "Short",
        "entry_price": 68430,
        "tp": 69200,
        "sl": 67800
    }
    load_dotenv()
    template = os.getenv(key='IMAGE_PATH') + '/BTCUSDT_Short_template.jpg'
    output = os.getenv(key='IMAGE_PATH') + '/BTC_signal.jpg'
    

    img_path = ImageGenerator.create_signal_card(signal, None, None,template,output)