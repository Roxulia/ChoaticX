class Model:
    def __init__(self, model, transformer):
        self.model = model
        self.transformer = transformer

    def predict(self, features):
        transformed = self.transformer.transform(features)
        prediction = self.model.predict(transformed)
        return prediction