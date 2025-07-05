class SignalGenerator:
    def __init__(self, models):
        self.models = models

    def generate(self, candle, zone, reaction):
        # Output: Signal dict (direction, sl, tp, rr, confidence)
        signal = None
        # TODO: Use next zone model + penetration model + rr filter
        return signal