#!/usr/bin/env python3
"""
yfinance 디버깅 스크립트
다양한 방법으로 데이터 수집을 시도하여 정확한 원인 파악
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timedelta

def test_basic_yfinance():
    """기본 yfinance 테스트"""
    print("=" * 50)
    print("🧪 Basic yfinance test")
    print("=" * 50)
    
    try:
        ticker = yf.Ticker("AAPL")
        
        # 1. Ticker info 테스트
        print("📊 Testing ticker info...")
        try:
            info = ticker.info
            print(f"✅ Ticker info keys: {len(info.keys()) if info else 0}")
            if info:
                print(f"   - Company: {info.get('longName', 'N/A')}")
                print(f"   - Symbol: {info.get('symbol', 'N/A')}")
        except Exception as e:
            print(f"❌ Ticker info failed: {e}")
        
        # 2. History 테스트 (다양한 period)
        periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "3y"]
        
        for period in periods:
            print(f"\n📈 Testing period: {period}")
            try:
                data = ticker.history(period=period)
                if not data.empty:
                    print(f"✅ {period}: {data.shape} - {data.index[0]} to {data.index[-1]}")
                    return True, period, data  # 성공한 첫 번째 period 반환
                else:
                    print(f"❌ {period}: Empty data")
            except Exception as e:
                print(f"❌ {period}: {e}")
        
        return False, None, None
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False, None, None

def test_manual_api():
    """Yahoo Finance API 직접 호출 테스트"""
    print("\n" + "=" * 50)
    print("🌐 Manual API test")
    print("=" * 50)
    
    # Yahoo Finance API URL 직접 테스트
    urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
        "https://query2.finance.yahoo.com/v8/finance/chart/AAPL",
        "https://finance.yahoo.com/quote/AAPL/history",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    for url in urls:
        print(f"\n🔗 Testing: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.text)}")
            
            if response.status_code == 200:
                # JSON 응답인지 확인
                try:
                    if 'chart' in url:
                        data = response.json()
                        if 'chart' in data and 'result' in data['chart']:
                            print(f"✅ Valid chart data received")
                            return True
                    else:
                        print(f"✅ HTML response received")
                except:
                    print(f"⚠️ Non-JSON response")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    return False

def test_alternative_symbols():
    """다른 심볼들로 테스트"""
    print("\n" + "=" * 50)
    print("📊 Alternative symbols test")
    print("=" * 50)
    
    symbols = ["MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"]
    
    for symbol in symbols:
        print(f"\n🔍 Testing: {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d")
            
            if not data.empty:
                print(f"✅ {symbol}: {data.shape}")
                print(f"   Latest close: ${data['Close'][-1]:.2f}")
                return True, symbol, data
            else:
                print(f"❌ {symbol}: Empty data")
                
        except Exception as e:
            print(f"❌ {symbol}: {e}")
    
    return False, None, None

def test_date_range():
    """날짜 범위 지정 테스트"""
    print("\n" + "=" * 50)
    print("📅 Date range test")
    print("=" * 50)
    
    try:
        ticker = yf.Ticker("AAPL")
        
        # 최근 30일
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        data = ticker.history(start=start_date, end=end_date)
        
        if not data.empty:
            print(f"✅ Date range success: {data.shape}")
            return True, data
        else:
            print(f"❌ Date range failed: Empty data")
            
    except Exception as e:
        print(f"❌ Date range test failed: {e}")
    
    return False, None

def test_without_session():
    """세션 없이 테스트"""
    print("\n" + "=" * 50)
    print("🔄 Test without session")
    print("=" * 50)
    
    try:
        # 세션 없이 순수 yfinance 사용
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="1mo")
        
        if not data.empty:
            print(f"✅ Without session success: {data.shape}")
            return True, data
        else:
            print(f"❌ Without session failed: Empty data")
            
    except Exception as e:
        print(f"❌ Without session test failed: {e}")
    
    return False, None

def main():
    """메인 디버깅 함수"""
    print("🔍 yfinance 디버깅 시작...")
    print(f"🐍 yfinance 버전: {yf.__version__}")
    
    tests = [
        ("Basic yfinance", test_basic_yfinance),
        ("Manual API", test_manual_api),
        ("Alternative symbols", test_alternative_symbols),
        ("Date range", test_date_range),
        ("Without session", test_without_session),
    ]
    
    success_count = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if isinstance(result, tuple):
                success = result[0]
            else:
                success = result
                
            if success:
                print(f"\n✅ {test_name}: SUCCESS")
                success_count += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"\n💥 {test_name}: CRASHED - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 디버깅 결과: {success_count}/{len(tests)} 성공")
    print("=" * 50)
    
    if success_count == 0:
        print("💔 모든 테스트 실패 - yfinance/Yahoo Finance API 문제")
        print("🔧 권장사항:")
        print("   1. yfinance 버전 다운그레이드: pip install yfinance==0.2.18")
        print("   2. 대체 데이터 소스 사용 고려")
        print("   3. VPN 사용 시도")
    elif success_count < len(tests):
        print("⚠️ 일부 테스트 성공 - 특정 조건에서만 작동")
    else:
        print("🎉 모든 테스트 성공 - yfinance 정상 작동")

if __name__ == "__main__":
    main()