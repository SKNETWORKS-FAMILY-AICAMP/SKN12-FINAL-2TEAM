# =============================================================================
# AI Trading Platform - 하나의 이미지로 두 서버 지원
# =============================================================================
# 
# 📦 이 이미지로 실행 가능한 서버:
# 1️⃣ Base Web Server (메인 API) - 포트 8000
# 2️⃣ Model Server (ML 예측) - 포트 8001
#
# 🎯 핵심 개념:
# - 하나의 Docker 이미지에 두 서버 코드가 모두 포함됨
# - 실행 시 CMD를 다르게 지정하여 원하는 서버 선택
# - 각각 별도의 컨테이너로 실행되어 독립적으로 동작
# - 같은 코드베이스를 공유하므로 일관성 유지

FROM python:3.11-slim

# 기본 환경 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치 (Docker 레이어 캐싱 최적화를 위해 먼저)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 전체 애플리케이션 코드 복사
COPY . .

# Python path 설정
ENV PYTHONPATH=/app:$PYTHONPATH

# 🔒 보안: .dockerignore에서 민감한 파일들을 빌드 컨텍스트에서 제외
# - 설정 파일 (*.json): DB 패스워드, API 키 등 민감 정보 
# - 문서 파일 (docs/, *.md): 시스템 구조 노출 방지
# - 로그/캐시 파일: 불필요한 데이터 제외
# - 개발/테스트 파일: 운영 환경에 불필요한 파일 제외

# 필수 디렉토리 생성
RUN mkdir -p /app/logs

# 포트 노출 선언 (실제 바인딩은 docker run -p 옵션에서)
EXPOSE 8000
EXPOSE 8001

# 헬스체크 설정 (Base Web Server 기준)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 🚀 기본 실행 명령어 (Base Web Server)
# 컨테이너가 시작될 때 기본적으로 실행될 명령어
CMD ["python", "-m", "uvicorn", "application.base_web_server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# 🚀 사용법 - 하나의 이미지로 두 서버 실행
# =============================================================================
#
# 1️⃣ 이미지 빌드 (한 번만 실행):
#    docker build -t ai-trading-platform .
#
# 2️⃣ 호스트에 설정 파일 준비:
#    # Base Web Server 설정
#    mkdir -p /opt/base-configs
#    # base_web_server-config.json, base_web_server-config_debug.json 등
#
#    # Model Server 설정  
#    mkdir -p /opt/model-configs
#    # model_server-config.json 등
#
# 3️⃣ Base Web Server 실행:
#    docker run -d \
#      --name trading-web-server \
#      -p 8000:8000 \
#      -e APP_ENV=PROD \
#      -v /opt/base-configs:/app/application/base_web_server:ro \
#      ai-trading-platform
#    
#    # 기본 CMD가 base_web_server이므로 별도 명령어 불필요
#
# 4️⃣ Model Server 실행 (같은 이미지, 다른 명령어):
#    docker run -d \
#      --name trading-model-server \
#      -p 8001:8001 \
#      -e APP_ENV=PROD \
#      -v /opt/model-configs:/app/application/model_server:ro \
#      ai-trading-platform \
#      uvicorn application.model_server.main:app --host 0.0.0.0 --port 8001
#    
#    # 마지막 줄이 CMD 오버라이드 (model_server 실행 명령어)
#
# 5️⃣ docker-compose로 두 서버 함께 실행:
#    version: '3.8'
#    services:
#      web-server:
#        image: ai-trading-platform
#        ports:
#          - "8000:8000"
#        environment:
#          - APP_ENV=PROD
#        volumes:
#          - /opt/base-configs:/app/application/base_web_server:ro
#        # 기본 CMD 사용 (base_web_server)
#      
#      model-server:
#        image: ai-trading-platform  # 같은 이미지 사용!
#        ports:
#          - "8001:8001"
#        environment:
#          - APP_ENV=PROD
#        volumes:
#          - /opt/model-configs:/app/application/model_server:ro
#        command: ["uvicorn", "application.model_server.main:app", "--host", "0.0.0.0", "--port", "8001"]
#        # command로 CMD 오버라이드
#
# 6️⃣ 확인:
#    curl http://localhost:8000/    # Base Web Server
#    curl http://localhost:8001/    # Model Server
#
# =============================================================================
# 💡 핵심 개념 설명:
# =============================================================================
# 
# 🔹 하나의 이미지, 여러 컨테이너:
#   - Docker 이미지는 '템플릿' 개념
#   - 같은 이미지로 여러 컨테이너 생성 가능
#   - 각 컨테이너는 독립적인 프로세스
#
# 🔹 CMD 오버라이드:
#   - Dockerfile의 CMD는 '기본값'
#   - docker run 마지막에 명령어를 주면 CMD 대체
#   - docker-compose에서는 command: 옵션으로 대체
#
# 🔹 포트 바인딩:
#   - 컨테이너 내부 포트는 독립적
#   - 호스트 포트로 매핑: -p 호스트포트:컨테이너포트
#   - 8000:8000 (Base Web), 8001:8001 (Model)
#
# 🔹 볼륨 마운팅:
#   - 각 서버는 다른 설정 파일 필요
#   - 다른 호스트 경로를 각각 마운트
#   - /opt/base-configs → base_web_server/
#   - /opt/model-configs → model_server/
# =============================================================================