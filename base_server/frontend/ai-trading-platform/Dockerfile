# =============================================================================
# AI Trading Platform Frontend - Next.js 애플리케이션
# =============================================================================
# 
# 📦 이 이미지의 특징:
# - Next.js 14 기반 프론트엔드 서버
# - 볼륨 마운팅을 통한 설정 파일 주입 (.env)
# - Backend API 프록시 지원
# - 멀티 스테이지 빌드로 이미지 크기 최적화
#
# 🎯 핵심 개념:
# - Build stage: 의존성 설치 및 Next.js 빌드
# - Production stage: 최소 런타임 환경
# - 설정 파일은 컨테이너 실행 시 볼륨 마운팅으로 제공

FROM node:18-alpine AS builder

# 🔧 Build Arguments (Jenkins에서 주입)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000
ARG NEXT_PUBLIC_API_TIMEOUT=10000

# 🌍 Build-time 환경변수 설정 (Next.js 빌드에서 사용)
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
ENV NEXT_PUBLIC_API_TIMEOUT=${NEXT_PUBLIC_API_TIMEOUT}
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# 의존성 파일 복사 (캐싱 최적화)
COPY package*.json ./

# 의존성 설치 (npm install 사용 - lock 파일 재생성)
RUN npm install && \
    npm cache clean --force

# 소스 코드 복사
COPY . .

# 빌드 시 .env 파일 동적 생성 (build-arg 값 사용)
RUN echo "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}" > .env && \
    echo "NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}" >> .env && \
    echo "NEXT_PUBLIC_API_TIMEOUT=${NEXT_PUBLIC_API_TIMEOUT}" >> .env && \
    echo "NODE_ENV=production" >> .env

# Next.js 빌드 (이제 .env 파일을 읽을 수 있음)
RUN npm run build

# =============================================================================
# Production Stage
# =============================================================================
FROM node:18-alpine AS runner

WORKDIR /app

# 시스템 패키지 설치
RUN apk add --no-cache libc6-compat

# Builder stage에서 필요한 파일만 복사 (root로 실행)
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.mjs ./next.config.mjs

# 권한 문제 회피: root로 실행 (프로덕션에서 일반적)

# 포트 노출
EXPOSE 3000

# 환경 변수 기본값 (볼륨 마운팅된 .env로 오버라이드 가능)
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {r.statusCode === 200 ? process.exit(0) : process.exit(1)})"

# Next.js 서버 실행
CMD ["npm", "start"]

# =============================================================================
# 🚀 사용법
# =============================================================================
#
# 1️⃣ 이미지 빌드:
#    docker build -t ai-trading-frontend .
#
# 2️⃣ 설정 파일 준비:
#    # .env.docker 파일 생성
#    NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
#    NEXT_PUBLIC_WS_URL=ws://host.docker.internal:8000
#    BACKEND_URL=http://host.docker.internal:8000
#
# 3️⃣ 컨테이너 실행 (볼륨 마운팅):
#    docker run -d \
#      --name trading-frontend \
#      -p 3000:3000 \
#      -v "C:/path/to/.env.docker:/app/.env:ro" \
#      ai-trading-frontend
#
# =============================================================================
