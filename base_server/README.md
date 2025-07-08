
  📋 단계별 실행 가이드

  1️⃣ Conda 환경 설정

# base_server 디렉토리로 이동

  cd /mnt/c/job_directory/base_server

# conda 가상환경 생성 (Python 3.9 권장)

  conda create -n base_server python=3.9 -y

# 가상환경 활성화

  conda activate base_server

# 의존성 설치

  pip install -r requirements.txt

  2️⃣ 데이터베이스 설정 (MySQL)

# MySQL 서버가 실행 중인지 확인

# Windows에서 MySQL 서비스 시작

  net start mysql

# 또는 MySQL Workbench/phpMyAdmin 사용

  DB 스크립트 실행 순서:
  -- 1. finance_global DB 생성
  source /mnt/c/job_directory/db_scripts/01_create_fin
  ance_global_db.sql

  -- 2. 프로시저 생성
  source /mnt/c/job_directory/db_scripts/02_create_fin
  ance_procedures.sql

  -- 3. 샤드 DB 생성
  source /mnt/c/job_directory/db_scripts/03_create_fin
  ance_shard_dbs.sql

  3️⃣ Redis 서버 실행

# Windows에서 Redis 실행 (Redis가 설치되어 있다면)

  redis-server

# 또는 Docker로 실행

  docker run -d -p 6379:6379 redis:latest

  4️⃣ 서버 실행

# base_server 디렉토리에서 실행

  cd /mnt/c/job_directory/base_server

# uvicorn으로 서버 실행 (개발 모드)

  uvicorn application.base_web_server.main:app
  --reload --host 0.0.0.0 --port 8000

# 또는 환경별로 실행

  uvicorn application.base_web_server.main:app
  --reload --host 0.0.0.0 --port 8000 --
  --logLevel=Debug --env=LOCAL

  5️⃣ 서버 동작 확인

  브라우저에서 확인:

- Health Check: http://localhost:8000/
- API 문서: http://localhost:8000/docs
- Admin Ping: http://localhost:8000/api/admin/ping

---

  🔧 Postman API 테스트

1. 회원가입 API

  POST http://localhost:8000/api/account/signup

  Headers:
  Content-Type: application/json

  Body (JSON):
  {
    "platform_type": 1,
    "account_id": "testuser01",
    "password": "password123",
    "nickname": "테스트유저",
    "email": "test@example.com",
    "sequence": 1
  }

  예상 응답:
  {
    "errorCode": 0,
    "sequence": 1,
    "account_db_key": 1703123456789,
    "message": "회원가입 성공"
  }

2. 로그인 API

  POST http://localhost:8000/api/account/login

  Headers:
  Content-Type: application/json

  Body (JSON):
  {
    "platform_type": 1,
    "account_id": "testuser01",
    "password": "password123",
    "sequence": 2
  }

  예상 응답:
  {
    "errorCode": 0,
    "sequence": 2,
    "accessToken":
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "account_db_key": 1703123456789,
    "nickname": "테스트유저",
    "account_level": 1,
    "shard_id": 1,
    "account_info": {
      "accessToken":
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "account_db_key": 1703123456789,
      "platform_type": 1,
      "account_id": "testuser01",
      "account_level": 1,
      "shard_id": 1
    }
  }

3. 로그아웃 API

  POST http://localhost:8000/api/account/accountlogout

  Headers:
  Content-Type: application/json
  Authorization: Bearer
  a1b2c3d4-e5f6-7890-abcd-ef1234567890

  Body (JSON):
  {
    "sequence": 3
  }

  예상 응답:
  {
    "errorCode": 0,
    "sequence": 3,
    "message": "로그아웃 성공"
  }

4. Admin API 테스트

  POST http://localhost:8000/api/admin/healthcheck

  Body (JSON):
  {
    "sequence": 1
  }

  GET http://localhost:8000/api/admin/ping

---

  🚨 문제 해결

  서버 실행 오류 시:

1. 포트 충돌:

# 다른 포트 사용

  uvicorn application.base_web_server.main:app
  --reload --port 8001
  2. 모듈 import 오류:

# PYTHONPATH 설정

  export PYTHONPATH=/mnt/c/job_directory/base_server:$
  PYTHONPATH
  3. DB 연결 오류:
    - MySQL 서비스 실행 확인
    - base_web_server-config_local.json의 DB 정보 확인
  4. Redis 연결 오류:
    - Redis 서버 실행 확인
    - 포트 6379 사용 가능 여부 확인

  API 테스트 시 주의사항:

- sequence: 각 요청마다 고유한 sequence 값 사용
- accessToken: 로그인 응답에서 받은 토큰을 로그아웃
  시 사용
- Content-Type: 반드시 application/json 설정

  이제 단계별로 실행해보세요!
