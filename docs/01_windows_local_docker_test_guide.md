# 🐳 Windows 로컬 Docker 테스트 가이드

> **목적**: AWS 배포 전에 Windows 환경에서 Docker 이미지를 빌드하고 테스트하여 문제를 미리 발견하고 해결합니다.

---

## 🚀 빠른 시작 가이드

### 처음 시작하는 경우
이 문서를 **처음부터 순서대로** 실행하면 됩니다:
1. [사전 준비 체크리스트](#📋-사전-준비-체크리스트) 확인
2. [Step 1: 디렉토리 준비](#🛠️-step-1-로컬-테스트-디렉토리-준비)
3. [Step 2: Docker 이미지 빌드](#🏗️-step-2-docker-이미지-빌드)
4. [Step 3: 컨테이너 실행](#🚀-step-3-컨테이너-실행-핵심)
5. [Step 4: 동작 확인](#✅-step-4-동작-확인)

### 이미 작업 중인 경우
현재 Docker 상태를 확인하고 선택하세요:

```bash
# 현재 상태 확인
docker ps                           # 실행 중인 컨테이너
docker images | findstr ai-trading  # 빌드된 이미지
```

**선택지:**
- **🔄 처음부터 다시 시작**: 기존 리소스 정리 후 Step 1부터
- **➡️ 계속 진행**: Step 4 (동작 확인)부터 시작

#### 🔄 처음부터 다시 시작하기
```bash
# 기존 컨테이너와 이미지 제거
docker rm -f trading-web-server-test 2>nul
docker rmi ai-trading-platform:test 2>nul

# Step 1부터 다시 시작
```

#### ➡️ 현재 상태에서 계속하기
이미 이미지와 컨테이너가 있다면 [Step 4: 동작 확인](#✅-step-4-동작-확인)으로 바로 이동

---

## 📌 핵심 개념: Config 파일의 이해

### 왜 Config 파일이 중요한가?

우리 시스템은 **환경별로 다른 설정**을 사용합니다:

```
로컬 개발 환경 (Windows)          Docker 컨테이너 환경
├─ MySQL: localhost:3306    →    ├─ MySQL: host.docker.internal:3306
├─ Redis: localhost:6379     →    ├─ Redis: host.docker.internal:6379
└─ 파일: 로컬 경로           →    └─ 파일: 컨테이너 내부 경로
```

### Config 파일 종류와 용도

| 파일명 | APP_ENV 값 | 용도 | 특징 |
|--------|-----------|------|------|
| `base_web_server-config.json` | PROD, RELEASE | 운영 환경 | 모든 설정 포함, AWS 서비스 활성화 |
| `base_web_server-config_local.json` | LOCAL | **Docker 테스트용** | host.docker.internal 설정 |
| `base_web_server-config_debug.json` | DEBUG | 개발/디버깅 | 디버그 모드, 상세 로그 |

### 🔥 핵심: localhost vs host.docker.internal

```yaml
# ❌ 잘못된 설정 (Docker 컨테이너 내에서)
"host": "localhost"  # 컨테이너 자신을 가리킴

# ✅ 올바른 설정 (Docker 컨테이너 내에서)
"host": "host.docker.internal"  # Windows 호스트를 가리킴
```

**이유**: Docker 컨테이너는 격리된 환경이므로, `localhost`는 컨테이너 자신을 의미합니다.
Windows 호스트의 서비스에 접근하려면 `host.docker.internal`을 사용해야 합니다.

---

## 📋 사전 준비 체크리스트

### 1️⃣ 필수 소프트웨어 확인

```bash
# PowerShell 또는 CMD에서 실행
docker --version      # Docker Desktop for Windows
docker-compose --version

# MySQL과 Redis가 Windows에서 실행 중인지 확인
netstat -an | findstr :3306  # MySQL
netstat -an | findstr :6379  # Redis
```

### 2️⃣ 프로젝트 구조 확인

```bash
cd C:\SKN12-FINAL-2TEAM\base_server
dir

# 필수 파일 확인
# ✅ Dockerfile
# ✅ requirements.txt
# ✅ application/base_web_server/main.py
# ✅ application/base_web_server/base_web_server-config_local.json
```

### 3️⃣ Config 파일 준비 상태 확인

```bash
# base_web_server-config_local.json이 Docker용으로 설정되었는지 확인
type application\base_web_server\base_web_server-config_local.json | findstr "host"

# 예상 결과:
# "host": "host.docker.internal",  ← MySQL (올바름)
# "host": "host.docker.internal",  ← Redis (올바름)
```

### 🔍 Config 파일 내부 구조 및 동작 원리

`base_web_server-config_local.json`의 핵심 설정들:

```json
{
  "databaseConfig": {
    "type": "mysql",
    "host": "host.docker.internal",    // ← 핵심! Windows 호스트의 MySQL 접근
    "port": 3306,
    "database": "finance_global",
    "user": "root",
    "password": "Wkdwkrdhkd91!"
  },
  "cacheConfig": {
    "type": "redis", 
    "host": "host.docker.internal",    // ← 핵심! Windows 호스트의 Redis 접근
    "port": 6379
  },
  "netConfig": {
    "host": "0.0.0.0",                // ← 모든 네트워크 인터페이스에서 접속 허용
    "port": 8000
  }
}
```

**🔧 각 설정이 작동하는 이유:**

| 설정 | 값 | 동작 원리 |
|-----|-----|----------|
| `databaseConfig.host` | `host.docker.internal` | Docker Desktop이 제공하는 특별한 DNS 이름. 컨테이너에서 Windows 호스트로 네트워크 접근 |
| `cacheConfig.host` | `host.docker.internal` | 동일하게 Windows 호스트의 Redis(6379)에 접속 |
| `netConfig.host` | `0.0.0.0` | 컨테이너 내부의 모든 네트워크 인터페이스에 바인딩하여 외부 접근 허용 |
| `netConfig.port` | `8000` | 컨테이너 내부 포트. Docker run -p 8000:8000으로 호스트 포트와 매핑 |

**⚡ 네트워크 흐름:**
```
[Windows 호스트]                    [Docker 컨테이너]
MySQL (3306) ←── host.docker.internal ──── 애플리케이션
Redis (6379) ←── host.docker.internal ──── 애플리케이션
브라우저(8000) ───── -p 8000:8000 ────── 0.0.0.0:8000
```

---

## ⚠️ 중요: Docker 테스트 전 데이터베이스 샤드 설정 변경

Docker 컨테이너에서 MySQL 샤드 데이터베이스에 접근하려면 `table_shard_config` 테이블의 호스트 설정을 변경해야 합니다.

### 문제 상황
- 기본 설정: `localhost` → Docker 컨테이너 내부를 참조
- 필요 설정: `host.docker.internal` → Windows 호스트의 MySQL을 참조

### 해결 방법

```sql
-- MySQL에 접속하여 실행
USE finance_global;

-- 샤드 설정을 Docker용으로 변경
UPDATE table_shard_config 
SET host = 'host.docker.internal' 
WHERE shard_id IN (1, 2);

-- 변경 확인
SELECT shard_id, shard_name, host, database_name FROM table_shard_config;
```

**예상 결과:**
```
+-----------+------------------+----------------------+------------------+
| shard_id  | shard_name       | host                 | database_name    |
+-----------+------------------+----------------------+------------------+
| 1         | finance_shard_1  | host.docker.internal | finance_shard_1  |
| 2         | finance_shard_2  | host.docker.internal | finance_shard_2  |
+-----------+------------------+----------------------+------------------+
```

> **💡 참고**: 로컬 개발 환경으로 돌아갈 때는 다시 `localhost`로 변경해야 합니다:
> ```sql
> UPDATE table_shard_config SET host = 'localhost' WHERE shard_id IN (1, 2);
> ```

---

## 🛠️ Step 1: 로컬 테스트 디렉토리 준비

```bash
# 로그 저장용 디렉토리 생성
mkdir C:\docker-logs -Force

# Config 백업용 디렉토리 생성 (선택사항)
mkdir C:\docker-configs -Force

# 프로덕션 config 파일 백업 (선택사항)
copy application\base_web_server\base_web_server-config.json C:\docker-configs\
copy application\base_web_server\base_web_server-config_debug.json C:\docker-configs\
```

---

## 🏗️ Step 2: Docker 이미지 빌드

### 이미지 빌드 실행

```bash
# base_server 디렉토리에서 실행
cd C:\SKN12-FINAL-2TEAM\base_server

# 이미지 빌드 (5-10분 소요)
docker build -t ai-trading-platform:test .
```

### 빌드 프로세스 이해

```
[+] Building...
 => [1/7] FROM python:3.11-slim              # 베이스 이미지
 => [2/7] RUN apt-get update && install...   # 시스템 패키지 (mysql-client 등)
 => [3/7] WORKDIR /app                        # 작업 디렉토리 설정
 => [4/7] COPY requirements.txt               # Python 패키지 목록
 => [5/7] RUN pip install -r requirements.txt # Python 패키지 설치 (가장 오래 걸림)
 => [6/7] COPY . .                           # 소스코드 복사
 => [7/7] ENV PYTHONPATH=/app                # Python 경로 설정
```

### 빌드 완료 확인

```bash
# 생성된 이미지 확인
docker images | findstr ai-trading-platform

# 결과 예시:
# ai-trading-platform   test    abc123def    2 minutes ago    1.73GB
```

---

## 🚀 Step 3: 컨테이너 실행 (핵심!)

### ⚠️ 중요: 볼륨 마운팅 방식

```bash
# ❌ 잘못된 방법: 디렉토리 전체 마운트
-v "C:/docker-configs:/app/application/base_web_server:ro"
# 문제: Python 파일들이 모두 덮어씌워짐!

# ✅ 올바른 방법: 개별 파일 마운트
-v "C:/SKN12-FINAL-2TEAM/base_server/application/base_web_server/base_web_server-config_local.json:/app/application/base_web_server/base_web_server-config_local.json:ro"
# 장점: config 파일만 교체, Python 파일은 유지
```

### 컨테이너 실행 명령

```bash
# 기존 컨테이너가 있다면 제거
docker rm -f trading-web-server-test 2>nul

# 컨테이너 실행
docker run -d \
  --name trading-web-server-test \
  -p 8000:8000 \
  -e APP_ENV=LOCAL \
  -v "C:/SKN12-FINAL-2TEAM/base_server/application/base_web_server/base_web_server-config_local.json:/app/application/base_web_server/base_web_server-config_local.json:ro" \
  -v "C:/docker-logs:/app/logs" \
  ai-trading-platform:test
```

### 명령어 상세 설명

| 옵션 | 설명 | 중요도 |
|------|------|--------|
| `-d` | 백그라운드 실행 | 필수 |
| `--name` | 컨테이너 이름 지정 | 관리 편의 |
| `-p 8000:8000` | 포트 매핑 (호스트:컨테이너) | 필수 |
| `-e APP_ENV=LOCAL` | config_local.json 사용 지시 | **핵심** |
| `-v ...config_local.json` | Config 파일 개별 마운트 | **핵심** |
| `-v .../logs` | 로그 디렉토리 마운트 | 디버깅용 |

---

## ✅ Step 4: 동작 확인

### 1️⃣ 컨테이너 상태 확인

```bash
# 실행 상태 확인
docker ps

# 예상 결과:
# CONTAINER ID   IMAGE                      STATUS                   PORTS
# abc123def456   ai-trading-platform:test   Up 30 seconds (healthy)  0.0.0.0:8000->8000/tcp
```

### 2️⃣ 로그 확인

```bash
# 실시간 로그 모니터링
docker logs -f trading-web-server-test

# 성공 시 예상 로그:
# ✅ Redis 전체 정리 성공
# ✅ 데이터베이스 서비스 초기화 완료
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### 3️⃣ API 테스트

```bash
# 기본 엔드포인트
curl http://localhost:8000

# 예상 응답:
# {"message":"base_web_server 동작 중","services":{"database":true,"cache":true}}

# Admin API 테스트
curl http://localhost:8000/api/admin/ping

# 예상 응답:
# {"status":"pong","timestamp":"2025-08-12T21:28:49.087997"}
```

---

## 🔍 트러블슈팅 (실제 경험 기반)

### 문제 1: "Could not import module"

**증상**:
```
ERROR: Error loading ASGI app. Could not import module "application.base_web_server.main"
```

**원인**: 
- 볼륨 마운팅 시 디렉토리 전체를 덮어씌워 Python 파일이 사라짐
- 또는 PYTHONPATH 설정 누락

**해결**:
1. 개별 파일만 마운트 (위 설명 참조)
2. Dockerfile에 `ENV PYTHONPATH=/app` 추가 확인

### 문제 2: "Can't connect to MySQL server"

**증상**:
```
ERROR: 데이터베이스 서비스 초기화 실패: Can't connect to MySQL server on 'localhost'
```

**원인**: 
- Config 파일에 `localhost` 사용 (컨테이너 내부를 가리킴)

**해결**:
- Config 파일에서 `"host": "localhost"`를 `"host": "host.docker.internal"`로 변경

### 문제 3: "Validation Error for AppConfig"

**증상**:
```
pydantic_core._pydantic_core.ValidationError: Field required
websocketConfig, emailConfig, smsConfig, notificationConfig
```

**원인**: 
- 불완전한 config 파일 사용 (필수 필드 누락)

**해결**:
- `base_web_server-config.json` (전체 설정 포함) 사용
- 또는 누락된 필드 추가

### 문제 4: 컨테이너가 즉시 종료됨

**체크 방법**:
```bash
docker ps -a  # 종료된 컨테이너도 표시
docker logs trading-web-server-test  # 에러 로그 확인
```

**일반적인 원인**:
1. Config 파일 문법 오류 (JSON 형식)
2. 필수 서비스 연결 실패 (MySQL/Redis)
3. Python 모듈 import 실패

---

## 🧹 Step 5: 정리

### 컨테이너 관리 명령어

```bash
# 컨테이너 중지 및 삭제
docker stop trading-web-server-test
docker rm trading-web-server-test

# 또는 강제 삭제 (실행 중이어도)
docker rm -f trading-web-server-test

# 이미지 삭제 (필요시)
docker rmi ai-trading-platform:test

# 전체 정리 (주의!)
docker system prune -a  # 모든 미사용 리소스 제거
```

---

## 📊 검증 체크리스트

| 항목 | 확인 방법 | 성공 기준 |
|------|----------|----------|
| ✅ Docker 이미지 빌드 | `docker images` | 이미지 목록에 표시 |
| ✅ 컨테이너 실행 | `docker ps` | STATUS: Up ... (healthy) |
| ✅ MySQL 연결 | 로그 확인 | "데이터베이스 서비스 초기화 완료" |
| ✅ Redis 연결 | 로그 확인 | "Redis 전체 정리 성공" |
| ✅ API 응답 | `curl localhost:8000` | JSON 응답 수신 |
| ✅ 로그 파일 | `dir C:\docker-logs` | 로그 파일 생성됨 |

---

## 💡 핵심 정리

### 🔑 성공의 열쇠

1. **Config 파일 이해**: 환경별로 다른 설정 사용
2. **host.docker.internal**: Docker에서 호스트 서비스 접근
3. **개별 파일 마운트**: 디렉토리 전체 마운트 피하기
4. **APP_ENV 환경변수**: 올바른 config 파일 선택
5. **로그 확인**: 문제 발생 시 즉시 로그 확인

### 🎯 다음 단계

로컬 Docker 테스트가 성공했다면:
1. AWS EC2 인스턴스 준비
2. Docker 이미지를 Docker Hub 또는 ECR에 푸시
3. EC2에서 이미지 풀 및 실행
4. 프로덕션 config 파일 적용

---

## 🔧 부록: Docker 명령어 치트시트

### 자주 사용하는 명령어

```bash
# 컨테이너 관련
docker ps                      # 실행 중인 컨테이너
docker ps -a                   # 모든 컨테이너
docker logs -f <container>     # 실시간 로그
docker exec -it <container> bash  # 컨테이너 접속
docker rm -f <container>       # 강제 삭제

# 이미지 관련
docker images                  # 이미지 목록
docker rmi <image>            # 이미지 삭제
docker build -t <name> .      # 이미지 빌드

# 정리
docker container prune        # 정지된 컨테이너 제거
docker image prune           # 미사용 이미지 제거
docker system prune -a       # 전체 정리 (주의!)
```

### 문제 해결 순서

1. `docker ps -a` → 컨테이너 상태 확인
2. `docker logs <container>` → 에러 메시지 확인
3. Config 파일 검증 → JSON 형식, 필수 필드
4. 네트워크 확인 → MySQL/Redis 실행 상태
5. 볼륨 마운트 확인 → 파일 경로 정확성

---

**작성일**: 2025-08-12  
**버전**: 2.0  
**테스트 환경**: Windows 11, Docker Desktop 4.x, Python 3.11