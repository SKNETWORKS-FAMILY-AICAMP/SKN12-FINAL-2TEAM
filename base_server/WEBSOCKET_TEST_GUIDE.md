# WebSocket 테스트 가이드

## 1. 사전 준비사항

### 필수 패키지 설치
```bash
# 서버 실행에 필요한 패키지 (uvicorn WebSocket 지원)
pip install 'uvicorn[standard]'
# 또는
pip install websockets uvloop httptools

# 클라이언트 테스트에 필요한 패키지
pip install websockets aiohttp
```

### 서버 실행
```bash
# 프로젝트 루트에서 실행 (인증 필수)
uvicorn base_server.application.base_web_server.main:app --reload

# LOCAL 환경으로 실행 (WebSocket 인증 비활성화)
uvicorn base_server.application.base_web_server.main:app --reload app_env=LOCAL

# DEBUG 환경으로 실행 (WebSocket 인증 비활성화)
uvicorn base_server.application.base_web_server.main:app --reload app_env=DEBUG
```

## 2. WebSocket 테스트 실행

### 기본 WebSocket 테스트 (인증 없음)
```bash
python3 base_server/test_websocket_client.py
```

### 로그인 포함 통합 테스트
```bash
python3 base_server/test_websocket_with_login.py
```

## 3. 테스트 시나리오

### test_websocket_client.py
- WebSocket 기본 연결 테스트
- Ping/Pong 테스트
- 채널 구독/구독해제
- 메시지 송수신
- 다중 클라이언트 동시 연결

### test_websocket_with_login.py
1. **회원가입** → 새 계정 생성
2. **로그인** → 액세스 토큰 획득
3. **API 테스트** → WebSocket 상태 조회, 브로드캐스트
4. **인증된 WebSocket** → 토큰 기반 연결
5. **미인증 WebSocket** → 토큰 없이 연결
6. **로그아웃** → 세션 종료

## 4. 주요 엔드포인트

### WebSocket 연결
- **URL**: `ws://localhost:8000/api/websocket/connect`
- **인증**: `?token={access_token}` 쿼리 파라미터

### REST API
- **상태 조회**: `GET /api/websocket/status`
- **채널 목록**: `GET /api/websocket/channels`
- **브로드캐스트**: `POST /api/websocket/broadcast`
- **클라이언트 조회**: `GET /api/websocket/clients`

## 5. 메시지 형식

### 클라이언트 → 서버
```json
{
  "type": "ping|subscribe|unsubscribe|chat_message|typing_indicator",
  "channel": "channel_name",
  "content": "message_content",
  "timestamp": "2025-07-19T23:30:00"
}
```

### 서버 → 클라이언트
```json
{
  "type": "pong|subscription_result|chat_message|error",
  "channel": "channel_name",
  "content": "message_content",
  "timestamp": "2025-07-19T23:30:00"
}
```

## 6. 문제 해결

### "No supported WebSocket library detected" 오류
```bash
# uvicorn 표준 패키지 설치
pip install 'uvicorn[standard]'
```

### 인증 실패
- 액세스 토큰이 올바른지 확인
- 토큰 만료 여부 확인
- TemplateService.check_session_info() 로그 확인

### 연결 거부
- 서버가 실행 중인지 확인
- WebSocketService가 초기화되었는지 확인
- 최대 연결 수 제한 확인 (기본값: 1000)

## 7. 성능 테스트

### 대량 클라이언트 테스트
```python
# test_websocket_client.py의 test_multiple_clients() 함수 수정
tasks = [client_task(i) for i in range(100)]  # 100개 동시 연결
```

### 메시지 처리량 테스트
- 초당 메시지 전송 수 측정
- 브로드캐스트 지연 시간 측정
- 메모리 사용량 모니터링