# 🪟 Windows 로컬 Docker 테스트 가이드

> **목적**: AWS 배포 전에 Windows 환경에서 Docker 이미지를 빌드하고 테스트하여 문제를 미리 발견하고 해결합니다.

---

## 📋 사전 준비 체크리스트

### 1️⃣ Windows Docker Desktop 설치 확인
```bash
# PowerShell 또는 CMD에서 실행
docker --version
docker-compose --version
```

**결과 예시**:
```
Docker version 24.0.7, build afdd53b
Docker Compose version v2.23.3-desktop.2
```

❌ **설치 안 된 경우**: [Docker Desktop for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe) 다운로드 후 설치

### 2️⃣ WSL2 백엔드 확인 (권장)
```bash
# Docker Desktop 설정에서 확인
# Settings → General → "Use the WSL 2 based engine" 체크
```

### 3️⃣ 프로젝트 경로 확인
```bash
# 현재 위치가 프로젝트 루트인지 확인
cd C:\SKN12-FINAL-2TEAM\base_server
dir
```

**확인할 파일들**:
- ✅ `Dockerfile`
- ✅ `requirements.txt`
- ✅ `application/` 폴더
- ✅ `.dockerignore`

---

## 🛠️ Step 1: 로컬 설정 파일 준비

### 1️⃣ 테스트용 설정 디렉토리 생성
```bash
# PowerShell에서 실행 (관리자 권한 필요 없음)
mkdir C:\docker-configs\base-configs -Force
mkdir C:\docker-configs\model-configs -Force
mkdir C:\docker-logs -Force
```

### 2️⃣ 설정 파일 복사 (실제 설정을 테스트용으로)
```bash
# Base Web Server 설정 복사
copy "application\base_web_server\base_web_server-config.json" "C:\docker-configs\base-configs\"
copy "application\base_web_server\base_web_server-config_debug.json" "C:\docker-configs\base-configs\" 2>nul
copy "application\base_web_server\base_web_server-config_local.json" "C:\docker-configs\base-configs\" 2>nul

# Model Server 설정 복사
copy "application\model_server\*.json" "C:\docker-configs\model-configs\" 2>nul
```

### 3️⃣ 설정 파일 확인
```bash
# 복사된 파일 확인
dir C:\docker-configs\base-configs\
dir C:\docker-configs\model-configs\
```

**⚠️ 중요**: 실제 운영 시에는 민감한 정보(패스워드, API 키)를 별도로 관리해야 합니다!

---

## 🐳 Step 2: Docker 이미지 빌드

### 1️⃣ 이미지 빌드 실행
```bash
# base_server 디렉토리에서 실행
cd C:\SKN12-FINAL-2TEAM\base_server

# 이미지 빌드 (시간이 오래 걸릴 수 있음: 5-10분)
docker build -t ai-trading-platform:test .
```

**빌드 과정 설명**:
```
[+] Building 234.5s (12/12) FINISHED
 => [internal] load build definition from Dockerfile      # Dockerfile 읽기
 => [internal] load .dockerignore                         # 제외 파일 처리  
 => [internal] load metadata for python:3.11-slim        # 베이스 이미지 다운로드
 => [2/8] RUN apt-get update && apt-get install -y ...   # 시스템 패키지 설치
 => [3/8] COPY requirements.txt .                         # Python 패키지 목록 복사
 => [4/8] RUN pip install --upgrade pip && ...           # Python 패키지 설치 (가장 오래 걸림)
 => [5/8] COPY . .                                        # 소스코드 복사
 => [6/8] RUN echo "🗑️ 보안 파일 삭제 중..." && ...        # 보안 파일 삭제
 => [7/8] RUN mkdir -p /app/logs                          # 로그 디렉토리 생성
 => exporting to image                                    # 최종 이미지 생성
 => => naming to ai-trading-platform:test                # 이미지 태그 지정
```

### 2️⃣ 빌드 결과 확인
```bash
# 생성된 이미지 확인
docker images | findstr ai-trading-platform

# 결과 예시:
# ai-trading-platform   test    1a2b3c4d5e6f   2 minutes ago   XXX MB
```

### 3️⃣ 빌드 에러 시 대처법

**❌ "No such file or directory: requirements.txt"**
```bash
# 현재 위치 확인
cd C:\SKN12-FINAL-2TEAM\base_server
dir requirements.txt
```

**❌ "Package installation failed"**
```bash
# Python 패키지 목록 확인
type requirements.txt
# 문제가 되는 패키지가 있다면 임시로 주석 처리 후 재빌드
```

