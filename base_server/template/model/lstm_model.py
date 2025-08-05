"""
LSTM 모델 구현
60일 데이터로 다음 5일의 추세와 Bollinger Band 예측
"""

import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, LayerNormalization, MultiHeadAttention
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.regularizers import l2
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
import logging
import pickle
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt

class StockLSTMModel:
    def __init__(self, 
                 sequence_length: int = 60,
                 prediction_length: int = 5,
                 num_features: int = 18,
                 num_targets: int = 3):
        """
        LSTM 모델 초기화
        
        Args:
            sequence_length: 입력 시퀀스 길이 (60일)
            prediction_length: 예측 길이 (5일)
            num_features: 입력 피처 수
            num_targets: 예측 타겟 수 (Close, BB_Upper, BB_Lower)
        """
        self.sequence_length = sequence_length
        self.prediction_length = prediction_length
        self.num_features = num_features
        self.num_targets = num_targets
        self.model = None
        self.history = None
        self.logger = logging.getLogger(__name__)
        
        # GPU 사용 설정
        self.setup_gpu()
    
    def setup_gpu(self):
        """GPU 설정 및 확인"""
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                # GPU 메모리 증가 허용
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                self.logger.info(f"Found {len(gpus)} GPU(s): {[gpu.name for gpu in gpus]}")
            except RuntimeError as e:
                self.logger.error(f"GPU setup error: {e}")
        else:
            self.logger.warning("No GPU found, using CPU")
    
    def build_model(self, model_type: str = "lstm_attention") -> Model:
        """
        LSTM 모델 구축
        
        Args:
            model_type: 모델 타입 ("lstm", "lstm_attention", "lstm_ensemble")
            
        Returns:
            컴파일된 Keras 모델
        """
        # 🚀 GPU 강제 사용으로 모든 모델 생성
        with tf.device('/GPU:0'):
            if model_type == "lstm":
                model = self._build_basic_lstm()
            elif model_type == "lstm_attention":
                model = self._build_lstm_with_attention()
            elif model_type == "lstm_ensemble":
                model = self._build_lstm_ensemble()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # 모델 컴파일도 GPU에서
            model.compile(
                optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
                loss='mse',
                metrics=['mae']
            )
        
        self.model = model
        self.logger.info(f"Built {model_type} model with {model.count_params():,} parameters")
        self.logger.info("🚀 Model created with GPU enforcement!")
        return model
    
    def _build_basic_lstm(self) -> Model:
        """기본 LSTM 모델"""
        model = Sequential([
            Input(shape=(self.sequence_length, self.num_features)),
            
            LSTM(128, return_sequences=True, dropout=0.2),  # cuDNN 최적화를 위해 recurrent_dropout 제거
            LayerNormalization(),
            
            LSTM(64, return_sequences=True, dropout=0.2),
            LayerNormalization(),
            
            LSTM(32, return_sequences=False, dropout=0.2),
            LayerNormalization(),
            
            Dense(64, activation='relu', kernel_regularizer=l2(0.001)),
            Dropout(0.3),
            
            Dense(32, activation='relu', kernel_regularizer=l2(0.001)),
            Dropout(0.3),
            
            # 출력: (5일 예측 * 3개 타겟)
            Dense(self.prediction_length * self.num_targets, activation='linear'),
            tf.keras.layers.Reshape((self.prediction_length, self.num_targets))
        ])
        
        return model
    
    def _build_lstm_with_attention(self) -> Model:
        """Attention 메커니즘이 있는 LSTM 모델"""
        # 입력
        inputs = Input(shape=(self.sequence_length, self.num_features))
        
        # LSTM 레이어들
        lstm1 = LSTM(128, return_sequences=True, dropout=0.2)(inputs)  # cuDNN 최적화
        lstm1_norm = LayerNormalization()(lstm1)
        
        lstm2 = LSTM(64, return_sequences=True, dropout=0.2)(lstm1_norm)
        lstm2_norm = LayerNormalization()(lstm2)
        
        # Multi-Head Attention
        attention = MultiHeadAttention(
            num_heads=8, 
            key_dim=64,
            dropout=0.1
        )(lstm2_norm, lstm2_norm)
        
        # Attention과 LSTM 출력 결합
        attention_norm = LayerNormalization()(attention)
        combined = tf.keras.layers.Add()([lstm2_norm, attention_norm])
        
        # Global Average Pooling
        pooled = tf.keras.layers.GlobalAveragePooling1D()(combined)
        
        # Dense 레이어들
        dense1 = Dense(128, activation='relu', kernel_regularizer=l2(0.001))(pooled)
        dropout1 = Dropout(0.3)(dense1)
        
        dense2 = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(dropout1)
        dropout2 = Dropout(0.3)(dense2)
        
        # 출력
        outputs = Dense(self.prediction_length * self.num_targets, activation='linear')(dropout2)
        outputs_reshaped = tf.keras.layers.Reshape((self.prediction_length, self.num_targets))(outputs)
        
        model = Model(inputs=inputs, outputs=outputs_reshaped)
        return model
    
    def _build_lstm_ensemble(self) -> Model:
        """앙상블 LSTM 모델"""
        inputs = Input(shape=(self.sequence_length, self.num_features))
        
        # 여러 LSTM 브랜치
        branches = []
        
        # 브랜치 1: 짧은 기간 패턴
        branch1 = LSTM(64, return_sequences=True, dropout=0.2)(inputs)
        branch1 = LSTM(32, return_sequences=False, dropout=0.2)(branch1)
        branches.append(branch1)
        
        # 브랜치 2: 중간 기간 패턴  
        branch2 = LSTM(96, return_sequences=True, dropout=0.2)(inputs)
        branch2 = LSTM(48, return_sequences=False, dropout=0.2)(branch2)
        branches.append(branch2)
        
        # 브랜치 3: 긴 기간 패턴
        branch3 = LSTM(128, return_sequences=True, dropout=0.2)(inputs)
        branch3 = LSTM(64, return_sequences=False, dropout=0.2)(branch3)
        branches.append(branch3)
        
        # 브랜치 결합
        combined = tf.keras.layers.Concatenate()(branches)
        combined_norm = LayerNormalization()(combined)
        
        # 최종 Dense 레이어들
        dense1 = Dense(128, activation='relu', kernel_regularizer=l2(0.001))(combined_norm)
        dropout1 = Dropout(0.3)(dense1)
        
        dense2 = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(dropout1)
        dropout2 = Dropout(0.3)(dense2)
        
        # 출력
        outputs = Dense(self.prediction_length * self.num_targets, activation='linear')(dropout2)
        outputs_reshaped = tf.keras.layers.Reshape((self.prediction_length, self.num_targets))(outputs)
        
        model = Model(inputs=inputs, outputs=outputs_reshaped)
        return model
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray = None,
              y_val: np.ndarray = None,
              epochs: int = 100,
              batch_size: int = 32,
              save_path: str = "models/") -> Dict:
        """
        모델 학습
        
        Args:
            X_train: 학습 데이터 입력
            y_train: 학습 데이터 타겟
            X_val: 검증 데이터 입력
            y_val: 검증 데이터 타겟
            epochs: 학습 에포크
            batch_size: 배치 크기
            save_path: 모델 저장 경로
            
        Returns:
            학습 히스토리
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        # 콜백 설정
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=10,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        # 모델 저장 경로 생성
        os.makedirs(save_path, exist_ok=True)
        model_save_path = os.path.join(save_path, "best_model.keras")
        
        callbacks.append(
            ModelCheckpoint(
                model_save_path,
                monitor='val_loss' if X_val is not None else 'loss',
                save_best_only=True,
                verbose=1
            )
        )
        
        self.logger.info(f"Starting training with {len(X_train)} samples")
        
        # 🚀 GPU 강제 사용으로 모델 학습
        with tf.device('/GPU:0'):
            validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
            
            self.history = self.model.fit(
                X_train, y_train,
                validation_data=validation_data,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1,
                shuffle=True
            )
            
        self.logger.info("🚀 Training completed with GPU enforcement!")
        
        self.logger.info("Training completed")
        
        # 학습 히스토리 저장
        history_path = os.path.join(save_path, "training_history.pkl")
        with open(history_path, 'wb') as f:
            pickle.dump(self.history.history, f)
        
        return self.history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        예측 수행
        
        Args:
            X: 입력 시퀀스 데이터
            
        Returns:
            예측 결과 (batch_size, 5일, 3개 타겟)
        """
        if self.model is None:
            raise ValueError("Model not trained. Train the model first.")
        
        # 🚀 GPU 강제 사용으로 예측
        with tf.device('/GPU:0'):
            predictions = self.model.predict(X, verbose=0)
        return predictions
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        모델 평가
        
        Args:
            X_test: 테스트 입력 데이터
            y_test: 테스트 타겟 데이터
            
        Returns:
            평가 지표
        """
        predictions = self.predict(X_test)
        
        # 전체 평가
        mse = mean_squared_error(y_test.reshape(-1), predictions.reshape(-1))
        mae = mean_absolute_error(y_test.reshape(-1), predictions.reshape(-1))
        
        # 타겟별 평가 (Close, BB_Upper, BB_Lower)
        target_names = ['Close', 'BB_Upper', 'BB_Lower']
        target_metrics = {}
        
        for i, target_name in enumerate(target_names):
            target_true = y_test[:, :, i].reshape(-1)
            target_pred = predictions[:, :, i].reshape(-1)
            
            target_mse = mean_squared_error(target_true, target_pred)
            target_mae = mean_absolute_error(target_true, target_pred)
            
            target_metrics[f'{target_name}_MSE'] = target_mse
            target_metrics[f'{target_name}_MAE'] = target_mae
        
        metrics = {
            'Overall_MSE': mse,
            'Overall_MAE': mae,
            **target_metrics
        }
        
        self.logger.info(f"Evaluation metrics: {metrics}")
        return metrics
    
    def save_model(self, path: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("No model to save")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        self.logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """모델 로드"""
        self.model = tf.keras.models.load_model(path)
        self.logger.info(f"Model loaded from {path}")
    
    def plot_training_history(self, save_path: str = None):
        """학습 히스토리 시각화"""
        if self.history is None:
            self.logger.warning("No training history available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss 플롯
        ax1.plot(self.history.history['loss'], label='Training Loss')
        if 'val_loss' in self.history.history:
            ax1.plot(self.history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # MAE 플롯
        ax2.plot(self.history.history['mae'], label='Training MAE')
        if 'val_mae' in self.history.history:
            ax2.plot(self.history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"Training history plot saved to {save_path}")
        
        plt.show()


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터 생성
    batch_size = 100
    sequence_length = 60
    num_features = 18
    prediction_length = 5
    num_targets = 3
    
    X_sample = np.random.randn(batch_size, sequence_length, num_features)
    y_sample = np.random.randn(batch_size, prediction_length, num_targets)
    
    # 모델 생성 및 테스트
    model = StockLSTMModel(
        sequence_length=sequence_length,
        prediction_length=prediction_length,
        num_features=num_features,
        num_targets=num_targets
    )
    
    # 모델 구축
    keras_model = model.build_model("lstm_attention")
    print(f"Model built successfully: {keras_model.summary()}")
    
    # 간단한 학습 테스트
    history = model.train(X_sample[:80], y_sample[:80], 
                         X_sample[80:], y_sample[80:], 
                         epochs=2, batch_size=16)
    
    # 예측 테스트
    predictions = model.predict(X_sample[:10])
    print(f"Prediction shape: {predictions.shape}")
    
    # 평가 테스트
    metrics = model.evaluate(X_sample[80:], y_sample[80:])
    print(f"Evaluation metrics: {metrics}")
    
    print("LSTM model test completed successfully!")