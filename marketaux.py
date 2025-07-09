# 이 파일은 marketaux api를 사용합니다.
import os
from dotenv import load_dotenv
import requests
import csv
from datetime import datetime, timedelta
import time
import re
import pandas as pd

# .env 파일에서 환경 변수(API 키)를 불러옴
load_dotenv()
MY_API_TOKEN = os.getenv('MARKETAUX_API_KEY')

def clean_text(text):
    """텍스트 정제 함수"""
    if not text or text.strip() == "":
        return ""
    
    # 줄바꿈 문자를 공백으로 변환
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # 불필요한 문구 제거
    patterns_to_remove = [
        r'\d+\s*min\s+read',  # "5 min read", "10min read" 등
        r'read\s+more',       # "read more"
        r'click\s+here',      # "click here"
        r'learn\s+more',      # "learn more"
        r'see\s+more',        # "see more"
        r'view\s+more',       # "view more"
        r'continue\s+reading', # "continue reading"
        r'full\s+story',      # "full story"
        r'reuters',           # "Reuters" 출처 표시
        r'bloomberg',         # "Bloomberg" 출처 표시
        r'source:.*$',        # "Source: ..." 등
        r'image:.*$',         # "Image: ..." 등
        r'photo:.*$',         # "Photo: ..." 등
        r'video:.*$',         # "Video: ..." 등
        r'\[.*?\]',           # 대괄호 안의 내용
        r'\(.*?\)',           # 소괄호 안의 내용 (너무 길지 않은 경우)
        r'https?://\S+',      # URL 제거
        r'www\.\S+',          # www로 시작하는 URL
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # 연속된 공백을 하나로 압축
    text = re.sub(r'\s+', ' ', text)
    
    # 양 끝 공백 제거
    text = text.strip()
    
    return text

def clean_source_name(source):
    """언론사 이름 정제 함수"""
    if not source or source.strip() == "":
        return ""
    
    source = source.strip().lower()
    
    # 도메인 제거 패턴들
    domain_patterns = [
        r'\.com$', r'\.net$', r'\.org$', r'\.co\.uk$',
        r'\.asia$', r'\.io$', r'\.ca$', r'\.au$',
        r'\.de$', r'\.fr$', r'\.jp$', r'\.kr$',
        r'\.in$', r'\.br$', r'\.mx$', r'\.it$',
        r'\.es$', r'\.nl$', r'\.ch$', r'\.se$',
        r'\.no$', r'\.dk$', r'\.fi$'
    ]
    
    for pattern in domain_patterns:
        source = re.sub(pattern, '', source)
    
    # 서브도메인 제거
    subdomain_patterns = [
        r'^forums\.', r'^www\.', r'^news\.', r'^blog\.',
        r'^media\.', r'^press\.', r'^finance\.', r'^business\.',
        r'^tech\.', r'^sports\.', r'^health\.', r'^science\.'
    ]
    
    for pattern in subdomain_patterns:
        source = re.sub(pattern, '', source)
    
    # 불필요한 문구 제거
    unwanted_phrases = [
        'news', 'media', 'press', 'times', 'daily',
        'herald', 'tribune', 'gazette', 'journal',
        'magazine', 'today', 'now', 'live'
    ]
    
    # 단어 단위로 제거 (전체 이름이 아닌 경우에만)
    source_words = source.split()
    if len(source_words) > 1:
        source_words = [word for word in source_words if word not in unwanted_phrases]
        source = ' '.join(source_words)
    
    # 첫 글자를 대문자로 변환
    source = source.capitalize()
    
    return source

def preprocess_news_data(news_data):
    """뉴스 데이터 전처리 함수"""
    print("🔄 뉴스 데이터 전처리를 시작합니다...")
    
    original_count = len(news_data)
    
    # 1. 텍스트 정제
    for article in news_data:
        article['title'] = clean_text(article.get('title', ''))
        article['snippet'] = clean_text(article.get('snippet', ''))
        article['source'] = clean_source_name(article.get('source', ''))
    
    # 2. 결측치 제거 (제목이나 요약이 비어있는 경우)
    news_data = [article for article in news_data 
                 if article.get('title', '').strip() and 
                    article.get('snippet', '').strip() and 
                    article.get('source', '').strip()]
    
    after_missing_count = len(news_data)
    print(f"  → 결측치 제거: {original_count - after_missing_count}개 제거")
    
    # 3. 중복 제거 (제목과 언론사가 완전히 똑같은 경우)
    seen_combinations = set()
    unique_news = []
    
    for article in news_data:
        combination = (article.get('title', ''), article.get('source', ''))
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            unique_news.append(article)
    
    final_count = len(unique_news)
    print(f"  → 중복 제거: {after_missing_count - final_count}개 제거")
    print(f"  → 최종 데이터 개수: {final_count}개")
    
    return unique_news

def get_weekly_news_and_save_to_csv():
    """Marketaux API를 이용해 일주일치 뉴스를 최대한 많이 수집하여 CSV로 저장"""
    if not MY_API_TOKEN:
        print("❌ API 키를 찾을 수 없습니다. .env 파일을 확인하세요.")
        return

    print("✅ API 키 로드 성공! 지난 7일간의 뉴스 수집을 시작합니다.")

    # 1. 날짜 설정: 정확히 7일 전부터 오늘까지
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)
    
    # 시작일과 종료일을 명확히 설정
    start_date = seven_days_ago.strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    print(f"수집 기간: {start_date} ~ {end_date}")
    print("-" * 50)

    all_news_data = []
    seen_urls = set()  # 중복 제거를 위한 URL 집합
    
    # 2. 여러 방법으로 뉴스 수집하여 데이터 양 확보
    print("📰 방법 1: 전체 뉴스 수집 (모든 국가, 모든 카테고리)")
    collect_news_by_method(all_news_data, seen_urls, start_date, end_date, method=1)
    
    print(f"\n📰 방법 2: 주요 국가별 뉴스 수집 (현재 총 {len(all_news_data)}개)")
    collect_news_by_method(all_news_data, seen_urls, start_date, end_date, method=2)
    
    print(f"\n📰 방법 3: 카테고리별 뉴스 수집 (현재 총 {len(all_news_data)}개)")
    collect_news_by_method(all_news_data, seen_urls, start_date, end_date, method=3)
    
    # 3. 목표 개수 확인
    print(f"\n📊 최종 수집된 뉴스 개수: {len(all_news_data)}개")
    if len(all_news_data) < 500:
        print("⚠️  목표 500개에 미달했습니다. 추가 수집을 시도합니다.")
        collect_additional_news(all_news_data, seen_urls, start_date)
    
    # 4. 데이터 전처리
    print(f"\n🔄 전처리 전 데이터 개수: {len(all_news_data)}개")
    all_news_data = preprocess_news_data(all_news_data)
    
    # 5. CSV 파일로 저장 (요구사항에 맞춰 4개 컬럼만)
    if not all_news_data:
        print("❌ 전처리 후 저장할 뉴스가 없습니다.")
        return

    # 현재 스크립트가 있는 폴더에 저장
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(current_dir, f"주간_해외뉴스_{today.strftime('%Y%m%d')}.csv")

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 요구사항에 맞춰 4개 컬럼만 저장
            writer.writerow(['날짜', '제목', '요약', '언론사'])
            
            for article in all_news_data:
                # 날짜/시간 형식 정리
                try:
                    published_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                except:
                    published_date = article.get('published_at', '')
                
                # 4개 컬럼만 저장 (이미 전처리된 데이터)
                writer.writerow([
                    published_date,
                    article.get('title', ''),
                    article.get('snippet', ''),
                    article.get('source', '')
                ])
        
        print("-" * 50)
        print(f"✅ 총 {len(all_news_data)}개의 전처리된 뉴스를 '{os.path.basename(filename)}' 파일에 저장했습니다.")
        print(f"📁 저장 위치: {filename}")
        print("🔧 전처리 완료: 텍스트 정제, 언론사 이름 정제, 결측치 및 중복 제거 완료")

    except Exception as e:
        print(f"❌ CSV 파일 저장 중 오류 발생: {e}")

