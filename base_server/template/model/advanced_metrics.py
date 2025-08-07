"""
고급 손실함수 및 평가지표 모듈
주식 예측에 특화된 손실함수와 성능 지표들
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

class DirectionalLoss(nn.Module):
    """
    방향성 손실함수
    가격 방향(상승/하락) 예측 정확도에 가중치를 둔 손실함수
    """
    def __init__(self, mse_weight: float = 0.7, direction_weight: float = 0.3):
        super(DirectionalLoss, self).__init__()
        self.mse_weight = mse_weight
        self.direction_weight = direction_weight
        self.mse_loss = nn.MSELoss()
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor, 
                previous_prices: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: (batch_size, seq_len, num_targets) 예측값
            targets: (batch_size, seq_len, num_targets) 실제값
            previous_prices: (batch_size, seq_len, num_targets) 이전 가격 (방향성 계산용)
        """
        # 기본 MSE 손실
        mse_loss = self.mse_loss(predictions, targets)
        
        # 방향성 손실 계산
        pred_direction = (predictions - previous_prices).sign()  # 1(상승), -1(하락), 0(변화없음)
        true_direction = (targets - previous_prices).sign()
        
        # 방향성 일치 여부 (1: 일치, 0: 불일치)
        direction_accuracy = (pred_direction == true_direction).float()
        
        # 방향성 손실 (불일치에 대한 페널티)
        direction_loss = 1.0 - direction_accuracy.mean()
        
        # 가중 평균 손실
        total_loss = self.mse_weight * mse_loss + self.direction_weight * direction_loss
        
        return total_loss

class VolatilityAwareLoss(nn.Module):
    """
    변동성 인식 손실함수
    변동성이 클 때는 관대하게, 작을 때는 엄격하게 평가
    """
    def __init__(self, base_weight: float = 1.0, volatility_factor: float = 0.5):
        super(VolatilityAwareLoss, self).__init__()
        self.base_weight = base_weight
        self.volatility_factor = volatility_factor
        self.mse_loss = nn.MSELoss(reduction='none')
    
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor,
                volatility: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: 예측값
            targets: 실제값  
            volatility: 각 시점의 변동성 지표
        """
        # 기본 MSE 손실 (reduction='none'으로 개별 손실 계산)
        mse_losses = self.mse_loss(predictions, targets)
        
        # 변동성에 따른 가중치 계산 (변동성이 클수록 가중치 감소)
        volatility_weights = 1.0 / (1.0 + self.volatility_factor * volatility)
        
        # 가중 손실 적용
        weighted_losses = mse_losses * volatility_weights
        
        return weighted_losses.mean()

class MultiTargetLoss(nn.Module):
    """
    다중 목표 손실함수
    Close, BB_Upper, BB_Lower에 각각 다른 가중치 적용
    """
    def __init__(self, close_weight: float = 0.6, bb_upper_weight: float = 0.2, bb_lower_weight: float = 0.2):
        super(MultiTargetLoss, self).__init__()
        self.close_weight = close_weight
        self.bb_upper_weight = bb_upper_weight  
        self.bb_lower_weight = bb_lower_weight
        self.mse_loss = nn.MSELoss()
    
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: (batch_size, seq_len, 3) [Close, BB_Upper, BB_Lower]
            targets: (batch_size, seq_len, 3)
        """
        # 각 타겟별 손실 계산
        close_loss = self.mse_loss(predictions[..., 0], targets[..., 0])
        bb_upper_loss = self.mse_loss(predictions[..., 1], targets[..., 1])
        bb_lower_loss = self.mse_loss(predictions[..., 2], targets[..., 2])
        
        # 가중 평균
        total_loss = (self.close_weight * close_loss + 
                     self.bb_upper_weight * bb_upper_loss +
                     self.bb_lower_weight * bb_lower_loss)
        
        return total_loss

