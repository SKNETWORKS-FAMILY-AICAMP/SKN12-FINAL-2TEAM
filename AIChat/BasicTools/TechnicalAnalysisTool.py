from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field
from sqlalchemy import false
import yfinance as yf
import ta
from AIChat.BaseFinanceTool import BaseFinanceTool

class TechnicalAnalysisInput(BaseModel):
    tickers: List[str] = Field(
        ...,
        description="분석할 미국 주식의 종목 코드 리스트. 예: ['AAPL', 'TSLA', 'NVDA']"
    )

class TechnicalAnalysisSingleOutput:
    def __init__(
        self,
        agent: str,
        ticker: str,
        summary: str,
        rsi: Optional[float] = None,
        macd: Optional[float] = None,
        ema: Optional[float] = None,
        data: Optional[Dict[str, float]] = None
    ):
        self.agent = agent
        self.ticker = ticker
        self.summary = summary
        self.rsi = rsi
        self.macd = macd
        self.ema = ema
        self.data = data

class TechnicalAnalysisOutput:
    def __init__(
        self,
        agent: str,
        results: Union[List[TechnicalAnalysisSingleOutput], Dict[str, TechnicalAnalysisSingleOutput]]
    ):
        self.agent = agent
        self.results = results  # 여러 종목의 기술적 분석 결과들

class TechnicalAnalysisTool(BaseFinanceTool):
    def get_data(self, **params) -> TechnicalAnalysisOutput:
        # params: dict로 들어오므로 모델로 변환
        try:
            input_data = TechnicalAnalysisInput(**params)
        except Exception as e:
            return TechnicalAnalysisOutput(
                agent="error",
                results=[TechnicalAnalysisSingleOutput(
                    agent="error",
                    ticker=params.get('tickers', ['UNKNOWN'])[0],
                    summary=f"입력 파라미터 오류: {e}"
                )]
            )

        results = []

        for ticker in input_data.tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo", auto_adjust=False)

                print(hist)

                if "Adj Close" in hist.columns:
                    close = hist["Adj Close"]
                elif "Close" in hist.columns:
                    close = hist["Close"]
                else:
                    print(hist.columns.tolist())
                    if hist.empty:
                        results.append(TechnicalAnalysisSingleOutput(
                            agent="error",
                            ticker=ticker,
                            summary=f"{ticker}의 가격 데이터에 'Close' 또는 'Adj Close' 컬럼이 없습니다."
                        ))
                        continue
                    rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]
                    macd = ta.trend.MACD(close).macd().iloc[-1]
                    ema = ta.trend.EMAIndicator(close, window=20).ema_indicator().iloc[-1]

                    summary = (
                        f"{ticker}의 기술적 분석: RSI={rsi:.2f}, MACD={macd:.2f}, 20일 EMA={ema:.2f}입니다."
                    )

                    results.append(TechnicalAnalysisSingleOutput(
                        agent="TechnicalAnalysisTool",
                        ticker=ticker,
                        summary=summary,
                        rsi=rsi,
                        macd=macd,
                        ema=ema,
                        data={"rsi": rsi, "macd": macd, "ema": ema}
                    ))
            except Exception as e:
                results.append(TechnicalAnalysisSingleOutput(
                    agent="error",
                    ticker=ticker,
                    summary=f"기술적 분석 오류: {e}"
                ))

        return TechnicalAnalysisOutput(
            agent="TechnicalAnalysisTool",
            results=results
        )
