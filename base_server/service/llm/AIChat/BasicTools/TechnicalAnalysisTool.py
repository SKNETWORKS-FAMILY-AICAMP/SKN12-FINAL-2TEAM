from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field
import yfinance as yf
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
import pandas as pd

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
    def __init__(self, ai_chat_service):
        # 지연 임포트로 순환 참조 방지
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service

    def get_data(self, **params) -> TechnicalAnalysisOutput:
        print(f"[TechnicalAnalysisTool] Called with params: {params}")
        # params: dict로 들어오므로 모델로 변환
        try:
            input_data = TechnicalAnalysisInput(**params)
            print(f"[TechnicalAnalysisTool] Input data: {input_data}")
        except Exception as e:
            print(f"[TechnicalAnalysisTool] Input error: {e}")
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
            print(f"[TechnicalAnalysisTool] Processing ticker: {ticker}")
            try:
                stock = yf.Ticker(ticker)
                print(f"[TechnicalAnalysisTool] Fetching history for {ticker}...")
                
                # 간단한 예외 처리로 yfinance 호출
                try:
                    hist = stock.history(period="6mo", auto_adjust=False)
                    print(f"[TechnicalAnalysisTool] Successfully fetched {len(hist)} rows for {ticker}")
                except Exception as fetch_error:
                    print(f"[TechnicalAnalysisTool] Fetch error for {ticker}: {fetch_error}")
                    raise fetch_error
                
                print(hist)
                
                # 데이터가 비어있는지 먼저 확인
                if hist.empty:
                    print(f"[TechnicalAnalysisTool] Empty data for {ticker}")
                    results.append(TechnicalAnalysisSingleOutput(
                        agent="error",
                        ticker=ticker,
                        summary=f"{ticker}의 가격 데이터가 비어있습니다."
                    ))
                    continue
                
                # Close 컬럼 찾기
                print(f"[TechnicalAnalysisTool] Available columns for {ticker}: {hist.columns.tolist()}")
                if "Adj Close" in hist.columns:
                    close = hist["Adj Close"]
                    print(f"[TechnicalAnalysisTool] Using Adj Close for {ticker}")
                elif "Close" in hist.columns:
                    close = hist["Close"]
                    print(f"[TechnicalAnalysisTool] Using Close for {ticker}")
                else:
                    print(f"[TechnicalAnalysisTool] No Close/Adj Close found for {ticker}")
                    results.append(TechnicalAnalysisSingleOutput(
                        agent="error",
                        ticker=ticker,
                        summary=f"{ticker}의 가격 데이터에 'Close' 또는 'Adj Close' 컬럼이 없습니다."
                    ))
                    continue
                
                # Series가 아닌 경우 변환
                if not isinstance(close, pd.Series):
                    close = pd.Series(close)
                    print(f"[TechnicalAnalysisTool] Converted to Series for {ticker}")
                
                print(f"[TechnicalAnalysisTool] Close data type: {type(close)}, length: {len(close)}")
                print(f"[TechnicalAnalysisTool] Last 5 close values: {close.tail().tolist()}")
                
                # 기술적 지표 계산
                try:
                    print(f"[TechnicalAnalysisTool] Calculating RSI for {ticker}...")
                    rsi = RSIIndicator(close).rsi().iloc[-1]
                    print(f"[TechnicalAnalysisTool] RSI calculated: {rsi}")
                    
                    print(f"[TechnicalAnalysisTool] Calculating MACD for {ticker}...")
                    macd = MACD(close).macd().iloc[-1]
                    print(f"[TechnicalAnalysisTool] MACD calculated: {macd}")
                    
                    print(f"[TechnicalAnalysisTool] Calculating EMA for {ticker}...")
                    ema = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
                    print(f"[TechnicalAnalysisTool] EMA calculated: {ema}")
                    
                except Exception as calc_error:
                    print(f"[TechnicalAnalysisTool] Calculation error for {ticker}: {calc_error}")
                    results.append(TechnicalAnalysisSingleOutput(
                        agent="error",
                        ticker=ticker,
                        summary=f"기술적 지표 계산 오류: {calc_error}"
                    ))
                    continue

                # 성공적으로 계산된 경우 결과 생성
                print(f"[TechnicalAnalysisTool] About to create summary for {ticker}")
                summary = (
                    f"{ticker}의 기술적 분석: RSI={rsi:.2f}, MACD={macd:.2f}, 20일 EMA={ema:.2f}입니다."
                )
                print(f"[TechnicalAnalysisTool] Summary created: {summary}")
                
                print(f"[TechnicalAnalysisTool] Creating result for {ticker}: RSI={rsi:.2f}, MACD={macd:.2f}, EMA={ema:.2f}")
                
                try:
                    result = TechnicalAnalysisSingleOutput(
                        agent="TechnicalAnalysisTool",
                        ticker=ticker,
                        summary=summary,
                        rsi=rsi,
                        macd=macd,
                        ema=ema,
                        data={"rsi": rsi, "macd": macd, "ema": ema}
                    )
                    print(f"[TechnicalAnalysisTool] Result object created successfully for {ticker}")
                    
                    results.append(result)
                    print(f"[TechnicalAnalysisTool] Result added for {ticker}")
                except Exception as result_error:
                    print(f"[TechnicalAnalysisTool] Error creating result for {ticker}: {result_error}")
                    raise result_error
            except Exception as e:
                print(f"[TechnicalAnalysisTool] Error processing {ticker}: {e}")
                results.append(TechnicalAnalysisSingleOutput(
                    agent="error",
                    ticker=ticker,
                    summary=f"기술적 분석 오류: {e}"
                ))

        print(f"[TechnicalAnalysisTool] Returning {len(results)} results")
        return TechnicalAnalysisOutput(
            agent="TechnicalAnalysisTool",
            results=results
        )