#!/usr/bin/env python3
"""
모델 예측 올인원 런처
모든 예측 방법을 하나의 스크립트로 실행
"""

import sys
import subprocess
import time

def print_banner():
    """배너 출력"""
    print("🚀 Stock Prediction Model Launcher")
    print("="*50)
    print("1. 🌐 API Server      - Web API 서버 실행")
    print("2. 🔮 Inference       - 배치 추론 실행")
    print("3. 🧪 Test Model      - 직접 모델 테스트")
    print("4. 📊 Interactive     - 시각적 분석")
    print("5. 💻 CLI Tool        - 명령줄 도구")
    print("6. ❓ Model Info      - 모델 정보")
    print("0. 🚪 Exit")
    print("="*50)

def run_api_server():
    """API 서버 실행"""
    print("🌐 Starting API Server...")
    print("서버가 시작되면 http://localhost:8000 에서 접근 가능합니다.")
    print("종료하려면 Ctrl+C를 누르세요.")
    print()
    
    try:
        subprocess.run([sys.executable, "api_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 API Server stopped by user")
    except Exception as e:
        print(f"❌ API Server error: {e}")

def run_inference():
    """배치 추론 실행"""
    print("🔮 Running Batch Inference...")
    
    symbols = input("종목 입력 (공백으로 구분, 기본값=AAPL MSFT GOOGL): ").strip()
    if not symbols:
        symbols = "AAPL MSFT GOOGL"
    
    output_file = input("출력 파일명 (기본값=predictions.json): ").strip()
    if not output_file:
        output_file = "predictions.json"
    
    try:
        cmd = [sys.executable, "inference_pipeline.py", 
               "--symbols"] + symbols.split() + ["--output", output_file]
        subprocess.run(cmd, check=True)
        print(f"✅ Results saved to {output_file}")
    except Exception as e:
        print(f"❌ Inference error: {e}")

def run_test_model():
    """모델 테스트 실행"""
    print("🧪 Running Model Test...")
    
    try:
        subprocess.run([sys.executable, "test_trained_model.py"], check=True)
    except Exception as e:
        print(f"❌ Test error: {e}")

def run_interactive():
    """인터랙티브 분석 실행"""
    print("📊 Running Interactive Analysis...")
    
    try:
        subprocess.run([sys.executable, "model_testing_notebook.py"], check=True)
    except Exception as e:
        print(f"❌ Interactive analysis error: {e}")

def run_cli():
    """CLI 도구 실행"""
    print("💻 CLI Tool Options:")
    print("1. Single prediction")
    print("2. Batch prediction")
    print("3. Model info")
    
    choice = input("선택 (1-3): ").strip()
    
    try:
        if choice == "1":
            symbol = input("종목 심볼 (예: AAPL): ").strip().upper()
            if symbol:
                subprocess.run([sys.executable, "predict_cli.py", symbol, "--verbose"], check=True)
        
        elif choice == "2":
            symbols = input("종목들 (공백으로 구분): ").strip().upper()
            if symbols:
                cmd = [sys.executable, "predict_cli.py", "--batch"] + symbols.split()
                subprocess.run(cmd, check=True)
        
        elif choice == "3":
            subprocess.run([sys.executable, "predict_cli.py", "--info"], check=True)
        
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        print(f"❌ CLI error: {e}")

def show_model_info():
    """모델 정보 출력"""
    print("❓ Model Information:")
    
    try:
        subprocess.run([sys.executable, "predict_cli.py", "--info"], check=True)
    except Exception as e:
        print(f"❌ Info error: {e}")

def main():
    """메인 실행 함수"""
    
    while True:
        print_banner()
        
        try:
            choice = input("\n선택하세요 (0-6): ").strip()
            
            if choice == "0":
                print("👋 종료합니다.")
                break
            
            elif choice == "1":
                run_api_server()
            
            elif choice == "2":
                run_inference()
            
            elif choice == "3":
                run_test_model()
            
            elif choice == "4":
                run_interactive()
            
            elif choice == "5":
                run_cli()
            
            elif choice == "6":
                show_model_info()
            
            else:
                print("❌ 잘못된 선택입니다. 0-6 중에서 선택하세요.")
            
            if choice != "0":
                input("\n아무 키나 누르면 메뉴로 돌아갑니다...")
                print("\n" + "="*50)
        
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            input("아무 키나 누르면 계속...")

if __name__ == "__main__":
    main()