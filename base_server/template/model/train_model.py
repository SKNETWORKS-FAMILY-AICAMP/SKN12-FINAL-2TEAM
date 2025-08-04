"""
LSTM 모델 학습 스크립트
데이터 수집, 전처리, 모델 학습을 통합하여 실행
"""

import os
import sys
import logging
import argparse
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 모듈 import
from data_collector import StockDataCollector
from data_preprocessor import StockDataPreprocessor
from pytorch_lstm_model import PyTorchStockLSTM
from config import get_model_save_dir, get_workspace_path, is_runpod_environment

class ModelTrainer:
    def __init__(self, 
                 data_dir: str = None,
                 model_dir: str = None,
                 log_dir: str = None):
        """
        모델 학습기 초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리 (None시 환경에 따라 자동 설정)
            model_dir: 모델 저장 디렉토리 (None시 환경에 따라 자동 설정)
            log_dir: 로그 저장 디렉토리 (None시 환경에 따라 자동 설정)
        """
        # RunPod 환경 고려한 기본 경로 설정
        if is_runpod_environment():
            workspace = get_workspace_path()
            self.data_dir = data_dir or f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/data"
            self.model_dir = model_dir or f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/models"
            self.log_dir = log_dir or f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/logs"
        else:
            self.data_dir = data_dir or "data"
            self.model_dir = model_dir or "models"
            self.log_dir = log_dir or "logs"
        
        # 디렉토리 생성
        for directory in [self.data_dir, self.model_dir, self.log_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 컴포넌트 초기화
        self.data_collector = StockDataCollector()
        self.preprocessor = StockDataPreprocessor()
        self.model = None
        
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """로깅 설정"""
        log_file = os.path.join(self.log_dir, f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # PyTorch 사용으로 TensorFlow 로깅 설정 제거
        # os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        # logging.getLogger('tensorflow').setLevel(logging.WARNING)
    
    def collect_data(self, force_reload: bool = False) -> dict[str, pd.DataFrame]:
        """
        학습 데이터 수집
        
        Args:
            force_reload: 강제로 데이터 재수집 여부
            
        Returns:
            수집된 데이터 딕셔너리
        """
        data_file = os.path.join(self.data_dir, "collected_data.pkl")
        
        if os.path.exists(data_file) and not force_reload:
            self.logger.info("Loading existing data...")
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            self.logger.info(f"Loaded data for {len(data)} symbols")
            return data
        
        self.logger.info("Collecting new data...")
        data = self.data_collector.collect_top_100_data()
        
        # 데이터 저장
        with open(data_file, 'wb') as f:
            pickle.dump(data, f)
        
        # CSV로도 저장
        self.data_collector.save_data_to_csv(data, self.data_dir)
        
        self.logger.info(f"Data collection completed: {len(data)} symbols")
        return data
    
    def preprocess_data(self, raw_data: dict[str, pd.DataFrame]) -> tuple[np.ndarray, np.ndarray]:
        """
        데이터 전처리 및 시퀀스 생성
        
        Args:
            raw_data: 원본 데이터 딕셔너리
            
        Returns:
            (X, y) - 학습용 시퀀스 데이터
        """
        self.logger.info("Starting data preprocessing...")
        
        all_X = []
        all_y = []
        
        for symbol, df in raw_data.items():
            try:
                # 최소 데이터 길이 확인 (60일 + 5일 예측 + 여유분)
                if len(df) < 100:
                    self.logger.warning(f"Insufficient data for {symbol}: {len(df)} records")
                    continue
                
                # 전처리
                processed_df = self.preprocessor.preprocess_data(df)
                
                # 시퀀스 생성 (종목별 개별 정규화)
                X, y = self.preprocessor.create_sequences(processed_df, symbol)
                
                if len(X) > 0:
                    all_X.append(X)
                    all_y.append(y)
                    self.logger.info(f"Processed {symbol}: {X.shape[0]} sequences")
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        if not all_X:
            raise ValueError("No valid data sequences generated")
        
        # 모든 시퀀스 결합
        X_combined = np.vstack(all_X)
        y_combined = np.vstack(all_y)
        
        self.logger.info(f"Combined sequences - X: {X_combined.shape}, y: {y_combined.shape}")
        
        # 전처리된 데이터 저장 (종목별 스케일러 포함)
        processed_data_file = os.path.join(self.data_dir, "processed_sequences.pkl")
        with open(processed_data_file, 'wb') as f:
            pickle.dump({
                'X': X_combined,
                'y': y_combined,
                'scaler': self.preprocessor.scaler,  # 기존 호환성
                'symbol_scalers': self.preprocessor.symbol_scalers,  # 종목별 피처 스케일러
                'target_scalers': self.preprocessor.target_scalers   # 종목별 타겟 스케일러
            }, f)
        
        return X_combined, y_combined
    
    def prepare_training_data(self, X: np.ndarray, y: np.ndarray, 
                            test_size: float = 0.2, 
                            val_size: float = 0.1) -> tuple:
        """
        학습/검증/테스트 데이터 분할
        
        Args:
            X: 입력 시퀀스
            y: 타겟 시퀀스
            test_size: 테스트 데이터 비율
            val_size: 검증 데이터 비율
            
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        self.logger.info("Splitting data into train/validation/test sets...")
        
        # 먼저 train+val과 test로 분할
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=True
        )
        
        # train과 validation으로 분할
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=42, shuffle=True
        )
        
        self.logger.info(f"Data split - Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train_model(self, 
                   X_train: np.ndarray, 
                   y_train: np.ndarray,
                   X_val: np.ndarray, 
                   y_val: np.ndarray,
                   model_type: str = "lstm_attention",
                   epochs: int = 100,
                   batch_size: int = 128) -> dict:  # 🔥 RTX 4090 최적화
        """
        모델 학습 실행
        
        Args:
            X_train, y_train: 학습 데이터
            X_val, y_val: 검증 데이터
            model_type: 모델 타입
            epochs: 학습 에포크
            batch_size: 배치 크기
            
        Returns:
            학습 히스토리
        """
        self.logger.info(f"Starting model training with {model_type}")
        
        # 🚀 PyTorch 모델 초기화
        self.model = PyTorchStockLSTM(
            sequence_length=X_train.shape[1],
            prediction_length=y_train.shape[1],
            num_features=X_train.shape[2],
            num_targets=y_train.shape[2]
        )
        
        # 🔥 RTX 4090 최적화 모델 구축
        pytorch_model = self.model.build_model(hidden_size=512, num_layers=4, dropout=0.2)
        print(f"🚀 RTX 4090 최적화 모델 구축 완료!")
        
        # 학습 실행 (PyTorch)
        history = self.model.train_model(
            X_train, y_train,
            X_val, y_val,
            epochs=epochs,
            batch_size=batch_size,
            patience=15
        )
        
        # 모델 저장 (PyTorch)
        model_save_path = os.path.join(self.model_dir, "pytorch_model.pth")
        self.model.save_model(model_save_path)
        
        # 학습 히스토리 시각화
        plot_path = os.path.join(self.model_dir, "training_history.png")
        self.model.plot_training_history(plot_path)
        
        self.logger.info("Model training completed")
        return history
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
        """
        모델 평가
        
        Args:
            X_test: 테스트 입력
            y_test: 테스트 타겟
            
        Returns:
            평가 지표
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        self.logger.info("Evaluating model on test set...")
        metrics = self.model.evaluate(X_test, y_test)
        
        # 평가 결과 저장
        metrics_file = os.path.join(self.model_dir, "evaluation_metrics.pkl")
        with open(metrics_file, 'wb') as f:
            pickle.dump(metrics, f)
        
        # 평가 결과 로그
        for metric_name, value in metrics.items():
            self.logger.info(f"{metric_name}: {value:.6f}")
        
        return metrics
    
    def save_training_artifacts(self):
        """학습 결과물 저장"""
        if self.model is None:
            return
        
        # 최종 모델 저장 (PyTorch)
        final_model_path = os.path.join(self.model_dir, "final_model.pth")
        self.model.save_model(final_model_path)
        
        # 전처리기 저장
        preprocessor_path = os.path.join(self.model_dir, "preprocessor.pkl")
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(self.preprocessor, f)
        
        self.logger.info(f"Training artifacts saved to {self.model_dir}")
    
    def run_full_training_pipeline(self,
                                 force_reload_data: bool = False,
                                 model_type: str = "lstm_attention",
                                 epochs: int = 100,
                                 batch_size: int = 128):  # 🔥 RTX 4090 최적화
        """
        전체 학습 파이프라인 실행
        
        Args:
            force_reload_data: 데이터 강제 재수집
            model_type: 모델 타입
            epochs: 학습 에포크
            batch_size: 배치 크기
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("STARTING FULL TRAINING PIPELINE")
            self.logger.info("=" * 50)
            
            # 1. 데이터 수집
            raw_data = self.collect_data(force_reload_data)
            
            # 2. 데이터 전처리
            X, y = self.preprocess_data(raw_data)
            
            # 3. 데이터 분할
            X_train, X_val, X_test, y_train, y_val, y_test = self.prepare_training_data(X, y)
            
            # 4. 모델 학습
            history = self.train_model(X_train, y_train, X_val, y_val, 
                                     model_type, epochs, batch_size)
            
            # 5. 모델 평가
            metrics = self.evaluate_model(X_test, y_test)
            
            # 6. 결과물 저장
            self.save_training_artifacts()
            
            self.logger.info("=" * 50)
            self.logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 50)
            
            return {
                'history': history,
                'metrics': metrics,
                'model_path': os.path.join(self.model_dir, "final_model.pth")
            }
            
        except Exception as e:
            self.logger.error(f"Training pipeline failed: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Stock LSTM Model Training")
    parser.add_argument("--data-dir", default=None, help="Data directory (auto-detect if not specified)")
    parser.add_argument("--model-dir", default=None, help="Model save directory (auto-detect if not specified)")
    parser.add_argument("--log-dir", default=None, help="Log directory (auto-detect if not specified)")
    parser.add_argument("--force-reload", action="store_true", help="Force reload data")
    parser.add_argument("--model-type", default="lstm_attention", 
                       choices=["lstm", "lstm_attention", "lstm_ensemble"],
                       help="Model type to train")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    
    args = parser.parse_args()
    
    # 학습 실행
    trainer = ModelTrainer(args.data_dir, args.model_dir, args.log_dir)
    
    results = trainer.run_full_training_pipeline(
        force_reload_data=args.force_reload,
        model_type=args.model_type,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    print(f"\nTraining completed!")
    print(f"Model saved at: {results['model_path']}")
    print(f"Final test metrics: {results['metrics']}")


if __name__ == "__main__":
    main()