def collect_news_by_method(all_news_data, seen_urls, start_date, end_date, method):
    """다양한 방법으로 뉴스 수집"""
    page = 1
    
    while page <= 10:  # 최대 10페이지까지 수집
        print(f"  페이지 {page} 수집 중...")
        
        if method == 1:
            # 방법 1: 전체 뉴스 (필터 최소화)
            url = (f"https://api.marketaux.com/v1/news/all"
                   f"?language=en"
                   f"&published_after={start_date}"
                   f"&published_before={end_date}"
                   f"&limit=100"
                   f"&page={page}"
                   f"&sort=published_desc")
        elif method == 2:
            # 방법 2: 주요 국가별
            countries = ["us", "gb", "ca", "au", "de", "fr", "jp", "in"]
            country = countries[(page - 1) % len(countries)]
            url = (f"https://api.marketaux.com/v1/news/all"
                   f"?countries={country}"
                   f"&language=en"
                   f"&published_after={start_date}"
                   f"&published_before={end_date}"
                   f"&limit=100"
                   f"&page={page}"
                   f"&sort=published_desc")
        else:
            # 방법 3: 카테고리별
            categories = ["general", "business", "technology", "entertainment", "health", "science", "sports"]
            category = categories[(page - 1) % len(categories)]
            url = (f"https://api.marketaux.com/v1/news/all"
                   f"?categories={category}"
                   f"&language=en"
                   f"&published_after={start_date}"
                   f"&published_before={end_date}"
                   f"&limit=100"
                   f"&page={page}"
                   f"&sort=published_desc")
        
        headers = {'Authorization': f'Bearer {MY_API_TOKEN}'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('data', [])
            
            if articles:
                new_articles = []
                for article in articles:
                    url_key = article.get('url', '')
                    if url_key and url_key not in seen_urls:
                        seen_urls.add(url_key)
                        new_articles.append(article)
                
                all_news_data.extend(new_articles)
                print(f"    -> {len(new_articles)}개 새로운 뉴스 발견. 총 {len(all_news_data)}개")
                
                # 이미 충분한 데이터를 수집했다면 중단
                if len(all_news_data) >= 1000:
                    print("    -> 1000개 이상 수집 완료. 다음 방법으로 이동.")
                    break
            else:
                print("    -> 더 이상 뉴스가 없습니다.")
                break
            
            page += 1
            time.sleep(0.3)  # API 요청 간격
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ API 요청 중 오류 발생: {e}")
            if "429" in str(e):
                print("    ⏳ Rate limit 에러. 3초 대기 후 재시도...")
                time.sleep(3)
                continue
            break

def collect_additional_news(all_news_data, seen_urls, start_date):
    """추가 뉴스 수집 (목표 500개 달성을 위해)"""
    print("🔄 추가 뉴스 수집 시작...")
    
    # 더 넓은 날짜 범위로 수집
    extended_start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    
    page = 1
    while len(all_news_data) < 500 and page <= 20:
        print(f"  추가 수집 페이지 {page}...")
        
        url = (f"https://api.marketaux.com/v1/news/all"
               f"?language=en"
               f"&published_after={extended_start}"
               f"&limit=100"
               f"&page={page}"
               f"&sort=published_desc")
        
        headers = {'Authorization': f'Bearer {MY_API_TOKEN}'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('data', [])
            
            if articles:
                new_articles = []
                for article in articles:
                    url_key = article.get('url', '')
                    if url_key and url_key not in seen_urls:
                        seen_urls.add(url_key)
                        new_articles.append(article)
                
                all_news_data.extend(new_articles)
                print(f"    -> {len(new_articles)}개 추가. 총 {len(all_news_data)}개")
                
                if len(all_news_data) >= 500:
                    print("    ✅ 목표 500개 달성!")
                    break
            else:
                break
            
            page += 1
            time.sleep(0.3)
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ 추가 수집 중 오류: {e}")
            break


if __name__ == "__main__":
    get_weekly_news_and_save_to_csv()