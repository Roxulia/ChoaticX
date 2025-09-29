import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from xgboost import XGBClassifier
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from tqdm import tqdm
from dotenv import load_dotenv
import os
from Data.Paths import Paths

class ModelHandler:
    def __init__(self,symbol = "BTCUSDT",timeframes = ['1h','4h','1D'],total_line=1000,chunk = 1000,model_type='rf', n_estimators_step=10):
        """
        model_type: 'rf' (RandomForest), 'sgd' (SGDClassifier), or 'xgb' (XGBoost)
        """
        self.model_type = model_type
        self.symbol = symbol
        self.Paths = Paths()
        filename = f"{symbol}"+"_".join(timeframes)
        self.model_path = f'{self.Paths.model_root}/Model_{filename}_.pkl'
        self.target_col = 'target'
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
        
    def getFeatureImportance(self,feature_names = None):
        if self.model_type == 'rf':
            importances = self.model.feature_importances_
            if feature_names is None:
                feature_names = [f"f{i}" for i in range(len(importances))]
            return dict(zip(feature_names, importances.tolist()))
        elif self.model_type == 'sgd':
            importances = abs(self.model.coef_[0])  
            if feature_names is None:
                feature_names = [f"f{i}" for i in range(len(importances))]
            return dict(zip(feature_names, importances.tolist()))
        elif self.model_type == 'xgb':
            booster: xgb.Booster = self.model.get_booster()
            importance_dict = booster.get_score(importance_type='gain')  # options: weight, gain, cover
            if feature_names is not None:
                # remap feature indices (e.g., f0, f1, ...) to your feature names
                importance_dict = {feature_names[int(k[1:])]: v for k, v in importance_dict.items()}
            return importance_dict
        else:
            raise ValueError(f"Unsupported model type : {self.model_type}")

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
                if not hasattr(self, "is_initialized"):
                    self.is_initialized = False

                if len(np.unique(y_batch)) < 2:
                    print(f"Skipping batch {iteration} because it only contains one class: {np.unique(y_batch)}")
                    return

                if not self.is_initialized:
                    # First valid batch → initialize model
                    self.model.set_params(n_estimators=self.n_estimators_step)
                    self.model.fit(X_batch, y_batch, xgb_model=None)
                    self.is_initialized = True
                    print(f"Model initialized at batch {iteration}")
                else:
                    # Continue training
                    prev_booster = self.model.get_booster()
                    new_estimators = self.model.n_estimators + self.n_estimators_step
                    self.model.set_params(n_estimators=new_estimators)
                    self.model.fit(X_batch, y_batch, xgb_model=prev_booster)
                    print(f"Trained on batch {iteration}")

    def data_generator(self):
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
        for chunk in pd.read_csv(f'{self.Paths.train_data}/{self.symbol}_data.csv', chunksize=self.chunk):
            X = chunk.drop(columns = [self.target_col]).values
            y = chunk[self.target_col].values
            yield X, y

    def train(self):
        for i, (X_batch, y_batch) in tqdm(enumerate(self.data_generator()),desc="Model Training",total=self.total_line,dynamic_ncols=True):
            self.partial_train(X_batch, y_batch, iteration=i)
        joblib.dump(self.model, self.model_path)

    def test_result(self):
        test = pd.read_csv(f'{self.Paths.test_data}/{self.symbol}_data.csv')
        X = test.drop(columns=[self.target_col])
        y = test[self.target_col]
        y_pred = self.predict(X)
        print(classification_report(y, y_pred))
        
    def load(self,path = None):
        if path is not None:
            self.model = joblib.load(path)
        else:
            self.model = joblib.load(self.model_path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
    
    def get_model(self):
        return self.model
