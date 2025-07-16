# market_data_tool.py
# ────────────────────────────────────────────────────────────────
#  📈  MarketDataTool  —  다중 자산 가격‧리스크‧VIX 한‑방 조회
#     · 선택일 종가 / 최근 종가 / 기대수익률 / 변동성 / 공분산 / VIX
#     · 단일‑날짜 조회·휴장일 대응, 타임존 오프셋 및 NaN 문제 해결
# ────────────────────────────────────────────────────────────────

from __future__ import annotations

import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Any, Type
from pydantic import BaseModel, Field
from datetime import date, timedelta, datetime

from AIChat.BaseFinanceTool import BaseFinanceTool  # 👈 프로젝트 내부 베이스 툴

# ────────────────────────────────
# 1. 헬퍼
# ────────────────────────────────
def _pick_price_col(df: pd.DataFrame) -> str:
    """auto_adjust=True 일 때는 Close, 아닐 때는 Adj Close 유무가 달라진다."""
    return "Close" if "Close" in df.columns else "Adj Close"

def today_str() -> str:       return date.today().isoformat()
def yesterday_str() -> str:   return (date.today() - timedelta(days=1)).isoformat()

def _find_nearest_row(df: pd.DataFrame, target: str) -> Optional[pd.Series]:
    """target(YYYY‑MM‑DD) 과 일치 ↘ 없으면 직전 영업일 row"""
    if df.empty:
        return None
    target_date = pd.to_datetime(target).date()

    # Date 열에서 순수 date 만 캐싱
    if "_only_date" not in df.columns:
        df["_only_date"] = pd.to_datetime(df["Date"]).dt.date

    exact = df[df["_only_date"] == target_date]
    if not exact.empty:
        return exact.iloc[-1]

    before = df[df["_only_date"] < target_date]
    return None if before.empty else before.iloc[-1]

def extract_latest_values(price_data: Dict[str, pd.DataFrame]):
    latest_prices, latest_returns, latest_date = {}, {}, None
    for t, df in price_data.items():
        if df.empty:
            continue
        price_col = _pick_price_col(df)
        latest_prices[t]  = float(df[price_col].iloc[-1])
        latest_returns[t] = float(df["Daily Return"].iloc[-1])
        if latest_date is None:
            latest_date = df["Date"].iloc[-1].strftime("%Y-%m-%d")
    return latest_prices, latest_returns, latest_date

# ────────────────────────────────
# 2. 입력/출력 모델
# ────────────────────────────────
class MarketDataInput(BaseModel):
    tickers: List[str] = Field(..., description="예: ['TSLA','AAPL']")
    start_date: str    = Field(default_factory=yesterday_str)
    end_date:   str    = Field(default_factory=today_str)
    select_data: str   = Field(default_factory=today_str,
                               description="선택일 (YYYY‑MM‑DD)")

class MarketDataOutput(BaseModel):
    price_data: Dict[str, List[Dict[str, Any]]]
    latest_prices: Dict[str, float]
    latest_returns: Dict[str, float]
    latest_date: Optional[str]

    selected_prices:  Dict[str, float]
    selected_returns: Dict[str, float]
    selected_date:    Optional[str]

    expected_returns: Dict[str, float]
    volatility:       Dict[str, float]
    covariance_matrix: Dict[str, Any] | None = None
    vix: Optional[float] = None
    summary: str

