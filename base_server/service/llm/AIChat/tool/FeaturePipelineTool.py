from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
try:
    from pydantic import BaseModel
except ImportError:
    # pydantic이 없을 경우 간단한 클래스로 대체
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

from service.llm.AIChat.BasicTools.FinancialStatementTool import FinancialStatementTool
from service.llm.AIChat.BasicTools.NewsTool import NewsTool
from service.llm.AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput
import pandas as pd
import numpy as np

class CompositeFormula(BaseModel):
    """
    Composite 공식 정의 및 문서화를 위한 클래스
    
    Attributes:
        name: 공식 이름
        func: 공식 함수 (Dict[str, float] -> float)
        description: 공식 설명
        category: 공식 카테고리 (예: "macro", "technical", "sentiment")
        version: 공식 버전
    """
    def __init__(self, name: str, func: Callable[[Dict[str, float]], float], 
                 description: Optional[str] = None, category: Optional[str] = None, 
                 version: Optional[str] = "1.0"):
        self.name = name
        self.func = func
        self.description = description
        self.category = category
        self.version = version
    
    def __call__(self, features: Dict[str, float]) -> float:
        """공식 함수 실행"""
        return self.func(features)
    
    def get_formula_map(self) -> Dict[str, Callable[[Dict[str, float]], float]]:
        """FeaturePipelineTool에서 사용할 수 있는 형태로 변환"""
        return {self.name: self.func}

