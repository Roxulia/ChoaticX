import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from tqdm import tqdm

class ModelHandler:
    def __init__(self,total_line=1000,chunk = 1000,model_type='rf', model_path='model.pkl', n_estimators_step=10):
        """
        model_type: 'rf' (RandomForest), 'sgd' (SGDClassifier), or 'xgb' (XGBoost)
        """
        self.model_type = model_type
        self.model_path = model_path
        self.target_col = 'is_target'
        self.chunk = chunk
        self.n_estimators_step = n_estimators_step
        self.total_line = total_line
        self.classes = None
        self.model = self._init_model()

    def _init_model(self):
        if self.model_type == 'rf':
            return RandomForestClassifier(warm_start=True, n_estimators=self.n_estimators_step)
        elif self.model_type == 'sgd':
            return SGDClassifier()
        elif self.model_type == 'xgb':
            return XGBClassifier( eval_metric='logloss', n_estimators=self.n_estimators_step)
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

    def data_generator(self,path):
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
        for chunk in pd.read_csv(path, chunksize=self.chunk):
            X = chunk.drop(columns = [self.target_col]).values
            y = chunk[self.target_col].values
            yield X, y

    def train(self,path):
        for i, (X_batch, y_batch) in tqdm(enumerate(self.data_generator(path)),desc="Model Training",total=self.total_line,dynamic_ncols=True):
            self.partial_train(X_batch, y_batch, iteration=i)
        joblib.dump(self.model, self.model_path)

    def test_result(self,path):
        test = pd.read_csv(path)
        X = test.drop(columns=[self.target_col])
        y = test[self.target_col]
        y_pred = self.predict(X)
        print(classification_report(y, y_pred))
        
    def load(self):
        self.model = joblib.load(self.model_path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
    
    def get_model(self):
        self.load()
        return self.model
