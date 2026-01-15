import numpy as np
import pandas as pd
from Core.Indicators.registry import get_indicator
from Core.Structures.registry import get_structure
from .registry import register_regime

@register_regime
class LiquidityRegimeDetector:
    def __init__(
        self,
        sweep_atr_factor=0.5,
        post_sweep_bars=5,
        void_atr_factor=2.0,
        wick_ratio_threshold=0.15
    ):
        self.sweep_atr_factor = sweep_atr_factor
        self.post_sweep_bars = post_sweep_bars
        self.void_atr_factor = void_atr_factor
        self.wick_ratio_threshold = wick_ratio_threshold

        self.current_regime = "NONE"
        self.liq_age = 0
        self.liq_event = "NONE"

    def detect_candle(self, candle, liquidity_zones):
        """
        candle: dict with open, high, low, close, atr
        liquidity_zones: list of zones with {price, side}
        """

        # Default output
        regime = self.current_regime
        event = self.liq_event

        # --- Step 1: Liquidity Void detection ---
        candle_range = candle["high"] - candle["low"]
        body = abs(candle["close"] - candle["open"])
        wick_ratio = body / candle_range if candle_range > 0 else 0

        if (
            candle_range > candle["atr"] * self.void_atr_factor
            and wick_ratio > (1 - self.wick_ratio_threshold)
        ):
            self.current_regime = "LIQUIDITY_VOID"
            self.liq_age = 0
            self.liq_event = "NONE"

            return self._output("LIQUIDITY_VOID", "NONE", 0, 0.9)

        # --- Step 2: Sweep detection ---
        for zone in liquidity_zones:
            if zone["side"] == "BUY":
                if (
                    candle["high"] > zone["price"] + candle["atr"] * self.sweep_atr_factor
                    and candle["close"] < zone["price"]
                ):
                    self.current_regime = "LIQUIDITY_SWEEP"
                    self.liq_age = 0
                    self.liq_event = "BUY_SIDE"
                    return self._output("LIQUIDITY_SWEEP", "BUY_SIDE", 0, 0.85)

            if zone["side"] == "SELL":
                if (
                    candle["low"] < zone["price"] - candle["atr"] * self.sweep_atr_factor
                    and candle["close"] > zone["price"]
                ):
                    self.current_regime = "LIQUIDITY_SWEEP"
                    self.liq_age = 0
                    self.liq_event = "SELL_SIDE"
                    return self._output("LIQUIDITY_SWEEP", "SELL_SIDE", 0, 0.85)

        # --- Step 3: Post-sweep decay ---
        if self.current_regime in ("LIQUIDITY_SWEEP", "POST_SWEEP"):
            self.liq_age += 1

            if self.liq_age <= self.post_sweep_bars:
                self.current_regime = "POST_SWEEP"
                return self._output("POST_SWEEP", self.liq_event, self.liq_age, 0.6)

            self.current_regime = "NONE"
            self.liq_event = "NONE"
            self.liq_age = 0

        return self._output("NONE", "NONE", 0, 0.0)

    def _output(self, regime, event, age, conf):
        return {
            "liq_regime": regime,
            "liq_event": event,
            "liq_age": age,
            "liq_conf": conf
        }
