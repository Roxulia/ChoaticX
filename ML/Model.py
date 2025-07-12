import joblib
from sklearn.ensemble import RandomForestClassifier

class ModelHandler:
    def __init__(self, model_path='model.pkl'):
        self.model_path = model_path
        self.model = RandomForestClassifier()

    def train(self, X, y):
        self.model.fit(X, y)
        joblib.dump(self.model, self.model_path)

    def load(self):
        self.model = joblib.load(self.model_path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
