"""
Transformer 기반 주식 예측 모델
시계열 데이터에 최적화된 Transformer 아키텍처
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
from typing import Optional, Tuple, Dict, List
import logging

class PositionalEncoding(nn.Module):
    """
    시계열 데이터용 위치 인코딩
    주식 데이터는 순서가 매우 중요하므로 강화된 위치 인코딩 사용
    """
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (seq_len, batch_size, d_model)
        """
        return x + self.pe[:x.size(0), :]

class MultiHeadFinancialAttention(nn.Module):
    """
    주식 데이터에 특화된 멀티헤드 어텐션
    - 시간적 중요도 가중치
    - 변동성 기반 어텐션 스케일링
    """
    def __init__(self, d_model: int, n_heads: int = 8, dropout: float = 0.1):
        super(MultiHeadFinancialAttention, self).__init__()
        
        assert d_model % n_heads == 0
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        
        # 🚀 주식 특화: 시간 거리별 가중치
        self.time_decay = nn.Parameter(torch.tensor(0.1))
        
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            query, key, value: (batch_size, seq_len, d_model)
            mask: (batch_size, seq_len, seq_len)
        """
        batch_size, seq_len, _ = query.size()
        
        # Multi-head 분할
        Q = self.w_q(query).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        K = self.w_k(key).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        V = self.w_v(value).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        
        # Scaled Dot-Product Attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        # 🚀 주식 특화: 시간 거리 기반 가중치 적용
        time_matrix = self._create_time_decay_matrix(seq_len, query.device)
        scores = scores + time_matrix.unsqueeze(0).unsqueeze(0)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Attention 적용
        context = torch.matmul(attention_weights, V)
        
        # Multi-head 결합
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )
        
        output = self.w_o(context)
        
        return output
    
    def _create_time_decay_matrix(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """시간 거리에 따른 감쇠 행렬 생성"""
        positions = torch.arange(seq_len, device=device).float()
        time_diff = positions.unsqueeze(1) - positions.unsqueeze(0)
        
        # 최근 데이터에 더 높은 가중치 (음수는 미래 데이터이므로 마스킹)
        decay_matrix = -self.time_decay * torch.abs(time_diff)
        
        return decay_matrix

class TransformerEncoderLayer(nn.Module):
    """
    주식 예측용 Transformer 인코더 레이어
    """
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
        super(TransformerEncoderLayer, self).__init__()
        
        self.self_attention = MultiHeadFinancialAttention(d_model, n_heads, dropout)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),  # GELU가 금융 데이터에서 더 좋은 성능
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Self-Attention with residual connection
        attn_output = self.self_attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # Feed Forward with residual connection  
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x

class StockTransformer(nn.Module):
    """
    주식 예측용 Transformer 모델
    - 시계열 특화 아키텍처
    - 다중 목표 예측 (Close, BB_Upper, BB_Lower)
    """
    def __init__(self, 
                 input_size: int = 42,          # 고급 피처 수
                 d_model: int = 512,            # 모델 차원
                 n_heads: int = 8,              # 어텐션 헤드 수
                 n_layers: int = 6,             # 인코더 레이어 수
                 d_ff: int = 2048,              # Feed Forward 차원
                 max_seq_len: int = 60,         # 최대 시퀀스 길이
                 prediction_length: int = 5,     # 예측 길이
                 num_targets: int = 3,          # 예측 타겟 수
                 dropout: float = 0.1):
        super(StockTransformer, self).__init__()
        
        self.input_size = input_size
        self.d_model = d_model
        self.prediction_length = prediction_length
        self.num_targets = num_targets
        
        # 입력 임베딩
        self.input_embedding = nn.Linear(input_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model, max_seq_len)
        
        # Transformer Encoder 스택
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])
        
        # 출력 헤드들
        self.output_projection = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, prediction_length * num_targets)
        )
        
        # 🚀 주식 특화: 타겟별 전문화 헤드
        self.close_head = nn.Linear(d_model, prediction_length)
        self.bb_upper_head = nn.Linear(d_model, prediction_length)  
        self.bb_lower_head = nn.Linear(d_model, prediction_length)
        
        self.dropout = nn.Dropout(dropout)
        
        # 파라미터 초기화
        self._initialize_weights()
        
    def _initialize_weights(self):
        """Xavier 초기화 적용"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, input_size)
            mask: (batch_size, seq_len, seq_len)
        Returns:
            (batch_size, prediction_length, num_targets)
        """
        batch_size, seq_len, _ = x.size()
        
        # 입력 임베딩 + 위치 인코딩
        x = self.input_embedding(x) * math.sqrt(self.d_model)
        x = x.transpose(0, 1)  # (seq_len, batch_size, d_model)
        x = self.positional_encoding(x)
        x = x.transpose(0, 1)  # (batch_size, seq_len, d_model)
        
        x = self.dropout(x)
        
        # Transformer Encoder 레이어들 통과
        for encoder_layer in self.encoder_layers:
            x = encoder_layer(x, mask)
        
        # 🚀 Global Average Pooling (시계열의 모든 정보 활용)
        pooled = x.mean(dim=1)  # (batch_size, d_model)
        
        # 🚀 타겟별 전문화 예측
        close_pred = self.close_head(pooled)        # (batch_size, prediction_length)
        bb_upper_pred = self.bb_upper_head(pooled)  # (batch_size, prediction_length)
        bb_lower_pred = self.bb_lower_head(pooled)  # (batch_size, prediction_length)
        
        # 결합하여 최종 출력
        output = torch.stack([close_pred, bb_upper_pred, bb_lower_pred], dim=-1)
        # (batch_size, prediction_length, num_targets)
        
        return output

class PyTorchStockTransformer:
    """
    Transformer 기반 주식 예측 시스템
    """
    def __init__(self,
                 sequence_length: int = 60,
                 prediction_length: int = 5,
                 num_features: int = 42,
                 num_targets: int = 3,
                 device: str = None):
        
        self.sequence_length = sequence_length
        self.prediction_length = prediction_length
        self.num_features = num_features
        self.num_targets = num_targets
        
        # GPU 설정
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"🚀 Transformer Using device: {self.device}")
        
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.history = {'train_loss': [], 'val_loss': []}
        
        self.logger = logging.getLogger(__name__)
    
    def build_model(self,
                   d_model: int = 512,
                   n_heads: int = 8,
                   n_layers: int = 6,
                   d_ff: int = 2048,
                   dropout: float = 0.1,
                   loss_type: str = "multi_target"):
        """Transformer 모델 구축"""
        
        self.model = StockTransformer(
            input_size=self.num_features,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            d_ff=d_ff,
            max_seq_len=self.sequence_length,
            prediction_length=self.prediction_length,
            num_targets=self.num_targets,
            dropout=dropout
        ).to(self.device)
        
        # 옵티마이저 (Transformer에는 AdamW가 더 적합)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(), 
            lr=0.0001,  # Transformer는 더 작은 학습률 사용
            weight_decay=1e-4,
            betas=(0.9, 0.999)
        )
        
        # 🚀 고급 손실함수 적용
        from advanced_metrics import get_advanced_loss_function
        if loss_type != "mse":
            self.criterion = get_advanced_loss_function(loss_type).to(self.device)
        else:
            self.criterion = nn.MSELoss()
            
        self.loss_type = loss_type
        
        # 모델 파라미터 수 출력
        total_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"🏗️ Transformer built with {total_params:,} trainable parameters")
        
        self.logger.info(f"🚀 Transformer model built with {loss_type} loss function")
        
        return self.model
    
    def create_padding_mask(self, seq_len: int) -> torch.Tensor:
        """패딩 마스크 생성 (현재는 사용하지 않음)"""
        mask = torch.ones(seq_len, seq_len, device=self.device)
        return mask
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray,
                   epochs: int = 100, batch_size: int = 64, patience: int = 15) -> Dict[str, List[float]]:
        """
        Transformer 모델 학습
        
        Args:
            X_train, y_train: 학습 데이터
            X_val, y_val: 검증 데이터
            epochs: 학습 에포크
            batch_size: 배치 크기 (Transformer는 더 작은 배치 사용)
            patience: 조기 종료 인내
        
        Returns:
            학습 히스토리
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        from torch.utils.data import DataLoader, TensorDataset
        
        # 데이터를 PyTorch 텐서로 변환
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train)
        X_val_tensor = torch.FloatTensor(X_val)
        y_val_tensor = torch.FloatTensor(y_val)
        
        # DataLoader 생성
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 학습률 스케줄러 (Transformer에 적합한 웜업 스케줄러)
        from torch.optim.lr_scheduler import OneCycleLR
        scheduler = OneCycleLR(
            self.optimizer,
            max_lr=0.001,
            epochs=epochs,
            steps_per_epoch=len(train_loader),
            pct_start=0.1  # 10% 웜업
        )
        
        # 학습 기록
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        patience_counter = 0
        
        self.logger.info(f"🚀 Starting Transformer training for {epochs} epochs...")
        
        for epoch in range(epochs):
            # 학습 모드
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                self.optimizer.zero_grad()
                
                # 순전파
                outputs = self.model(batch_X)
                
                # 손실 계산 (손실함수 타입에 따라 다르게 처리)
                if self.loss_type == "multi_target":
                    loss = self.criterion(outputs, batch_y)
                elif self.loss_type == "directional":
                    # 이전 가격 정보가 필요하므로 기본 MSE 사용
                    loss = torch.nn.MSELoss()(outputs, batch_y)
                else:
                    loss = self.criterion(outputs, batch_y)
                
                # 역전파
                loss.backward()
                
                # 그래디언트 클리핑 (Transformer 안정성)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                scheduler.step()  # 스텝마다 학습률 업데이트
                
                train_loss += loss.item()
            
            # 검증 모드
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                    
                    outputs = self.model(batch_X)
                    
                    if self.loss_type == "multi_target":
                        loss = self.criterion(outputs, batch_y)
                    else:
                        loss = torch.nn.MSELoss()(outputs, batch_y)
                    
                    val_loss += loss.item()
            
            # 평균 손실 계산
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            train_losses.append(avg_train_loss)
            val_losses.append(avg_val_loss)
            
            # 로깅
            if (epoch + 1) % 10 == 0:
                current_lr = scheduler.get_last_lr()[0]
                self.logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}, "
                               f"Val Loss: {avg_val_loss:.6f}, LR: {current_lr:.6f}")
            
            # 조기 종료 체크
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                # 최고 모델 저장 (메모리에)
                self.best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                self.logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # 최고 모델 복원
        if hasattr(self, 'best_model_state'):
            self.model.load_state_dict(self.best_model_state)
        
        # 히스토리 저장
        self.history = {
            'train_loss': train_losses,
            'val_loss': val_losses
        }
        
        self.logger.info(f"✅ Transformer training completed. Best val loss: {best_val_loss:.6f}")
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """예측 수행"""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            predictions = self.model(X_tensor)
            
        return predictions.cpu().numpy()
    
    def save_model(self, filepath: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("Model not built.")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_config': {
                'sequence_length': self.sequence_length,
                'prediction_length': self.prediction_length,
                'num_features': self.num_features,
                'num_targets': self.num_targets
            },
            'history': self.history
        }, filepath)
        
        self.logger.info(f"Transformer model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """모델 로드"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        # 설정 복원
        config = checkpoint['model_config']
        self.sequence_length = config['sequence_length']
        self.prediction_length = config['prediction_length']
        self.num_features = config['num_features']
        self.num_targets = config['num_targets']
        
        # 모델 빌드 (기본 설정으로)
        self.build_model()
        
        # 가중치 로드
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        # 히스토리 복원
        if 'history' in checkpoint:
            self.history = checkpoint['history']
        
        self.logger.info(f"Transformer model loaded from {filepath}")
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """모델 평가 (고급 평가지표 사용)"""
        predictions = self.predict(X_test)
        
        # 고급 평가지표 계산
        if hasattr(self, 'metrics_calculator'):
            # Close 가격에 대한 평가 (첫 번째 타겟)
            close_predictions = predictions[:, :, 0].flatten()
            close_targets = y_test[:, :, 0].flatten()
            
            # 이전 가격 추정 (첫 번째 값으로 근사)
            previous_prices = np.roll(close_targets, 1)
            previous_prices[0] = close_targets[0]
            
            # 종합 평가지표 계산
            metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                predictions=close_predictions,
                targets=close_targets,
                previous_prices=previous_prices
            )
            
            self.logger.info(f"✅ Transformer evaluation completed with {len(metrics)} metrics")
            return metrics
        else:
            # 기본 평가지표
            from sklearn.metrics import mean_squared_error, mean_absolute_error
            
            mse = mean_squared_error(y_test.reshape(-1), predictions.reshape(-1))
            mae = mean_absolute_error(y_test.reshape(-1), predictions.reshape(-1))
            
            return {
                'MSE': mse,
                'MAE': mae,
                'RMSE': np.sqrt(mse)
            }
    
    def get_model_info(self) -> Dict[str, any]:
        """모델 정보 반환"""
        if self.model is None:
            return {"status": "Model not built"}
            
        total_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            "model_type": "Stock Transformer",
            "architecture": "Multi-Head Self-Attention",
            "sequence_length": self.sequence_length,
            "prediction_length": self.prediction_length,
            "num_features": self.num_features,
            "num_targets": self.num_targets,
            "total_parameters": total_params,
            "device": str(self.device),
            "loss_function": getattr(self, 'loss_type', 'unknown')
        }

