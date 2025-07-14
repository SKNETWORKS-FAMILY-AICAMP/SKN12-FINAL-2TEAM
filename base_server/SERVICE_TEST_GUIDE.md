# 🎯 서비스 초기화 및 테스트 가이드

## 📖 개요

base_web_server에 추가된 새로운 서비스들(LockService, SchedulerService, QueueService)의 초기화, 테스트, 실제 동작을 확인할 수 있는 완전한 가이드입니다.

## 🚀 서버 실행

```bash
cd /mnt/c/SKN12-FINAL-2TEAM/base_server/application/base_web_server
uvicorn main:app --reload --log-level debug
```

## 🔧 초기화 과정

서버 시작 시 다음 순서로 서비스가 초기화됩니다:

1. **Database Service** - MySQL 연결
2. **Cache Service** - Redis 연결
3. **LockService** - Redis 분산락 초기화
4. **SchedulerService** - 스케줄러 시작
5. **QueueService** - 메시지큐/이벤트큐 통합 초기화
6. **빠른 테스트 자동 실행**

## 📊 API 엔드포인트

### 🔍 상태 확인

| 엔드포인트 | 설명 | 응답 |
|------------|------|------|
| `GET /` | 기본 서비스 상태 | 모든 서비스 초기화 상태 |
| `GET /health` | 상세 헬스체크 | DB/Redis 연결 테스트 포함 |
| `GET /debug/services` | 디버그 정보 | 각 서비스 상세 상태 |
| `GET /queue/stats` | 큐 통계 | 메시지/이벤트 큐 통계 |

### 🧪 테스트 API

| 엔드포인트 | 설명 | 소요시간 |
|------------|------|----------|
| `GET /test/quick` | 빠른 기본 테스트 | ~10초 |
| `GET /test/full` | 전체 서비스 테스트 | ~30초 |
| `GET /test/cache` | 캐시 서비스 집중 테스트 | ~15초 |
| `GET /test/lock` | 분산락 집중 테스트 | ~10초 |
| `GET /test/scheduler` | 스케줄러 집중 테스트 | ~20초 |
| `GET /test/queue` | 큐 서비스 집중 테스트 | ~25초 |

### 📤 수동 테스트

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/test/message` | POST | 테스트 메시지 전송 |
| `/test/event` | POST | 테스트 이벤트 발행 |

### 🎬 실제 시나리오 데모

| 엔드포인트 | 설명 | 소요시간 |
|------------|------|----------|
| `GET /demo/status` | 데모 정보 | 즉시 |
| `GET /demo/quick` | 빠른 거래 데모 | ~30초 |
| `GET /demo/scheduler` | 스케줄러 데모 | ~15초 |
| `GET /demo/complete` | **완전한 금융 시나리오** | ~2-3분 |

## 🎪 실제 동작 확인 방법

### 1️⃣ 기본 상태 확인

```bash
# 서비스 상태 확인
curl http://localhost:8000/

# 상세 헬스체크
curl http://localhost:8000/health
```

### 2️⃣ 빠른 테스트 실행

```bash
# 모든 서비스 빠른 테스트
curl http://localhost:8000/test/quick

# 개별 서비스 테스트
curl http://localhost:8000/test/cache
curl http://localhost:8000/test/lock
curl http://localhost:8000/test/queue
```

### 3️⃣ 실제 시나리오 데모

```bash
# 빠른 금융 데모
curl http://localhost:8000/demo/quick

# 완전한 금융 서비스 시나리오
curl http://localhost:8000/demo/complete
```

### 4️⃣ 수동 메시지/이벤트 테스트

```bash
# 테스트 메시지 전송
curl -X POST http://localhost:8000/test/message \
  -H "Content-Type: application/json" \
  -d '{"test_data": "my custom message"}'

# 테스트 이벤트 발행
curl -X POST http://localhost:8000/test/event \
  -H "Content-Type: application/json" \
  -d '{"action": "custom_test", "data": {"key": "value"}}'
```

## 📋 테스트 시나리오 상세

### 🔧 캐시 서비스 테스트
- 문자열 저장/조회
- 해시 데이터 저장/조회  
- 리스트 연산
- TTL 만료 테스트

### 🔒 분산락 테스트
- 기본 락 획득/해제
- 중복 락 획득 차단
- 컨텍스트 매니저 테스트
- 락 상태 확인

### ⏰ 스케줄러 테스트
- 즉시 실행 작업
- 인터벌 작업 (주기적 실행)
- 작업 상태 조회
- 작업 제거 및 중지

### 📬 큐 서비스 테스트
- 메시지 전송/소비
- 이벤트 발행/구독
- 지연 메시지 처리
- 우선순위 처리
- 파티션별 순서 보장

### 💰 금융 서비스 시나리오
1. **계정 생성** - 사용자 등록 및 환영 작업
2. **포트폴리오 관리** - 포트폴리오 생성 및 리밸런싱 스케줄
3. **거래 실행** - 주식 매매 및 후속 처리
4. **시장 데이터** - 실시간 가격 업데이트 및 알림
5. **리스크 분석** - VaR 계산 및 고위험 알림
6. **알림 시스템** - 일일/월간 보고서 스케줄

## 🔍 로그 확인

서버 실행 중 콘솔에서 다음 로그들을 확인할 수 있습니다:

```
✅ [CACHE] 문자열 저장/조회 성공
✅ [LOCK] 락 획득 성공: abc12345...
✅ [QUEUE] 메시지 전송 성공: test_queue (test_message)
📊 일일 포트폴리오 요약 생성 시작
🔄 포트폴리오 리밸런싱 실행: 김투자의 성장형 포트폴리오
```

## 🚨 문제 해결

### Redis 연결 실패
- Redis 서버가 실행 중인지 확인
- `redis-server` 명령으로 Redis 시작

### 데이터베이스 연결 실패
- MySQL 서버 상태 확인
- 설정 파일 경로 확인: `base_web_server-config.json`

### 서비스 초기화 실패
- 로그에서 구체적인 오류 메시지 확인
- `/debug/services` API로 상세 상태 확인

## 🎯 성공 지표

### ✅ 정상 동작 확인
- 모든 서비스 `initialized: true`
- 빠른 테스트 100% 성공
- 데모 시나리오 오류 없이 완료
- 큐 통계에서 메시지 처리 확인

### 📈 성능 지표
- 메시지 처리 지연시간 < 100ms
- 이벤트 발행/구독 지연시간 < 50ms
- 분산락 획득 시간 < 10ms
- 캐시 응답 시간 < 5ms

## 🔄 지속적 모니터링

```bash
# 1분마다 서비스 상태 확인
watch -n 60 'curl -s http://localhost:8000/health | jq .status'

# 큐 통계 실시간 모니터링
watch -n 30 'curl -s http://localhost:8000/queue/stats | jq .service_stats'
```

## 📚 추가 정보

- 각 서비스는 독립적으로 실패해도 다른 서비스에 영향 없음
- 모든 테스트는 실제 Redis/DB 연결 상태에 따라 결과가 달라짐
- 데모 시나리오는 실제 금융 서비스 워크플로우를 시뮬레이션
- 스케줄러 작업은 백그라운드에서 지속적으로 실행됨

---

🎉 **이제 모든 서비스가 실제로 동작하는 것을 확인할 수 있습니다!**