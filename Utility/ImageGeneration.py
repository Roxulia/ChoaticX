import cv2
import numpy as np
from datetime import datetime

class ImageGenerator():
    @staticmethod
    def create_signal_card(signal, lot_size, rr_ratio=None, output_path="signal_card.jpg"):
        """
        Create a compact ChaoticX signal image using OpenCV.
        """

        # Image size and background color
        width, height = 600, 350
        bg_color = (15, 15, 15)  # dark background
        img = np.full((height, width, 3), bg_color, np.uint8)

        # Text colors
        white = (240, 240, 240)
        green = (50, 205, 50)
        red = (0, 100, 255)
        gray = (130, 130, 130)
        cyan = (0, 255, 255)

        # Title
        cv2.putText(img, "📊  ChaoticX Signal Alert", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, cyan, 2, cv2.LINE_AA)
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
            f"Entry: {entry}",
            f"TP: {tp}",
            f"SL: {sl}",
            f"Lot Size: {lot_size}",
        ]

        if rr_ratio:
            lines.append(f"R/R Ratio: {rr_ratio}")

        y = 120
        for line in lines:
            if "Side" in line:
                color = side_color
            elif "TP" in line:
                color = green
            elif "SL" in line:
                color = red
            else:
                color = white
            cv2.putText(img, line, (60, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
            y += 40

        # Footer
        cv2.line(img, (30, height - 60), (width - 30, height - 60), (80, 80, 80), 1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, f"{timestamp}", (60, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, gray, 1, cv2.LINE_AA)
        cv2.putText(img, "ChaoticX AI Trader", (width - 220, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cyan, 1, cv2.LINE_AA)

        # Save
        cv2.imwrite(output_path, img)
        return output_path

if __name__ == "__main__":
    signal = {
        "symbol": "BTCUSDT",
        "position": "LONG",
        "entry_price": 68430,
        "tp": 69200,
        "sl": 67800
    }

    lot_size = 0.015
    rr_ratio = 2.3

    img_path = ImageGenerator.create_signal_card(signal, lot_size, rr_ratio)