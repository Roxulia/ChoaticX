class Filter:
    def __init__(self, min_rr=2):
        self.min_rr = min_rr

    def is_valid(self, entry_price, sl, tp):
        rr = abs(tp - entry_price) / abs(entry_price - sl)
        return rr >= self.min_rr