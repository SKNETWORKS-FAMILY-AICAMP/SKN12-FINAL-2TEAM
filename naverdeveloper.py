import os
import requests
from dotenv import load_dotenv
import json
import csv
from datetime import datetime
import time
import re
import html

# .env 파일에서 환경 변수(API 키)를 불러옴
load_dotenv()
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def clean_naver_text(text):
    """네이버 API 텍스트 정제 함수"""
    if not text or text.strip() == "":
        return ""
    
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # HTML 태그 제거 (네이버 API 특성)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 네이버 특수 문자 제거
    text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    
    # 줄바꿈 문자를 공백으로 변환
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # 불필요한 문구 제거
    patterns_to_remove = [
        r'기사\s*원문',           # "기사 원문"
        r'더\s*보기',            # "더 보기"
        r'자세히\s*보기',         # "자세히 보기"
        r'관련\s*기사',          # "관련 기사"
        r'이\s*기사를',          # "이 기사를"
        r'뉴스\s*제보',          # "뉴스 제보"
        r'사진\s*=',            # "사진 = "
        r'그래픽\s*=',          # "그래픽 = "
        r'영상\s*=',            # "영상 = "
        r'\[.*?\]',             # 대괄호 안의 내용
        r'\(.*?\)',             # 소괄호 안의 내용 (짧은 것만)
        r'【.*?】',              # 일본식 괄호
        r'◆.*?◆',              # 특수 기호
        r'▶.*?◀',              # 특수 기호
        r'※.*?※',              # 특수 기호
        r'★.*?★',              # 별표
        r'●.*?●',              # 원형 기호
        r'■.*?■',              # 사각형 기호
        r'▲.*?▲',              # 삼각형 기호
        r'=\s*연합뉴스',        # "= 연합뉴스"
        r'=\s*뉴시스',          # "= 뉴시스"
        r'=\s*뉴스1',           # "= 뉴스1"
        r'기자\s*$',            # 끝에 나오는 "기자"
        r'특파원\s*$',          # 끝에 나오는 "특파원"
        r'@.*?\..*?$',          # 이메일 주소
        r'\.{3,}$',             # 끝에 있는 "..." (3개 이상 연속 점)
        r'…+$',                 # 끝에 있는 "…" (줄임표)
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # 연속된 공백을 하나로 압축
    text = re.sub(r'\s+', ' ', text)
    
    # CSV 구분자 충돌 방지: 슬래시(/)를 다른 문자로 치환
    text = text.replace('/', '｜')  # 전각 파이프 문자로 치환
    
    # 양 끝 공백 제거
    text = text.strip()
    
    return text

def extract_source_name(original_link):
    """원본 링크에서 언론사 이름 추출"""
    if not original_link:
        return ""
    
    try:
        # URL에서 도메인 추출
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', original_link)
        if not domain_match:
            return ""
        
        domain = domain_match.group(1)
        
        # 언론사 도메인 매핑 (국내 + 해외)
        source_mapping = {
            # 한국 언론사
            'yna.co.kr': '연합뉴스',
            'yonhapnews.co.kr': '연합뉴스',
            'newsis.com': '뉴시스',
            'news1.kr': '뉴스1',
            'mk.co.kr': '매일경제',
            'hankyung.com': '한국경제',
            'sedaily.com': '서울경제',
            'edaily.co.kr': '이데일리',
            'etnews.com': 'ET뉴스',
            'dt.co.kr': '디지털타임스',
            'zdnet.co.kr': 'ZDNet',
            'bloter.net': '블로터',
            'chosun.com': '조선일보',
            'joongang.co.kr': '중앙일보',
            'donga.com': '동아일보',
            'hani.co.kr': '한겨레',
            'khan.co.kr': '경향신문',
            'kbs.co.kr': 'KBS',
            'sbs.co.kr': 'SBS',
            'mbc.co.kr': 'MBC',
            'jtbc.co.kr': 'JTBC',
            'tvchosun.com': 'TV조선',
            'mtn.co.kr': 'MTN',
            
            # 해외 주요 언론사
            'reuters.com': 'Reuters',
            'cnn.com': 'CNN',
            'bbc.com': 'BBC',
            'bbc.co.uk': 'BBC',
            'bloomberg.com': 'Bloomberg',
            'wsj.com': 'Wall Street Journal',
            'nytimes.com': 'New York Times',
            'ft.com': 'Financial Times',
            'cnbc.com': 'CNBC',
            'marketwatch.com': 'MarketWatch',
            'forbes.com': 'Forbes',
            'ap.org': 'Associated Press',
            'apnews.com': 'Associated Press',
            'yahoo.com': 'Yahoo News',
            'finance.yahoo.com': 'Yahoo Finance',
            'techcrunch.com': 'TechCrunch',
            'theverge.com': 'The Verge',
            'engadget.com': 'Engadget',
            'arstechnica.com': 'Ars Technica',
            'wired.com': 'Wired',
            'guardian.co.uk': 'The Guardian',
            'theguardian.com': 'The Guardian',
            'independent.co.uk': 'The Independent',
            'telegraph.co.uk': 'The Telegraph',
            'economist.com': 'The Economist',
            'time.com': 'Time',
            'newsweek.com': 'Newsweek',
            'usatoday.com': 'USA Today',
            'washingtonpost.com': 'Washington Post',
            'latimes.com': 'Los Angeles Times',
            'abcnews.go.com': 'ABC News',
            'cbsnews.com': 'CBS News',
            'nbcnews.com': 'NBC News',
            'foxnews.com': 'Fox News',
            'business.com': 'Business.com',
            'businessinsider.com': 'Business Insider',
            'investopedia.com': 'Investopedia',
            'fool.com': 'The Motley Fool',
            'seekingalpha.com': 'Seeking Alpha',
            'benzinga.com': 'Benzinga',
            'zacks.com': 'Zacks',
            'morningstar.com': 'Morningstar',
            'barrons.com': 'Barrons',
            'investor.com': 'Investors Business Daily',
            'thestreet.com': 'TheStreet',
            'moneycontrol.com': 'MoneyControl',
            'livemint.com': 'LiveMint',
            'economictimes.indiatimes.com': 'Economic Times',
            'nikkei.com': 'Nikkei',
            'japantimes.co.jp': 'Japan Times',
            'scmp.com': 'South China Morning Post',
            'straitstimes.com': 'Straits Times',
            'channelnewsasia.com': 'Channel NewsAsia',
            'aljazeera.com': 'Al Jazeera',
            'dw.com': 'Deutsche Welle',
            'france24.com': 'France 24',
            'euronews.com': 'Euronews',
            'rt.com': 'RT',
            'sputniknews.com': 'Sputnik News',
        }
        
        # 매핑된 언론사 이름 찾기
        for domain_key, source_name in source_mapping.items():
            if domain_key in domain:
                return source_name
        
        # 매핑되지 않은 경우 도메인에서 추출
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            return domain_parts[0].capitalize()
        
        return domain
        
    except Exception:
        return ""

def preprocess_naver_news(news_items):
    """네이버 뉴스 데이터 전처리"""
    print("🔄 네이버 뉴스 데이터 전처리를 시작합니다...")
    
    original_count = len(news_items)
    
    # 1. 텍스트 정제 및 언론사 정보 추출
    for item in news_items:
        item['title'] = clean_naver_text(item.get('title', ''))
        item['description'] = clean_naver_text(item.get('description', ''))
        item['source_name'] = extract_source_name(item.get('originallink', ''))
    
    # 2. 결측치 제거 (제목이나 요약이 비어있는 경우)
    news_items = [item for item in news_items 
                  if item.get('title', '').strip() and 
                     item.get('description', '').strip()]
    
    after_missing_count = len(news_items)
    print(f"  → 결측치 제거: {original_count - after_missing_count}개 제거")
    
    # 3. 다단계 중복 제거 시스템 (최고 정확도)
    print("  🔄 다단계 중복 제거 시작...")
    
    # 3-1단계: 완전 동일 제목 제거
    stage1_news = exact_title_removal(news_items)
    print(f"    → 1단계 (완전동일): {len(news_items) - len(stage1_news)}개 제거")
    
    # 3-2단계: 정규화된 제목으로 제거
    stage2_news = normalized_title_removal(stage1_news)
    print(f"    → 2단계 (정규화): {len(stage1_news) - len(stage2_news)}개 제거")
    
    # 3-3단계: 유사도 기반 제거
    stage3_news = similarity_based_removal(stage2_news)
    print(f"    → 3단계 (유사도): {len(stage2_news) - len(stage3_news)}개 제거")
    
    # 3-4단계: 키워드 패턴 기반 제거
    stage4_news = keyword_pattern_removal(stage3_news)
    print(f"    → 4단계 (키워드): {len(stage3_news) - len(stage4_news)}개 제거")
    
    # 3-5단계: 언론사 우선순위 기반 최종 선택
    final_news = priority_source_selection(stage4_news)
    print(f"    → 5단계 (우선순위): {len(stage4_news) - len(final_news)}개 제거")
    
    final_count = len(final_news)
    total_removed = after_missing_count - final_count
    removal_rate = (total_removed / after_missing_count * 100) if after_missing_count > 0 else 0
    
    print(f"  ✅ 총 중복 제거: {total_removed}개 제거 (제거율: {removal_rate:.1f}%)")
    print(f"  → 최종 데이터 개수: {final_count}개")
    
    return final_news

def exact_title_removal(news_items):
    """1단계: 완전히 동일한 제목 제거"""
    seen_exact = set()
    unique_news = []
    
    for item in news_items:
        title = item.get('title', '').strip()
        if title and title not in seen_exact:
            seen_exact.add(title)
            unique_news.append(item)
    
    return unique_news

def normalized_title_removal(news_items):
    """2단계: 정규화된 제목으로 제거 (공백, 특수문자, 숫자 무시)"""
    seen_normalized = set()
    unique_news = []
    
    for item in news_items:
        title = item.get('title', '').strip()
        
        # 강력한 정규화
        normalized = title.lower()
        normalized = re.sub(r'[^\w가-힣]', '', normalized)  # 특수문자 제거
        normalized = re.sub(r'\d+', 'NUM', normalized)       # 숫자 일반화
        normalized = re.sub(r'(주가|stock|price|급등|급락|상승|하락|발표|공개)', 'KEY', normalized)  # 자주 나오는 단어 일반화
        
        if normalized and len(normalized) > 10 and normalized not in seen_normalized:
            seen_normalized.add(normalized)
            unique_news.append(item)
    
    return unique_news

def similarity_based_removal(news_items):
    """3단계: 유사도 기반 제거 (85% 이상 유사하면 중복)"""
    from difflib import SequenceMatcher
    
    unique_news = []
    
    for current_item in news_items:
        current_title = current_item.get('title', '').strip()
        is_duplicate = False
        
        # 기존 아이템들과 유사도 비교
        for existing_item in unique_news:
            existing_title = existing_item.get('title', '').strip()
            
            # 유사도 계산
            similarity = SequenceMatcher(None, current_title.lower(), existing_title.lower()).ratio()
            
            if similarity >= 0.85:  # 85% 이상 유사하면 중복
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_news.append(current_item)
    
    return unique_news

def keyword_pattern_removal(news_items):
    """4단계: 핵심 키워드 패턴 기반 제거"""
    seen_patterns = set()
    unique_news = []
    
    for item in news_items:
        title = item.get('title', '').strip()
        
        # 핵심 키워드 추출
        keywords = re.findall(r'[가-힣A-Za-z]{2,}', title)  # 2글자 이상 단어만
        
        # 불용어 제거
        stop_words = {'관련', '발표', '소식', '뉴스', '기사', '보도', '오늘', '어제', '최근', '새로운', '최신'}
        keywords = [k for k in keywords if k.lower() not in stop_words]
        
        # 상위 5개 키워드로 패턴 생성
        if len(keywords) >= 3:
            pattern = '|'.join(sorted(keywords[:5]))
            
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                unique_news.append(item)
        else:
            # 키워드가 적으면 원본 제목으로 판단
            if title not in [item.get('title', '') for item in unique_news]:
                unique_news.append(item)
    
    return unique_news

def priority_source_selection(news_items):
    """5단계: 언론사 우선순위 기반 최종 선택"""
    
    # 언론사 신뢰도/우선순위 점수 (높을수록 우선)
    source_priority = {
        # 해외 주요 언론사 (최고 우선순위)
        'Reuters': 20, 'Bloomberg': 19, 'Wall Street Journal': 18,
        'Financial Times': 17, 'CNN': 16, 'BBC': 15,
        'CNBC': 14, 'MarketWatch': 13, 'Forbes': 12,
        
        # 국내 주요 경제지
        '연합뉴스': 10, '매일경제': 9, '한국경제': 9,
        '서울경제': 8, '이데일리': 8, '뉴시스': 7,
        '뉴스1': 6, 'ET뉴스': 6,
        
        # 기타 언론사
        'KBS': 5, 'SBS': 5, 'MBC': 5, 'JTBC': 4
    }
    
    # 비슷한 뉴스끼리 그룹화
    similar_groups = []
    
    for item in news_items:
        title = item.get('title', '').strip()
        
        # 기존 그룹과 유사한지 확인
        added_to_group = False
        for group in similar_groups:
            if group and is_similar_enough(title, group[0].get('title', '')):
                group.append(item)
                added_to_group = True
                break
        
        # 새 그룹 생성
        if not added_to_group:
            similar_groups.append([item])
    
    # 각 그룹에서 가장 우선순위 높은 언론사 선택
    final_news = []
    for group in similar_groups:
        if len(group) == 1:
            final_news.append(group[0])
        else:
            # 우선순위가 가장 높은 아이템 선택
            best_item = max(group, key=lambda x: source_priority.get(x.get('source_name', ''), 0))
            final_news.append(best_item)
    
    return final_news

def is_similar_enough(title1, title2, threshold=0.75):
    """두 제목이 충분히 유사한지 판단"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio() >= threshold

def get_naver_news(keyword):
    """네이버 뉴스 API를 이용해 특정 키워드의 뉴스를 검색하고 결과를 반환하는 함수"""
    
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ API 키를 찾을 수 없습니다. .env 파일을 확인하세요.")
        return []

    print(f"✅ '{keyword}' 키워드로 뉴스 검색 중...")
    url = "https://openapi.naver.com/v1/search/news.json"
    params = {
        "query": keyword, 
        "display": 50, 
        "sort": "date",
        "start": 1  # 검색 시작 위치 명시
    }
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # 검색된 각 뉴스에 '검색어' 필드 추가
        items = response.json()['items']
        for item in items:
            item['search_keyword'] = keyword
        return items
        
    except requests.exceptions.RequestException as e:
        print(f"❌ '{keyword}' 검색 중 API 요청 오류 발생: {e}")
        return []

def save_to_csv(all_items):
    """수집된 모든 뉴스 데이터를 하나의 CSV 파일로 저장하는 함수"""
    if not all_items:
        print("❌ 저장할 뉴스가 없습니다.")
        return

    # 현재 스크립트가 있는 폴더에 저장 (marketaux.py와 동일하게)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(current_dir, f"네이버뉴스_모음_{datetime.now().strftime('%Y%m%d')}.csv")

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter='/')  # 구분자를 슬래시(/)로 변경
            # CSV 헤더 작성 (언론사 정보 포함)
            writer.writerow(['검색어', '제목', '요약', '언론사', '링크', '날짜'])
            
            for item in all_items:
                # 이미 전처리된 데이터 사용
                title = item.get('title', '')
                description = item.get('description', '')
                source_name = item.get('source_name', '')
                
                # 날짜 형식 변환
                try:
                    pub_date = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y-%m-%d %H:%M')
                except:
                    pub_date = item.get('pubDate', '')

                writer.writerow([
                    item.get('search_keyword', ''),
                    title,
                    description,
                    source_name,  # 추출된 언론사 이름
                    item.get('originallink', ''),  # 원문 링크
                    pub_date
                ])
        
        print("-" * 50)
        print(f"✅ 총 {len(all_items)}개의 전처리된 뉴스를 '{os.path.basename(filename)}' 파일에 저장했습니다.")
        print(f"📁 저장 위치: {filename}")
        print("🔧 전처리 완료: 텍스트 정제, 언론사 정보 추출, 결측치 및 중복 제거 완료")

    except Exception as e:
        print(f"❌ CSV 파일 저장 중 오류 발생: {e}")


if __name__ == "__main__":
    # 1. 뉴스로 검색하고 싶은 키워드 예시
    search_keywords = ["semiconductor", "cloud computing", "global stock", "GAM", "세계 주식", "US stock market", 
    "Wall Street", "Federal Reserve", "oil price", "dollar index", "tech stocks", "inflation"]
    
    # 사용자가 키워드를 직접 입력하고 싶은 경우
    user_input = input("키워드를 직접 입력하시겠습니까? (y/n): ").lower()
    if user_input == 'y' or user_input == 'yes':
        custom_keywords = input("검색할 키워드들을 쉼표로 구분해서 입력하세요: ")
        search_keywords = [keyword.strip() for keyword in custom_keywords.split(',')]
    
    print(f"🔍 검색 키워드: {', '.join(search_keywords)}")
    print("-" * 50)
    
    all_news_items = []
    
    # 2. 목록에 있는 각 기업에 대해 뉴스 검색 실행
    for keyword in search_keywords:
        news_items = get_naver_news(keyword)
        all_news_items.extend(news_items) # 검색 결과를 큰 리스트에 추가
        time.sleep(3) # API 서버에 부담을 주지 않기 위해 요청 사이에 1초 대기

    # 3. 데이터 전처리
    print(f"\n🔄 전처리 전 데이터 개수: {len(all_news_items)}개")
    all_news_items = preprocess_naver_news(all_news_items)

    # 4. 모든 검색 결과를 하나의 CSV 파일로 저장
    save_to_csv(all_news_items)