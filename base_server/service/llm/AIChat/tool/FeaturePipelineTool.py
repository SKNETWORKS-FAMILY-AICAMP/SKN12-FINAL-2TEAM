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
        
        # ✅ 인스턴스 속성으로 정의
        self.feature_means = {
            "RSI": 50.0, "MACD": 0.0, "EMA": 100.0, "VIX": 20.0,
            "priceEarningsRatio": 15.0, "returnOnEquity": 10.0,
            "positive_news_ratio": 0.5, "CPIAUCSL": 300.0,
            "kalman_trend": 0.0, "kalman_momentum": 0.0,
            "kalman_volatility": 0.0, "kalman_macro": 0.0, "kalman_tech": 0.0,
            "GDP": 10.0,  # log1p(GDP) 기준치 (대략치)
            "PRICE": 6.5  # log1p(가격) 기준치 (대략치)
        }
        
        self.feature_stds = {
            "RSI": 15.0, "MACD": 1.5, "EMA": 20.0, "VIX": 8.0,  # 🆕 MACD std 0.5 → 1.5로 상향
            "priceEarningsRatio": 10.0, "returnOnEquity": 5.0,
            "positive_news_ratio": 0.2, "CPIAUCSL": 20.0,
            "kalman_trend": 1.0, "kalman_momentum": 1.0,
            "kalman_volatility": 1.0, "kalman_macro": 1.0, "kalman_tech": 1.0,
            "GDP": 1.0, "PRICE": 1.0
        }

        # ✅ 정규화 정책 정리
        self.LOG_SCALE_FEATURES = {"DEXKOUS", "marketCap"}  # VIX 제거
        self.Z_SCORE_FEATURES = {"RSI", "MACD", "EMA", "VIX", "priceEarningsRatio",
                                 "returnOnEquity", "positive_news_ratio",
                                 "kalman_trend","kalman_momentum","kalman_volatility",
                                 "kalman_macro","kalman_tech"}
        # log → z-score 2단계 적용 대상
        self.LOG_THEN_Z_FEATURES = {"GDP", "CPIAUCSL", "PRICE", "marketCap"}
        
        # 로그 분포용 mean/std (GDP, CPI 전용)
        self.log_feature_means = {
            "GDP": 10.0,        # log(GDP) 평균 (약 22,000 → 10.0)
            "CPIAUCSL": 5.7,    # log(CPI) 평균 (약 300 → 5.7)
        }
        
        self.log_feature_stds = {
            "GDP": 0.3,         # log(GDP) 표준편차
            "CPIAUCSL": 0.1,    # log(CPI) 표준편차
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
        
        print(f"[FeaturePipelineTool] _extract_macro: {feature_name} 데이터 추출 시작")
        print(f"[FeaturePipelineTool] _extract_macro: macro_data 길이 = {len(macro_data)}")
        
        for item in macro_data:
            if item.get("series_id") == feature_name:
                current_date = item.get("date", item.get("observation_date", ""))
                if current_date > latest_date:
                    latest_date = current_date
                    try:
                        # 'latest_value' 우선, 없으면 'value' 사용
                        value_str = item.get("latest_value", item.get("value", "0.0"))
                        print(f"[FeaturePipelineTool] _extract_macro: {feature_name} raw value = {value_str}, date = {current_date}")
                        
                        if isinstance(value_str, str) and value_str != '.':
                            latest_value = float(value_str)
                        elif isinstance(value_str, (int, float)):
                            latest_value = value_str
                        else:
                            latest_value = 0.0
                            print(f"[FeaturePipelineTool] _extract_macro: {feature_name} 값 파싱 실패 (value_str = {value_str})")
                    except (ValueError, TypeError) as e:
                        latest_value = 0.0
                        print(f"[FeaturePipelineTool] _extract_macro: {feature_name} 값 변환 실패 - {e}")
        
        print(f"[FeaturePipelineTool] _extract_macro: {feature_name} 최종 값 = {latest_value}")
        return latest_value

    def _log1p_normalize(self, value: float) -> float:
        """로그 정규화 (큰 값에 적용)"""
        if value > 0:
            return np.log1p(value)
        return 0.0
    
    def _zscore_normalize(self, value: float, feature_name: str) -> float:
        """Z-score 정규화 + 클리핑"""
        if feature_name in self.LOG_THEN_Z_FEATURES:
            # 로그 분포용 mean/std 사용
            mean = self.log_feature_means.get(feature_name, 0.0)
            std = self.log_feature_stds.get(feature_name, 1.0)
        else:
            # 기존 mean/std 사용
            mean = self.feature_means.get(feature_name, 0.0)
            std = self.feature_stds.get(feature_name, 1.0)
        
        if std == 0:
            return 0.0
        
        z_score = (value - mean) / std
        
        # 🆕 클리핑으로 이상치 제한
        if feature_name == "MACD":
            z_score = np.clip(z_score, -3.0, 3.0)  # MACD는 ±3으로 제한
        else:
            z_score = np.clip(z_score, -5.0, 5.0)  # 일반적으로 ±5로 제한
        
        return z_score

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
                elif target in self.LOG_THEN_Z_FEATURES:
                    normalized[target] = self._log1p_normalize(raw_value)
                    normalized[target] = self._zscore_normalize(normalized[target], target)
                    if debug:
                        print(f"[Selective Normalize] Applied log1p then z-score for {target}, value={raw_value:.4f} -> {normalized[target]:.4f}")
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
                    value = self._extract_macro(macro.data, feat)
                    if value == 0.0:
                        print(f"[FeaturePipelineTool] ⚠️ {feat} 값이 0.0 (데이터 미수집 가능성)")
                    else:
                        print(f"[FeaturePipelineTool] ✅ {feat}: {value}")
                    features[feat] = value
            else:
                print(f"[FeaturePipelineTool] ⚠️ MacroEconomicTool에서 데이터를 받아오지 못함")
                for feat in macro_series_ids:
                    features[feat] = 0.0

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

        # 1️⃣ 먼저 개별 feature 정규화
        if normalize:
            if normalize_targets:
                # 기본 피처만 정규화 (composite 제외)
                base_targets = [t for t in normalize_targets if not t.startswith('kalman_')]
                features_normalized = self._selective_normalize(features, base_targets, debug)
                if debug:
                    print(f"[FeaturePipelineTool] Base features normalization completed: {len(features_normalized)} features")
            else:
                # 전체 정규화 (기존 로직 유지)
                features_normalized = {}
                for feat_name, raw_value in features.items():
                    if not isinstance(raw_value, (int, float)) or pd.isna(raw_value):
                        features_normalized[feat_name] = 0.0
                        if debug:
                            print(f"[FeaturePipelineTool] Invalid value for {feat_name}, setting to 0.0")
                        continue
                    if feat_name in self.LOG_SCALE_FEATURES:
                        features_normalized[feat_name] = self._log1p_normalize(raw_value)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied log1p for {feat_name}, value={raw_value:.4f} -> {features_normalized[feat_name]:.4f}")
                    elif feat_name in self.LOG_THEN_Z_FEATURES:
                        features_normalized[feat_name] = self._log1p_normalize(raw_value)
                        features_normalized[feat_name] = self._zscore_normalize(features_normalized[feat_name], feat_name)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied log1p then z-score for {feat_name}, value={raw_value:.4f} -> {features_normalized[feat_name]:.4f}")
                    elif feat_name in self.Z_SCORE_FEATURES:
                        features_normalized[feat_name] = self._zscore_normalize(raw_value, feat_name)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied z-score for {feat_name}, value={raw_value:.4f} -> {features_normalized[feat_name]:.4f}")
                    else:
                        features_normalized[feat_name] = self._zscore_normalize(raw_value, feat_name)
                        if debug:
                            print(f"[FeaturePipelineTool] Applied default z-score for {feat_name}, value={raw_value:.4f} -> {features_normalized[feat_name]:.4f}")
                if debug:
                    print(f"[FeaturePipelineTool] Full normalization completed: {len(features_normalized)} features")
        else:
            features_normalized = features.copy()
            if debug:
                print(f"[FeaturePipelineTool] Raw values returned: {len(features_normalized)} features")

        # 2️⃣ 정규화된 값으로 composite feature 생성
        if generate_composites:
            composite_features = self._generate_composite_features(features_normalized, composite_formula_map, debug)
            if debug:
                print(f"[FeaturePipelineTool] Generated {len(composite_features)} composite features: {list(composite_features.keys())}")
            
            # 3️⃣ composite feature만 추가 정규화 (z-score)
            if normalize:
                composite_targets = list(composite_features.keys())
                norm_composites = self._selective_normalize(composite_features, composite_targets, debug)
                if debug:
                    print(f"[FeaturePipelineTool] Composite normalization completed: {len(norm_composites)} features")
                
                # 4️⃣ 기본 피처 + 정규화된 composite 피처 병합
                result = {**features_normalized, **norm_composites}
            else:
                # 정규화하지 않는 경우 기본 피처 + raw composite 피처 병합
                result = {**features_normalized, **composite_features}
        else:
            # composite 생성하지 않는 경우 기본 피처만 반환
            result = features_normalized

        # Raw 값 저장 (return_raw=True인 경우)
        raw_features = features.copy() if return_raw else None

        # Raw + Normalized 동시 반환
        if return_raw:
            return {
                "raw": raw_features,
                "normalized": result
            }
        else:
            return result
