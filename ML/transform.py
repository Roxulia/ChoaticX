from sklearn.preprocessing import StandardScaler

class DataTransformer:
    def __init__(self):
        self.scaler = StandardScaler()

    def fit_transform(self, df):
        X = df.drop('label', axis=1)
        y = df['label']
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    def transform(self, df):
        X = df.drop('label', axis=1)
        return self.scaler.transform(X)
