"""
Composite Formula 사용 예시
===========================

새로운 구조의 장점을 보여주는 예시 코드입니다.
"""

from typing import Dict, Callable
from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool, CompositeFormula

def example_kalman_filter_formulas():
    """
    칼만 필터 전용 composite 공식 예시
    """
    print("=== 칼만 필터 전용 Composite 공식 예시 ===")
    
    # 칼만 필터에 특화된 composite 공식들
    kalman_formulas = {
        # 거시경제 + 변동성 복합 지표 (trend 추정용)
        "kalman_macro_vol": lambda feats: (
            0.4 * feats.get("GDP", 0.0) + 
            0.3 * feats.get("CPIAUCSL", 0.0) + 
            0.3 * feats.get("VIX", 0.0)
        ),
        # 기술적 + 거시경제 복합 지표 (momentum 추정용)
        "kalman_tech_macro": lambda feats: (
            0.5 * feats.get("RSI", 0.0) + 
            0.3 * feats.get("MACD", 0.0) + 
            0.2 * feats.get("CPIAUCSL", 0.0)
        ),
        # 변동성 + 환율 복합 지표 (volatility 추정용)
        "kalman_vol_fx": lambda feats: (
            0.7 * feats.get("VIX", 0.0) + 
            0.3 * feats.get("DEXKOUS", 0.0)
        )
    }
    
    print("칼만 필터 공식들:")
    for name, func in kalman_formulas.items():
        print(f"  - {name}: {func.__doc__ or 'Custom formula'}")
    
    return kalman_formulas

def example_ml_ensemble_formulas():
    """
    ML 앙상블 전용 composite 공식 예시
    """
    print("\n=== ML 앙상블 전용 Composite 공식 예시 ===")
    
    # ML 앙상블에 특화된 composite 공식들
    ml_formulas = {
        # 기술적 + 거시경제 복합 지표 (XGBoost용)
        "ml_tech_macro": lambda feats: (
            0.4 * feats.get("RSI", 0.0) + 
            0.3 * feats.get("MACD", 0.0) + 
            0.3 * feats.get("GDP", 0.0)
        ),
        # 변동성 + 펀더멘털 복합 지표 (LSTM용)
        "ml_vol_fundamental": lambda feats: (
            0.5 * feats.get("VIX", 0.0) + 
            0.3 * feats.get("CPIAUCSL", 0.0) + 
            0.2 * feats.get("DEXKOUS", 0.0)
        ),
        # 모멘텀 + 밸류 복합 지표 (앙상블 가중치 조정용)
        "ml_momentum_value": lambda feats: (
            0.6 * feats.get("RSI", 0.0) + 
            0.4 * feats.get("MACD", 0.0)
        )
    }
    
    print("ML 앙상블 공식들:")
    for name, func in ml_formulas.items():
        print(f"  - {name}: {func.__doc__ or 'Custom formula'}")
    
    return ml_formulas

def example_mean_reversion_formulas():
    """
    Mean Reversion 전략 전용 composite 공식 예시
    """
    print("\n=== Mean Reversion 전략 전용 Composite 공식 예시 ===")
    
    # Mean Reversion에 특화된 composite 공식들
    mean_reversion_formulas = {
        # 과매수/과매도 지표
        "mean_rev_extreme": lambda feats: (
            (feats.get("RSI", 50.0) - 50.0) / 50.0 +  # RSI 중앙값 대비 편차
            (feats.get("MACD", 0.0) - 0.0) / 0.02     # MACD 중앙값 대비 편차
        ),
        # 변동성 기반 mean reversion 신호
        "mean_rev_volatility": lambda feats: (
            (feats.get("VIX", 20.0) - 20.0) / 20.0 +  # VIX 중앙값 대비 편차
            (feats.get("CPIAUCSL", 300.0) - 300.0) / 300.0  # CPI 중앙값 대비 편차
        ),
        # 거시경제 기반 mean reversion 신호
        "mean_rev_macro": lambda feats: (
            (feats.get("GDP", 20000.0) - 20000.0) / 20000.0 +  # GDP 중앙값 대비 편차
            (feats.get("DEXKOUS", 0.0007) - 0.0007) / 0.0007   # 환율 중앙값 대비 편차
        )
    }
    
    print("Mean Reversion 공식들:")
    for name, func in mean_reversion_formulas.items():
        print(f"  - {name}: {func.__doc__ or 'Custom formula'}")
    
    return mean_reversion_formulas

