import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Any, Union, Type
from pydantic import BaseModel, Field
from datetime import date, timedelta, datetime
from AIChat.BaseFinanceTool import BaseFinanceTool
# ────────────────────────────────────────────────────────────────
# 1. 헬퍼
# ────────────────────────────────────────────────────────────────
def _pick_price_col(df: pd.DataFrame) -> str:          # ⬅️
    """auto_adjust=True면 Close, 아니면 Adj Close가 있을 수 있음"""
    return "Close" if "Close" in df.columns else "Adj Close"

def today_str() -> str:
    return date.today().isoformat()

def yesterday_str() -> str:
    return (date.today() - timedelta(days=1)).isoformat()

def extract_latest_values(price_data: Dict[str, pd.DataFrame]):
    latest_prices, latest_returns, latest_date = {}, {}, None
    for ticker, df in price_data.items():
        if df.empty:
            continue
        # 1️⃣ 컬럼 존재 여부 확인
        price_col = _pick_price_col(df)  
        latest_prices[ticker]  = float(df[price_col].dropna().iloc[-1])

        ret_col = "Daily Return" if "Daily Return" in df.columns else None
        if ret_col:
            latest_returns[ticker] = float(df[ret_col].dropna().iloc[-1])

        if latest_date is None and "Date" in df.columns:
            val = df["Date"].iloc[-1]
            latest_date = val.strftime("%Y-%m-%d") if hasattr(val, "strftime") else str(val)

    return latest_prices, latest_returns, latest_date

# ────────────────────────────────────────────────────────────────
# 2. 입력/출력 모델
# ────────────────────────────────────────────────────────────────


class MarketDataInput(BaseModel):
    """시장 데이터 조회용 입력."""
    tickers: List[str] = Field(..., description="예: ['TSLA', 'AAPL']")
    start_date: str    = Field(default_factory=yesterday_str)
    end_date: str      = Field(default_factory=today_str)
    as_dict: bool      = Field(False, description="DataFrame → dict 변환 여부")

class MarketDataOutput(BaseModel):
    price_data: Dict[str, List[Dict[str, Any]]]
    latest_prices: Dict[str, float]
    latest_returns: Dict[str, float]
    latest_date: Optional[str]
    expected_returns: Dict[str, float]
    volatility: Dict[str, float]
    covariance_matrix: Dict[str, Any] | None = None
    vix: Optional[float] = None
    summary: str

    # 래퍼가 호출할 요약 함수
    def _build_summary(self) -> str:
        return self.summary

