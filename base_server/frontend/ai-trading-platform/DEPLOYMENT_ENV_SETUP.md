# 배포용 환경 변수 설정 가이드

## 환경 변수 설정

프로덕션 배포 시 다음 환경 변수들을 설정해야 합니다:

### 1. .env.local 파일 생성

프로젝트 루트에 `.env.local` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# API 서버 설정 (프로덕션 도메인으로 변경)
NEXT_PUBLIC_API_URL=http://your-production-domain.com:8000
NEXT_PUBLIC_API_BASE=http://your-production-domain.com:8000
NEXT_PUBLIC_WS_URL=ws://your-production-domain.com:8000

# 개발 환경용 (로컬 테스트 시)
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_API_BASE=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 2. Docker 배포 시 환경 변수 설정

Docker Compose를 사용하는 경우 `docker-compose.yml`에 환경 변수를 추가:

```yaml
version: '3.8'
services:
  frontend:
    build: .
    environment:
      - NEXT_PUBLIC_API_URL=http://your-production-domain.com:8000
      - NEXT_PUBLIC_API_BASE=http://your-production-domain.com:8000
      - NEXT_PUBLIC_WS_URL=ws://your-production-domain.com:8000
    ports:
      - "3000:3000"
```

### 3. 클라우드 배포 시 환경 변수 설정

#### Vercel 배포
- Vercel 대시보드 → Project Settings → Environment Variables
- 다음 변수들을 추가:
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_API_BASE`
  - `NEXT_PUBLIC_WS_URL`

#### AWS/EC2 배포
- 시스템 환경 변수로 설정:
```bash
export NEXT_PUBLIC_API_URL=http://your-production-domain.com:8000
export NEXT_PUBLIC_API_BASE=http://your-production-domain.com:8000
export NEXT_PUBLIC_WS_URL=ws://your-production-domain.com:8000
```

### 4. 환경별 설정 예시

#### 개발 환경
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

#### 스테이징 환경
```bash
NEXT_PUBLIC_API_URL=http://staging.your-domain.com:8000
NEXT_PUBLIC_API_BASE=http://staging.your-domain.com:8000
NEXT_PUBLIC_WS_URL=ws://staging.your-domain.com:8000
```

#### 프로덕션 환경
```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_API_BASE=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

## 주의사항

1. **HTTPS/WSS 사용**: 프로덕션에서는 보안을 위해 HTTPS와 WSS를 사용하세요.
2. **CORS 설정**: 백엔드에서 프론트엔드 도메인을 허용하도록 CORS를 설정하세요.
3. **환경 변수 확인**: 배포 후 브라우저 개발자 도구에서 환경 변수가 올바르게 설정되었는지 확인하세요.

## 변경된 파일들

다음 파일들이 환경 변수를 사용하도록 수정되었습니다:

- `app/api/[...path]/route.ts`
- `lib/api/client.ts`
- `utils/chatUtils.ts`
- `next.config.mjs`

모든 하드코딩된 localhost 주소가 환경 변수로 대체되었습니다.
