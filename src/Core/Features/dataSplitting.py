import pandas as pd
import numpy as np

class DataSplit:
    def __init__(self, train_size=0.7, test_size=0.3, shuffle=True, random_state=None):
        if train_size + test_size > 1:
            raise ValueError("train_size + test_size should not exceed 1.")
        self.shuffle = shuffle
        self.random_state = random_state
        self.train_size = train_size
        self.test_size = test_size 

    def split(self,data:pd.DataFrame):
        # Work with indices only (more memory-efficient)
        n = len(data)
        train = int(np.ceil(n*self.train_size))
        test = int(np.floor(n*self.test_size))
        indices = np.arange(len(data))
        if self.shuffle:
            rng = np.random.default_rng(self.random_state)
            rng.shuffle(indices)

        # Index split
        train_idx = indices[:train]
        test_idx = indices[train:train+test]

        # Direct indexing avoids creating temp DataFrames
        return data.iloc[train_idx], data.iloc[test_idx]