# ────────────────────────────────
# 3. 메인 툴
# ────────────────────────────────
class MarketDataTool(BaseFinanceTool):
    """다중 자산 가격·리스크·VIX 조회"""
    name        = "market_data"
    description = "주식·ETF·채권·원자재·VIX 시계열과 리스크 지표를 반환"
    args_schema: Type[BaseModel] = MarketDataInput

    # LangChain function‑calling entry
    def _run(self, **kwargs) -> str:
        return self.get_data(**kwargs).model_dump_json()

    # ── 핵심 로직 ──────────────────────────────────────────
    def get_data(self, **params) -> MarketDataOutput:
        inp = MarketDataInput(**params)

        # 날짜 sanity (end < start → 교정, 동일날짜 → 그대로 두어 “하루” 조회 허용)
        if inp.end_date < inp.start_date:
            inp.end_date = inp.start_date

        raw = yf.download(
            inp.tickers,
            start=inp.start_date,
            end=(datetime.strptime(inp.end_date, "%Y-%m-%d") +
                 timedelta(days=1)).strftime("%Y-%m-%d"),  # yfinance end 는 exclusive
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )

        price_data: Dict[str, pd.DataFrame] = {}
        for t in inp.tickers:
            df = raw[t].copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
            if df.empty:
                continue
            close_col = _pick_price_col(df)
            df = df.reset_index()                       # Date 인덱스를 컬럼으로
            df["Daily Return"] = df[close_col].pct_change()
            if close_col != "Adj Close":
                df = df.rename(columns={close_col: "Adj Close"})

            # 🔑 NaN 처리 개선: 첫 행 Daily Return 0.0, 종가 NaN 행만 제거
            df = df[["Date", "Adj Close", "Daily Return"]]
            df["Daily Return"] = df["Daily Return"].fillna(0.0)
            df = df.dropna(subset=["Adj Close"])

            if not df.empty:
                price_data[t] = df

        # 데이터가 하나도 없으면 즉시 반환
        if not price_data:
            return MarketDataOutput(
                price_data={}, latest_prices={}, latest_returns={}, latest_date=None,
                selected_prices={}, selected_returns={}, selected_date=None,
                expected_returns={}, volatility={}, covariance_matrix=None, vix=None,
                summary="요청 종목의 데이터가 조회 구간에 존재하지 않습니다."
            )

        # 최신 시점·통계
        latest_prices, latest_returns, latest_date = extract_latest_values(price_data)
        cov = self._covariance_matrix(inp.tickers, inp.start_date, inp.end_date)
        exp = self._expected_returns(inp.tickers, inp.start_date, inp.end_date)
        vol = self._volatility(inp.tickers, inp.start_date, inp.end_date)
        vix = self._latest_vix()

        # 선택일 값
        selected_prices, selected_returns = {}, {}
        selected_date_global: Optional[str] = None
        for t, df in price_data.items():
            row = _find_nearest_row(df, inp.select_data)
            if row is not None:
                selected_prices[t]  = float(row["Adj Close"])
                selected_returns[t] = float(row["Daily Return"])
                if selected_date_global is None:
                    selected_date_global = row["Date"].strftime("%Y-%m-%d")

        # ── 요약 문자열 ──────────────────────────────────
        summary_lines = [
            "📊 [시장 데이터 요약]",
            f"📅 최신 기준일: {latest_date}",
            f"📌 선택일 ({inp.select_data}) 기준: {selected_date_global or '해당 없음'}",
            f"티커: {', '.join(price_data.keys())}",
        ]
        for t in exp:
            lp = latest_prices[t]; lr = latest_returns[t]
            sp = selected_prices.get(t); sr = selected_returns.get(t)
            part_sel = (f"선택종가 ${sp:.2f}, 선택수익률 {sr:.2%} | "
                        if sp is not None else "")
            summary_lines.append(
                f"  - {t}: 최신종가 ${lp:.2f}, 일수익률 {lr:.2%} | "
                f"{part_sel}기대수익률 {exp[t]:.4f}, 변동성 {vol[t]:.4f}"
            )
        if vix is not None:
            summary_lines.append(f"VIX: {vix:.2f}")
        if cov is not None:
            summary_lines.append(f"공분산 평균: {pd.DataFrame(cov).values.mean():.6f}")

        summary = "\n".join(summary_lines)

        # 직렬화
        price_serial = {k: v.to_dict("records") for k, v in price_data.items()}
        cov_serial   = None if cov is None else cov.to_dict()

        return MarketDataOutput(
            price_data        = price_serial,
            latest_prices     = latest_prices,
            latest_returns    = latest_returns,
            latest_date       = latest_date,
            selected_prices   = selected_prices,
            selected_returns  = selected_returns,
            selected_date     = selected_date_global,
            expected_returns  = exp,
            volatility        = vol,
            covariance_matrix = cov_serial,
            vix               = vix,
            summary           = summary,
        )

    # ── 내부 통계 메서드들 ───────────────────────────────
    def _covariance_matrix(self, tickers, start, end):
        data = yf.download(tickers, start=start, end=end,
                           group_by="ticker", progress=False, auto_adjust=True)
        returns = {}
        for t in tickers:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            price_col = _pick_price_col(df)
            returns[t] = df[price_col].pct_change().dropna()
        return pd.DataFrame(returns).cov()

    def _expected_returns(self, tickers, start, end, freq="daily"):
        data = yf.download(tickers, start=start, end=end,
                           group_by="ticker", progress=False, auto_adjust=True)
        scale = {"daily": 1, "monthly": 21, "annual": 252}[freq]
        exp = {}
        for t in tickers:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            price_col = _pick_price_col(df)
            exp[t] = df[price_col].pct_change().dropna().mean() * scale
        return exp

    def _volatility(self, tickers, start, end, freq="daily"):
        data = yf.download(tickers, start=start, end=end,
                           group_by="ticker", progress=False, auto_adjust=True)
        scale = {"daily": 1, "monthly": 21 ** 0.5, "annual": 252 ** 0.5}[freq]
        vol = {}
        for t in tickers:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            price_col = _pick_price_col(df)
            vol[t] = df[price_col].pct_change().dropna().std() * scale
        return vol

    def _latest_vix(self) -> Optional[float]:
        vix = yf.Ticker("^VIX").history(period="1d")
        return None if vix.empty else float(vix["Close"].iloc[-1])
