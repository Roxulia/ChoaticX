class DatasetGenerator:
    def __init__(self, df, zones_with_reactions, n_future=10, rr=2.0):
        self.df = df
        self.zones_with_reactions = zones_with_reactions
        self.n_future = n_future
        self.rr = rr

    def extract_features_and_labels(self):
        dataset = []
        # TODO: Loop over each zone and generate feature vector + label
        return dataset