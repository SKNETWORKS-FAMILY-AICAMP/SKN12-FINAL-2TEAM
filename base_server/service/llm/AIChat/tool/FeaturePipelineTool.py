from typing import Dict, Any, List, Optional
from datetime import datetime
from service.llm.AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput
import pandas as pd # pandas import 추가

class FeaturePipelineTool:
    def __init__(self, ai_chat_service) -> None:
        self.ai_chat_service = ai_chat_service

    def transform(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        feature_set: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        feature_set: GDP, CPIAUCSL, DEXKOUS, RSI, MACD, VIX 등
        """

        end_date = end_date or datetime.today().strftime("%Y-%m-%d")
        feature_set = feature_set or ["GDP", "CPIAUCSL", "DEXKOUS", "RSI", "MACD", "VIX", "PRICE"] # PRICE 추가
        features: Dict[str, Any] = {}

        # Macro
        macro_series_ids = [f for f in ["GDP", "CPIAUCSL", "DEXKOUS"] if f in feature_set]
        if macro_series_ids:
            macro = MacroEconomicTool(self.ai_chat_service).get_data(
                series_ids=macro_series_ids
            )
            for feat in macro_series_ids:
                features[feat] = self._extract_macro(macro.data, feat)

        # Technical
        tech_features = [f for f in ["RSI", "MACD"] if f in feature_set]
        if tech_features:
            ta = TechnicalAnalysisTool(self.ai_chat_service).get_data(tickers=tickers)
            ta_data = None
            if isinstance(ta.results, dict):
                if tickers and tickers[0] in ta.results:
                    ta_data = ta.results[tickers[0]]
                elif ta.results: # 첫번째 키의 값이라도 가져옴
                    ta_data = next(iter(ta.results.values()))
            elif isinstance(ta.results, list) and ta.results:
                ta_data = ta.results[0]
            
            if ta_data:
                if "RSI" in feature_set:
                    features["RSI"] = getattr(ta_data, "rsi", 0.0)
                if "MACD" in feature_set:
                    features["MACD"] = getattr(ta_data, "macd", 0.0)
                # EMA도 추가 (TechnicalAnalysisTool에 EMA가 있으므로)
                if "EMA" in feature_set:
                    features["EMA"] = getattr(ta_data, "ema", 0.0)


        # Market
        market_features = [f for f in ["VIX", "PRICE"] if f in feature_set]
        if market_features:
            market_inp = MarketDataInput(tickers=tickers, start_date=start_date, end_date=end_date)
            market = MarketDataTool(self.ai_chat_service).get_data(**market_inp.dict())
            if "VIX" in feature_set:
                features["VIX"] = market.vix or 0.0
            if "PRICE" in feature_set:
                df = market.price_data.get(tickers[0], [])
                # price_data는 list[dict] 형태이므로 마지막 dict에서 'Adj Close' 추출
                features["PRICE"] = float(df[-1].get("Adj Close", 0)) if df else 0.0

        return features

    @staticmethod
    def _extract_macro(data_list, series_id: str, default=0.0):
        for item in data_list:
            if isinstance(item, dict) and item.get('series_id') == series_id:
                return item.get('latest_value', default)
            if hasattr(item, 'series_id') and getattr(item, 'series_id') == series_id:
                return getattr(item, 'latest_value', default)
        return default