**❌ "Docker daemon is not running"**
```bash
# Docker Desktop 시작 확인
# 시작 → Docker Desktop 실행
```

---

## 🚀 Step 3: 컨테이너 실행 테스트

### 1️⃣ Base Web Server 단독 테스트
```bash
# Base Web Server 컨테이너 실행
docker run -d \
  --name trading-web-server-test \
  -p 8000:8000 \
  -e APP_ENV=LOCAL \
  -v "C:/docker-configs/base-configs:/app/application/base_web_server:ro" \
  -v "C:/docker-logs:/app/logs" \
  ai-trading-platform:test
```

**명령어 상세 설명**:
- `docker run -d`: 백그라운드에서 컨테이너 실행
- `--name trading-web-server-test`: 컨테이너에 이름 지정 (관리 편의)
- `-p 8000:8000`: 호스트 8000포트 → 컨테이너 8000포트 연결
- `-e APP_ENV=LOCAL`: 환경변수 설정 (로컬 테스트용)
- `-v "C:/docker-configs/...:/app/application/..."`: 설정 파일 마운트
- `-v "C:/docker-logs:/app/logs"`: 로그 디렉토리 마운트
- `ai-trading-platform:test`: 앞서 빌드한 이미지 사용

### 2️⃣ 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker ps

# 로그 확인 (실시간)
docker logs -f trading-web-server-test

# 로그 확인 (마지막 50줄)
docker logs --tail 50 trading-web-server-test
```

**정상 실행 시 로그 예시**:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3️⃣ API 동작 테스트
```bash
# 웹 브라우저에서 접속
# http://localhost:8000

# 또는 PowerShell에서 테스트
curl http://localhost:8000
# 또는 
Invoke-WebRequest -Uri http://localhost:8000
```

**응답 예시**:
```json
{"message": "AI Trading Platform API", "status": "running"}
```

### 4️⃣ Model Server 테스트 (같은 이미지, 다른 명령어)
```bash
# Model Server 컨테이너 실행
docker run -d \
  --name trading-model-server-test \
  -p 8001:8001 \
  -e APP_ENV=LOCAL \
  -v "C:/docker-configs/model-configs:/app/application/model_server:ro" \
  -v "C:/docker-logs:/app/logs" \
  ai-trading-platform:test \
  uvicorn application.model_server.main:app --host 0.0.0.0 --port 8001
```

**마지막 줄이 핵심**: `uvicorn application.model_server.main:app ...`
→ 기본 CMD를 오버라이드하여 Model Server 실행

### 5️⃣ Model Server 확인
```bash
# Model Server 상태 확인
docker ps | findstr model

# Model Server API 테스트  
curl http://localhost:8001
```

---

## 🐍 Step 4: Docker Compose로 두 서버 함께 실행

### 1️⃣ 기존 컨테이너 정리
```bash
# 기존 테스트 컨테이너 정지 및 삭제
docker stop trading-web-server-test trading-model-server-test
docker rm trading-web-server-test trading-model-server-test
```

### 2️⃣ Docker Compose 파일 복사 및 수정
```bash
# 예시 파일을 실제 설정으로 복사
copy docker-compose.example.yml docker-compose.test.yml
```

### 3️⃣ `docker-compose.test.yml` 수정 (Windows 경로 맞춤)
```yaml
version: '3.8'

