#!/usr/bin/env python3
"""
명령줄 인터페이스로 모델 예측
간편한 CLI 도구
"""

import argparse
import sys
from test_trained_model import load_trained_model, test_single_prediction, test_multiple_predictions

def predict_single(symbol, days=60, verbose=False):
    """단일 종목 예측"""
    
    if verbose:
        print(f"🔮 Predicting {symbol} using {days} days of historical data...")
    
    result = test_single_prediction(symbol, days)
    
    if result is None:
        print(f"❌ Failed to predict {symbol}")
        return False
    
    current_price = result['current_price']
    predictions = result['predictions']
    
    print(f"\n📊 {symbol} Prediction Results:")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Prediction Period: Next 5 days")
    print("-" * 40)
    
    # 정규화된 예측값 출력 (실제 가격 변환은 스케일러 필요)
    for day in range(5):
        close_norm = predictions[0, day, 0]
        bb_upper_norm = predictions[0, day, 1]
        bb_lower_norm = predictions[0, day, 2]
        
        print(f"Day {day+1}: Close={close_norm:.4f} | BB_Upper={bb_upper_norm:.4f} | BB_Lower={bb_lower_norm:.4f}")
    
    if verbose:
        processed_data = result['processed_data']
        print(f"\n📈 Technical Indicators:")
        print(f"RSI: {processed_data['RSI'].iloc[-1]:.2f}")
        print(f"MA_5: ${processed_data['MA_5'].iloc[-1]:.2f}")
        print(f"MA_20: ${processed_data['MA_20'].iloc[-1]:.2f}")
        print(f"BB_Upper: ${processed_data['BB_Upper'].iloc[-1]:.2f}")
        print(f"BB_Lower: ${processed_data['BB_Lower'].iloc[-1]:.2f}")
    
    return True

def predict_batch(symbols, output_file=None, verbose=False):
    """배치 예측"""
    
    if verbose:
        print(f"🔮 Batch predicting {len(symbols)} symbols...")
    
    results = test_multiple_predictions(symbols)
    
    # 결과 출력
    print(f"\n📊 Batch Prediction Results:")
    print("-" * 60)
    print(f"{'Symbol':<8} {'Price':<10} {'Status':<10} {'Info'}")
    print("-" * 60)
    
    for symbol, data in results.items():
        if data.get('success'):
            price = f"${data['current_price']:.2f}"
            status = "✅ Success"
            info = "Predicted"
        else:
            price = "N/A"
            status = "❌ Failed"
            info = data.get('error', 'Unknown error')[:30]
        
        print(f"{symbol:<8} {price:<10} {status:<10} {info}")
    
    # 파일 저장
    if output_file:
        try:
            import json
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to {output_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    return results

def show_model_info():
    """모델 정보 출력"""
    
    try:
        model, preprocessor = load_trained_model()
        
        print("🤖 Model Information:")
        print("-" * 40)
        print(f"Model Type: PyTorch LSTM")
        print(f"Sequence Length: 60 days")
        print(f"Prediction Length: 5 days")
        print(f"Input Features: 18")
        print(f"Output Targets: 3 (Close, BB_Upper, BB_Lower)")
        print(f"Architecture: Multi-layer LSTM with Attention")
        
        # 모델 파라미터 수 계산 (근사)
        total_params = sum(p.numel() for p in model.model.parameters())
        print(f"Total Parameters: {total_params:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load model info: {e}")
        return False

def main():
    """메인 CLI 함수"""
    
    parser = argparse.ArgumentParser(
        description="Stock Price Prediction CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predict_cli.py AAPL                          # Predict AAPL
  python predict_cli.py AAPL --days 90 --verbose     # Detailed AAPL prediction
  python predict_cli.py --batch AAPL MSFT GOOGL      # Batch prediction
  python predict_cli.py --info                        # Show model info
        """
    )
    
    # 위치 인수
    parser.add_argument('symbol', nargs='?', help='Stock symbol to predict (e.g., AAPL)')
    
    # 옵션 인수
    parser.add_argument('--batch', nargs='+', help='Batch predict multiple symbols')
    parser.add_argument('--days', type=int, default=60, help='Days of historical data to use (default: 60)')
    parser.add_argument('--output', '-o', help='Output file for batch results (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--info', action='store_true', help='Show model information')
    
    args = parser.parse_args()
    
    # 인수 검증
    if not any([args.symbol, args.batch, args.info]):
        parser.print_help()
        sys.exit(1)
    
    # 모델 정보 출력
    if args.info:
        show_model_info()
        return
    
    # 배치 예측
    if args.batch:
        predict_batch(args.batch, args.output, args.verbose)
        return
    
    # 단일 예측
    if args.symbol:
        success = predict_single(args.symbol, args.days, args.verbose)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()