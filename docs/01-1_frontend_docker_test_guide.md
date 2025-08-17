# 🐳 Frontend Docker 로컬 테스트 가이드 (Windows)

> 이 문서는 AI Trading Platform의 **Frontend(Next.js)를 Docker로 실행**하는 방법을 설명합니다.
> Backend는 이미 `01_windows_local_docker_test_guide.md`에 따라 실행 중이어야 합니다.

## 📋 빠른 시작 (Quick Start)

```powershell
# 1. 디렉토리 이동
cd C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform

# 2. 이미지 빌드
docker build -t ai-trading-frontend:local .

# 3. 설정 파일 생성
echo "NEXT_PUBLIC_API_URL=http://host.docker.internal:8000" > .env.docker
echo "NEXT_PUBLIC_WS_URL=ws://host.docker.internal:8000" >> .env.docker
echo "BACKEND_URL=http://host.docker.internal:8000" >> .env.docker

# 4. 컨테이너 실행 (볼륨 마운팅)
docker run -d --name trading-frontend-test -p 3000:3000 -v "C:/SKN12-FINAL-2TEAM/base_server/frontend/ai-trading-platform/.env.docker:/app/.env:ro" ai-trading-frontend:local

# 5. 접속 확인
start http://localhost:3000
```

---

## 🎯 아키텍처 이해

### Backend와 Frontend 설정 방식 통일

| 구분 | Backend | Frontend |
|------|---------|----------|
| **설정 파일** | `base_web_server-config_local.json` | `.env.docker` |
| **주입 방식** | 볼륨 마운팅 | 볼륨 마운팅 |
| **경로** | `/app/application/base_web_server/` | `/app/.env` |
| **환경 변수** | `APP_ENV=LOCAL` | `NODE_ENV=production` |

### 핵심 개념

```
호스트 머신 (Windows)
├── Backend Container (8000)
│   └── 설정: config_local.json (볼륨 마운팅)
├── Frontend Container (3000)
│   └── 설정: .env.docker (볼륨 마운팅)
└── host.docker.internal → localhost 연결
```

---

## 🛠️ Step 1: 로컬 테스트 디렉토리 준비

### 1.1 작업 디렉토리 이동

```powershell
# Frontend 디렉토리로 이동
cd C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform

# 현재 위치 확인
pwd
```

### 1.2 Backend 실행 상태 확인

```powershell
# Backend 컨테이너 확인
docker ps | findstr trading-backend

# API 응답 테스트
curl http://localhost:8000
```

예상 출력:
```json
{"message":"AI Trading Platform API Server","version":"1.0.0","status":"healthy"}
```

> ⚠️ **중요**: Backend가 실행되지 않았다면 `01_windows_local_docker_test_guide.md` 참고

---

## 🏗️ Step 2: Docker 이미지 빌드

### 이미지 빌드 실행

```powershell
# 이미지 빌드 (5-10분 소요)
docker build -t ai-trading-frontend:local .
```

### 빌드 프로세스 이해

```
[+] Building...
 => [builder 1/7] FROM node:18-alpine         # Node.js 베이스 이미지
 => [builder 2/7] WORKDIR /app                # 작업 디렉토리
 => [builder 3/7] COPY package*.json          # 의존성 목록
 => [builder 4/7] RUN npm ci                  # 패키지 설치 (가장 오래 걸림)
 => [builder 5/7] COPY . .                    # 소스 코드 복사
 => [builder 6/7] RUN npm run build           # Next.js 빌드
 => [runner  1/7] FROM node:18-alpine         # 프로덕션 이미지
 => [runner  2/7] COPY --from=builder         # 빌드 결과물만 복사
```

### 빌드 완료 확인

```powershell
# 이미지 확인
docker images | findstr ai-trading-frontend

# 결과 예시:
# ai-trading-frontend   test    abc123def    2 minutes ago    450MB
```

---

## 🚀 Step 3: 설정 파일 준비 (핵심!)

### ⚠️ 중요: 볼륨 마운팅용 .env 파일 생성

```powershell
# .env.docker 파일 생성 (Docker 컨테이너용)
@"
NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
NEXT_PUBLIC_WS_URL=ws://host.docker.internal:8000
NEXT_PUBLIC_API_TIMEOUT=10000
BACKEND_URL=http://host.docker.internal:8000
NODE_ENV=production
"@ | Out-File -FilePath .env.docker -Encoding UTF8

# 파일 생성 확인
type .env.docker
```

### 설정 파일 경로 확인

```powershell
# 절대 경로 확인 (중요!)
(Get-Item .env.docker).FullName

# 결과 예시:
# C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform\.env.docker
```

---

## 🎯 Step 4: 컨테이너 실행 (핵심!)

### 컨테이너 실행 명령

```powershell
# 기존 컨테이너가 있다면 제거
docker rm -f trading-frontend-test 2>nul

# 컨테이너 실행 (볼륨 마운팅 방식)
docker run -d `
  --name trading-frontend-test `
  -p 3000:3000 `
  -v "C:/SKN12-FINAL-2TEAM/base_server/frontend/ai-trading-platform/.env.docker:/app/.env:ro" `
  ai-trading-frontend:local
```

### 명령어 상세 설명

| 옵션 | 설명 | 중요도 |
|------|------|--------|
| `-d` | 백그라운드 실행 | 필수 |
| `--name` | 컨테이너 이름 지정 | 관리 편의 |
| `-p 3000:3000` | 포트 매핑 (호스트:컨테이너) | 필수 |
| `-v .env.docker:/app/.env:ro` | 설정 파일 마운팅 | **핵심** |

