import yfinance as yf
import pandas as pd
import hashlib
import json
import os
import schedule
import time
from datetime import datetime

# --- 설정 ---
# 파일 경로 설정
HASH_FILE = "news_hashes.json"      # 해시값 저장 파일
YAHOO_NEWS_FILE = "yahoo_finance_news.json"  # Yahoo Finance 뉴스 파일 (지속적으로 업데이트)

class NewsDeduplicator:
    """뉴스 중복 제거 클래스"""
    
    def __init__(self):
        """초기화: 기존 해시값 및 뉴스 데이터 로드"""
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.hash_file_path = os.path.join(self.current_dir, HASH_FILE)
        self.yahoo_news_file_path = os.path.join(self.current_dir, YAHOO_NEWS_FILE)
        
        # 기존 해시값 로드
        self.existing_hashes = self._load_existing_hashes()
        print(f"📁 기존 해시값 {len(self.existing_hashes)}개 로드 완료")
        
        # 기존 뉴스 데이터 로드 (yahoo_finance_news.json에서)
        self.existing_news = self._load_existing_news()
        print(f"📁 기존 뉴스 {len(self.existing_news)}개 로드 완료")
    
    def _load_existing_hashes(self):
        """기존 해시값들을 JSON 파일에서 로드"""
        try:
            if os.path.exists(self.hash_file_path):
                with open(self.hash_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('hashes', []))
            return set()
        except Exception as e:
            print(f"⚠️ 해시 파일 로드 중 오류: {e}")
            return set()
    
    def _load_existing_news(self):
        """기존 뉴스 데이터를 yahoo_finance_news.json 파일에서 로드"""
        try:
            if os.path.exists(self.yahoo_news_file_path):
                with open(self.yahoo_news_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('articles', [])
            return []
        except Exception as e:
            print(f"⚠️ 뉴스 파일 로드 중 오류: {e}")
            return []
    

    def _collect_latest_news(self):
        """yfinance를 사용하여 최신 뉴스 직접 수집"""
        print("📡 최신 뉴스 수집 중...")
        
        # Ticker 리스트
        tickers = [ # 대형 테크주 (FAANG+)
         "AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "ORCL", "CRM", "ADBE", "INTC", "AMD", "CSCO", "IBM",
    
    # 반도체
    "QCOM", "AVGO", "TXN", "MU", "AMAT", "LRCX", "ADI", "MCHP", "KLAC", "MRVL",
    
    # 주요 ETF들
    "SPY", "QQQ", "VTI", "IWM", "VEA", "VWO", "EFA", "GLD", "SLV", "TLT", "HYG", "LQD", "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLU", "XLRE",
    
    # 금융 (은행, 보험, 핀테크)
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BRK-B", "V", "MA", "PYPL", "SQ", "AXP", "USB", "PNC", "TFC", "COF",
    
    # 헬스케어/제약
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD", "BIIB", "CVS", "CI", "ANTM", "HUM",
    
    # 소비재 (필수/임의)
    "PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "COST", "DIS", "BABA", "AMZN", "EBAY", "ETSY",
    
    # 에너지
    "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "KMI", "OKE", "WMB",
    
    # 산업재/항공
    "BA", "CAT", "DE", "GE", "HON", "MMM", "UPS", "FDX", "LMT", "RTX", "AAL", "DAL", "UAL", "LUV",
    
    # 통신
    "VZ", "T", "TMUS", "CHTR", "CMCSA", "DISH",
    
    # 자동차
    "F", "GM", "RIVN", "LCID", "NIO", "XPEV", "LI",
    
    # 부동산 REITs
    "AMT", "PLD", "CCI", "EQIX", "SPG", "O", "WELL", "EXR", "AVB", "EQR",
    
    # 유틸리티
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "SRE", "PEG", "ED",
    
    # 엔터테인먼트/미디어
    "DIS", "NFLX", "ROKU", "SPOT", "WBD", "PARA", "FOX", "FOXA",
    
    # 중국 ADR
    "BABA", "JD", "PDD", "BIDU", "BILI", "DIDI", "TME",
    
    # 암호화폐 관련
    "COIN", "MSTR", "RIOT", "MARA", "BITB", "IBIT",
    
    # 기타 주요 기업들
    "TSLA", "UBER", "LYFT", "SNAP", "TWTR", "ZOOM", "DOCU", "PLTR", "SNOW", "CRM", "WORK", "ZM", "PTON", "ARKK", "ARKG", "ARKW"
    ]         
        new_news_list = []
        
        for ticker_symbol in tickers:
            try:
                print(f"  -> {ticker_symbol} 뉴스 수집 중...")
                
                # yfinance를 통해 뉴스 수집
                ticker = yf.Ticker(ticker_symbol)
                news_list = ticker.news
                
                if not news_list:
                    print(f"    ℹ️ {ticker_symbol}: 뉴스 없음")
                    continue
                
                # 뉴스 데이터 파싱
                parsed_count = 0
                for news_item in news_list:
                    try:
                        if not news_item or not isinstance(news_item, dict):
                            continue
                        
                        content = news_item.get('content', {})
                        if not content or not isinstance(content, dict):
                            continue
                        
                        # 제목 추출
                        title = content.get('title', '')
                        if not title or title == 'N/A':
                            continue
                        
                        # 기타 정보 추출
                        provider = content.get('provider', {})
                        if not isinstance(provider, dict):
                            provider = {}
                        
                        click_url = content.get('clickThroughUrl', {})
                        if not isinstance(click_url, dict):
                            click_url = {}
                        
                        # 날짜 파싱
                        pub_date_str = content.get('pubDate', '')
                        if pub_date_str:
                            try:
                                pub_date = pd.to_datetime(pub_date_str)
                                if pub_date.tz is None:
                                    pub_date = pub_date.tz_localize('UTC')
                                formatted_date = pub_date.strftime('%Y-%m-%d %H:%M')
                            except:
                                formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                        else:
                            formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        # 뉴스 데이터 구성
                        news_data = {
                            '날짜': formatted_date,
                            '티커': ticker_symbol,
                            '제목': title,
                            '언론사': provider.get('displayName', 'N/A'),
                            '링크': click_url.get('url', 'N/A')
                        }
                        
                        new_news_list.append(news_data)
                        parsed_count += 1
                        
                    except Exception as e:
                        print(f"    ⚠️ 뉴스 파싱 오류: {e}")
                        continue
                
                print(f"    ✅ {ticker_symbol}: {parsed_count}개 뉴스 수집")
                time.sleep(0.5)  # API 호출 간격 조절
                
            except Exception as e:
                print(f"    ❌ {ticker_symbol} 오류: {e}")
                continue
        
        print(f"✅ 총 {len(new_news_list)}개의 최신 뉴스 수집 완료")
        return new_news_list
    
    def _generate_hash(self, title):
        """뉴스 제목을 MD5 해시값으로 변환"""
        # 1. 제목을 UTF-8로 인코딩한 후 MD5 해시 생성
        return hashlib.md5(title.encode('utf-8')).hexdigest()
    
    def _save_hashes(self):
        """해시값들을 JSON 파일에 저장"""
        try:
            hash_data = {
                'hashes': list(self.existing_hashes),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(self.existing_hashes)
            }
            
            with open(self.hash_file_path, 'w', encoding='utf-8') as f:
                json.dump(hash_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 해시값 {len(self.existing_hashes)}개 저장 완료")
            
        except Exception as e:
            print(f"❌ 해시 파일 저장 중 오류: {e}")
    
    def _save_news_to_yahoo_file(self):
        """중복 제거된 뉴스를 yahoo_finance_news.json 파일에 저장"""
        try:
            # 4. 최신순으로 정렬 (날짜 기준)
            sorted_news = sorted(self.existing_news, 
                                key=lambda x: x.get('날짜', ''), 
                                reverse=True)
            
            # 기존 yahoo_finance_news.json 구조를 유지하면서 업데이트
            news_data = {
                'articles': sorted_news,
                'metadata': {
                    'total_count': len(sorted_news),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'unique_hashes_count': len(self.existing_hashes),
                    'collection_method': 'Scheduled with duplicate removal'
                }
            }
            
            with open(self.yahoo_news_file_path, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 yahoo_finance_news.json 파일에 {len(sorted_news)}개 뉴스 저장 완료")
            
        except Exception as e:
            print(f"❌ 뉴스 파일 저장 중 오류: {e}")
    
    def collect_and_process_news(self):
        """최신 뉴스를 직접 수집하여 중복 제거 처리"""
        print("🔍 뉴스 수집 시작...")
        
        try:
            # 1. 직접 yfinance를 사용하여 최신 뉴스 수집
            new_news_list = self._collect_latest_news()
            
            if not new_news_list:
                print("ℹ️ 새로 수집된 뉴스가 없습니다.")
                return 0
            
            print(f"📊 새로 수집된 뉴스 {len(new_news_list)}개 확인")
            
            # 2. 중복 제거 처리
            return self._process_duplicate_removal(new_news_list)
            
        except Exception as e:
            print(f"❌ 뉴스 수집 중 오류: {e}")
            return 0
    
    def _process_duplicate_removal(self, news_list):
        """뉴스 중복 제거 처리"""
        print("🔄 뉴스 중복 제거 처리 시작...")
        
        new_count = 0
        duplicate_count = 0
        
        # 각 뉴스에 대해 중복 검사
        for news in news_list:
            title = news.get('제목', '')
            if not title or title == 'N/A':
                continue
            
            # 1. 뉴스 제목을 MD5 해시값으로 변환
            title_hash = self._generate_hash(title)
            
            # 2. 기존 해시값과 비교하여 중복 검사
            if title_hash in self.existing_hashes:
                duplicate_count += 1
                print(f"    🔄 중복 뉴스 제외: {title[:50]}...")
            else:
                # 3. 중복이 아닌 경우 저장
                self.existing_hashes.add(title_hash)
                # 수집 시간 정보 추가
                news_with_collection_time = news.copy()
                news_with_collection_time['수집시간'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.existing_news.append(news_with_collection_time)
                new_count += 1
                print(f"    ✅ 새로운 뉴스 추가: {title[:50]}...")
        
        print(f"📈 처리 결과: 새로운 뉴스 {new_count}개, 중복 {duplicate_count}개")
        
        # 4. 파일에 저장
        if new_count > 0:
            self._save_hashes()
            self._save_news_to_yahoo_file()
            print(f"💾 {new_count}개의 새로운 뉴스가 yahoo_finance_news.json에 저장되었습니다!")
        else:
            print("ℹ️ 저장할 새로운 뉴스가 없습니다.")
        
        return new_count

def run_news_collection():
    """뉴스 수집 작업 실행"""
    print("=" * 70)
    print(f"🚀 뉴스 수집 작업 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # 뉴스 중복 제거 객체 생성
        deduplicator = NewsDeduplicator()
        
        # 뉴스 수집 및 중복 제거 처리
        new_count = deduplicator.collect_and_process_news()
        
        if new_count > 0:
            print(f"🎉 작업 완료: {new_count}개의 새로운 뉴스 추가")
        else:
            print("ℹ️ 새로운 뉴스가 없습니다.")
            
    except Exception as e:
        print(f"❌ 작업 중 오류 발생: {e}")
    
    print("=" * 70)
    print(f"✅ 뉴스 수집 작업 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

def main():
    """메인 함수: 스케줄러 설정 및 실행"""
    print("📰 뉴스 수집 스케줄러 시작")
    print("⏰ 1분마다 뉴스 수집 작업을 수행합니다.")
    print("🛑 중단하려면 Ctrl+C를 눌러주세요.")
    print()
    
    # 5. 스케줄 설정: 1분마다 뉴스 수집 작업 실행
    schedule.every(1).minutes.do(run_news_collection)
    
    # 시작 시 즉시 한 번 실행
    print("🔄 초기 뉴스 수집 작업 실행...")
    run_news_collection()
    
    # 6. 스케줄러 실행 (무한 루프)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            print("🛑 스케줄러가 중단되었습니다.")
            print("👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 스케줄러 오류: {e}")
            time.sleep(5)  # 오류 발생 시 5초 대기 후 재시도

if __name__ == "__main__":
    main() 