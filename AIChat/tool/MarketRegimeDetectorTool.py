from typing import Dict, Any, List, Optional
import numpy as np
from AIChat.BaseFinanceTool import BaseFinanceTool
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
    def get_data(self, macro_data: Dict[str, Any], technical_data: Dict[str, Any], prev_state: Optional[str] = None) -> Dict[str, Any]:
        """
        macro_data: {'gdp_growth': float, 'cpi': float}
        technical_data: {'rsi': float, 'vix': float, 'macd': float}
        prev_state: 이전 상태명 (선택)
        """
        regime, probabilities, transition_matrix = self.detector.detect_regime(macro_data, technical_data, prev_state)
        return {
            'regime': regime,
            'probabilities': probabilities,
            'transition_matrix': transition_matrix
        }

# --- 워크플로우 예시 (LangGraph 등 오케스트레이션 툴에서 노드/엣지 구조 정의) ---
workflow_nodes = [
    {
        'id': 'macro_node',
        'tool': 'MacroEconomicTool', # 거시경제 데이터를 불러오는 하급툴
        'input': {'macro_series_ids': ['GDP', 'CPI']}, # 필요한 시리즈 ID
        'output_key': 'macro_data'
    },
    {
        'id': 'tech_node',
        'tool': 'TechnicalAnalysisTool', # 기술적 분석 하급툴
        'input': {'tickers': ['AAPL', 'MSFT', 'GOOG']},
        'output_key': 'technical_data'
    },
    {
        'id': 'regime_detector_node',
        'tool': 'MarketRegimeDetectorTool', # 지금 정의한 고급툴
        'input': {
            'macro_data': {'from_node': 'macro_node', 'output_key': 'macro_data'},
            'technical_data': {'from_node': 'tech_node', 'output_key': 'technical_data'}
        },
        'output_key': 'market_regime_result'
    },
    {
        'id': 'print_node',
        'tool': 'PrintTool',  # 최종 출력 노드 (실제 구현 필요)
        'input': {
            'regime': {'from_node': 'regime_detector_node', 'output_key': 'market_regime_result.regime'},
            'probabilities': {'from_node': 'regime_detector_node', 'output_key': 'market_regime_result.probabilities'},
            'transition_matrix': {'from_node': 'regime_detector_node', 'output_key': 'market_regime_result.transition_matrix'}
        },
        'output_key': None
    }
]

# --- 노드 간 데이터 흐름 정의 ---
workflow_edges = [
    {'from': 'macro_node', 'to': 'regime_detector_node', 'output_key': 'macro_data', 'input_key': 'macro_data'},
    {'from': 'tech_node', 'to': 'regime_detector_node', 'output_key': 'technical_data', 'input_key': 'technical_data'},
    {'from': 'regime_detector_node', 'to': 'print_node', 'output_key': 'market_regime_result.regime', 'input_key': 'regime'},
    {'from': 'regime_detector_node', 'to': 'print_node', 'output_key': 'market_regime_result.probabilities', 'input_key': 'probabilities'},
    {'from': 'regime_detector_node', 'to': 'print_node', 'output_key': 'market_regime_result.transition_matrix', 'input_key': 'transition_matrix'},
]