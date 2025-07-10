import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import re
from urllib.parse import urljoin

# --- 설정 ---
BASE_URL = "https://www.investing.com/news"
OUTPUT_FILE = "investing_news.csv"
START_DATE = datetime(2025, 7, 3)
END_DATE = datetime(2025, 7, 9, 23, 59, 59)
MAX_PAGES = 10  # 최대 페이지 수 (일주일치 뉴스를 위해)
# --- 설정 끝 ---

def get_headers():
    """적절한 헤더를 반환합니다."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def parse_date(date_str):
    """다양한 날짜 형식을 파싱합니다."""
    try:
        # "Jan 09, 2025" 형식
        if ',' in date_str:
            return datetime.strptime(date_str.strip(), "%b %d, %Y")
        
        # "2 hours ago", "1 day ago" 등의 형식
        if 'ago' in date_str.lower():
            now = datetime.now()
            if 'hour' in date_str:
                match = re.search(r'(\d+)', date_str)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)
            elif 'day' in date_str:
                match = re.search(r'(\d+)', date_str)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)
            elif 'minute' in date_str:
                match = re.search(r'(\d+)', date_str)
                if match:
                    minutes = int(match.group(1))
                    return now - timedelta(minutes=minutes)
        
        # 기본적으로 현재 시간 반환
        return datetime.now()
        
    except Exception as e:
        print(f"날짜 파싱 오류: {date_str} - {e}")
        return datetime.now()

def scrape_investing_news():
    """investing.com에서 뉴스를 크롤링합니다."""
    
    session = requests.Session()
    session.headers.update(get_headers())
    
    all_news = []
    page = 1
    
    print("✅ investing.com 뉴스 크롤링을 시작합니다...")
    print(f"수집 기간: {START_DATE.date()} ~ {END_DATE.date()}")
    print("-" * 50)
    
    while page <= MAX_PAGES:
        print(f"-> 페이지 {page} 크롤링 중...")
        
        try:
            # 페이지 URL 구성
            if page == 1:
                url = BASE_URL
            else:
                url = f"{BASE_URL}/{page}"
            
            # 페이지 요청
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 아티클 찾기 (investing.com의 구조에 맞게)
            news_items = soup.find_all('article', class_='js-article-item') or \
                        soup.find_all('div', class_='largeTitle') or \
                        soup.find_all('div', class_='textDiv')
            
            if not news_items:
                # 다른 선택자 시도
                news_items = soup.find_all('a', href=re.compile(r'/news/'))
                
            if not news_items:
                print(f"  ⚠️ 페이지 {page}에서 뉴스를 찾을 수 없습니다.")
                break
            
            page_news_count = 0
            old_news_count = 0
            
            for item in news_items:
                try:
                    # 제목 추출
                    title_elem = item.find('a') or item
                    if title_elem and title_elem.get('title'):
                        title = title_elem.get('title').strip()
                    elif title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        continue
                    
                    # 링크 추출
                    link_elem = item.find('a') or item
                    if link_elem and link_elem.get('href'):
                        link = urljoin(BASE_URL, link_elem.get('href'))
                    else:
                        continue
                    
                    # 날짜 추출 (다양한 방법 시도)
                    date_elem = item.find('time') or \
                               item.find('span', class_='date') or \
                               item.find('div', class_='date')
                    
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                        news_date = parse_date(date_str)
                    else:
                        news_date = datetime.now()  # 기본값
                    
                    # 날짜 필터링
                    if news_date < START_DATE:
                        old_news_count += 1
                        continue
                    elif news_date > END_DATE:
                        continue
                    
                    # 뉴스 데이터 저장
                    news_data = {
                        'date': news_date,
                        'title': title,
                        'source': 'Investing.com',
                        'link': link,
                        'page': page
                    }
                    
                    all_news.append(news_data)
                    page_news_count += 1
                    
                except Exception as e:
                    print(f"  ⚠️ 뉴스 파싱 중 오류: {e}")
                    continue
            
            print(f"  ✅ 페이지 {page}: {page_news_count}개 뉴스 수집 완료")
            
            # 오래된 뉴스가 많으면 중단
            if old_news_count > page_news_count * 2:
                print(f"  ℹ️ 오래된 뉴스가 많아 크롤링을 중단합니다.")
                break
            
            page += 1
            time.sleep(2)  # 서버 부담 방지
            
        except requests.RequestException as e:
            print(f"  ❌ 페이지 {page} 요청 오류: {e}")
            break
        except Exception as e:
            print(f"  ❌ 페이지 {page} 처리 오류: {e}")
            break
    
    if not all_news:
        print("❌ 수집된 뉴스가 없습니다.")
        return
    
    # DataFrame으로 변환 및 저장
    df = pd.DataFrame(all_news)
    df = df.drop_duplicates(subset=['title', 'link'])  # 중복 제거
    df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M')
    df = df.sort_values('date', ascending=False)
    
    # 현재 스크립트가 있는 폴더(crawling)에 저장
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, OUTPUT_FILE)
    
    # 슬래시로 구분하여 저장
    df.to_csv(output_path, index=False, encoding='utf-8-sig', sep='/')
    
    print("-" * 50)
    print(f"✅ 총 {len(df)}개의 뉴스를 성공적으로 저장했습니다!")
    print(f"   -> 파일 위치: {output_path}")
    print(f"   -> 날짜 범위: {df['date'].min()} ~ {df['date'].max()}")

def test_connection():
    """investing.com 연결 테스트"""
    try:
        response = requests.get(BASE_URL, headers=get_headers(), timeout=10)
        print(f"연결 테스트: HTTP {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            print(f"페이지 제목: {title.get_text() if title else 'N/A'}")
            return True
        return False
    except Exception as e:
        print(f"연결 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    if test_connection():
        scrape_investing_news()
    else:
        print("❌ investing.com에 연결할 수 없습니다.") 