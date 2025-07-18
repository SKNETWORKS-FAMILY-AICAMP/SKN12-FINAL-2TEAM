# Postman 테스트 시나리오 가이드

## 파일 임포트 방법

### 1. 컬렉션 임포트
1. Postman 실행
2. **Import** 버튼 클릭
3. `Base_Server_API_Collection.postman_collection.json` 파일 선택
4. **Import** 클릭

### 2. 환경 변수 임포트
1. Postman에서 **Environments** 탭으로 이동
2. **Import** 버튼 클릭
3. `Base_Server_Environment.postman_environment.json` 파일 선택
4. **Import** 클릭
5. 환경을 **Base Server Environment**로 선택

## 테스트 시나리오 (순서대로 실행)

### Phase 1: 서버 상태 확인
```
1.1 Ping 테스트
1.2 서버 메트릭스 조회
```
**목적**: 서버가 정상적으로 실행되고 있는지 확인

### Phase 2: 계정 관리
```
2.1 회원가입 → 2.2 로그인 → 2.3 계정 정보 조회 → 2.4 프로필 설정
```
**목적**: 
- 회원가입 후 자동으로 `user_id` 저장
- 로그인 후 자동으로 `access_token` 저장
- 이후 모든 API 호출에 `access_token` 사용

### Phase 3: 관리자 기능 테스트
```
3.1 서버 상태 조회 → 3.2 헬스체크 → 3.3 세션 카운트 조회
```
**목적**: 시스템 상태 모니터링 기능 확인

### Phase 4: 시장 데이터 조회
```
4.1 시장 개요 → 4.2 종목 검색 → 4.3 시장 가격 조회 → 4.4 시장 뉴스
```
**목적**: 외부 API 연동 및 시장 데이터 제공 기능 확인

### Phase 5: 포트폴리오 관리
```
5.1 포트폴리오 조회 → 5.2 주식 추가 → 5.3 포트폴리오 성과 조회 → 5.4 포트폴리오 리밸런싱
```
**목적**: 핵심 투자 관리 기능 확인

### Phase 6: 채팅 및 AI 분석
```
6.1 채팅방 목록 → 6.2 채팅방 생성 → 6.3 메시지 전송 → 6.4 AI 분석 요청
```
**목적**: 
- 채팅방 생성 시 자동으로 `room_id` 저장
- AI 기반 투자 상담 기능 확인

### Phase 7: 자동거래 전략
```
7.1 전략 목록 조회 → 7.2 전략 생성 → 7.3 AI 전략 생성
```
**목적**: 자동거래 및 AI 전략 생성 기능 확인

### Phase 8: 알림 관리
```
8.1 알림 목록 조회 → 8.2 가격 알림 생성 → 8.3 알림 목록 조회
```
**목적**: 가격 알림 및 알림 시스템 기능 확인

### Phase 9: 설정 관리
```
9.1 설정 조회 → 9.2 설정 업데이트
```
**목적**: 사용자 설정 관리 기능 확인

### Phase 10: 대시보드
```
10.1 대시보드 메인 정보 → 10.2 대시보드 알림 → 10.3 대시보드 성과 분석
```
**목적**: 대시보드 통합 정보 제공 기능 확인

### Phase 11: 튜토리얼
```
11.1 튜토리얼 목록 → 11.2 튜토리얼 시작
```
**목적**: 신규 사용자를 위한 튜토리얼 기능 확인

### Phase 12: 크롤러 (관리자용)
```
12.1 크롤러 헬스체크 → 12.2 크롤러 작업 실행 → 12.3 크롤러 상태 조회
```
**목적**: AWS Lambda 스케줄러 연동 크롤러 기능 확인

### Phase 13: 로그아웃
```
13.1 로그아웃
```
**목적**: 세션 정리 및 자동으로 토큰 클리어

## 자동화된 테스트 스크립트

각 요청에는 테스트 스크립트가 포함되어 있습니다:

