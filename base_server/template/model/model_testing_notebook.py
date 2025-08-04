#!/usr/bin/env python3
"""
Jupyter 노트북 스타일 모델 테스트
Interactive한 모델 분석 및 시각화
"""

# 필요한 라이브러리 임포트
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from test_trained_model import load_trained_model, test_single_prediction
from data_collector import StockDataCollector

def interactive_prediction_analysis(symbol="AAPL"):
    """인터랙티브 예측 분석"""
    
    print(f"📊 {symbol} 상세 분석")
    print("="*50)
    
    # 모델 테스트
    result = test_single_prediction(symbol)
    if result is None:
        return
    
    # 현재 데이터
    processed_data = result['processed_data']
    predictions = result['predictions']
    current_price = result['current_price']
    
    print(f"\n💰 현재 정보:")
    print(f"  현재 종가: ${current_price:.2f}")
    print(f"  MA_5: ${processed_data['MA_5'].iloc[-1]:.2f}")
    print(f"  MA_20: ${processed_data['MA_20'].iloc[-1]:.2f}")
    print(f"  RSI: {processed_data['RSI'].iloc[-1]:.2f}")
    print(f"  BB_Upper: ${processed_data['BB_Upper'].iloc[-1]:.2f}")
    print(f"  BB_Lower: ${processed_data['BB_Lower'].iloc[-1]:.2f}")
    
    # 예측 결과 시각화
    plt.figure(figsize=(15, 10))
    
    # 1. 주가 차트
    plt.subplot(2, 2, 1)
    recent_dates = processed_data['Date'].tail(30)
    recent_closes = processed_data['Close'].tail(30)
    
    plt.plot(recent_dates, recent_closes, 'b-', linewidth=2, label='실제 종가')
    plt.plot(recent_dates, processed_data['MA_5'].tail(30), 'g--', alpha=0.7, label='MA_5')
    plt.plot(recent_dates, processed_data['MA_20'].tail(30), 'r--', alpha=0.7, label='MA_20')
    
    plt.title(f'{symbol} 최근 30일 주가')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # 2. 볼린저 밴드
    plt.subplot(2, 2, 2)
    plt.plot(recent_dates, recent_closes, 'b-', linewidth=2, label='종가')
    plt.plot(recent_dates, processed_data['BB_Upper'].tail(30), 'r--', alpha=0.7, label='BB_Upper')
    plt.plot(recent_dates, processed_data['BB_Lower'].tail(30), 'g--', alpha=0.7, label='BB_Lower')
    plt.fill_between(recent_dates, 
                     processed_data['BB_Upper'].tail(30), 
                     processed_data['BB_Lower'].tail(30), 
                     alpha=0.1, color='gray')
    
    plt.title(f'{symbol} 볼린저 밴드')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # 3. RSI
    plt.subplot(2, 2, 3)
    plt.plot(recent_dates, processed_data['RSI'].tail(30), 'purple', linewidth=2)
    plt.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='과매수(70)')
    plt.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='과매도(30)')
    plt.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
    
    plt.title(f'{symbol} RSI')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    
    # 4. 거래량
    plt.subplot(2, 2, 4)
    plt.bar(recent_dates, processed_data['Volume'].tail(30), alpha=0.7, color='orange')
    plt.title(f'{symbol} 거래량')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 예측 결과 분석
    print(f"\n🔮 5일 예측 (정규화된 값):")
    for day in range(5):
        close_pred = predictions[0, day, 0]
        bb_upper_pred = predictions[0, day, 1]
        bb_lower_pred = predictions[0, day, 2]
        
        print(f"  Day {day+1}: Close={close_pred:.4f} | BB_Upper={bb_upper_pred:.4f} | BB_Lower={bb_lower_pred:.4f}")
    
    return result

def compare_multiple_stocks(symbols=["AAPL", "MSFT", "GOOGL", "AMZN"]):
    """여러 종목 비교 분석"""
    
    print(f"📊 {len(symbols)}개 종목 비교 분석")
    print("="*50)
    
    collector = StockDataCollector()
    model, preprocessor = load_trained_model()
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    results = {}
    
    for i, symbol in enumerate(symbols):
        try:
            # 데이터 수집 및 예측
            recent_data = collector.get_recent_data(symbol, 30)
            if recent_data is None:
                continue
                
            processed_data = preprocessor.preprocess_data(recent_data)
            
            # 차트 그리기
            ax = axes[i]
            dates = processed_data['Date']
            closes = processed_data['Close']
            
            ax.plot(dates, closes, 'b-', linewidth=2, label='종가')
            ax.plot(dates, processed_data['MA_5'], 'g--', alpha=0.7, label='MA_5')
            ax.plot(dates, processed_data['MA_20'], 'r--', alpha=0.7, label='MA_20')
            
            current_price = closes.iloc[-1]
            rsi = processed_data['RSI'].iloc[-1]
            
            ax.set_title(f'{symbol}: ${current_price:.2f} (RSI: {rsi:.1f})')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            
            results[symbol] = {
                'current_price': current_price,
                'rsi': rsi,
                'ma_5': processed_data['MA_5'].iloc[-1],
                'ma_20': processed_data['MA_20'].iloc[-1]
            }
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    plt.tight_layout()
    plt.show()
    
    # 비교 결과 출력
    print(f"\n📋 종목 비교 요약:")
    for symbol, data in results.items():
        trend = "상승" if data['ma_5'] > data['ma_20'] else "하락"
        rsi_status = "과매수" if data['rsi'] > 70 else "과매도" if data['rsi'] < 30 else "중립"
        
        print(f"  {symbol}: ${data['current_price']:.2f} | 추세: {trend} | RSI: {rsi_status} ({data['rsi']:.1f})")
    
    return results

def main():
    """메인 실행 함수"""
    print("🚀 Interactive 모델 분석 시작")
    print("="*50)
    
    # 단일 종목 상세 분석
    print("\n1️⃣ AAPL 상세 분석")
    interactive_prediction_analysis("AAPL")
    
    # 다중 종목 비교
    print("\n2️⃣ 주요 종목 비교")
    compare_multiple_stocks(["AAPL", "MSFT", "GOOGL", "AMZN"])
    
    print("\n🎉 분석 완료!")

if __name__ == "__main__":
    main()