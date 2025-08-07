import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from xgboost import XGBClassifier

class ModelHandler:
    def __init__(self, model_type='rf', model_path='model.pkl', n_estimators_step=10):
        """
        model_type: 'rf' (RandomForest), 'sgd' (SGDClassifier), or 'xgb' (XGBoost)
        """
        self.model_type = model_type
        self.model_path = model_path
        self.n_estimators_step = n_estimators_step
        self.classes = None
        self.model = self._init_model()

    def _init_model(self):
        if self.model_type == 'rf':
            return RandomForestClassifier(warm_start=True, n_estimators=self.n_estimators_step)
        elif self.model_type == 'sgd':
            return SGDClassifier()
        elif self.model_type == 'xgb':
            return XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=self.n_estimators_step)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def partial_train(self, X_batch, y_batch, iteration=0):
        if self.model_type == 'sgd':
            if self.classes is None:
                self.classes = np.unique(y_batch)
            if iteration == 0:
                self.model.partial_fit(X_batch, y_batch, classes=self.classes)
            else:
                self.model.partial_fit(X_batch, y_batch)

        elif self.model_type == 'rf':
            if iteration > 0:
                n_estimators = self.model.n_estimators + self.n_estimators_step
                self.model.set_params(n_estimators=n_estimators)
            self.model.fit(X_batch, y_batch)

        elif self.model_type == 'xgb':
            if iteration == 0:
                self.model.set_params(n_estimators=self.n_estimators_step)
                self.model.fit(X_batch, y_batch, xgb_model=None)
            else:
                prev_booster = self.model.get_booster()
                new_estimators = self.model.n_estimators + self.n_estimators_step
                self.model.set_params(n_estimators=new_estimators)
                self.model.fit(X_batch, y_batch, xgb_model=prev_booster)

    def data_generator(self,file_path,target_col, chunksize=1000):
        """
        Generator that yields X, y batches from a CSV file.

        Args:
            file_path (str): Path to CSV file.
            feature_cols (list): List of feature column names.
            target_col (str): Target column name.
            chunksize (int): Number of rows per batch.

        Yields:
            X (ndarray): Features batch.
            y (ndarray): Target batch.
        """
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            X = chunk.drop(column = [target_col]).values
            y = chunk[target_col].values
            yield X, y

    def train(self):
        for i, (X_batch, y_batch) in enumerate(self.data_generator()):
            self.partial_train(X_batch, y_batch, iteration=i)
        joblib.dump(self.model, self.model_path)
        
    def load(self):
        self.model = joblib.load(self.model_path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
