import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class RollingRegression():
    def __init__(self,based_df,market_df):
        self.based_df = based_df
        self.market_df = market_df
        self.poly = PolynomialFeatures(degree=2)
        self.model = LinearRegression()

    def rolling_regression(
        self,
        y: pd.Series,
        x: pd.Series,
        window: int = 50,
        fillna: bool = True
    ) -> pd.DataFrame:
        """
        Rolling linear regression between two time series (like SOL vs BTC).

        Returns a DataFrame with columns: ['alpha', 'beta', 'r2'].
        Similar to ta.trend indicators.
        """
        if len(y) != len(x):
            raise ValueError("Input series must have the same length.")
        
        alphas, betas, r2s = [np.nan] * len(y), [np.nan] * len(y), [np.nan] * len(y)
        gammas = [np.nan] * len(y)

        for i in range(window, len(y)):
            y_window = y.iloc[i - window:i].values.reshape(-1, 1)
            x_window = x.iloc[i - window:i].values.reshape(-1, 1)
            X_poly = self.poly.fit_transform(x_window)
            self.model.fit(X_poly, y_window)
            
            alpha = float(self.model.intercept_)
            beta = float(self.model.coef_[0][1])
            gamma = float(self.model.coef_[0][2])
            r2 = self.model.score(X_poly, y_window)
            alphas[i] = alpha
            betas[i] = beta
            r2s[i] = r2
            gammas[i] = gamma

        df_result = pd.DataFrame({
            'alpha': alphas,
            'beta': betas,
            'gamma' : gammas,
            'r2': r2s
        }, index=y.index)

        if fillna:
            df_result = df_result.fillna(method='bfill')

        return df_result
    
    def AddRegressionValues(self):
        df = pd.DataFrame({
            'market': self.market_df['close'],
            'base': self.based_df['close']
        }).dropna()

        df = df.pct_change().dropna()

        reg = self.rolling_regression(df['base'], df['market'], window=50)

        return self.based_df.join(reg)