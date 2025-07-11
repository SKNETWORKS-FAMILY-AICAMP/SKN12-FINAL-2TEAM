'''
1. 거시경제 + 기술적 지표 데이터를 받아서
2. Bayesian + Hidden Markov Model 스타일로 각 국면의 likelihood(매수, 매도, 회보중 제일 유사) 계산 후
3. 마르코프 전이 확률(prior) 곱하여 posterior 계산
4. 가장 확률 높은 국면(Bull/Bear/Sideways)을 최종 시장 상태로 예측
'''

from typing import Dict, Any, List, Optional
import numpy as np
from AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field
from AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool, TechnicalAnalysisInput
from AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput

class MarketRegimeDetectorInput(BaseModel):
    """
    Market Regime Detector Tool 입력 스키마.
    이 클래스는 고급툴 내부에서 MacroEconomicTool, TechnicalAnalysisTool 호출 시 필요한 모든 파라미터를 포함한다.
    """
    series_ids: List[str] = Field(
        ...,
        description=(
            "FRED macroeconomic series IDs 리스트.\n"
            "예시: ['CPIAUCSL', 'FEDFUNDS', 'UNRATE']"
        )
    )
    tickers: List[str] = Field(
        ...,
        description=(
            "기술적 분석용 ticker 리스트.\n"
            "예시: ['AAPL', 'MSFT', 'GOOG']"
        )
    )
    start_date: str = Field(
        ...,
        description="조회 시작일 (yyyy-mm-dd). 예: '2024-01-01'"
    )
    end_date: str = Field(
        ...,
        description="조회 종료일 (yyyy-mm-dd). 예: '2024-12-31'"
    )
    prev_state: Optional[str] = Field(
        None,
        description="이전 시장 상태 (예: 'Bull', 'Bear', 'Sideways')"
    )

class MarketRegimeDetectorOutput(BaseModel):
    summary: str
    data: Dict[str, Any]

# 현재 시장이 Bear, Sideways, Bull 중 어디 상태인지 판별하는 클래스
class MarketRegimeDetector:
    def __init__(self):
        # 시장 상태 레이블 정의
        self.states = ['Bear', 'Sideways', 'Bull']
        
        # 상태명을 인덱스로 매핑 (예: 'Bear':0, 'Sideways':1, 'Bull':2)
        self.state_idx = {s: i for i, s in enumerate(self.states)}
        
        # 상태 전이 확률 행렬 (마르코프 체인)
        # 예: Bear 상태에 있으면 85% 확률로 Bear 유지, 10% Sideways, 5% Bull로 전이
        self.transition_matrix = np.array([
            [0.85, 0.10, 0.05],
            [0.25, 0.50, 0.25],
            [0.05, 0.10, 0.85]
        ])
        
        # 각 상태별 관측값의 평균 벡터와 공분산 행렬
        # 관측값 벡터: [GDP 성장률, CPI, RSI, VIX, MACD]
        self.observation_params = {
            'Bear': {
                'mean': np.array([-0.5, 4.0, 35, 30, -0.5]),
                'cov': np.diag([0.25, 1.0, 100, 25, 0.1])
            },
            'Sideways': {
                'mean': np.array([1.5, 2.5, 50, 20, 0.0]),
                'cov': np.diag([0.5, 0.5, 64, 16, 0.05])
            },
            'Bull': {
                'mean': np.array([3.0, 2.0, 65, 15, 0.5]),
                'cov': np.diag([0.75, 0.25, 81, 9, 0.1])
            }
        }

    # 관측값(observation)이 주어진 상태(state)에서 나올 확률밀도 계산
    def calculate_likelihood(self, observation, state):
        from scipy.stats import multivariate_normal # 다변량 정규분포 함수 import
        params = self.observation_params[state] # 선택된 상태의 평균과 공분산 가져오기
        # 다변량 정규분포 PDF 계산: 관측값이 해당 상태 분포에서 나올 likelihood 반환
        return multivariate_normal.pdf(observation, mean=params['mean'], cov=params['cov'])

    # 베이지안 방식으로 상태 분류
    def bayesian_regime_classification(self, macro_data, technical_data, prev_state=None):
        # macro_data + technical_data를 하나의 관측값 벡터로 결합
        obs = np.array([
            macro_data['gdp_growth'],
            macro_data['cpi'],
            technical_data['rsi'],
            technical_data['vix'],
            technical_data['macd']
        ])
        
        # 이전 상태가 없으면 모든 상태 prior = 1/3로 균등 분포 가정
        if prev_state is None:
            priors = np.array([1/3, 1/3, 1/3])
        else:
            # 이전 상태가 있으면, Transition Matrix의 해당 행을 prior로 사용
            priors = self.transition_matrix[self.state_idx[prev_state]]
        
        # 각 상태별 likelihood 계산
        likelihoods = np.array([self.calculate_likelihood(obs, s) for s in self.states])
        
        # 베이즈 정리를 이용해 posterior 계산 (likelihood * prior)
        numerators = likelihoods * priors
        posteriors = numerators / numerators.sum() # 정규화
        
        # 상태명: posterior 확률 딕셔너리로 반환
        return {s: posteriors[i] for i, s in enumerate(self.states)}

    # 최종적으로 시장 국면(regime) 탐지
    def detect_regime(self, macro_data, technical_data, prev_state=None):
        # posterior 계산
        posteriors = self.bayesian_regime_classification(macro_data, technical_data, prev_state)
        # posterior가 가장 높은 상태를 regime으로 선택
        regime = max(posteriors, key=posteriors.get)
        # regime, 각 상태 posterior 확률, 전이행렬 반환
        return regime, posteriors, self.transition_matrix.copy()

