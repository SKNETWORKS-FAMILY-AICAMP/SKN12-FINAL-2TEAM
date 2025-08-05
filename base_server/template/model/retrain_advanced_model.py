#!/usr/bin/env python3
"""
고급 피처 + Transformer 모델 재학습 스크립트
42개 고급 피처를 사용한 차세대 모델 학습
"""

import logging
import sys
import os
import shutil

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def retrain_advanced_model():
    """고급 피처 + Transformer 모델 재학습"""
    try:
        from train_model import ModelTrainer
        
        print("🚀 " + "="*60)
        print("🚀 고급 피처 (42개) + Transformer 모델 재학습 시작")
        print("🚀 " + "="*60)
        
        # RunPod 환경 감지 및 경로 설정
        from config import is_runpod_environment, get_workspace_path
        
        if is_runpod_environment():
            workspace = get_workspace_path()
            model_dir = f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/models"
            data_dir = f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/data"
            log_dir = f"{workspace}/SKN12-FINAL-2TEAM/base_server/template/model/logs"
            print(f"🔧 RunPod 환경 감지됨. 영구 저장소 사용: {model_dir}")
        else:
            model_dir = "models"
            data_dir = "data"
            log_dir = "logs"
            print(f"🔧 로컬 환경 감지됨. 상대 경로 사용: {model_dir}")
        
        # 기존 모델 백업
        pytorch_model_path = os.path.join(model_dir, "pytorch_model.pth")
        preprocessor_path = os.path.join(model_dir, "preprocessor.pkl")
        
        if os.path.exists(pytorch_model_path):
            backup_path = os.path.join(model_dir, "pytorch_model_18features_backup.pth")
            shutil.copy(pytorch_model_path, backup_path)
            print(f"📦 기존 모델을 백업했습니다: {backup_path}")
        
        if os.path.exists(preprocessor_path):
            backup_path = os.path.join(model_dir, "preprocessor_18features_backup.pkl")
            shutil.copy(preprocessor_path, backup_path)
            print(f"📦 기존 전처리기를 백업했습니다: {backup_path}")
        
        # 모델 트레이너 초기화 (RunPod 환경 고려)
        trainer = ModelTrainer(data_dir=data_dir, model_dir=model_dir, log_dir=log_dir)
        
        # 1. 데이터 수집 (기존 데이터 재사용)
        print("\n📊 1단계: 데이터 수집 중...")
        raw_data = trainer.collect_data(force_reload_data=False)
        
        # 2. 고급 피처 전처리 (42개 피처)
        print("\n🔧 2단계: 고급 피처 전처리 중... (42개 피처 생성)")
        
        # 고급 피처 활성화
        if hasattr(trainer.preprocessor, 'advanced_features_enabled'):
            trainer.preprocessor.advanced_features_enabled = True
            print("✅ 고급 피처 엔지니어링 활성화됨")
        else:
            print("⚠️ 고급 피처 속성이 없습니다. data_preprocessor.py를 확인하세요.")
        
        X, y = trainer.preprocess_data(raw_data)
        print(f"✅ 전처리 완료: X={X.shape}, y={y.shape}")
        
        # 3. 데이터 분할
        print("\n📈 3단계: 데이터 분할 중...")
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.prepare_training_data(X, y)
        
        # 4. Transformer 모델 학습
        print("\n🧠 4단계: Transformer 모델 학습 중...")
        history = trainer.train_model(
            X_train, y_train, X_val, y_val,
            model_type="transformer",  # 🚀 Transformer 사용
            epochs=100,
            batch_size=64  # Transformer는 작은 배치 사용
        )
        
        # 5. 모델 평가
        print("\n📊 5단계: 모델 평가 중...")
        metrics = trainer.evaluate_model(X_test, y_test)
        
        # 6. 결과 저장
        print("\n💾 6단계: 모델 저장 중...")
        trainer.save_training_artifacts()
        
        print("\n🎉 " + "="*60)
        print("🎉 고급 Transformer 모델 재학습 완료!")
        print("🎉 " + "="*60)
        
        print(f"\n📊 최종 성능 지표:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.6f}")
        
        print(f"\n📁 저장된 파일들:")
        print(f"  - {os.path.join(model_dir, 'final_model.pth')} (Transformer 모델)")
        print(f"  - {os.path.join(model_dir, 'preprocessor.pkl')} (고급 피처 전처리기)")
        print(f"  - {os.path.join(model_dir, 'evaluation_metrics.pkl')} (평가 지표)")
        
        print(f"\n🔄 API 서버 업데이트 방법:")
        print(f"  1. API 서버 설정은 이미 완료됨 ✅")
        print(f"     - num_features=42 (자동 설정)")
        print(f"     - advanced_features_enabled=True (자동 설정)")
        print(f"  2. python api_server.py로 서버 재시작만 하면 됨!")
        
        return True
        
    except Exception as e:
        print(f"❌ 재학습 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = retrain_advanced_model()
    
    if success:
        print("\n✅ 재학습이 성공적으로 완료되었습니다!")
        print("이제 API 서버를 42개 피처 모드로 업데이트할 수 있습니다.")
    else:
        print("\n❌ 재학습에 실패했습니다.")
        print("기존 18개 피처 모델을 계속 사용하세요.")
        sys.exit(1)