class SharpeRatioLoss(nn.Module):
    """
    샤프 비율 기반 손실함수
    투자 성과 최적화에 중점
    """
    def __init__(self, risk_free_rate: float = 0.02):
        super(SharpeRatioLoss, self).__init__()
        self.risk_free_rate = risk_free_rate / 252  # 일간 무위험 수익률
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor,
                current_prices: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: 예측 가격
            targets: 실제 가격
            current_prices: 현재 가격 (수익률 계산용)
        """
        # 예측 기반 수익률 계산
        pred_returns = (predictions - current_prices) / current_prices
        true_returns = (targets - current_prices) / current_prices
        
        # 예측 수익률의 샤프 비율 계산
        pred_sharpe = (pred_returns.mean() - self.risk_free_rate) / (pred_returns.std() + 1e-8)
        true_sharpe = (true_returns.mean() - self.risk_free_rate) / (true_returns.std() + 1e-8)
        
        # 샤프 비율 차이를 손실로 사용
        sharpe_loss = F.mse_loss(pred_sharpe, true_sharpe)
        
        return sharpe_loss

class AdvancedMetrics:
    """
    고급 평가지표 계산기
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_directional_accuracy(self, predictions: np.ndarray, targets: np.ndarray,
                                     previous_prices: np.ndarray) -> float:
        """방향 정확도 계산"""
        pred_direction = np.sign(predictions - previous_prices)
        true_direction = np.sign(targets - previous_prices)
        
        accuracy = (pred_direction == true_direction).mean()
        return float(accuracy)
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """샤프 비율 계산"""
        if len(returns) == 0:
            return 0.0
            
        daily_rf_rate = risk_free_rate / 252
        excess_returns = returns - daily_rf_rate
        
        if np.std(returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)
        return float(sharpe)
    
    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """최대 손실률 계산"""
        if len(prices) == 0:
            return 0.0
            
        cumulative = np.cumprod(1 + prices)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        max_dd = np.min(drawdown)
        return float(abs(max_dd))
    
    def calculate_win_rate(self, returns: np.ndarray) -> float:
        """승률 계산 (양의 수익률 비율)"""
        if len(returns) == 0:
            return 0.0
            
        positive_returns = returns > 0
        win_rate = positive_returns.mean()
        return float(win_rate)
    
    def calculate_volatility(self, returns: np.ndarray, annualize: bool = True) -> float:
        """변동성 계산"""
        if len(returns) == 0:
            return 0.0
            
        vol = np.std(returns)
        if annualize:
            vol *= np.sqrt(252)
            
        return float(vol)
    
    def calculate_information_ratio(self, predictions: np.ndarray, targets: np.ndarray,
                                  benchmark_returns: np.ndarray) -> float:
        """정보 비율 계산"""
        pred_returns = np.diff(predictions) / predictions[:-1]
        true_returns = np.diff(targets) / targets[:-1]
        
        # 예측 기반 초과 수익률
        pred_excess = pred_returns - benchmark_returns
        true_excess = true_returns - benchmark_returns
        
        # 추적 오차
        tracking_error = np.std(pred_excess - true_excess)
        
        if tracking_error == 0:
            return 0.0
            
        # 정보 비율
        info_ratio = np.mean(pred_excess - true_excess) / tracking_error
        return float(info_ratio)
    
    def calculate_comprehensive_metrics(self, predictions: np.ndarray, targets: np.ndarray,
                                      previous_prices: np.ndarray,
                                      benchmark_returns: Optional[np.ndarray] = None) -> Dict[str, float]:
        """종합 성능 지표 계산"""
        
        # 기본적인 오차 지표
        mse = np.mean((predictions - targets) ** 2)
        mae = np.mean(np.abs(predictions - targets))
        rmse = np.sqrt(mse)
        
        # 수익률 계산
        pred_returns = (predictions - previous_prices) / previous_prices
        true_returns = (targets - previous_prices) / targets
        
        # 고급 지표들
        metrics = {
            # 기본 지표
            'MSE': float(mse),
            'MAE': float(mae), 
            'RMSE': float(rmse),
            
            # 방향성 지표
            'Directional_Accuracy': self.calculate_directional_accuracy(predictions, targets, previous_prices),
            
            # 수익률 지표
            'Sharpe_Ratio': self.calculate_sharpe_ratio(pred_returns),
            'Max_Drawdown': self.calculate_max_drawdown(pred_returns),
            'Win_Rate': self.calculate_win_rate(pred_returns),
            'Volatility': self.calculate_volatility(pred_returns),
            
            # 상대적 지표 (실제 수익률과 비교)
            'True_Sharpe_Ratio': self.calculate_sharpe_ratio(true_returns),
            'Return_Correlation': float(np.corrcoef(pred_returns, true_returns)[0, 1]) if len(pred_returns) > 1 else 0.0,
        }
        
        # 벤치마크 대비 지표 (제공된 경우)
        if benchmark_returns is not None and len(benchmark_returns) == len(pred_returns):
            metrics['Information_Ratio'] = self.calculate_information_ratio(
                predictions, targets, benchmark_returns
            )
        
        return metrics

def get_advanced_loss_function(loss_type: str = "directional", **kwargs) -> nn.Module:
    """
    고급 손실함수 팩토리 함수
    
    Args:
        loss_type: "directional", "volatility_aware", "multi_target", "sharpe_ratio"
        **kwargs: 각 손실함수별 파라미터
    
    Returns:
        선택된 손실함수 인스턴스
    """
    if loss_type == "directional":
        return DirectionalLoss(**kwargs)
    elif loss_type == "volatility_aware":
        return VolatilityAwareLoss(**kwargs)
    elif loss_type == "multi_target":
        return MultiTargetLoss(**kwargs)
    elif loss_type == "sharpe_ratio":
        return SharpeRatioLoss(**kwargs)
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 더미 데이터로 테스트
    batch_size, seq_len, num_targets = 32, 5, 3
    
    predictions = torch.randn(batch_size, seq_len, num_targets)
    targets = torch.randn(batch_size, seq_len, num_targets)
    previous_prices = torch.randn(batch_size, seq_len, num_targets)
    
    # 방향성 손실함수 테스트
    dir_loss = DirectionalLoss()
    loss_value = dir_loss(predictions, targets, previous_prices)
    print(f"Directional Loss: {loss_value:.4f}")
    
    # 평가지표 계산 테스트
    metrics_calc = AdvancedMetrics()
    
    # numpy 변환
    pred_np = predictions.detach().numpy()[:, :, 0]  # Close 가격만
    target_np = targets.detach().numpy()[:, :, 0]
    prev_np = previous_prices.detach().numpy()[:, :, 0]
    
    # 종합 지표 계산
    comprehensive_metrics = metrics_calc.calculate_comprehensive_metrics(
        pred_np.flatten(), target_np.flatten(), prev_np.flatten()
    )
    
    print("\n=== Comprehensive Metrics ===")
    for metric_name, value in comprehensive_metrics.items():
        print(f"{metric_name}: {value:.4f}")