class FeaturePipelineTool:
    def __init__(self, ai_chat_service) -> None:
        self.ai_chat_service = ai_chat_service

    # 정규화 대상 피처 상수 정의
    LOG_SCALE_FEATURES = {
        "GDP", "CPIAUCSL", "marketCap", "news_count", 
        "PRICE", "DEXKOUS", "composite_1", "composite_3"
    }
    
    Z_SCORE_FEATURES = {
        "RSI", "MACD", "EMA", "VIX", "priceEarningsRatio", 
        "returnOnEquity", "positive_news_ratio", "composite_2"
    }

    # 🆕 기본 Composite 공식들 (참고용)
    @staticmethod
    def get_default_composite_formulas() -> Dict[str, CompositeFormula]:
        """기본 composite 공식들을 반환"""
        return {
            "macro_economic_index": CompositeFormula(
                name="composite_1",
                func=lambda feats: 0.5 * (feats.get("GDP", 0.0) + feats.get("CPIAUCSL", 0.0)),
                description="거시경제 복합 지표 (GDP + CPI)",
                category="macro"
            ),
            "inflation_volatility_index": CompositeFormula(
                name="composite_2", 
                func=lambda feats: 0.7 * feats.get("CPIAUCSL", 0.0) + 0.3 * feats.get("VIX", 0.0),
                description="인플레이션 + 변동성 지표 (CPI + VIX)",
                category="macro"
            ),
            "technical_volatility_index": CompositeFormula(
                name="composite_3",
                func=lambda feats: 0.6 * feats.get("RSI", 0.0) + 0.4 * feats.get("VIX", 0.0),
                description="기술적 + 변동성 지표 (RSI + VIX)",
                category="technical"
            )
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

    def _log1p_normalize(self, value: float) -> float:
        """로그 정규화 (큰 값에 적용)"""
        if value > 0:
            return np.log1p(value)
        return 0.0
    
    def _zscore_normalize(self, value: float, feature_name: str) -> float:
        """Z-score 정규화 (일반적인 범위의 값에 적용)"""
        # 피처별 고정된 기준값 사용
        feature_means = {
            "RSI": 50.0,              # RSI 평균
            "MACD": 0.0,              # MACD 평균
            "EMA": 100.0,             # EMA 평균
            "VIX": 20.0,              # VIX 평균
            "priceEarningsRatio": 15.0,  # PER 평균
            "returnOnEquity": 10.0,   # ROE 평균
            "positive_news_ratio": 0.5,  # 긍정 뉴스 비율 평균
            "CPIAUCSL": 300.0,        # CPI 평균
        }
        
        feature_stds = {
            "RSI": 15.0,              # RSI 표준편차
            "MACD": 0.02,             # MACD 표준편차
            "EMA": 20.0,              # EMA 표준편차
            "VIX": 8.0,               # VIX 표준편차
            "priceEarningsRatio": 10.0,  # PER 표준편차
            "returnOnEquity": 5.0,    # ROE 표준편차
            "positive_news_ratio": 0.2,  # 긍정 뉴스 비율 표준편차
            "CPIAUCSL": 20.0,         # CPI 표준편차
        }
        
        mean_val = feature_means.get(feature_name, 0.0)
        std_val = feature_stds.get(feature_name, 1.0)
        
        if std_val > 1e-8:
            return (value - mean_val) / std_val
        return 0.0

    def _generate_composite_features(
        self, 
        features: Dict[str, Any], 
        composite_formula_map: Optional[Dict[str, Callable[[Dict[str, float]], float]]] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        복합 피처 생성 - 외부에서 정의된 공식 또는 기본 공식 사용
        
        Args:
            features: 기본 피처 딕셔너리
            composite_formula_map: 외부에서 정의된 composite 공식 맵
            debug: 디버깅 로그 출력 여부
            
        Returns:
            복합 피처 딕셔너리
        """
        composites = {}
        
        # 🆕 외부에서 정의된 공식 사용
        if composite_formula_map:
            for comp_name, func in composite_formula_map.items():
                try:
                    composites[comp_name] = func(features)
                    if debug:
                        print(f"[Composite] {comp_name}: {composites[comp_name]:.4f}")
                except Exception as e:
                    if debug:
                        print(f"[Composite Error] {comp_name}: {e}")
                    composites[comp_name] = 0.0
        
        return composites

    def _selective_normalize(self, features: Dict[str, Any], targets: List[str], debug: bool = False) -> Dict[str, Any]:
        """
        선택적 정규화 - 지정된 피처만 정규화
        
        Args:
            features: 정규화할 피처 딕셔너리
            targets: 정규화할 피처 리스트
            debug: 디버깅 로그 출력 여부
            
        Returns:
            정규화된 피처 딕셔너리
        """
        normalized = features.copy()
        
        for target in targets:
            if target in features:
                raw_value = features[target]
                
                if not isinstance(raw_value, (int, float)) or pd.isna(raw_value):
                    normalized[target] = 0.0
                    if debug:
                        print(f"[Selective Normalize] Invalid value for {target}, setting to 0.0")
                    continue
                
                # 피처별 정규화 방식 선택
                if target in self.LOG_SCALE_FEATURES:
                    normalized[target] = self._log1p_normalize(raw_value)
                    if debug:
                        print(f"[Selective Normalize] Applied log1p for {target}, value={raw_value:.4f} -> {normalized[target]:.4f}")
                elif target in self.Z_SCORE_FEATURES:
                    normalized[target] = self._zscore_normalize(raw_value, target)
                    if debug:
                        print(f"[Selective Normalize] Applied z-score for {target}, value={raw_value:.4f} -> {normalized[target]:.4f}")
                else:
                    # 기본적으로 Z-score 적용
                    normalized[target] = self._zscore_normalize(raw_value, target)
                    if debug:
                        print(f"[Selective Normalize] Applied default z-score for {target}, value={raw_value:.4f} -> {normalized[target]:.4f}")
        
        return normalized

    def transform(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        feature_set: Optional[List[str]] = None,
        normalize: bool = True,
        normalize_targets: Optional[List[str]] = None,
        generate_composites: bool = False,
        composite_formula_map: Optional[Dict[str, Callable[[Dict[str, float]], float]]] = None,
        return_raw: bool = False,
        debug: bool = False
    ) -> Dict[str, Any]:
        if debug:
            print(f"[FeaturePipelineTool] transform called with:")
            print(f"  - tickers: {tickers}")
            print(f"  - feature_set: {feature_set}")
            print(f"  - debug: {debug}")
        """
        완전한 피처 파이프라인 - 복합 피처 생성 + 선택적 정규화 + Raw/Normalized 동시 반환 지원
        
        Parameters
        ----------
        tickers : List[str]
            분석할 종목 리스트
        start_date : str
            데이터 시작일
        end_date : Optional[str]
            데이터 종료일
        feature_set : Optional[List[str]]
            추출할 피처 리스트
        normalize : bool, default True
            정규화 적용 여부
        normalize_targets : Optional[List[str]]
            정규화할 피처 리스트 (None이면 모든 피처 정규화)
        generate_composites : bool, default False
            복합 피처 생성 여부
        composite_formula_map : Optional[Dict[str, Callable]]
            외부에서 정의된 composite 공식 맵
            예: {"composite_1": lambda feats: 0.5 * (feats.get("GDP", 0.0) + feats.get("CPIAUCSL", 0.0))}
        return_raw : bool, default False
            Raw 값과 Normalized 값을 동시에 반환할지 여부
        debug : bool, default False
            디버깅용 로그 출력 여부
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
        if debug:
            print(f"[FeaturePipelineTool] Technical features requested: {tech_features}")
            print(f"[FeaturePipelineTool] Tickers: {tickers}")
        if tech_features and tickers:
            if debug:
                print(f"[FeaturePipelineTool] Calling TechnicalAnalysisTool...")
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

        # 🆕 복합 피처 생성 (외부 공식 또는 기본 공식)
        if generate_composites:
            composite_features = self._generate_composite_features(features, composite_formula_map, debug)
            features.update(composite_features)
            if debug:
                print(f"[FeaturePipelineTool] Generated {len(composite_features)} composite features: {list(composite_features.keys())}")
            
            # 🆕 Composite 피처 자동 정규화 대상 추가
            if normalize and normalize_targets is not None:
                composite_keys = list(composite_features.keys())
                for key in composite_keys:
                    if key not in normalize_targets:
                        normalize_targets.append(key)
                if debug:
                    print(f"[FeaturePipelineTool] Auto-added composite features to normalize_targets: {composite_keys}")

        # 🆕 Raw 값 저장 (return_raw=True인 경우)
        raw_features = features.copy() if return_raw else None

        # 🆕 완전한 정규화 파이프라인
        if normalize:
            if normalize_targets:
                # 선택적 정규화
                result = self._selective_normalize(features, normalize_targets, debug)
                if debug:
                    print(f"[FeaturePipelineTool] Selective normalization completed: {len(result)} features")
            else:
                # 전체 정규화 (기존 로직 유지)
                result = {}
                for feat_name, raw_value in features.items():
                    if not isinstance(raw_value, (int, float)) or pd.isna(raw_value):
                        result[feat_name] = 0.0
                        if debug:
                            print(f"[FeaturePipelineTool] Invalid value for {feat_name}, setting to 0.0")
                        continue
                        
                    # 피처별 정규화 방식 선택
                    if feat_name in self.LOG_SCALE_FEATURES:
                        result[feat_name] = self._log1p_normalize(raw_value)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied log1p for {feat_name}, value={raw_value:.4f} -> {result[feat_name]:.4f}")
                    elif feat_name in self.Z_SCORE_FEATURES:
                        result[feat_name] = self._zscore_normalize(raw_value, feat_name)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied z-score for {feat_name}, value={raw_value:.4f} -> {result[feat_name]:.4f}")
                    else:
                        # 기본적으로 Z-score 적용
                        result[feat_name] = self._zscore_normalize(raw_value, feat_name)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied default z-score for {feat_name}, value={raw_value:.4f} -> {result[feat_name]:.4f}")
                
                if debug:
                    print(f"[FeaturePipelineTool] Full normalization completed: {len(result)} features")
        else:
            # 정규화하지 않고 raw 값 그대로 반환
            result = features
            if debug:
                print(f"[FeaturePipelineTool] Raw values returned: {len(result)} features")
        
        # 🆕 Raw + Normalized 동시 반환
        if return_raw:
            return {
                "raw": raw_features,
                "normalized": result
            }
        else:
            return result
