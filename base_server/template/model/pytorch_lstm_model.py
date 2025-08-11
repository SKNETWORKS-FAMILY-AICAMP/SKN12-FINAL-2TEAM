"""
PyTorch LSTM 모델 구현
TensorFlow 대신 PyTorch 사용으로 GPU 문제 해결
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
import logging
import pickle
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

# 🚀 고급 손실함수 및 평가지표 import
# Support both package and script execution contexts for advanced_metrics
try:
    from .advanced_metrics import (
        DirectionalLoss, VolatilityAwareLoss, MultiTargetLoss,
        AdvancedMetrics, get_advanced_loss_function
    )
except ImportError:  # executed when run as a script from this folder
    from advanced_metrics import (
        DirectionalLoss, VolatilityAwareLoss, MultiTargetLoss,
        AdvancedMetrics, get_advanced_loss_function
    )

class StockLSTM(nn.Module):
    def __init__(self, 
                 input_size: int = 42,       # 🚀 고급 피처 확장 (18 → 42)
                 hidden_size: int = 512,     # 🔥 4배 증가 (RTX 4090 활용)
                 num_layers: int = 4,        # 🔥 2배 증가 
                 output_size: int = 15,      # 5일 * 3타겟
                 dropout: float = 0.2):
        super(StockLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        # 🔥 RTX 4090 최적화 LSTM 스택 (4층)
        self.lstm1 = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bidirectional=False
        )
        self.dropout1 = nn.Dropout(dropout)
        self.layernorm1 = nn.LayerNorm(hidden_size)
        
        self.lstm2 = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bidirectional=False
        )
        self.dropout2 = nn.Dropout(dropout)
        self.layernorm2 = nn.LayerNorm(hidden_size)
        
        self.lstm3 = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bidirectional=False
        )
        self.dropout3 = nn.Dropout(dropout)
        self.layernorm3 = nn.LayerNorm(hidden_size)
        
        self.lstm4 = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size//2,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bidirectional=False
        )
        self.dropout4 = nn.Dropout(dropout)
        self.layernorm4 = nn.LayerNorm(hidden_size//2)
        
        # 🔥 RTX 4090 최적화 Dense 스택 (더 큰 레이어들)
        self.fc1 = nn.Linear(hidden_size//2, hidden_size*2)
        self.dropout5 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(hidden_size*2, hidden_size)
        self.dropout6 = nn.Dropout(dropout)
        
        self.fc3 = nn.Linear(hidden_size, hidden_size//2)
        self.dropout7 = nn.Dropout(dropout)
        
        self.fc4 = nn.Linear(hidden_size//2, 128)
        self.dropout8 = nn.Dropout(dropout)
        
        self.output_layer = nn.Linear(128, output_size)
        
        # 🔥 더 복잡한 활성화 함수
        self.relu = nn.ReLU()
        self.gelu = nn.GELU()
        
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        
        # 🔥 4층 LSTM 스택 (RTX 4090 최적화)
        # LSTM 1
        lstm1_out, _ = self.lstm1(x)
        lstm1_out = self.dropout1(lstm1_out)
        lstm1_out = self.layernorm1(lstm1_out)
        
        # LSTM 2
        lstm2_out, _ = self.lstm2(lstm1_out)
        lstm2_out = self.dropout2(lstm2_out)
        lstm2_out = self.layernorm2(lstm2_out)
        
        # LSTM 3
        lstm3_out, _ = self.lstm3(lstm2_out)
        lstm3_out = self.dropout3(lstm3_out)
        lstm3_out = self.layernorm3(lstm3_out)
        
        # LSTM 4
        lstm4_out, _ = self.lstm4(lstm3_out)
        lstm4_out = self.dropout4(lstm4_out)
        lstm4_out = self.layernorm4(lstm4_out)
        
        # 마지막 시퀀스만 사용
        last_output = lstm4_out[:, -1, :]
        
        # 🔥 5층 Dense 스택 (RTX 4090 최적화)
        x = self.gelu(self.fc1(last_output))
        x = self.dropout5(x)
        
        x = self.relu(self.fc2(x))
        x = self.dropout6(x)
        
        x = self.gelu(self.fc3(x))
        x = self.dropout7(x)
        
        x = self.relu(self.fc4(x))
        x = self.dropout8(x)
        
        # 출력
        output = self.output_layer(x)
        
        # (batch_size, 15) -> (batch_size, 5, 3) 형태로 변환
        output = output.view(-1, 5, 3)
        
        return output

class PyTorchStockLSTM:
    def __init__(self, 
                 sequence_length: int = 60,
                 prediction_length: int = 5,
                 num_features: int = 42,     # 🚀 고급 피처 확장 (18 → 42)
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
        
        print(f"🚀 Using device: {self.device}")
        if self.device.type == 'cuda':
            print(f"🔥 GPU: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.history = {'train_loss': [], 'val_loss': []}
        
        self.logger = logging.getLogger(__name__)
        
    def build_model(self, 
                   hidden_size: int = 512,    # 🔥 RTX 4090 최적화 (4배 증가)
                   num_layers: int = 4,       # 🔥 RTX 4090 최적화 (2배 증가)
                   dropout: float = 0.2,
                   loss_type: str = "multi_target"):  # 🚀 고급 손실함수 선택
        """모델 구축 (고급 손실함수 적용)"""
        
        output_size = self.prediction_length * self.num_targets
        
        self.model = StockLSTM(
            input_size=self.num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=output_size,
            dropout=dropout
        ).to(self.device)  # GPU로 이동
        
        # 옵티마이저
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        
        # 🚀 고급 손실함수 적용
        if loss_type == "multi_target":
            self.criterion = MultiTargetLoss(
                close_weight=0.6,      # Close 가격에 60% 가중치
                bb_upper_weight=0.2,   # BB_Upper에 20% 가중치  
                bb_lower_weight=0.2    # BB_Lower에 20% 가중치
            ).to(self.device)
            self.loss_type = "multi_target"
        elif loss_type == "directional":
            self.criterion = DirectionalLoss(
                mse_weight=0.7,        # MSE에 70% 가중치
                direction_weight=0.3   # 방향성에 30% 가중치
            ).to(self.device)
            self.loss_type = "directional"
        elif loss_type == "volatility_aware":
            self.criterion = VolatilityAwareLoss(
                base_weight=1.0,
                volatility_factor=0.5
            ).to(self.device)
            self.loss_type = "volatility_aware"
        else:
            # 기본 MSE (하위 호환성)
            self.criterion = nn.MSELoss()
            self.loss_type = "mse"
            
        # 🚀 고급 평가지표 계산기 초기화
        self.metrics_calculator = AdvancedMetrics()
        
        self.logger.info(f"🚀 Model built with {loss_type} loss function")
        
        # 모델 파라미터 수 출력
        total_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"🏗️ Model built with {total_params:,} trainable parameters")
        
        return self.model
    
    def train_model(self,
                   X_train: np.ndarray,
                   y_train: np.ndarray,
                   X_val: np.ndarray = None,
                   y_val: np.ndarray = None,
                   epochs: int = 100,
                   batch_size: int = 128,    # 🔥 RTX 4090 최적화 (4배 증가)
                   patience: int = 15):
        """모델 학습"""
        
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        # 데이터를 PyTorch 텐서로 변환하고 GPU로 이동
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).to(self.device)
        
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        # 검증 데이터 준비
        val_loader = None
        if X_val is not None and y_val is not None:
            X_val_tensor = torch.FloatTensor(X_val).to(self.device)
            y_val_tensor = torch.FloatTensor(y_val).to(self.device)
            val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 학습 시작
        print(f"🚀 Starting training on {self.device}")
        print(f"📊 Training samples: {len(X_train)}")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            # 학습 모드
            self.model.train()
            train_loss = 0.0
            
            # 🔥 GPU 사용 상태 출력
            if epoch == 0 and self.device.type == 'cuda':
                print(f"🚀 GPU 학습 시작 - 메모리: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
            
            batch_count = 0
            for batch_X, batch_y in train_loader:
                batch_count += 1
                
                # 🔥 GPU 디바이스 확인 (첫 배치에서만)
                if epoch == 0 and batch_count == 1:
                    print(f"📊 Batch X device: {batch_X.device}")
                    print(f"📊 Batch y device: {batch_y.device}")
                    print(f"📊 Model device: {next(self.model.parameters()).device}")
                
                # 그래디언트 초기화
                self.optimizer.zero_grad()
                
                # 순전파
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # 🔥 첫 배치에서 출력 디바이스 확인
                if epoch == 0 and batch_count == 1:
                    print(f"📊 Outputs device: {outputs.device}")
                    print(f"📊 Loss device: {loss.device}")
                
                # 역전파
                loss.backward()
                
                # 그래디언트 클리핑
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                # 옵티마이저 스텝
                self.optimizer.step()
                
                train_loss += loss.item()
                
                # 🔥 GPU 메모리 사용량 주기적 출력
                if batch_count % 10 == 0 and self.device.type == 'cuda':
                    print(f"  Batch {batch_count}: GPU 메모리 {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
            
            avg_train_loss = train_loss / len(train_loader)
            self.history['train_loss'].append(avg_train_loss)
            
            # 검증
            val_loss = 0.0
            if val_loader is not None:
                self.model.eval()
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        outputs = self.model(batch_X)
                        loss = self.criterion(outputs, batch_y)
                        val_loss += loss.item()
                
                avg_val_loss = val_loss / len(val_loader)
                self.history['val_loss'].append(avg_val_loss)
                
                print(f"Epoch {epoch+1}/{epochs} - "
                      f"Train Loss: {avg_train_loss:.6f} - "
                      f"Val Loss: {avg_val_loss:.6f}")
                
                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f"Early stopping at epoch {epoch+1}")
                        break
            else:
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}")
        
        print("🎉 Training completed!")
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """예측 수행"""
        if self.model is None:
            raise ValueError("Model not trained. Train the model first.")
        
        self.model.eval()
        
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(X_tensor)
        
        # CPU로 이동하고 numpy로 변환
        return predictions.cpu().numpy()
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray, 
                 previous_prices: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        🚀 고급 평가지표를 사용한 모델 평가
        
        Args:
            X_test: 테스트 입력 데이터
            y_test: 테스트 타겟 데이터 (정규화된 상태)
            previous_prices: 이전 가격 데이터 (방향성 계산용)
            
        Returns:
            종합 평가 메트릭 딕셔너리
        """
        self.logger.info("🔍 Starting comprehensive model evaluation...")
        
        predictions = self.predict(X_test)
        
        # 1. 기본 메트릭 (하위 호환성)
        normalized_mse = mean_squared_error(y_test.reshape(-1), predictions.reshape(-1))
        normalized_mae = mean_absolute_error(y_test.reshape(-1), predictions.reshape(-1))
        normalized_rmse = np.sqrt(normalized_mse)
        
        epsilon = 1e-8  # 0으로 나누기 방지
        mape = np.mean(np.abs((y_test - predictions) / (y_test + epsilon))) * 100
        
        # 기본 메트릭
        metrics = {
            'MSE': normalized_mse,
            'MAE': normalized_mae,
            'RMSE': normalized_rmse,
            'MAPE': mape,
        }
        
        # 2. 🚀 고급 평가지표 계산
        if hasattr(self, 'metrics_calculator'):
            # Close 가격에 대한 고급 지표 (첫 번째 타겟)
            close_predictions = predictions[:, :, 0].flatten()  # Close 예측
            close_targets = y_test[:, :, 0].flatten()           # Close 실제
            
            # 이전 가격이 없으면 현재 데이터에서 추정
            if previous_prices is None:
                # 첫 번째 시점의 이전 가격을 현재 첫 값으로 근사
                previous_prices = np.roll(close_targets, 1)
                previous_prices[0] = close_targets[0]  # 첫 값 보정
            else:
                previous_prices = previous_prices[:, :, 0].flatten()
            
            # 🚀 종합 고급 지표 계산
            advanced_metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                predictions=close_predictions,
                targets=close_targets,
                previous_prices=previous_prices
            )
            
            # 고급 지표를 메인 지표에 통합
            metrics.update(advanced_metrics)
            
            self.logger.info(f"✅ Advanced metrics calculated: {len(advanced_metrics)} indicators")
        
        # 3. 타겟별 상세 평가
        target_names = ['Close', 'BB_Upper', 'BB_Lower']
        
        for i, target_name in enumerate(target_names):
            target_true = y_test[:, :, i]
            target_pred = predictions[:, :, i]
            
            # 정규화된 상태 메트릭
            target_mse = mean_squared_error(target_true.reshape(-1), target_pred.reshape(-1))
            target_mae = mean_absolute_error(target_true.reshape(-1), target_pred.reshape(-1))
            
            # MAPE (타겟별)
            target_mape = np.mean(np.abs((target_true - target_pred) / (target_true + epsilon))) * 100
            
            # 방향성 정확도 (타겟별)
            pred_dir = np.sign(np.diff(target_pred, axis=1))
            true_dir = np.sign(np.diff(target_true, axis=1))
            target_direction_acc = np.mean(pred_dir == true_dir) * 100
            
            # R² Score (결정계수)
            ss_res = np.sum((target_true - target_pred) ** 2)
            ss_tot = np.sum((target_true - np.mean(target_true)) ** 2)
            r2_score = 1 - (ss_res / (ss_tot + epsilon))
            
            metrics.update({
                f'Normalized_{target_name}_MSE': target_mse,
                f'Normalized_{target_name}_MAE': target_mae,
                f'{target_name}_MAPE': target_mape,
                f'{target_name}_Direction_Accuracy': target_direction_acc,
                f'{target_name}_R2_Score': r2_score
            })
        
        return metrics
    
    def save_model(self, save_path: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("No model to save")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history,
            'model_config': {
                'sequence_length': self.sequence_length,
                'prediction_length': self.prediction_length,
                'num_features': self.num_features,
                'num_targets': self.num_targets
            }
        }, save_path)
        
        print(f"💾 Model saved to {save_path}")
    
    def load_model(self, load_path: str, hidden_size: int = 128):
        """모델 로드"""
        checkpoint = torch.load(load_path, map_location=self.device)
        
        # 모델 구축
        self.build_model(hidden_size=hidden_size)
        
        # 가중치 로드
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        
        print(f"📥 Model loaded from {load_path}")
        
    def plot_training_history(self, save_path: str = None):
        """학습 히스토리 시각화"""
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(self.history['train_loss'], label='Train Loss')
        if 'val_loss' in self.history and self.history['val_loss']:
            plt.plot(self.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        if save_path:
            plt.savefig(save_path)
            print(f"📊 Training history saved to {save_path}")
        else:
            plt.show()

# 테스트 코드
if __name__ == "__main__":
    print("=== PyTorch LSTM 모델 테스트 ===")
    
    # 🔥 RTX 4090 최적화 더미 데이터 생성
    batch_size = 1000              # 🔥 10배 증가
    sequence_length = 60
    num_features = 18
    
    X_dummy = np.random.randn(batch_size, sequence_length, num_features).astype(np.float32)
    y_dummy = np.random.randn(batch_size, 5, 3).astype(np.float32)
    
    print(f"📊 RTX 4090 Test data shape: X={X_dummy.shape}, y={y_dummy.shape}")
    print(f"💾 예상 GPU 메모리 사용량: ~{batch_size * sequence_length * num_features * 4 / 1024**3:.2f}GB")
    
    # 🔥 RTX 4090 최적화 모델 생성
    model = PyTorchStockLSTM()
    model.build_model(hidden_size=512, num_layers=4)  # 큰 모델
    
    print("\n🚀 RTX 4090 최적화 학습 시작...")
    print("💡 다른 터미널에서 nvidia-smi 확인하세요!")
    history = model.train_model(X_dummy, y_dummy, epochs=10, batch_size=128)
    
    print("\n🔮 Testing prediction...")
    predictions = model.predict(X_dummy[:10])
    print(f"Predictions shape: {predictions.shape}")
    
    print("\n✅ RTX 4090 최적화 PyTorch LSTM 모델 테스트 완료!")
    print("GPU 사용률이 90% 이상 올라갔나요? 🔥")