import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from AIChat.BaseFinanceTool import BaseFinanceTool
from datetime import date

def today_str():
    return date.today().isoformat()

class MarketDataInput(BaseModel):
    """
    미국/글로벌 주식, ETF, 채권, 원자재 등 자산의 시장 데이터를 조회할 때 사용하는 입력 모델입니다.
    - tickers: 조회할 자산(종목) 코드들의 리스트. 예: ['TSLA', 'AAPL']
    - start_date: 조회 시작 날짜 (YYYY-MM-DD). 예: '2023-10-01'
    - end_date: 조회 종료 날짜 (YYYY-MM-DD). 예: '2023-10-31'
    (날짜를 입력하지 않으면 자동으로 오늘 날짜가 들어갑니다.)
    """
    tickers: List[str] = Field(
        ...,
        description="조회할 종목(티커) 리스트. 예: ['TSLA', 'AAPL']"
    )
    start_date: str = Field(
        default_factory=today_str,
        description="조회 시작일 (YYYY-MM-DD). 예: '2023-10-01', 입력하지 않으면 오늘 날짜가 기본값"
    )
    end_date: str = Field(
        default_factory=today_str,
        description="조회 종료일 (YYYY-MM-DD). 예: '2023-10-31', 입력하지 않으면 오늘 날짜가 기본값"
    )

class MarketDataOutput:
    def __init__(
        self,
        price_data: Dict[str, pd.DataFrame],
        covariance_matrix: pd.DataFrame,
        expected_returns: Dict[str, float],
        volatility: Dict[str, float],
        vix: Optional[float] = None,
    ):
        self.price_data = price_data
        self.covariance_matrix = covariance_matrix
        self.expected_returns = expected_returns
        self.volatility = volatility
        self.vix = vix
        self.summary = self._build_summary()

    def _build_summary(self) -> str:
        summary = "📊 [시장 데이터 요약]\n"
        summary += f"티커: {', '.join(self.price_data.keys())}\n"
        for t in self.expected_returns:
            summary += (
                f"  - {t}: 기대수익률 {self.expected_returns[t]:.4f}, "
                f"변동성 {self.volatility[t]:.4f}\n"
            )
        if self.vix is not None:
            summary += f"VIX(변동성): {self.vix:.2f}\n"
        if self.covariance_matrix is not None:
            vals = self.covariance_matrix.values
            avg_cov = vals.mean() if vals.size > 0 else 0
            summary += f"공분산 행렬 평균값: {avg_cov:.6f}\n"
        return summary

