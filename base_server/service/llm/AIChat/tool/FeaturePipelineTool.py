from typing import List, Dict, Optional, Any
from datetime import datetime
from service.llm.AIChat.BasicTools.FinancialStatementTool import FinancialStatementTool
from service.llm.AIChat.BasicTools.NewsTool import NewsTool
from service.llm.AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput
import pandas as pd
import numpy as np

class FeaturePipelineTool:
    def __init__(self, ai_chat_service) -> None:
        self.ai_chat_service = ai_chat_service

        # 정규화용 기준값 (샘플 수치, 실측 데이터로 업데이트 가능)
        self.scaling_mean = {
            "RSI": 50.0, "MACD": 0.0, "VIX": 18.0,
            "priceEarningsRatio": 15.0, "returnOnEquity": 10.0,
            "news_count": 10.0, "positive_news_ratio": 0.5
        }
        self.scaling_std = {
            "RSI": 10.0, "MACD": 0.02, "VIX": 5.0,
            "priceEarningsRatio": 10.0, "returnOnEquity": 5.0,
            "news_count": 5.0, "positive_news_ratio": 0.2
        }

    def _extract_macro(self, macro_data: List[Dict[str, Any]], feature_name: str) -> float:
        """Extracts the latest value for a given feature from macro data."""
        latest_value = 0.0
        latest_date = ""
        for item in macro_data:
            if item.get("series_id") == feature_name:
                current_date = item.get("date", "")
                if current_date > latest_date:
                    latest_date = current_date
                    try:
                        value_str = item.get("value", "0.0")
                        if isinstance(value_str, str) and value_str != '.':
                            latest_value = float(value_str)
                        elif isinstance(value_str, (int, float)):
                            latest_value = value_str
                        else:
                            latest_value = 0.0
                    except (ValueError, TypeError):
                        latest_value = 0.0
        return latest_value

    def transform(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        feature_set: Optional[List[str]] = None,
        normalize: bool = False
    ) -> Dict[str, Any]:
        """
        feature_set: GDP, CPIAUCSL, DEXKOUS, RSI, MACD, EMA, VIX, PRICE, PRICE_HISTORY, priceEarningsRatio, returnOnEquity, marketCap 등
        """
        end_date = end_date or datetime.today().strftime("%Y-%m-%d")
        feature_set = feature_set or [
            "GDP", "CPIAUCSL", "DEXKOUS", "RSI", "MACD", "EMA", "VIX", "PRICE",
            "PRICE_HISTORY", "priceEarningsRatio", "returnOnEquity", "marketCap",
            "news_count", "positive_news_ratio"
        ]
        features: Dict[str, Any] = {}

        # Macro
        macro_series_ids = [f for f in ["GDP", "CPIAUCSL", "DEXKOUS"] if f in feature_set]
        if macro_series_ids:
            macro = MacroEconomicTool(self.ai_chat_service).get_data(series_ids=macro_series_ids)
            if macro.data:
                for feat in macro_series_ids:
                    features[feat] = self._extract_macro(macro.data, feat)

        # Technical
        tech_features = [f for f in ["RSI", "MACD", "EMA"] if f in feature_set]
        if tech_features and tickers:
            ta = TechnicalAnalysisTool(self.ai_chat_service).get_data(tickers=tickers)
            ta_data = None
            if isinstance(ta.results, dict):
                ta_data = ta.results.get(tickers[0]) or (next(iter(ta.results.values())) if ta.results else None)
            elif isinstance(ta.results, list) and ta.results:
                ta_data = ta.results[0]
            
            if ta_data:
                if "RSI" in feature_set: features["RSI"] = getattr(ta_data, "rsi", 0.0)
                if "MACD" in feature_set: features["MACD"] = getattr(ta_data, "macd", 0.0)
                if "EMA" in feature_set: features["EMA"] = getattr(ta_data, "ema", 0.0)

        # Financial Statements
        fs_features = [f for f in ["priceEarningsRatio", "returnOnEquity", "marketCap"] if f in feature_set]
        if fs_features and tickers:
            ticker = tickers[0]
            if "priceEarningsRatio" in fs_features or "returnOnEquity" in fs_features:
                ratios_tool = FinancialStatementTool(self.ai_chat_service, "ratios")
                ratios_result = ratios_tool.get_data(ticker=ticker, period="annual", limit=1)
                if ratios_result.data:
                    ratios_data = ratios_result.data[0]
                    if "priceEarningsRatio" in fs_features: features["priceEarningsRatio"] = ratios_data.get("priceEarningsRatio")
                    if "returnOnEquity" in fs_features: features["returnOnEquity"] = ratios_data.get("returnOnEquity")
            
            if "marketCap" in fs_features:
                key_metrics_data = FinancialStatementTool(self.ai_chat_service, "key-metrics").get_data(ticker=ticker, limit=1)
                if key_metrics_data.data:
                    features["marketCap"] = key_metrics_data.data[0].get("marketCap", 0.0)

        # News Features
        news_features = [f for f in ["news_count", "positive_news_ratio"] if f in feature_set]
        if news_features:
            query = tickers[0] if tickers else "stock market"
            news_result = NewsTool(self.ai_chat_service).get_data(query=query, k=10)
            if news_result and news_result.data:
                total = len(news_result.data)
                positive = sum(1 for item in news_result.data if item.get("sentiment") == "positive")
                features["news_count"] = total
                features["positive_news_ratio"] = round(positive / total, 3) if total > 0 else 0.0

        # Market
        market_features = [f for f in ["VIX", "PRICE", "PRICE_HISTORY"] if f in feature_set]
        if market_features and tickers:
            market_inp = MarketDataInput(tickers=tickers, start_date=start_date, end_date=end_date)
            market = MarketDataTool(self.ai_chat_service).get_data(**market_inp.dict())
            if "VIX" in feature_set: features["VIX"] = market.vix or 0.0
            
            price_data = market.price_data.get(tickers[0], [])
            if "PRICE" in feature_set:
                features["PRICE"] = float(price_data[-1].get("Adj Close", 0)) if price_data else 0.0
            if "PRICE_HISTORY" in feature_set:
                features["PRICE_HISTORY"] = pd.DataFrame(price_data) if price_data else pd.DataFrame()

        # Normalization (로그 or 제트스코어 fallback 전략)
        if normalize:
            log1p_targets = {"GDP", "CPIAUCSL", "marketCap", "news_count"}

            for k, v in features.items():
                if not isinstance(v, (int, float)) or pd.isna(v):
                    features[k] = 0.0
                    continue

                # 로그 스케일링 대상: 로그 or 제트스코어 fallback
                if k in log1p_targets:
                    if v > 0:
                        features[k] = np.log1p(v)  # ✅ 양수면 로그 압축 효과
                    elif k in self.scaling_mean and self.scaling_std.get(k, 0) > 1e-8:
                        features[k] = (v - self.scaling_mean[k]) / self.scaling_std[k]  # ⚠️ 음수면 Z-score fallback
                    else:
                        features[k] = 0.0  # 비정상값 안전 처리

                # 일반 Z-score 정규화 대상
                elif k in self.scaling_mean and self.scaling_std.get(k, 0) > 1e-8:
                    features[k] = (v - self.scaling_mean[k]) / self.scaling_std[k]

                # 처리 불가능한 값은 원본 유지
                else:
                    features[k] = float(v)
        return features