services:
  # 🌐 Base Web Server
  web-server:
    image: ai-trading-platform:test
    container_name: trading-web-server
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=LOCAL  # 로컬 테스트용
    volumes:
      # Windows 경로 (절대 경로 사용)
      - C:/docker-configs/base-configs:/app/application/base_web_server:ro
      - C:/docker-logs/web-server:/app/logs
    restart: unless-stopped

  # 🤖 Model Server  
  model-server:
    image: ai-trading-platform:test  # 같은 이미지!
    container_name: trading-model-server
    ports:
      - "8001:8001"
    environment:
      - APP_ENV=LOCAL  # 로컬 테스트용
    volumes:
      - C:/docker-configs/model-configs:/app/application/model_server:ro
      - C:/docker-logs/model-server:/app/logs
    restart: unless-stopped
    # CMD 오버라이드로 Model Server 실행
    command: ["uvicorn", "application.model_server.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 4️⃣ Compose로 실행
```bash
# 두 서버 함께 실행
docker-compose -f docker-compose.test.yml up -d

# 실행 확인
docker-compose -f docker-compose.test.yml ps
```

**실행 결과 예시**:
```
NAME                   COMMAND                  SERVICE       STATUS    PORTS
trading-model-server   "uvicorn application…"   model-server  running   0.0.0.0:8001->8001/tcp
trading-web-server     "uvicorn application…"   web-server    running   0.0.0.0:8000->8000/tcp
```

### 5️⃣ 두 서버 동시 테스트
```bash
# 웹 브라우저에서 확인:
# http://localhost:8000  ← Base Web Server
# http://localhost:8001  ← Model Server

# PowerShell에서 확인
curl http://localhost:8000
curl http://localhost:8001
```

---

## 🔍 Step 5: 트러블슈팅 및 디버깅

### 1️⃣ 컨테이너가 실행되지 않는 경우
```bash
# 컨테이너 상태 확인 (중지된 것도 포함)
docker ps -a

# 실패 원인 확인
docker logs trading-web-server
docker logs trading-model-server
```

**일반적인 오류와 해결책**:

**❌ "Port already in use"**
```bash
# 포트를 사용 중인 프로세스 확인
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# 기존 컨테이너 정리
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

**❌ "No such file or directory" (설정 파일)**
```bash
# 설정 파일 경로 확인
dir C:\docker-configs\base-configs\
dir C:\docker-configs\model-configs\

# 빈 설정 파일이라도 생성
echo {} > C:\docker-configs\base-configs\base_web_server-config.json
```

**❌ "Permission denied" (볼륨 마운트)**
```bash
# Docker Desktop 설정 확인
# Settings → Resources → File Sharing에서 C:\ 드라이브 공유 확인
```

### 2️⃣ API 응답이 없는 경우
```bash
# 컨테이너 내부로 접속하여 직접 확인
docker exec -it trading-web-server bash

# 컨테이너 내부에서
curl http://localhost:8000
ps aux | grep uvicorn
```

### 3️⃣ 로그 확인 방법
```bash
# 실시간 로그 모니터링
docker-compose -f docker-compose.test.yml logs -f

# 특정 서비스만 로그 확인
docker-compose -f docker-compose.test.yml logs web-server
docker-compose -f docker-compose.test.yml logs model-server

# 호스트 로그 디렉토리 확인
dir C:\docker-logs\
```

---

## 🧹 Step 6: 정리 및 종료

### 1️⃣ 테스트 완료 후 정리
```bash
# Compose 서비스 정지 및 제거
docker-compose -f docker-compose.test.yml down

# 개별 컨테이너 정리 (필요 시)
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# 테스트 이미지 제거 (필요 시)
docker rmi ai-trading-platform:test
```

### 2️⃣ 불필요한 리소스 정리
```bash
# 사용하지 않는 이미지 정리
docker image prune

# 사용하지 않는 볼륨 정리  
docker volume prune

# 사용하지 않는 네트워크 정리
docker network prune
```

---

## ✅ 테스트 성공 체크리스트

### 로컬 테스트 완료 기준:
- [ ] Docker 이미지 빌드 성공
- [ ] Base Web Server (8000 포트) 정상 응답  
- [ ] Model Server (8001 포트) 정상 응답
- [ ] Docker Compose로 두 서버 동시 실행 성공
- [ ] 설정 파일 볼륨 마운팅 정상 동작
- [ ] 로그 파일이 호스트에 정상 저장

### 🎯 다음 단계:
로컬 테스트가 성공했다면 이제 AWS EC2에서 실제 배포 환경을 구축할 준비가 완료되었습니다!

---

## 💡 핵심 개념 정리

### 🔹 하나의 이미지, 두 서버:
- 같은 Docker 이미지를 사용하되 CMD만 다르게 하여 서로 다른 서버 실행
- 코드 일관성 유지 + 배포 복잡성 감소

### 🔹 볼륨 마운팅:
- 컨테이너 외부에 설정 파일 저장
- 이미지 재빌드 없이 설정 변경 가능
- 보안: 민감한 설정이 이미지에 포함되지 않음

### 🔹 환경 변수 활용:
- `APP_ENV=LOCAL/DEBUG/PROD`로 환경별 설정 자동 선택
- Docker/Kubernetes 배포 시 유연성 제공

### 🔹 Windows Docker 특이사항:
- 경로는 `/` 또는 `\` 모두 사용 가능하지만 `/` 권장
- 볼륨 마운트 시 절대 경로 사용 (`C:/...`)
- WSL2 백엔드 사용 시 성능 향상