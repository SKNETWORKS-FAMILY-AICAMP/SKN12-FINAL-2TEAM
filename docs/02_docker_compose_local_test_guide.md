# 🐳 Docker Compose 로컬 통합 테스트 가이드 (Windows)

> 이 문서는 **Backend + Frontend를 Docker Compose로 통합 실행**하는 방법을 설명합니다.
> 01, 01-1 문서의 개별 테스트 완료 후 진행하세요.

## 📋 빠른 시작 (Quick Start)

### A. 로컬 빌드 버전 (01, 01-1 문서 연계)
```powershell
# 1. 설정 준비
mkdir C:\docker-logs -Force
mkdir C:\docker-frontend-configs -Force

# 2. Frontend 설정 파일 생성
@"
NEXT_PUBLIC_API_URL=http://backend:8000
NEXT_PUBLIC_WS_URL=ws://backend:8000
BACKEND_URL=http://backend:8000
NODE_ENV=production
"@ | Out-File -FilePath C:\docker-frontend-configs\.env -Encoding UTF8

# 3. Docker Compose 실행 (로컬 빌드)
cd C:\SKN12-FINAL-2TEAM
docker-compose -f docker-compose.local.yml up -d

# 4. 접속 확인
start http://localhost:3000
```

### B. Docker Hub 버전 (배포 테스트용)
```powershell
# 1. Docker Hub 로그인
docker login

# 2. 이미지 태그 및 업로드
docker tag ai-trading-backend:local [username]/ai-trading-backend:latest
docker push [username]/ai-trading-backend:latest

docker tag ai-trading-frontend:local [username]/ai-trading-frontend:latest
docker push [username]/ai-trading-frontend:latest

# 3. Hub 이미지로 실행
set DOCKERHUB_USERNAME=[username]
docker-compose -f docker-compose.hub.yml up -d
```

---

## 🎯 아키텍처 이해

### 통합 서비스 구조

```
Windows 호스트 (로컬 개발)
├── 01 문서: Backend 테스트 완료 ✅
│   └── 이미지: ai-trading-backend:local
├── 01-1 문서: Frontend 테스트 완료 ✅
│   └── 이미지: ai-trading-frontend:local
│
└── 02 문서: Docker Compose 통합 (현재)
    ├── Option A: 로컬 이미지 사용
    │   └── docker-compose.local.yml
    └── Option B: Hub 이미지 사용
        └── docker-compose.hub.yml
```

---

## 🛠️ Step 1: 사전 확인

### 1.1 개별 이미지 확인 (01, 01-1 문서 완료 여부)

```powershell
# 이미지 확인
docker images

# 필수 이미지 (01, 01-1 문서에서 생성됨)
# REPOSITORY                TAG      IMAGE ID
# ai-trading-backend        local    xxx...     # Backend (01 문서)
# ai-trading-frontend       local    yyy...     # Frontend (01-1 문서)
```

**이미지가 없다면?**
- 01 문서로 가서 Backend 빌드
- 01-1 문서로 가서 Frontend 빌드

### 1.2 개별 테스트 확인

```powershell
# Backend 단독 테스트 (01 문서 방식)
docker run -d --name test-backend -p 8000:8000 ai-trading-backend:local
curl http://localhost:8000
docker stop test-backend && docker rm test-backend

# Frontend 단독 테스트 (01-1 문서 방식)  
docker run -d --name test-frontend -p 3000:3000 ai-trading-frontend:local
start http://localhost:3000
docker stop test-frontend && docker rm test-frontend
```

---

## 🏗️ Step 2: 설정 파일 준비

### 2.1 디렉토리 생성

```powershell
# Backend 로그용 (01 문서와 동일)
mkdir C:\docker-logs -Force

# Frontend 설정용 (01-1 문서 방식 적용)
mkdir C:\docker-frontend-configs -Force
```

### 2.2 Frontend 설정 파일 생성

```powershell
# Docker 네트워크용 설정 (중요: backend:8000 사용)
@"
NEXT_PUBLIC_API_URL=http://backend:8000
NEXT_PUBLIC_WS_URL=ws://backend:8000
BACKEND_URL=http://backend:8000
NODE_ENV=production
"@ | Out-File -FilePath C:\docker-frontend-configs\.env -Encoding UTF8

# 파일 확인
type C:\docker-frontend-configs\.env
```

> 💡 **왜 backend:8000?**
> - Docker Compose 내부에서 서비스명으로 통신
> - `localhost`가 아닌 `backend` 사용

### 2.3 Backend 설정 파일 확인

```powershell
# 01 문서에서 사용한 설정 파일 확인
dir C:\SKN12-FINAL-2TEAM\base_server\application\base_web_server\base_web_server-config_local.json
```

---

## 🚀 Step 3: Docker Compose 실행 (로컬 이미지)

### 3.1 docker-compose.local.yml 확인

```yaml
version: '3.8'

services:
  backend:
    build: ./base_server                          # 또는 image: ai-trading-backend:local
    container_name: trading-backend-test
    ports:
      - "8000:8000"
    volumes:
      - "./base_server/application/base_web_server/base_web_server-config_local.json:/app/application/base_web_server/base_web_server-config_local.json:ro"
      - "C:/docker-logs:/app/logs"
    environment:
      - APP_ENV=LOCAL
    networks:
      - trading-network

  frontend:
    build: ./base_server/frontend/ai-trading-platform  # 또는 image: ai-trading-frontend:local
    container_name: trading-frontend-test
    ports:
      - "3000:3000"
    volumes:
      - "C:/docker-frontend-configs/.env:/app/.env:ro"
    depends_on:
      - backend
    networks:
      - trading-network

networks:
  trading-network:
    driver: bridge
```

