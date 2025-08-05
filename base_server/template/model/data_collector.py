"""
미국 주식 데이터 수집 모듈
yfinance 라이브러리 문제로 인해 Yahoo Finance API를 직접 호출
Manual API 방식으로 거래량 상위 100개 종목의 3년치 OHLCV 데이터 수집
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import time
import requests
import random
import json

class StockDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Manual API 방식용 헤더 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://finance.yahoo.com/',
            'Origin': 'https://finance.yahoo.com',
        }
        
        # Yahoo Finance API URLs
        self.base_urls = [
            "https://query1.finance.yahoo.com/v8/finance/chart",
            "https://query2.finance.yahoo.com/v8/finance/chart",
        ]
        
        # 요청 설정
        self.request_delay = (2.0, 4.0)
        self.retry_attempts = 3
        self.timeout = 30
        
        # 미국 주식 거래량 상위 100개 종목 (예시 - 실제로는 동적으로 가져와야 함)
        self.top_100_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", "AMD", "INTC",
            "ADBE", "CRM", "PYPL", "AVGO", "TXN", "QCOM", "COST", "SBUX", "INTU", "AMGN",
            "GILD", "MDLZ", "BKNG", "ADP", "VRTX", "FISV", "CSX", "REGN", "ATVI", "MELI",
            "ASML", "MU", "AMAT", "LRCX", "ADI", "MCHP", "KLAC", "SNPS", "CDNS", "PDD",
            "ORLY", "CTAS", "FAST", "PAYX", "VRSK", "DXCM", "BIIB", "ILMN", "WDAY", "EXC",
            "EA", "CTSH", "DLTR", "KDP", "CRWD", "ZM", "TEAM", "OKTA", "DDOG", "SNOW",
            "NET", "TWLO", "ZS", "PLTR", "U", "RBLX", "PATH", "COIN", "HOOD", "AFRM",
            "SQ", "SHOP", "UBER", "LYFT", "DASH", "ABNB", "PINS", "SNAP", "SPOT", "ZG",
            "ETSY", "ROKU", "NTNX", "FSLY", "ESTC", "MDB", "VEEV", "CZR", "TTWO", "WDC",
            "STX", "SWKS", "MRVL", "ON", "MPWR", "ENTG", "TER", "ALGN", "IDXX", "ANSS"
        ]
    
    def _add_request_delay(self):
        """요청 간 랜덤 지연시간 추가"""
        delay = random.uniform(*self.request_delay)
        time.sleep(delay)
    
    def _convert_period_to_timestamps(self, period: str) -> Tuple[int, int]:
        """
        period 문자열을 timestamp로 변환
        
        Args:
            period: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "3y"
            
        Returns:
            (start_timestamp, end_timestamp)
        """
        end_time = datetime.now()
        
        if period == "1d":
            start_time = end_time - timedelta(days=1)
        elif period == "5d":
            start_time = end_time - timedelta(days=5)
        elif period == "1mo":
            start_time = end_time - timedelta(days=30)
        elif period == "3mo":
            start_time = end_time - timedelta(days=90)
        elif period == "6mo":
            start_time = end_time - timedelta(days=180)
        elif period == "1y":
            start_time = end_time - timedelta(days=365)
        elif period == "2y":
            start_time = end_time - timedelta(days=730)
        elif period == "3y":
            start_time = end_time - timedelta(days=1095)
        else:
            # 기본값: 1년
            start_time = end_time - timedelta(days=365)
        
        return int(start_time.timestamp()), int(end_time.timestamp())
    
    def get_stock_data(self, symbol: str, period: str = "3y") -> Optional[pd.DataFrame]:
        """
        Manual API를 사용해 주식 데이터 수집
        
        Args:
            symbol: 주식 심볼 (e.g., "AAPL")
            period: 데이터 기간 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "3y")
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        start_ts, end_ts = self._convert_period_to_timestamps(period)
        
        for attempt in range(self.retry_attempts):
            try:
                if attempt > 0:
                    self.logger.info(f"Retrying {symbol} (attempt {attempt + 1}/{self.retry_attempts})")
                    time.sleep(random.uniform(3, 7))
                else:
                    self._add_request_delay()
                
                # API URL 순환 사용
                base_url = self.base_urls[attempt % len(self.base_urls)]
                
                # API 호출
                url = f"{base_url}/{symbol}"
                params = {
                    'period1': start_ts,
                    'period2': end_ts,
                    'interval': '1d',
                    'includePrePost': 'true',
                    'events': 'div%2Csplit',
                    'corsDomain': 'finance.yahoo.com'
                }
                
                self.logger.info(f"📡 Calling Manual API: {url}")
                response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
                
                if response.status_code != 200:
                    self.logger.warning(f"HTTP {response.status_code} for {symbol}")
                    continue
                
                # JSON 파싱
                data = response.json()
                
                if 'chart' not in data or 'result' not in data['chart']:
                    self.logger.warning(f"Invalid response structure for {symbol}")
                    continue
                
                results = data['chart']['result']
                if not results:
                    self.logger.warning(f"No results in response for {symbol}")
                    continue
                
                result = results[0]
                
                # 타임스탬프 확인
                if 'timestamp' not in result:
                    self.logger.warning(f"No timestamp data for {symbol}")
                    continue
                
                timestamps = result['timestamp']
                if not timestamps:
                    self.logger.warning(f"Empty timestamp data for {symbol}")
                    continue
                
                # OHLCV 데이터 추출
                indicators = result.get('indicators', {})
                quote = indicators.get('quote', [{}])[0]
                
                # 필수 데이터 확인
                required_fields = ['open', 'high', 'low', 'close', 'volume']
                for field in required_fields:
                    if field not in quote:
                        self.logger.warning(f"Missing {field} data for {symbol}")
                        continue
                
                # DataFrame 생성
                df_data = {
                    'Date': [datetime.fromtimestamp(ts) for ts in timestamps],
                    'Open': quote['open'],
                    'High': quote['high'],
                    'Low': quote['low'],
                    'Close': quote['close'],
                    'Volume': quote['volume'],
                    'Symbol': symbol
                }
                
                df = pd.DataFrame(df_data)
                
                # None 값 제거
                df = df.dropna()
                
                if df.empty:
                    self.logger.warning(f"DataFrame is empty after cleaning for {symbol}")
                    continue
                
                # 날짜 순 정렬
                df = df.sort_values('Date').reset_index(drop=True)
                
                self.logger.info(f"✅ Successfully collected {symbol}: {len(df)} records from {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()}")
                return df
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"🌐 Network error for {symbol}: {str(e)}")
            except json.JSONDecodeError as e:
                self.logger.warning(f"📊 JSON decode error for {symbol}: {str(e)}")
            except Exception as e:
                self.logger.error(f"❌ Unexpected error for {symbol}: {str(e)}")
        
        self.logger.error(f"❌ Failed to collect data for {symbol} after {self.retry_attempts} attempts")
        return None
    
    def get_recent_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        특정 종목의 최근 N일 데이터 수집 (추론용, 재시도 로직 포함)
        
        Args:
            symbol: 주식 심볼
            days: 수집할 일수 (기본 60일)
            
        Returns:
            pandas DataFrame with recent OHLCV data
        """
        for attempt in range(self.retry_attempts):
            try:
                # 요청 전 지연시간 추가
                if attempt > 0:
                    self.logger.info(f"Retrying recent data for {symbol} (attempt {attempt + 1}/{self.retry_attempts})")
                    time.sleep(random.uniform(2, 5))
                else:
                    self._add_request_delay()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days + 10)  # 여유분 추가
                
                # 기본 yfinance 사용 (세션 문제 방지)
                stock = yf.Ticker(symbol)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    self.logger.warning(f"No recent data found for symbol: {symbol}")
                    return None
                
                # 실제 컬럼 구조 확인 및 로그
                self.logger.info(f"Original columns for {symbol}: {list(data.columns)}")
                
                # 최근 N일만 선택
                data = data.tail(days)
                
                # 필요한 컬럼만 선택 (OHLCV)
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # 컬럼이 존재하는지 확인하고 선택
                available_columns = [col for col in required_columns if col in data.columns]
                if len(available_columns) < 5:
                    self.logger.error(f"Missing required columns for {symbol}. Available: {available_columns}")
                    return None
                
                # 필요한 컬럼만 선택
                data = data[available_columns].copy()
                data['Symbol'] = symbol
                data.reset_index(inplace=True)
                
                self.logger.info(f"✅ Successfully collected recent data for {symbol}: {len(data)} records")
                return data
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many requests" in error_msg:
                    self.logger.warning(f"Rate limit hit for recent data {symbol}, attempt {attempt + 1}/{self.retry_attempts}")
                    if attempt == self.retry_attempts - 1:
                        self.logger.error(f"❌ Rate limit exceeded for recent data {symbol} after {self.retry_attempts} attempts")
                        return None
                else:
                    self.logger.error(f"❌ Error collecting recent data for {symbol}: {str(e)}")
                    if attempt == self.retry_attempts - 1:
                        return None
        
        return None
    
    def collect_batch_data(self, symbols: List[str], max_workers: int = 1) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 데이터를 순차적으로 수집 (429 오류 방지)
        
        Args:
            symbols: 수집할 종목 리스트
            max_workers: 사용되지 않음 (순차 처리로 변경)
            
        Returns:
            Dict[symbol, DataFrame]
        """
        results = {}
        
        self.logger.info(f"🔄 Starting sequential collection for {len(symbols)} symbols (429 오류 방지)")
        
        # 병렬 처리 제거 → 순차 처리로 변경 (429 오류 방지)
        for i, symbol in enumerate(symbols):
            self.logger.info(f"📊 Processing {symbol} ({i+1}/{len(symbols)})")
            
            try:
                data = self.get_stock_data(symbol)
                if data is not None:
                    results[symbol] = data
                    self.logger.info(f"✅ Success: {symbol} - Shape: {data.shape}")
                else:
                    self.logger.warning(f"❌ Failed to collect data for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"❌ Exception collecting {symbol}: {str(e)}")
            
            # 각 요청 후 지연시간 추가 (429 오류 방지)
            if i < len(symbols) - 1:  # 마지막이 아니면
                delay = random.uniform(*self.request_delay)
                self.logger.info(f"⏱️ Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
        
        success_rate = len(results) / len(symbols) * 100 if symbols else 0
        self.logger.info(f"🎯 Sequential collection completed: {len(results)}/{len(symbols)} symbols ({success_rate:.1f}% success rate)")
        return results
    
    def collect_top_100_data(self) -> Dict[str, pd.DataFrame]:
        """
        거래량 상위 100개 종목의 3년치 데이터 수집 (Rate Limiting 최적화)
        
        Returns:
            Dict[symbol, DataFrame]
        """
        self.logger.info("🚀 Starting collection of top 100 stocks data with rate limiting protection...")
        
        # 배치별로 수집 (API 제한 고려하여 작은 배치 크기)
        batch_size = 10  # 20 → 10으로 축소
        all_results = {}
        total_batches = (len(self.top_100_symbols) + batch_size - 1) // batch_size
        
        for i in range(0, len(self.top_100_symbols), batch_size):
            batch_num = i // batch_size + 1
            batch_symbols = self.top_100_symbols[i:i+batch_size]
            
            self.logger.info(f"📦 Collecting batch {batch_num}/{total_batches}: {batch_symbols}")
            
            batch_results = self.collect_batch_data(batch_symbols, max_workers=2)  # worker 수도 줄임
            all_results.update(batch_results)
            
            # 배치 간 대기 시간 증가 (Rate Limiting 방지)
            if i + batch_size < len(self.top_100_symbols):  # 마지막 배치가 아니면
                wait_time = random.uniform(3, 7)  # 3-7초 랜덤 대기
                self.logger.info(f"⏳ Waiting {wait_time:.1f} seconds before next batch...")
                time.sleep(wait_time)
        
        success_rate = len(all_results) / len(self.top_100_symbols) * 100
        self.logger.info(f"🎉 Completed data collection: {len(all_results)}/{len(self.top_100_symbols)} symbols ({success_rate:.1f}% success rate)")
        return all_results
    
    def save_data_to_csv(self, data_dict: Dict[str, pd.DataFrame], output_dir: str = "data"):
        """
        수집된 데이터를 CSV 파일로 저장
        
        Args:
            data_dict: 종목별 데이터 딕셔너리
            output_dir: 저장 디렉토리
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 전체 데이터를 하나의 파일로 저장
        all_data = []
        for symbol, df in data_dict.items():
            all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            output_file = os.path.join(output_dir, "stock_data_3y.csv")
            combined_df.to_csv(output_file, index=False)
            self.logger.info(f"Saved combined data to {output_file}: {len(combined_df)} records")
            
            # 각 종목별로도 저장
            for symbol, df in data_dict.items():
                symbol_file = os.path.join(output_dir, f"{symbol}_3y.csv")
                df.to_csv(symbol_file, index=False)
        
        self.logger.info(f"Data saved to {output_dir} directory")


def quick_column_test():
    """빠른 컬럼 구조 확인 테스트"""
    import yfinance as yf
    
    print("🔍 Quick column structure test...")
    
    try:
        # yfinance 기본 동작 사용 (세션 설정 없음)
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="5d")
        
        print(f"✅ Data shape: {data.shape}")
        print(f"✅ Columns: {list(data.columns)}")
        print(f"✅ Index: {data.index.name}")
        print("✅ Sample data:")
        print(data.head(2))
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        print("🔧 Trying to install curl_cffi...")
        
        # curl_cffi 설치 시도
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi"])
            print("✅ curl_cffi installed, retrying...")
            
            # 재시도
            ticker = yf.Ticker("AAPL")
            data = ticker.history(period="5d")
            
            print(f"✅ Data shape: {data.shape}")
            print(f"✅ Columns: {list(data.columns)}")
            return True
            
        except Exception as e2:
            print(f"❌ Still failed after curl_cffi install: {e2}")
            return False

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 빠른 컬럼 테스트 먼저
    if not quick_column_test():
        print("❌ Column test failed, exiting...")
        exit(1)
    
    print("\n" + "="*50)
    
    # 데이터 수집기 초기화
    collector = StockDataCollector()
    
    print("🧪 Testing data collection with rate limiting protection...")
    
    # 테스트용 소수 종목 먼저 시도
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"Testing with symbols: {test_symbols}")
    
    # 단일 종목 테스트
    print("\n1️⃣ Single symbol test:")
    test_data = collector.get_recent_data("AAPL", 10)
    if test_data is not None:
        print(f"✅ Single test passed: {len(test_data)} records for AAPL")
        print("Data columns:", list(test_data.columns))
        print(test_data.head(3))
    else:
        print("❌ Single test failed")
        exit(1)
    
    # 소규모 배치 테스트
    print(f"\n2️⃣ Small batch test:")
    test_batch_data = collector.collect_batch_data(test_symbols)
    if test_batch_data:
        print(f"✅ Batch test passed: {len(test_batch_data)} symbols collected")
        for symbol, df in test_batch_data.items():
            print(f"  - {symbol}: {len(df)} records")
    else:
        print("❌ Batch test failed")
        exit(1)
    
    # 사용자 선택
    print(f"\n3️⃣ Options:")
    print("A. Collect all top 100 stocks (will take 30-60 minutes)")
    print("B. Collect test data only and proceed to next step")
    print("C. Exit")
    
    choice = input("Choose option (A/B/C): ").upper()
    
    if choice == "A":
        print("🚀 Starting full data collection...")
        data = collector.collect_top_100_data()
        collector.save_data_to_csv(data)
        print(f"✅ Data collection completed for {len(data)} symbols")
    elif choice == "B":
        print("📊 Saving test data...")
        collector.save_data_to_csv(test_batch_data)
        print("✅ Test data saved. You can now proceed to model training!")
    else:
        print("👋 Exiting...")
        exit(0)