# ────────────────────────────────────────────────────────────────
# 3. 메인 툴
# ────────────────────────────────────────────────────────────────
class MarketDataTool(BaseFinanceTool):
    """📈 전 세계 자산 가격·리스크 지표 한방 조회"""
    name: str = "market_data"
    description: str = (
        "미국/글로벌 주식·ETF·채권·원자재 등의 OHLC, 수익률, 공분산, 변동성, VIX를 반환한다."
    )
    args_schema: Type[BaseModel] = MarketDataInput

    # 3-1. 툴 진입점 (LangChain/Function-Calling 호환)
    def _run(self, **kwargs) -> str:            # JSON 문자열!
        return self.get_data(**kwargs).model_dump_json()
    # 3-2. 실질 로직
    def get_data(self, **params) -> MarketDataOutput:
        inp = MarketDataInput(**params)
        today = date.today().isoformat()
        if inp.end_date < today:
            inp.start_date = (date.today() - timedelta(days=14)).isoformat()
            inp.end_date   = today
            
        if inp.start_date == inp.end_date:
            inp.end_date = (datetime.strptime(inp.end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        raw = yf.download(
            inp.tickers,
            start=inp.start_date,
            end=inp.end_date,
            group_by="ticker",
            auto_adjust=True,         # ← 여기
            progress=False,
        )

        price_data = {}
        for t in inp.tickers:
            df = raw[t].copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
            if df.empty:
                continue
            close_col = _pick_price_col(df)
            df = df.reset_index()
            df["Daily Return"] = df[close_col].pct_change()
            if close_col != "Adj Close":
                df = df.rename(columns={close_col: "Adj Close"})
            df = df[["Date", "Adj Close", "Daily Return"]].dropna()
            if not df.empty:
                price_data[t] = df

        # 데이터 없으면 바로 빈 껍데기 리턴
        if not price_data:
            return MarketDataOutput(
                price_data={},
                latest_prices={},
                latest_returns={},
                latest_date=None,
                expected_returns={},
                volatility={},
                covariance_matrix=None,
                vix=None,
                summary="요청하신 종목은 최근 2주간 거래 데이터가 없습니다.",
            )

        # 추가 지표 계산
        cov = self._covariance_matrix(inp.tickers, inp.start_date, inp.end_date)
        exp = self._expected_returns(inp.tickers, inp.start_date, inp.end_date)
        vol = self._volatility(inp.tickers, inp.start_date, inp.end_date)
        vix = self._latest_vix()

        # 종가·수익률·기준일
        latest_prices, latest_returns, latest_date = extract_latest_values(price_data)

        # 요약
        summary_lines = [
            "📊 [시장 데이터 요약]",
            f"📅 기준일: {latest_date}",
            f"티커: {', '.join(price_data.keys())}",
        ]
        for t in exp:
            summary_lines.append(
                f"  - {t}: 종가 ${latest_prices[t]:.2f}, "
                f"일간 수익률 {latest_returns[t]:.2%}, "
                f"기대수익률 {exp[t]:.4f}, 변동성 {vol[t]:.4f}"
            )
        if vix is not None:
            summary_lines.append(f"VIX(변동성): {vix:.2f}")
        if cov is not None:
            summary_lines.append(f"공분산 평균: {pd.DataFrame(cov).values.mean():.6f}")
        summary = "\n".join(summary_lines)

        # 직렬화 준비
# ── 직렬화 준비 ──
        price_serial = {k: v.to_dict("records") for k, v in price_data.items()}
        cov_serial   = None if cov is None else cov.to_dict()

        return MarketDataOutput(
            price_data=price_serial,
            latest_prices=latest_prices,
            latest_returns=latest_returns,
            latest_date=latest_date,
            expected_returns=exp,
            volatility=vol,
            covariance_matrix=cov_serial,
            vix=vix,
            summary=summary,
        )

    # ─── 내부 계산용 메서드들 ───
    def _covariance_matrix(self, tickers, start, end):
        data = yf.download(tickers, start=start, end=end, group_by="ticker", progress=False, auto_adjust=True)
        returns = pd.DataFrame({
            t: (
                data[t][_pick_price_col(data[t])].pct_change()
                if isinstance(data.columns, pd.MultiIndex)
                else data[_pick_price_col(data)].pct_change()
            ).dropna()
            for t in tickers
        })
        return returns.cov()

    def _expected_returns(self, tickers, start, end, freq="daily"):
        data = yf.download(tickers, start=start, end=end,
                        group_by="ticker", progress=False,
                        auto_adjust=True)                     # ← 명시
        scale = {"daily": 1, "monthly": 21, "annual": 252}[freq]
        mean_dict = {}
        for t in tickers:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            price_col = _pick_price_col(df)
            series = df[price_col].pct_change().dropna()
            mean_dict[t] = series.mean() * scale
        return mean_dict

    def _volatility(self, tickers, start, end, freq="daily"):
        data = yf.download(tickers, start=start, end=end,
                        group_by="ticker", progress=False,
                        auto_adjust=True)           # ← 추가
        scale = {"daily": 1, "monthly": 21 ** 0.5, "annual": 252 ** 0.5}[freq]
        std_dict = {}
        for t in tickers:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            price_col = _pick_price_col(df)            # ← 교체
            series = df[price_col].pct_change().dropna()
            std_dict[t] = series.std() * scale
        return std_dict

    def _latest_vix(self) -> Optional[float]:
        vix = yf.Ticker("^VIX").history(period="1d")
        return None if vix.empty else float(vix["Close"].iloc[-1])