### 1. 토큰 자동 저장
```javascript
// 로그인 성공 시 access_token 자동 저장
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.accessToken) {
        pm.collectionVariables.set('access_token', response.accessToken);
    }
}
```

### 2. 응답 검증
```javascript
// 기본 응답 검증
pm.test('API 호출 성공', function () {
    const response = pm.response.json();
    pm.expect(response.errorCode).to.eql(0);
});
```

### 3. 데이터 연결
```javascript
// 채팅방 생성 시 room_id 자동 저장
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.room_id) {
        pm.collectionVariables.set('room_id', response.room_id);
    }
}
```

## 에러 처리 테스트

### 1. 인증 오류 테스트
- `access_token`을 잘못된 값으로 변경 후 API 호출
- 예상 결과: `errorCode: 1001` (인증 실패)

### 2. 권한 오류 테스트
- 일반 사용자 토큰으로 관리자 API 호출
- 예상 결과: `errorCode: 1002` (권한 없음)

### 3. 파라미터 오류 테스트
- 필수 파라미터 누락 후 API 호출
- 예상 결과: `errorCode: 1003` (잘못된 파라미터)

## 성능 테스트

### 1. Collection Runner 사용
1. 컬렉션 우클릭 → **Run collection**
2. **Iterations**: 10 (10번 반복)
3. **Delay**: 100ms (요청 간 지연)
4. **Run** 클릭

### 2. Newman (CLI) 사용
```bash
# Newman 설치
npm install -g newman

# 컬렉션 실행
newman run Base_Server_API_Collection.postman_collection.json \
  -e Base_Server_Environment.postman_environment.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export report.html
```

## 환경별 테스트

### 개발 환경 (Development)
```json
{
  "base_url": "http://localhost:8000"
}
```

### 스테이징 환경 (Staging)
```json
{
  "base_url": "https://staging-api.example.com"
}
```

### 프로덕션 환경 (Production)
```json
{
  "base_url": "https://api.example.com"
}
```

## 모니터링 및 알림

### 1. Postman Monitor 설정
1. 컬렉션에서 **Monitor** 버튼 클릭
2. 모니터 이름 입력: "Base Server Health Check"
3. 실행 주기 설정: 매 5분
4. 알림 설정: 실패 시 이메일 발송

### 2. 슬랙 알림 연동
```javascript
// 테스트 실패 시 슬랙 알림
pm.test("API Health Check", function () {
    if (pm.response.code !== 200) {
        // 슬랙 웹훅 호출 코드
        pm.sendRequest({
            url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
            method: 'POST',
            header: {
                'Content-Type': 'application/json',
            },
            body: {
                mode: 'raw',
                raw: JSON.stringify({
                    text: `🚨 API 테스트 실패: ${pm.info.requestName}`
                })
            }
        });
    }
});
```

## 문제 해결 가이드

### 1. 서버 연결 실패
- `base_url`이 올바른지 확인
- 서버가 실행 중인지 확인
- 방화벽 설정 확인

### 2. 인증 토큰 만료
- 로그인 API 다시 호출
- 새로운 `access_token` 자동 저장 확인

### 3. 데이터베이스 연결 오류
- MySQL 서버 상태 확인
- 데이터베이스 설정 확인

### 4. 외부 API 연결 오류
- 인터넷 연결 확인
- API 키 유효성 확인

## 베스트 프랙티스

### 1. 테스트 순서 준수
- 반드시 로그인 → 기능 테스트 → 로그아웃 순서로 진행
- 의존성이 있는 API는 순서대로 실행

### 2. 환경 변수 활용
- 하드코딩된 값 대신 환경 변수 사용
- 환경별로 다른 설정 값 관리

### 3. 테스트 스크립트 활용
- 자동화된 검증 및 데이터 연결
- 반복적인 작업 자동화

### 4. 에러 처리
- 예상되는 에러 케이스 테스트
- 적절한 에러 메시지 확인

이 가이드를 따라하면 Base Server의 모든 API를 체계적으로 테스트할 수 있습니다.