class MarketDataTool(BaseFinanceTool):
    def __init__(self):
        super().__init__()

    def get_data(
        self,
        **params
    ) -> MarketDataOutput:
        input_data = MarketDataInput(**params)
        tickers = input_data.tickers
        start_date = input_data.start_date
        end_date = input_data.end_date

        data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            group_by='ticker',
            auto_adjust=False,
            progress=False
        )
        price_data = {}

        # 유연하게 tuple/string 컬럼 모두 지원
        def get_close_col(df: pd.DataFrame, ticker: Optional[str] = None) -> Union[str, tuple]:
            # 튜플 MultiIndex 케이스
            if isinstance(df.columns, pd.MultiIndex):
                candidates = []
                if ticker:
                    candidates = [(ticker, 'Adj Close'), (ticker, 'Close')]
                else:
                    # 혹시 ticker가 없으면 모든 티커 대상
                    candidates = [(t, 'Adj Close') for t in df.columns.get_level_values(0).unique()]
                    candidates += [(t, 'Close') for t in df.columns.get_level_values(0).unique()]
                for c in candidates:
                    if c in df.columns:
                        return c
            else:
                for c in ['Adj Close', 'Close']:
                    if c in df.columns:
                        return c
            raise ValueError(f"{ticker or ''}의 가격 데이터에 'Adj Close'나 'Close' 컬럼이 없습니다: {df.columns}")

        # 메인 루프: 싱글/멀티티커 모두 MultiIndex 방어
        for ticker in tickers:
            if isinstance(data.columns, pd.MultiIndex):
                # 멀티인덱스 데이터에서 이 ticker의 서브프레임 추출
                if ticker in data.columns.get_level_values(0):
                    sub = data[ticker].copy().reset_index()
                    try:
                        close_col = get_close_col(data, ticker)
                        # sub의 컬럼명을 str로 변환 (원래는 'Adj Close'나 'Close'가 있음)
                        if close_col not in sub.columns:
                            # 혹시 컬럼명이 string이 아니라 tuple인 경우도 있을 수 있음
                            close_col_str = close_col[1] if isinstance(close_col, tuple) else close_col
                        else:
                            close_col_str = close_col
                        sub['Daily Return'] = sub[close_col_str].pct_change()
                        if close_col_str != "Adj Close":
                            sub = sub.rename(columns={close_col_str: "Adj Close"})
                        sub = sub[['Date', 'Adj Close', 'Daily Return']]
                        price_data[ticker] = sub
                    except Exception as e:
                        print(f"[경고] {ticker} 가격 데이터 오류: {e}")
                        continue
                else:
                    print(f"[경고] {ticker}의 가격 데이터가 데이터프레임에 없음: {data.columns}")
                    continue
            else:
                sub = data.copy().reset_index()
                try:
                    close_col = get_close_col(sub)
                    sub['Daily Return'] = sub[close_col].pct_change()
                    if close_col != "Adj Close":
                        sub = sub.rename(columns={close_col: "Adj Close"})
                    sub = sub[['Date', 'Adj Close', 'Daily Return']]
                    price_data[ticker] = sub
                except Exception as e:
                    print(f"[경고] {ticker} 가격 데이터 오류: {e}")
                    continue

        # 나머지 메트릭
        cov = self.get_covariance_matrix(tickers, start_date, end_date)
        exp_ret = self.get_expected_returns(tickers, start_date, end_date)
        vol = self.get_volatility(tickers, start_date, end_date)
        vix = self._get_latest_vix_value()

        # Dict로 반환해야 할 경우
        if params.get('as_dict', False):
            price_data = {k: v.to_dict(orient='records') for k, v in price_data.items()}
            cov = cov.to_dict() if hasattr(cov, "to_dict") else cov

        return MarketDataOutput(
            price_data=price_data,
            covariance_matrix=cov,
            expected_returns=exp_ret,
            volatility=vol,
            vix=vix
        )

    def get_covariance_matrix(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False, progress=False)
        if len(tickers) == 1:
            ticker = tickers[0]
            if isinstance(data.columns, pd.MultiIndex):
                # => ('TSLA', 'Close') 식으로 접근
                col = (ticker, "Adj Close") if (ticker, "Adj Close") in data.columns else (ticker, "Close")
                returns = data[col].pct_change().dropna()
            else:
                col = "Adj Close" if "Adj Close" in data.columns else "Close"
                returns = data[col].pct_change().dropna()
            return pd.DataFrame([[returns.var()]], index=tickers, columns=tickers)
        else:
            returns = pd.DataFrame({
                ticker: (
                    data[ticker]["Adj Close"].pct_change()
                    if "Adj Close" in data[ticker] else data[ticker]["Close"].pct_change()
                )
                for ticker in tickers
            })
            return returns.cov()

    def get_expected_returns(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        freq: str = 'daily'
    ) -> Dict[str, float]:
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False, progress=False)
        if len(tickers) == 1:
            ticker = tickers[0]
            if isinstance(data.columns, pd.MultiIndex):
                col = (ticker, "Adj Close") if (ticker, "Adj Close") in data.columns else (ticker, "Close")
                returns = data[col].pct_change().dropna()
            else:
                col = "Adj Close" if "Adj Close" in data.columns else "Close"
                returns = data[col].pct_change().dropna()
            mean = returns.mean()
            if freq == 'annual':
                mean = mean * 252
            elif freq == 'monthly':
                mean = mean * 21
            return {ticker: mean}
        else:
            mean_dict = {}
            for ticker in tickers:
                sub = data[ticker]
                col = "Adj Close" if "Adj Close" in sub.columns else "Close"
                returns = sub[col].pct_change().dropna()
                mean = returns.mean()
                if freq == 'annual':
                    mean = mean * 252
                elif freq == 'monthly':
                    mean = mean * 21
                mean_dict[ticker] = mean
            return mean_dict


    def get_volatility(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        freq: str = 'daily'
    ) -> Dict[str, float]:
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False, progress=False)
        if len(tickers) == 1:
            ticker = tickers[0]
            if isinstance(data.columns, pd.MultiIndex):
                col = (ticker, "Adj Close") if (ticker, "Adj Close") in data.columns else (ticker, "Close")
                returns = data[col].pct_change().dropna()
            else:
                col = "Adj Close" if "Adj Close" in data.columns else "Close"
                returns = data[col].pct_change().dropna()
            std = returns.std()
            if freq == 'annual':
                std = std * (252 ** 0.5)
            elif freq == 'monthly':
                std = std * (21 ** 0.5)
            return {ticker: std}
        else:
            std_dict = {}
            for ticker in tickers:
                sub = data[ticker]
                col = "Adj Close" if "Adj Close" in sub.columns else "Close"
                returns = sub[col].pct_change().dropna()
                std = returns.std()
                if freq == 'annual':
                    std = std * (252 ** 0.5)
                elif freq == 'monthly':
                    std = std * (21 ** 0.5)
                std_dict[ticker] = std
            return std_dict


    def _get_latest_vix_value(self) -> Optional[float]:
        vix_hist = yf.Ticker("^VIX").history(period="1d")
        if not vix_hist.empty:
            return float(vix_hist["Close"].iloc[-1])
        return None