### 3.2 실행

```powershell
# 프로젝트 루트로 이동
cd C:\SKN12-FINAL-2TEAM

# 방법 1: 이미지가 이미 있는 경우 (01, 01-1 완료)
docker-compose -f docker-compose.local.yml up -d

# 방법 2: 이미지 재빌드 필요한 경우
docker-compose -f docker-compose.local.yml up -d --build
```

### 3.3 상태 확인

```powershell
# 컨테이너 확인
docker-compose -f docker-compose.local.yml ps

# 로그 확인
docker-compose -f docker-compose.local.yml logs -f
```

---

## 🐳 Step 4: Docker Hub 업로드 (선택사항)

### 4.1 Docker Hub 로그인

```powershell
docker login
# Username과 Password 입력
```

### 4.2 이미지 태그 변경

```powershell
# 01 문서의 Backend 이미지를 Hub용으로 태그
docker tag ai-trading-backend:local [username]/ai-trading-backend:latest

# 01-1 문서의 Frontend 이미지를 Hub용으로 태그  
docker tag ai-trading-frontend:local [username]/ai-trading-frontend:latest

# 태그 확인
docker images | findstr [username]
```

### 4.3 Docker Hub 업로드

```powershell
# Backend 업로드
docker push [username]/ai-trading-backend:latest

# Frontend 업로드
docker push [username]/ai-trading-frontend:latest
```

### 4.4 Hub 이미지로 테스트

```powershell
# 환경변수 설정
set DOCKERHUB_USERNAME=[username]

# 또는 .env 파일 생성
echo "DOCKERHUB_USERNAME=[username]" > .env

# Hub 이미지로 실행
docker-compose -f docker-compose.hub.yml up -d
```

---

## ✅ Step 5: 통합 테스트

### 5.1 서비스 접속

```powershell
# Backend API
curl http://localhost:8000
curl http://localhost:8000/health

# Frontend UI
start http://localhost:3000

# API 프록시 테스트 (Frontend → Backend)
curl http://localhost:3000/api/admin/ping
```

### 5.2 기능 테스트

1. **로그인 테스트**
   - http://localhost:3000/auth/login
   - 테스트 계정으로 로그인

2. **API 연동 테스트**
   - 대시보드 데이터 로딩 확인
   - WebSocket 연결 확인 (F12 → Console)

3. **내부 통신 테스트**
   ```powershell
   # Frontend에서 Backend 접근 확인
   docker exec trading-frontend-test sh -c "wget -qO- http://backend:8000/health"
   ```

---

## 🔧 Step 6: 트러블슈팅

### 6.1 이미지를 찾을 수 없음

```powershell
# 01, 01-1 문서의 이미지명 확인
docker images

# 없으면 다시 빌드
cd C:\SKN12-FINAL-2TEAM\base_server
docker build -t ai-trading-backend:local .

cd C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform
docker build -t ai-trading-frontend:local .
```

### 6.2 포트 충돌

```powershell
# 기존 컨테이너 정리
docker ps -a
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

### 6.3 네트워크 통신 실패

```powershell
# Docker 네트워크 확인
docker network ls
docker network inspect skn12-final-2team_trading-network

# 컨테이너 재시작
docker-compose -f docker-compose.local.yml restart
```

---

## 🧹 Step 7: 정리

### 7.1 Compose 정리

```powershell
# 서비스 중지 및 삭제
docker-compose -f docker-compose.local.yml down

# 네트워크까지 삭제
docker-compose -f docker-compose.local.yml down -v
```

### 7.2 전체 정리

```powershell
# 모든 컨테이너 정지
docker stop $(docker ps -aq)

# 모든 컨테이너 삭제
docker rm $(docker ps -aq)

# 이미지 정리 (주의: 모든 이미지 삭제)
docker system prune -a
```

---

## ✅ 완료 체크리스트

### 사전 준비 (01, 01-1 문서)
- [ ] Backend 이미지: `ai-trading-backend:local` 존재
- [ ] Frontend 이미지: `ai-trading-frontend:local` 존재
- [ ] 개별 테스트 성공

### Docker Compose 실행
- [ ] 설정 디렉토리 생성 완료
- [ ] Frontend .env 파일 생성 완료
- [ ] docker-compose.local.yml 실행 성공

### 통합 테스트
- [ ] http://localhost:8000 (Backend) 접속 성공
- [ ] http://localhost:3000 (Frontend) 접속 성공
- [ ] Frontend → Backend API 통신 성공

### Docker Hub (선택사항)
- [ ] Docker Hub 로그인 완료
- [ ] 이미지 업로드 완료
- [ ] Hub 이미지로 실행 성공

---

## 📝 요약

### 실행 순서

```
01 문서 (Backend) → 01-1 문서 (Frontend) → 02 문서 (Compose 통합)
     ↓                    ↓                        ↓
ai-trading-backend:local  ai-trading-frontend:local  통합 실행
```

### 핵심 명령어

```powershell
# 로컬 이미지로 실행 (01, 01-1 연계)
docker-compose -f docker-compose.local.yml up -d

# Hub 이미지로 실행 (배포 테스트)
docker-compose -f docker-compose.hub.yml up -d
```

### 다음 단계
- **03 문서**: Docker Hub 자동화
- **04 문서**: Jenkins CI/CD 구축
- **05 문서**: AWS EC2 배포