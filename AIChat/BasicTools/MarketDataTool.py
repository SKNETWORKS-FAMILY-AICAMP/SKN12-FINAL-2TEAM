"""
주식/ETF/채권/Commodity 등 전체 자산의 시계열 데이터를 가져오는 도구입니다.
이 도구는 yfinance를 사용하여 가격과 수익률을 반환합니다.
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Any
from AIChat.BaseFinanceTool import BaseFinanceTool

class MarketDataTool(BaseFinanceTool):
    def __init__(self):
        super().__init__()

    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        as_dict: bool = False
    ) -> Dict[str, Any]:
        result = {}
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
        price_data = {}
        if len(tickers) == 1:
            ticker = tickers[0]
            df = data.copy()
            df = df.reset_index()
            df['Daily Return'] = df['Adj Close'].pct_change()
            df = df[['Date', 'Adj Close', 'Daily Return']]
            price_data[ticker] = df
        else:
            for ticker in tickers:
                if (ticker,) in data.columns:
                    sub = data[ticker]
                else:
                    sub = data[ticker] if ticker in data else None
                if sub is None or sub.empty:
                    continue
                sub = sub.reset_index()
                sub['Daily Return'] = sub['Adj Close'].pct_change()
                sub = sub[['Date', 'Adj Close', 'Daily Return']]
                price_data[ticker] = sub
        # 공분산, 기대수익률, 변동성 계산
        cov = self.get_covariance_matrix(tickers, start_date, end_date)
        exp_ret = self.get_expected_returns(tickers, start_date, end_date)
        vol = self.get_volatility(tickers, start_date, end_date)
        if as_dict:
            # DataFrame을 dict로 변환
            price_data = {k: v.to_dict(orient='records') for k, v in price_data.items()}
            cov = cov.to_dict()
        result = {
            'price_data': price_data,
            'covariance_matrix': cov,
            'expected_returns': exp_ret,
            'volatility': vol
        }
        return result

    def get_covariance_matrix(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        자산군의 일간 수익률 공분산 행렬 반환
        """
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
        if len(tickers) == 1:
            returns = data['Adj Close'].pct_change().dropna()
            return pd.DataFrame([[returns.var()]], index=tickers, columns=tickers)
        else:
            returns = pd.DataFrame({ticker: data[ticker]['Adj Close'].pct_change() for ticker in tickers})
            return returns.cov()

    def get_expected_returns(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        freq: str = 'daily'
    ) -> Dict[str, float]:
        """
        자산군의 기대수익률(평균 수익률) 반환. freq: 'daily', 'monthly', 'annual'
        """
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
        if len(tickers) == 1:
            returns = data['Adj Close'].pct_change().dropna()
            mean = returns.mean()
            if freq == 'annual':
                mean = mean * 252
            elif freq == 'monthly':
                mean = mean * 21
            return {tickers[0]: mean}
        else:
            returns = pd.DataFrame({ticker: data[ticker]['Adj Close'].pct_change() for ticker in tickers})
            mean = returns.mean()
            if freq == 'annual':
                mean = mean * 252
            elif freq == 'monthly':
                mean = mean * 21
            return mean.to_dict()

    def get_volatility(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        freq: str = 'daily'
    ) -> Dict[str, float]:
        """
        자산군의 변동성(표준편차) 반환. freq: 'daily', 'monthly', 'annual'
        """
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
        if len(tickers) == 1:
            returns = data['Adj Close'].pct_change().dropna()
            std = returns.std()
            if freq == 'annual':
                std = std * (252 ** 0.5)
            elif freq == 'monthly':
                std = std * (21 ** 0.5)
            return {tickers[0]: std}
        else:
            returns = pd.DataFrame({ticker: data[ticker]['Adj Close'].pct_change() for ticker in tickers})
            std = returns.std()
            if freq == 'annual':
                std = std * (252 ** 0.5)
            elif freq == 'monthly':
                std = std * (21 ** 0.5)
            return std.to_dict() 