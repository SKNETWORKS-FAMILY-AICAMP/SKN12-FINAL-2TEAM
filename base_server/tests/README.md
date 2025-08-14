# Tests 실행 가이드

이 문서는 `base_server/tests` 전용 테스트 실행 방법을 안내합니다.

## 준비
- 가상환경 활성화 후 패키지 설치
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install pytest pytest-asyncio redis fakeredis pytest-cov
```

## 실행
- 전체 실행: `pytest -q base_server/tests`
- 스코프별: `pytest -q base_server/tests/unit`, `pytest -q base_server/tests/integration`, `pytest -q base_server/tests/e2e`
- 파일/케이스: 예) `pytest -q base_server/tests/integration/test_notification_queue_flow.py::test_send_notification_enqueues_per_channel`
- 커버리지: `pytest --cov=base_server/service --cov-report=term-missing base_server/tests`

## 참고
- 기본적으로 Redis 없이도 동작하도록 모킹/스킵을 사용합니다.
- 실제 Redis로 검증하려면 Docker로 `redis:7-alpine` 실행:
```
docker run -d --name dev-redis -p 6379:6379 redis:7-alpine
```
- Windows PowerShell 실행 정책 오류 시:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