### 📌 Backend와 비교

```powershell
# Backend (config 파일 마운팅)
-v "C:/.../config_local.json:/app/.../config_local.json:ro"

# Frontend (.env 파일 마운팅)
-v "C:/.../.env.docker:/app/.env:ro"
```

---

## ✅ Step 5: 동작 확인

### 5.1 컨테이너 상태 확인

```powershell
# 실행 상태 확인
docker ps

# 예상 출력:
CONTAINER ID   IMAGE                    PORTS                    NAMES
abc123...      ai-trading-frontend:local      0.0.0.0:3000->3000/tcp   trading-frontend-test
def456...      ai-trading-backend:local      0.0.0.0:8000->8000/tcp   trading-backend-test
```

### 5.2 로그 확인

```powershell
# 실시간 로그 확인
docker logs -f trading-frontend-test
```

예상 로그:
```
> ai-trading-platform@1.0.0 start
> next start

▲ Next.js 14.2.0
- Local:        http://localhost:3000
- Network:      http://0.0.0.0:3000

✓ Ready in 2.1s
```

### 5.3 브라우저 테스트

```powershell
# 브라우저 자동 열기
start http://localhost:3000

# API 프록시 테스트
curl http://localhost:3000/api/admin/ping
```

예상 응답:
```json
{"message":"pong","timestamp":"2024-..."}
```

### 5.4 환경 변수 확인

```powershell
# 컨테이너 내부 환경 변수 확인
docker exec trading-frontend-test sh -c "cat /app/.env"

# Backend 연결 테스트
docker exec trading-frontend-test sh -c "wget -qO- http://host.docker.internal:8000/health"
```

---

## 🔧 Step 6: 트러블슈팅

### 6.1 API 연결 실패 (ECONNREFUSED)

**증상**: `Error: connect ECONNREFUSED ::1:8000`

**해결**:
```powershell
# 1. .env.docker 파일 확인
type .env.docker

# 2. 볼륨 마운팅 확인
docker exec trading-frontend-test ls -la /app/.env

# 3. 컨테이너 재시작
docker restart trading-frontend-test
```

### 6.2 npm ci 에러

**증상**: `lock file's X does not satisfy Y`

**해결**:
```powershell
# package-lock.json 업데이트
npm install

# 캐시 없이 재빌드
docker build --no-cache -t ai-trading-frontend:local .
```

### 6.3 포트 충돌

```powershell
# 3000 포트 사용 확인
netstat -ano | findstr :3000

# 프로세스 종료
taskkill /PID [PID번호] /F
```

### 6.4 볼륨 마운팅 실패

```powershell
# Windows 경로 형식 확인 (중요!)
# ✅ 올바른 형식
-v "C:/SKN12-FINAL-2TEAM/.../file:/app/file:ro"

# ❌ 잘못된 형식
-v "C:\SKN12-FINAL-2TEAM\...\file:/app/file:ro"
```

---

## 🧹 Step 7: 정리 작업

### 컨테이너 정지 및 삭제

```powershell
# Frontend 컨테이너 정지
docker stop trading-frontend-test

# Frontend 컨테이너 삭제
docker rm trading-frontend-test

# 이미지 삭제 (필요시)
docker rmi ai-trading-frontend:local
```

### 전체 정리

```powershell
# 모든 테스트 컨테이너 정지 및 삭제
docker stop trading-frontend-test trading-backend-test
docker rm trading-frontend-test trading-backend-test

# 불필요한 리소스 정리
docker system prune -a
```

---

## ✅ 완료 체크리스트

### 준비 단계
- [ ] Docker Desktop 실행 중
- [ ] Backend 컨테이너 실행 중 (포트 8000)
- [ ] Frontend 디렉토리 이동 완료

### 빌드 단계
- [ ] Docker 이미지 빌드 성공
- [ ] .env.docker 파일 생성 완료
- [ ] 절대 경로 확인 완료

### 실행 단계
- [ ] 컨테이너 실행 성공 (볼륨 마운팅)
- [ ] 로그에 에러 없음
- [ ] http://localhost:3000 접속 성공

### 검증 단계
- [ ] API 프록시 동작 확인 (/api/admin/ping)
- [ ] Backend 연결 정상
- [ ] 주요 페이지 로딩 확인

---

## 📝 요약

### 실행된 서비스

| 서비스 | 컨테이너명 | 포트 | 설정 파일 | 상태 |
|--------|------------|------|-----------|------|
| Backend API | trading-backend-test | 8000 | config_local.json (볼륨) | ✅ |
| Frontend UI | trading-frontend-test | 3000 | .env.docker (볼륨) | ✅ |

### 핵심 명령어 정리

```powershell
# 빌드
docker build -t ai-trading-frontend:local .

# 실행 (볼륨 마운팅)
docker run -d --name trading-frontend-test -p 3000:3000 -v "C:/SKN12-FINAL-2TEAM/base_server/frontend/ai-trading-platform/.env.docker:/app/.env:ro" ai-trading-frontend:local

# 확인
docker logs trading-frontend-test
start http://localhost:3000

# 정리
docker stop trading-frontend-test
docker rm trading-frontend-test
```

### 다음 단계
Frontend와 Backend가 모두 정상 실행되면, `02_docker_compose_full_stack_guide.md`를 참고하여 MySQL, Redis를 포함한 전체 스택을 Docker Compose로 통합 실행할 수 있습니다.