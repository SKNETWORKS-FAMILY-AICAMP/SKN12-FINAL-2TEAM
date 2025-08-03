"""
GPU 최적화된 PyTorch LSTM 모델
RTX 4090을 100% 활용하도록 설계
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
import time
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

class OptimizedStockLSTM(nn.Module):
    def __init__(self, 
                 input_size: int = 18,
                 hidden_size: int = 256,  # 더 큰 hidden size
                 num_layers: int = 3,     # 더 많은 레이어
                 output_size: int = 15,
                 dropout: float = 0.2):
        super(OptimizedStockLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        # 🔥 더 큰 LSTM 스택 (GPU 사용률 증가)
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
        
        # 추가 LSTM 레이어 (GPU 사용률 더 증가)
        self.lstm3 = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size//2,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bidirectional=False
        )
        
        self.dropout3 = nn.Dropout(dropout)
        self.layernorm3 = nn.LayerNorm(hidden_size//2)
        
        # 🔥 더 큰 Dense 레이어들 (GPU 연산 증가)
        self.fc1 = nn.Linear(hidden_size//2, hidden_size)
        self.dropout4 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(hidden_size, hidden_size//2)
        self.dropout5 = nn.Dropout(dropout)
        
        self.fc3 = nn.Linear(hidden_size//2, 64)
        self.dropout6 = nn.Dropout(dropout)
        
        self.output_layer = nn.Linear(64, output_size)
        
        # 활성화 함수
        self.relu = nn.ReLU()
        self.gelu = nn.GELU()  # 더 복잡한 활성화 함수
        
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        
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
        
        # 마지막 시퀀스만 사용
        last_output = lstm3_out[:, -1, :]
        
        # 🔥 더 많은 Dense 연산 (GPU 사용률 증가)
        x = self.gelu(self.fc1(last_output))
        x = self.dropout4(x)
        
        x = self.relu(self.fc2(x))
        x = self.dropout5(x)
        
        x = self.relu(self.fc3(x))
        x = self.dropout6(x)
        
        # 출력
        output = self.output_layer(x)
        
        # (batch_size, 15) -> (batch_size, 5, 3) 형태로 변환
        output = output.view(-1, 5, 3)
        
        return output

class OptimizedPyTorchStockLSTM:
    def __init__(self, 
                 sequence_length: int = 60,
                 prediction_length: int = 5,
                 num_features: int = 18,
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
        self.scheduler = None  # 학습률 스케줄러 추가
        self.history = {'train_loss': [], 'val_loss': []}
        
        self.logger = logging.getLogger(__name__)
        
    def build_model(self, 
                   hidden_size: int = 256,  # 기본값 증가
                   num_layers: int = 3,     # 기본값 증가
                   dropout: float = 0.2):
        """GPU 최적화된 모델 구축"""
        
        output_size = self.prediction_length * self.num_targets
        
        self.model = OptimizedStockLSTM(
            input_size=self.num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=output_size,
            dropout=dropout
        ).to(self.device)  # GPU로 이동
        
        # 옵티마이저와 손실함수
        self.optimizer = optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        self.criterion = nn.MSELoss()
        
        # 학습률 스케줄러 추가
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=10, verbose=True
        )
        
        # 모델 파라미터 수 출력
        total_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"🏗️ Optimized model built with {total_params:,} trainable parameters")
        
        return self.model
    
    def train_model(self,
                   X_train: np.ndarray,
                   y_train: np.ndarray,
                   X_val: np.ndarray = None,
                   y_val: np.ndarray = None,
                   epochs: int = 100,
                   batch_size: int = 64,    # 더 큰 배치 크기
                   patience: int = 15,
                   num_workers: int = 4):   # DataLoader 최적화
        """GPU 최적화된 모델 학습"""
        
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        print(f"🔥 GPU 최적화 학습 시작!")
        print(f"📊 배치 크기: {batch_size}")
        print(f"💾 예상 GPU 메모리 사용량: ~{batch_size * self.sequence_length * self.num_features * 4 / 1024**3:.2f}GB")
        
        # 🔥 데이터를 GPU로 이동 (한 번에 모든 데이터)
        print("데이터를 GPU로 이동 중...")
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).to(self.device)
        
        print(f"✅ 학습 데이터 GPU 이동 완료: X={X_train_tensor.device}, y={y_train_tensor.device}")
        print(f"GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
        
        # DataLoader 설정 (GPU 최적화)
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(
            train_dataset, 
            batch_size=batch_size, 
            shuffle=True,
            num_workers=0,  # GPU에서는 0이 더 빠름
            pin_memory=False  # 이미 GPU에 있으므로 False
        )
        
        # 검증 데이터 준비
        val_loader = None
        if X_val is not None and y_val is not None:
            X_val_tensor = torch.FloatTensor(X_val).to(self.device)
            y_val_tensor = torch.FloatTensor(y_val).to(self.device)
            val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 학습 시작
        print(f"🚀 Starting optimized training on {self.device}")
        print(f"📊 Training samples: {len(X_train)}")
        print(f"🔢 Total batches per epoch: {len(train_loader)}")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            epoch_start_time = time.time()
            
            # 학습 모드
            self.model.train()
            train_loss = 0.0
            
            # 🔥 GPU 사용 상태 출력 (첫 epoch에만)
            if epoch == 0 and self.device.type == 'cuda':
                print(f"🚀 GPU 학습 시작 - 메모리: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
            
            batch_count = 0
            for batch_X, batch_y in train_loader:
                batch_count += 1
                
                # 🔥 첫 배치에서 디바이스 확인
                if epoch == 0 and batch_count == 1:
                    print(f"📊 Batch X device: {batch_X.device}")
                    print(f"📊 Batch y device: {batch_y.device}")
                    print(f"📊 Model device: {next(self.model.parameters()).device}")
                
                # 그래디언트 초기화
                self.optimizer.zero_grad()
                
                # 순전파
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # 🔥 첫 배치에서 출력 확인
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
                if batch_count % 20 == 0 and self.device.type == 'cuda':
                    print(f"  Batch {batch_count}/{len(train_loader)}: GPU 메모리 {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
            
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
                
                # 학습률 스케줄러 업데이트
                self.scheduler.step(avg_val_loss)
                
                epoch_time = time.time() - epoch_start_time
                print(f"Epoch {epoch+1}/{epochs} ({epoch_time:.1f}s) - "
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
                epoch_time = time.time() - epoch_start_time
                print(f"Epoch {epoch+1}/{epochs} ({epoch_time:.1f}s) - Train Loss: {avg_train_loss:.6f}")
        
        print("🎉 GPU 최적화 학습 완료!")
        print(f"최종 GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """GPU 최적화된 예측"""
        if self.model is None:
            raise ValueError("Model not trained. Train the model first.")
        
        self.model.eval()
        
        # GPU로 이동
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(X_tensor)
        
        # CPU로 이동하고 numpy로 변환
        return predictions.cpu().numpy()
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """모델 평가"""
        predictions = self.predict(X_test)
        
        # 전체 평가
        mse = mean_squared_error(y_test.reshape(-1), predictions.reshape(-1))
        mae = mean_absolute_error(y_test.reshape(-1), predictions.reshape(-1))
        
        # 타겟별 평가
        target_names = ['Close', 'BB_Upper', 'BB_Lower']
        metrics = {'Overall_MSE': mse, 'Overall_MAE': mae}
        
        for i, target_name in enumerate(target_names):
            target_true = y_test[:, :, i].reshape(-1)
            target_pred = predictions[:, :, i].reshape(-1)
            
            target_mse = mean_squared_error(target_true, target_pred)
            target_mae = mean_absolute_error(target_true, target_pred)
            
            metrics[f'{target_name}_MSE'] = target_mse
            metrics[f'{target_name}_MAE'] = target_mae
        
        return metrics
    
    def save_model(self, save_path: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("No model to save")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'history': self.history,
            'model_config': {
                'sequence_length': self.sequence_length,
                'prediction_length': self.prediction_length,
                'num_features': self.num_features,
                'num_targets': self.num_targets
            }
        }, save_path)
        
        print(f"💾 Optimized model saved to {save_path}")
    
    def load_model(self, load_path: str, hidden_size: int = 256):
        """모델 로드"""
        checkpoint = torch.load(load_path, map_location=self.device)
        
        # 모델 구축
        self.build_model(hidden_size=hidden_size)
        
        # 가중치 로드
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if 'scheduler_state_dict' in checkpoint and checkpoint['scheduler_state_dict']:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.history = checkpoint['history']
        
        print(f"📥 Optimized model loaded from {load_path}")

# 테스트 코드
if __name__ == "__main__":
    print("=== GPU 최적화 LSTM 모델 테스트 ===")
    
    # 더 큰 더미 데이터 생성
    batch_size = 500   # 더 큰 배치
    sequence_length = 60
    num_features = 18
    
    X_dummy = np.random.randn(batch_size, sequence_length, num_features).astype(np.float32)
    y_dummy = np.random.randn(batch_size, 5, 3).astype(np.float32)
    
    print(f"📊 Test data shape: X={X_dummy.shape}, y={y_dummy.shape}")
    
    # GPU 최적화 모델 생성
    model = OptimizedPyTorchStockLSTM()
    model.build_model(hidden_size=256, num_layers=3)
    
    print("\n🚀 GPU 최적화 학습 시작...")
    print("💡 nvidia-smi로 GPU 사용률 확인하세요!")
    
    history = model.train_model(
        X_dummy, y_dummy, 
        epochs=10, 
        batch_size=128  # 큰 배치 크기
    )
    
    print("\n🔮 예측 테스트...")
    predictions = model.predict(X_dummy[:50])
    print(f"예측 결과: {predictions.shape}")
    
    print("\n✅ GPU 최적화 LSTM 테스트 완료!")
    print("GPU 사용률이 90% 이상 올라갔나요? 🔥")