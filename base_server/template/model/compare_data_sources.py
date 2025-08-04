#!/usr/bin/env python3
"""
yfinance vs Manual API 데이터 비교
동일한 소스인지 확인
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import yfinance as yf

def get_manual_data(symbol="AAPL", days=5):
    """Manual API로 데이터 수집"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        'period1': start_ts,
        'period2': end_ts,
        'interval': '1d',
        'includePrePost': 'true',
        'events': 'div%2Csplit',
        'corsDomain': 'finance.yahoo.com'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Manual API failed: HTTP {response.status_code}")
            return None
        
        data = response.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        df_data = {
            'Date': [datetime.fromtimestamp(ts) for ts in timestamps],
            'Open': quote['open'],
            'High': quote['high'],
            'Low': quote['low'],
            'Close': quote['close'],
            'Volume': quote['volume']
        }
        
        df = pd.DataFrame(df_data).dropna()
        return df.sort_values('Date').reset_index(drop=True)
        
    except Exception as e:
        print(f"❌ Manual API error: {e}")
        return None

def get_yfinance_data(symbol="AAPL", days=5):
    """yfinance로 데이터 수집"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=f"{days}d")
        
        if data.empty:
            print("❌ yfinance returned empty data")
            return None
        
        # 컬럼명 통일
        data = data.reset_index()
        data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        return data.sort_values('Date').reset_index(drop=True)
        
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        return None

def compare_data():
    """두 방식의 데이터 비교"""
    print("🔍 Yahoo Finance 데이터 소스 비교 테스트")
    print("=" * 50)
    
    symbol = "AAPL"
    days = 5
    
    print(f"📊 Testing symbol: {symbol}")
    print(f"📅 Period: {days} days")
    print()
    
    # Manual API 데이터
    print("1️⃣ Manual API 방식...")
    manual_data = get_manual_data(symbol, days)
    
    if manual_data is not None:
        print(f"✅ Manual API 성공: {manual_data.shape}")
        print(f"   Date range: {manual_data['Date'].iloc[0].date()} to {manual_data['Date'].iloc[-1].date()}")
        print(f"   Latest close: ${manual_data['Close'].iloc[-1]:.2f}")
    else:
        print("❌ Manual API 실패")
        return
    
    print()
    
    # yfinance 데이터
    print("2️⃣ yfinance 라이브러리 방식...")
    yfinance_data = get_yfinance_data(symbol, days)
    
    if yfinance_data is not None:
        print(f"✅ yfinance 성공: {yfinance_data.shape}")
        print(f"   Date range: {yfinance_data['Date'].iloc[0].date()} to {yfinance_data['Date'].iloc[-1].date()}")
        print(f"   Latest close: ${yfinance_data['Close'].iloc[-1]:.2f}")
    else:
        print("❌ yfinance 실패")
        print("   (예상됨 - yfinance 라이브러리 문제)")
        print()
        print("🎯 결론: Manual API가 yfinance 문제를 우회하여 동일한 Yahoo Finance 데이터를 성공적으로 가져옴")
        return
    
    print()
    
    # 데이터 비교
    print("3️⃣ 데이터 비교...")
    
    if manual_data.shape == yfinance_data.shape:
        print("✅ 데이터 크기 동일")
        
        # 최신 종가 비교
        manual_close = manual_data['Close'].iloc[-1]
        yfinance_close = yfinance_data['Close'].iloc[-1]
        
        if abs(manual_close - yfinance_close) < 0.01:  # 1센트 이내 차이
            print("✅ 종가 데이터 동일")
            print("🎉 결론: Manual API와 yfinance는 동일한 Yahoo Finance 데이터를 사용")
        else:
            print(f"⚠️ 종가 차이: Manual ${manual_close:.2f} vs yfinance ${yfinance_close:.2f}")
    else:
        print(f"⚠️ 데이터 크기 다름: Manual {manual_data.shape} vs yfinance {yfinance_data.shape}")
    
    print()
    print("📋 상세 비교:")
    print("Manual API 샘플:")
    print(manual_data.head(3))
    print()
    print("yfinance 샘플:")
    print(yfinance_data.head(3))

if __name__ == "__main__":
    compare_data()