# --- MarketRegimeDetectorTool: 워크플로우에서 호출하기 위한 래퍼 클래스 ---
class MarketRegimeDetectorTool(BaseFinanceTool):
    def __init__(self):
        super().__init__()
        self.detector = MarketRegimeDetector() # 핵심 로직 클래스 인스턴스화

    # macro_data + technical_data 입력 받아 regime 결과 반환
    def get_data(
        self,
        input_data: MarketRegimeDetectorInput,
        max_latency: float = 1.0,
    ) -> MarketRegimeDetectorOutput:
        """
        단일 시점 Regime 예측. (하급툴 직접 호출)
        """
        # 1. MacroEconomicTool 호출
        macro_tool = MacroEconomicTool()
        macro_output = macro_tool.get_data(input_data.series_ids)
        # macro_output.data: List[dict] → {'series_id': ..., 'latest_value': ...}
        macro_data = {s['series_id']: s['latest_value'] for s in macro_output.data if s.get('latest_value') is not None}
        # 2. TechnicalAnalysisTool 호출
        ta_tool = TechnicalAnalysisTool()
        ta_input = TechnicalAnalysisInput(tickers=input_data.tickers)
        ta_output = ta_tool.get_data(ta_input, as_dict=True)
        # 예시: 첫 번째 ticker만 사용 (확장 가능)
        ticker = input_data.tickers[0]
        ta_result = ta_output.results[ticker]
        technical_data = {
            'rsi': ta_result.rsi,
            'macd': ta_result.macd,
            'ema': ta_result.ema
        }
        # 3. MarketDataTool에서 VIX 추출
        market_data_tool = MarketDataTool()
        market_input = MarketDataInput(
            tickers=input_data.tickers,
            start_date=input_data.start_date,
            end_date=input_data.end_date
        )
        market_data = market_data_tool.get_data(market_input)
        technical_data['vix'] = market_data['vix']
        # 4. prev_state
        prev_state = input_data.prev_state
        # 5. regime 예측
        regime, probabilities, transition_matrix = self.detector.detect_regime(macro_data, technical_data, prev_state)
        # summary 생성 예시
        summary = f"예측 Regime: {regime}, 확률: {probabilities}, 전이행렬: {transition_matrix.tolist()}"
        data = {
            'regime': regime,
            'probabilities': probabilities,
            'transition_matrix': transition_matrix.tolist()
        }
        return MarketRegimeDetectorOutput(summary=summary, data=data)

# --- 워크플로우 예시 (MarketRegimeDetectorTool 단일 호출 구조) ---

workflow_nodes = [
    {
        'id': 'market_regime_detector_node',
        'tool': 'MarketRegimeDetectorTool',
        'input': {
            'series_ids': ['CPIAUCSL', 'GDP'],        # FRED macroeconomic series IDs
            'tickers': ['AAPL', 'MSFT', 'GOOG'],     # 기술적 분석용 tickers
            'start_date': '2024-01-01',              # 조회 시작일
            'end_date': '2024-12-31',                # 조회 종료일
            'prev_state': 'Bull'                     # 이전 시장 상태 (선택)
        },
        'output_key': 'market_regime_result'
    },
    {
        'id': 'print_node',
        'tool': 'PrintTool',
        'input': {
            'summary': {
                'from_node': 'market_regime_detector_node',
                'output_key': 'market_regime_result.summary'
            },
            'data': {
                'from_node': 'market_regime_detector_node',
                'output_key': 'market_regime_result.data'
            }
        },
        'output_key': None
    }
]

# --- 노드 간 데이터 흐름 정의 ---
workflow_edges = [
    {
        'from': 'market_regime_detector_node',
        'to': 'print_node',
        'output_key': 'market_regime_result.summary',
        'input_key': 'summary'
    },
    {
        'from': 'market_regime_detector_node',
        'to': 'print_node',
        'output_key': 'market_regime_result.data',
        'input_key': 'data'
    }
]