def example_composite_formula_class():
    """
    CompositeFormula 클래스 사용 예시
    """
    print("\n=== CompositeFormula 클래스 사용 예시 ===")
    
    # 문서화된 composite 공식들
    documented_formulas = {
        "trend_following": CompositeFormula(
            name="trend_signal",
            func=lambda feats: (
                0.4 * feats.get("RSI", 0.0) + 
                0.3 * feats.get("MACD", 0.0) + 
                0.3 * feats.get("VIX", 0.0)
            ),
            description="트렌드 추종 전략용 복합 신호 (RSI + MACD + VIX)",
            category="trend_following",
            version="1.0"
        ),
        "value_investing": CompositeFormula(
            name="value_signal",
            func=lambda feats: (
                0.5 * feats.get("GDP", 0.0) + 
                0.3 * feats.get("CPIAUCSL", 0.0) + 
                0.2 * feats.get("DEXKOUS", 0.0)
            ),
            description="밸류 투자 전략용 복합 신호 (GDP + CPI + 환율)",
            category="value_investing",
            version="1.0"
        )
    }
    
    print("문서화된 공식들:")
    for name, formula in documented_formulas.items():
        print(f"  - {formula.name}: {formula.description}")
        print(f"    카테고리: {formula.category}, 버전: {formula.version}")
    
    return documented_formulas

def demonstrate_usage():
    """
    실제 사용 예시를 시연합니다.
    """
    print("\n=== 실제 사용 예시 ===")
    
    # 가상의 피처 데이터
    mock_features = {
        "GDP": 25000.0,
        "CPIAUCSL": 320.0,
        "RSI": 65.0,
        "MACD": 0.015,
        "VIX": 25.0,
        "DEXKOUS": 0.0008
    }
    
    print("가상 피처 데이터:")
    for key, value in mock_features.items():
        print(f"  {key}: {value}")
    
    # 칼만 필터 공식 테스트
    kalman_formulas = example_kalman_filter_formulas()
    print("\n칼만 필터 공식 결과:")
    for name, func in kalman_formulas.items():
        result = func(mock_features)
        print(f"  {name}: {result:.4f}")
    
    # ML 앙상블 공식 테스트
    ml_formulas = example_ml_ensemble_formulas()
    print("\nML 앙상블 공식 결과:")
    for name, func in ml_formulas.items():
        result = func(mock_features)
        print(f"  {name}: {result:.4f}")
    
    # Mean Reversion 공식 테스트
    mean_rev_formulas = example_mean_reversion_formulas()
    print("\nMean Reversion 공식 결과:")
    for name, func in mean_rev_formulas.items():
        result = func(mock_features)
        print(f"  {name}: {result:.4f}")

if __name__ == "__main__":
    print("🔄 Composite Formula 구조 개선 예시")
    print("=" * 50)
    
    # 각 전략별 공식 예시
    example_kalman_filter_formulas()
    example_ml_ensemble_formulas()
    example_mean_reversion_formulas()
    example_composite_formula_class()
    
    # 실제 사용 예시
    demonstrate_usage()
    
    print("\n" + "=" * 50)
    print("✅ 구조 개선 완료!")
    print("\n📋 주요 개선사항:")
    print("1. ✅ FeaturePipelineTool이 dumb하게 유지됨")
    print("2. ✅ 각 고급 툴이 자기만의 composite 정의 가능")
    print("3. ✅ 테스트가 쉬워짐 (공식만 바꾸면 다른 시나리오 실험 가능)")
    print("4. ✅ CompositeFormula 클래스로 문서화 및 버전 관리 가능")
    print("5. ✅ 하위 호환성 유지 (기존 코드 그대로 동작)") 