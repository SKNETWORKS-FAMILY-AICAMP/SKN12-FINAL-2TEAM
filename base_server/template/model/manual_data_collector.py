#!/usr/bin/env python3
"""
Manual Yahoo Finance API 데이터 수집기
yfinance 라이브러리 대신 requests로 직접 API 호출
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import time
import random
import json

class ManualStockDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # User-Agent 헤더 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://finance.yahoo.com/',
            'Origin': 'https://finance.yahoo.com',
        }
        
        # API 설정
        self.base_urls = [
            "https://query1.finance.yahoo.com/v8/finance/chart",
            "https://query2.finance.yahoo.com/v8/finance/chart",
        ]
        
        # 요청 설정
        self.request_delay = (2.0, 4.0)
        self.retry_attempts = 3
        self.timeout = 30
        
    def _add_request_delay(self):
        """요청 간 지연시간 추가"""
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
                
                self.logger.info(f"📡 Calling API: {url}")
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
    
    def collect_batch_data(self, symbols: List[str], max_workers: int = 1) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 데이터를 순차적으로 수집
        
        Args:
            symbols: 수집할 종목 리스트
            max_workers: 사용되지 않음 (순차 처리)
            
        Returns:
            Dict[symbol, DataFrame]
        """
        results = {}
        
        self.logger.info(f"🔄 Starting manual API collection for {len(symbols)} symbols")
        
        for i, symbol in enumerate(symbols):
            self.logger.info(f"📊 Processing {symbol} ({i+1}/{len(symbols)})")
            
            try:
                data = self.get_stock_data(symbol, period="3y")
                if data is not None:
                    results[symbol] = data
                    self.logger.info(f"✅ Success: {symbol} - Shape: {data.shape}")
                else:
                    self.logger.warning(f"❌ Failed to collect data for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"❌ Exception collecting {symbol}: {str(e)}")
            
            # 각 요청 후 지연시간 추가
            if i < len(symbols) - 1:
                delay = random.uniform(*self.request_delay)
                self.logger.info(f"⏱️ Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
        
        success_rate = len(results) / len(symbols) * 100 if symbols else 0
        self.logger.info(f"🎯 Manual API collection completed: {len(results)}/{len(symbols)} symbols ({success_rate:.1f}% success rate)")
        return results
    
    def get_recent_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        특정 종목의 최근 N일 데이터 수집 (추론용)
        
        Args:
            symbol: 주식 심볼
            days: 수집할 일수 (기본 60일)
            
        Returns:
            pandas DataFrame with recent OHLCV data
        """
        try:
            # 충분한 데이터를 얻기 위해 조금 더 긴 기간으로 수집
            if days <= 30:
                period = "3mo"
            elif days <= 90:
                period = "6mo"
            elif days <= 180:
                period = "1y"
            else:
                period = "3y"
            
            self.logger.info(f"📡 Collecting recent {days} days data for {symbol} (using {period} period)")
            
            # 전체 데이터 수집
            full_data = self.get_stock_data(symbol, period=period)
            
            if full_data is None or len(full_data) == 0:
                self.logger.error(f"❌ Failed to collect data for {symbol}")
                return None
            
            # 최근 N일만 추출
            if len(full_data) >= days:
                recent_data = full_data.tail(days).reset_index(drop=True)
                self.logger.info(f"✅ Successfully collected {len(recent_data)} days for {symbol}")
                self.logger.info(f"📅 Date range: {recent_data['Date'].iloc[0].date()} to {recent_data['Date'].iloc[-1].date()}")
                return recent_data
            else:
                self.logger.warning(f"⚠️ Only {len(full_data)} days available for {symbol} (requested {days})")
                return full_data
                
        except Exception as e:
            self.logger.error(f"❌ Error collecting recent data for {symbol}: {str(e)}")
            return None

def test_manual_collector():
    """Manual collector 테스트"""
    logging.basicConfig(level=logging.INFO)
    
    collector = ManualStockDataCollector()
    
    print("🧪 Testing manual data collector...")
    
    # 단일 종목 테스트
    result = collector.get_stock_data("AAPL", period="1mo")
    
    if result is not None:
        print(f"✅ Success! AAPL data shape: {result.shape}")
        print(f"📊 Columns: {list(result.columns)}")
        print(f"📅 Date range: {result['Date'].iloc[0].date()} to {result['Date'].iloc[-1].date()}")
        print(f"💰 Latest close: ${result['Close'].iloc[-1]:.2f}")
        return True
    else:
        print("❌ Failed to collect AAPL data")
        return False

if __name__ == "__main__":
    test_manual_collector()