# 모델 성능 비교 유틸리티
class ModelComparison:
    """LSTM vs Transformer 성능 비교"""
    
    @staticmethod
    def compare_architectures():
        """아키텍처 비교 정보"""
        comparison = {
            "LSTM": {
                "장점": ["순차 처리", "메모리 효율적", "잘 검증된 구조"],
                "단점": ["순차 처리로 인한 속도 저하", "긴 시퀀스에서 정보 손실", "병렬 처리 어려움"],
                "파라미터": "~2M",
                "학습 시간": "중간"
            },
            "Transformer": {
                "장점": ["병렬 처리", "긴 시퀀스 학습", "어텐션으로 중요도 파악", "최신 기술"],
                "단점": ["메모리 사용량 많음", "과적합 위험", "하이퍼파라미터 튜닝 복잡"],
                "파라미터": "~5M",
                "학습 시간": "빠름 (병렬 처리)"
            }
        }
        return comparison

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # Transformer 모델 테스트
    transformer = PyTorchStockTransformer()
    model = transformer.build_model(
        d_model=512,
        n_heads=8,
        n_layers=6
    )
    
    # 모델 정보 출력
    info = transformer.get_model_info()
    print("\n=== Transformer Model Info ===")
    for key, value in info.items():
        print(f"{key}: {value}")
    
    # 아키텍처 비교
    comparison = ModelComparison.compare_architectures()
    print("\n=== LSTM vs Transformer Comparison ===")
    for model_type, details in comparison.items():
        print(f"\n{model_type}:")
        for aspect, values in details.items():
            print(f"  {aspect}: {values}")
    
    # 더미 데이터로 예측 테스트
    dummy_input = np.random.randn(4, 60, 42)  # (batch, seq_len, features)
    predictions = transformer.predict(dummy_input)
    print(f"\n🔮 Prediction shape: {predictions.shape}")
    print(f"🔮 Sample prediction: {predictions[0, :, 0]}")  # 첫 번째 배치, Close 예측