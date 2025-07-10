import yfinance as yf
import pandas as pd
import os
import json
from datetime import datetime
import time

# --- 설정 ---
# 1. 원하는 종목의 티커 심볼을 리스트에 추가하세요.
TICKER_LIST = [
    # 대형 테크주 (FAANG+)
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

START_DATE = pd.to_datetime(datetime(2025, 7, 3)).tz_localize('UTC')
END_DATE = pd.to_datetime(datetime(2025, 7, 9, 23, 59, 59)).tz_localize('UTC')
OUTPUT_FILE = "yahoo_finance_news.json"  # JSON 파일로 변경
# --- 설정 끝 ---

def get_news_for_tickers():
    """yfinance를 이용해 여러 종목의 뉴스 목록을 JSON으로 저장합니다."""
    
    all_news_list = []
    
    print("✅ 뉴스 수집을 시작합니다...")
    print(f"대상 종목: {TICKER_LIST}")
    print(f"수집 기간: {START_DATE.date()} ~ {END_DATE.date()}")
    print("-" * 50)

    # 2. 리스트에 있는 각 종목에 대해 반복 작업
    for ticker_symbol in TICKER_LIST:
        print(f"-> '{ticker_symbol}'의 뉴스 데이터를 가져오는 중...")
        try:
            ticker = yf.Ticker(ticker_symbol)
            news_list = ticker.news
            
            # news_list가 None이거나 빈 리스트인 경우 처리
            if not news_list:
                print(f"  ℹ️ '{ticker_symbol}': 뉴스 데이터가 없습니다.")
                continue

            # 각 뉴스 데이터를 파싱하여 필요한 정보만 추출
            parsed_count = 0
            for news_item in news_list:
                try:
                    # news_item이 None이거나 딕셔너리가 아닌 경우 스킵
                    if not news_item or not isinstance(news_item, dict):
                        continue
                    
                    content = news_item.get('content', {})
                    
                    # content가 None이거나 딕셔너리가 아닌 경우 스킵
                    if not content or not isinstance(content, dict):
                        continue
                    
                    # 날짜 파싱 (ISO 형식)
                    pub_date_str = content.get('pubDate', '')
                    if pub_date_str:
                        pub_date = pd.to_datetime(pub_date_str)
                        # 타임존이 없는 경우 UTC로 설정
                        if pub_date.tz is None:
                            pub_date = pub_date.tz_localize('UTC')
                    else:
                        continue  # 날짜가 없으면 스킵
                    
                    # provider 정보 안전하게 추출
                    provider = content.get('provider', {})
                    if not isinstance(provider, dict):
                        provider = {}
                    
                    # clickThroughUrl 정보 안전하게 추출
                    click_url = content.get('clickThroughUrl', {})
                    if not isinstance(click_url, dict):
                        click_url = {}
                    
                    # 필요한 정보 추출
                    news_data = {
                        'datetime': pub_date,
                        'ticker': ticker_symbol,
                        'title': content.get('title', 'N/A'),
                        'publisher': provider.get('displayName', 'N/A'),
                        'link': click_url.get('url', 'N/A')
                    }
                    
                    all_news_list.append(news_data)
                    parsed_count += 1
                    
                except Exception as e:
                    print(f"  ⚠️ '{ticker_symbol}' 뉴스 파싱 중 오류: {e}")
                    continue
            
            print(f"  ✅ '{ticker_symbol}': {parsed_count}개 뉴스 파싱 완료")
            time.sleep(1)  # 서버에 부담을 주지 않기 위해 잠시 대기

        except Exception as e:
            print(f"❌ '{ticker_symbol}' 처리 중 오류 발생: {e}")

    if not all_news_list:
        print("수집된 뉴스가 없습니다.")
        return

    print("-" * 50)
    print(f"총 {len(all_news_list)}개의 최신 뉴스를 발견했습니다. 날짜 필터링 및 저장을 시작합니다.")

    # 3. DataFrame으로 변환하고 날짜 필터링
    all_news_df = pd.DataFrame(all_news_list)
    
    # 날짜 필터링
    mask = (all_news_df['datetime'] >= START_DATE) & (all_news_df['datetime'] <= END_DATE)
    filtered_df = all_news_df.loc[mask]

    if filtered_df.empty:
        print(f"❌ 해당 기간에 해당하는 뉴스가 없습니다.")
        return

    # 4. JSON으로 저장하기 위한 데이터 준비
    final_df = filtered_df[['datetime', 'ticker', 'title', 'publisher', 'link']].copy()
    
    # 날짜 컬럼을 문자열로 변환 (JSON 직렬화를 위해)
    final_df['datetime'] = final_df['datetime'].dt.tz_convert('UTC').dt.tz_localize(None)
    final_df['datetime'] = final_df['datetime'].dt.strftime('%Y-%m-%d %H:%M')
    
    # 최신순으로 정렬
    final_df = final_df.sort_values(by='datetime', ascending=False)
    
    # JSON 구조 생성: {"articles": [뉴스 객체들의 리스트]}
    articles_list = []
    for _, row in final_df.iterrows():
        article = {
            "날짜": row['datetime'],
            "티커": row['ticker'],
            "제목": row['title'],
            "언론사": row['publisher'],
            "링크": row['link']
        }
        articles_list.append(article)
    
    # 최종 JSON 구조
    json_data = {
        "articles": articles_list,
        "metadata": {
            "total_count": len(articles_list),
            "collection_period": {
                "start": START_DATE.strftime('%Y-%m-%d'),
                "end": END_DATE.strftime('%Y-%m-%d')
            },
            "tickers_covered": len(TICKER_LIST),
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }

    # 현재 스크립트가 있는 폴더(crawling)에 JSON 파일로 저장
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, OUTPUT_FILE)

    # JSON 파일 저장 (한글 깨짐 방지: ensure_ascii=False, 들여쓰기 적용: indent=2)
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    print("-" * 50)
    print(f"✅ 총 {len(articles_list)}개의 필터링된 뉴스를 성공적으로 JSON 파일로 저장했습니다!")
    print(f"   -> 파일 위치: {output_path}")
    print(f"   -> JSON 구조:")
    print(f"      📁 articles: {len(articles_list)}개 뉴스 객체")
    print(f"      📁 metadata: 수집 정보 및 통계")
    
    # JSON 구조 미리보기
    print("\n🔍 JSON 구조 미리보기:")
    print("```json")
    print("{")
    print('  "articles": [')
    print('    {')
    print(f'      "날짜": "{articles_list[0]["날짜"]}",')
    print(f'      "티커": "{articles_list[0]["티커"]}",')
    print(f'      "제목": "{articles_list[0]["제목"][:50]}...",')
    print(f'      "언론사": "{articles_list[0]["언론사"]}",')
    print(f'      "링크": "{articles_list[0]["링크"][:50]}..."')
    print('    },')
    print('    ...')
    print('  ],')
    print('  "metadata": { ... }')
    print('}')
    print("```")

if __name__ == "__main__":
    get_news_for_tickers() 