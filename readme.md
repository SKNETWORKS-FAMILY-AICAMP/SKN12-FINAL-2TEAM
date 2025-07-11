# 1. marketaux_news
```
작동 방식 : API 키 발급, request 라이브러리로 호출
무료 플랜 : Daily requests - 100회
장점 : 해외 뉴스 수집에 용이, 데이터 전처리 쉬움
단점 : API 요청 횟수 낮음, csv파일의 뉴스 제목 및 요약본 중간에 끊김
```

# 2. naverdeveloper_news
```
작동 방식 : API 키 발급
무료 플랜 : Daily requests - 25,000회
장점 : API 요청 횟수 높음, 크롤링 용이
단점 : 국내 기업과 관련된 뉴스가 대다수, 
       그마저도 언론사만 다르고 중복된 내용이 매우 많이 나옴, 
       csv파일의 뉴스 제목 및 요약본 중간에 끊김
```

# 3. yahoo_finance
```
작동 방식 : yfinance 라이브러리를 활용하여 yahoo finance의 news들을 수집
장점 : 무료, API 불필요, 굉장히 많은 양의 기사를 제약 없이 뽑아올 수 있음
단점 : 실질적 중요 부분은 날짜 & 제목 등만 나옴, 
       yahoo finance 측의 구조 변경이 생길 시 해당 코드는 무용지물
```

# 4. 최종 결정 -> yahoo_finance!!
```
1. yahoo finance의 뉴스를 n분마다 수집하는 Python 스케쥴러 파일 제작
2. 뉴스 제목 -> Hashkey로 바꿔서 고유하게 구분
3. 기존에 같은 Hashkey -> 중복된 뉴스임!! -> 저장 X
4. 기존에 다른 Hashkey -> 다른 뉴스임!! -> 저장 O

최종 구조
- yfinance_scheduler.py : 메인 파일
- requirements.txt : 필요한 라이브러리
- yahoo_finance_news.json : 결과 파일(자동 생성/업데이트)
- news_hashes.json : 해시값 저장(자동 생성)
```