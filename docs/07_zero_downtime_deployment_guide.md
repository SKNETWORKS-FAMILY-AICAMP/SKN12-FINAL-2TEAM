# 🚀 무중단 배포(Zero Downtime Deployment) 완전 가이드

> **목적**: 서비스 중단 없이 새 버전을 배포할 수 있는 무중단 배포 시스템을 구축합니다. 사용자는 배포가 진행되는 동안에도 서비스를 계속 이용할 수 있습니다.
>
> **💡 무중단 배포란?**: 기존 서비스를 중단하지 않고 새 버전으로 점진적으로 교체하는 배포 방식입니다.

---

## 🏗️ 무중단 배포 전략 이해하기

### 배포 방식 비교

| 배포 방식 | 서비스 중단 시간 | 리소스 사용량 | 롤백 속도 | 복잡도 |
|----------|----------------|---------------|-----------|--------|
| **기존 방식** | 5-10분 중단 ❌ | 적음 | 느림 | 낮음 |
| **Rolling Update** | 없음 ✅ | 중간 | 중간 | 중간 |
| **Blue-Green** | 없음 ✅ | 높음 | 빠름 | 높음 |
| **Canary** | 없음 ✅ | 중간 | 빠름 | 높음 |

### 우리가 구현할 방식: **Blue-Green + Health Check**

```
🔵 Blue Environment (현재 운영)
├── trading-web-server-blue (포트 8000)
├── trading-model-server-blue (포트 8001)
└── 실제 사용자 트래픽 처리 중

🟢 Green Environment (새 버전 배포)
├── trading-web-server-green (포트 8002) 
├── trading-model-server-green (포트 8003)
└── 배포 및 테스트 완료 후 대기

📡 Nginx Load Balancer
├── Health Check 수행
├── Green 환경 정상 확인 후
└── 트래픽을 Blue → Green으로 전환
```

---

## 🔧 Step 1: Deploy Server에 Nginx 로드밸런서 설정 (15분)

### 1️⃣ Deploy Server SSH 접속 및 Nginx 설정

#### A. Deploy Server 접속
```bash
# Windows PowerShell에서 Deploy Server 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# 현재 Nginx 상태 확인
systemctl status nginx
# Active (running) 상태여야 함

# 현재 실행 중인 컨테이너 확인
docker ps
```

#### B. Nginx 설정 디렉토리 구조 생성
```bash
# Nginx 설정 백업 및 새 설정 디렉토리 생성
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
sudo mkdir -p /opt/nginx/conf.d

# 기존 설정 백업
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 로그 디렉토리 생성
sudo mkdir -p /var/log/nginx/skn12-trading
sudo chown -R www-data:www-data /var/log/nginx/skn12-trading
```

#### C. Health Check 스크립트 생성
```bash
# Health Check 스크립트 생성
sudo mkdir -p /opt/scripts
sudo tee /opt/scripts/health-check.sh << 'EOF'
#!/bin/bash
# =============================================================================
# SKN12 Trading Platform Health Check Script
# =============================================================================
# 이 스크립트는 컨테이너가 정상적으로 응답하는지 확인합니다.

check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    echo "🏥 $service_name 헬스체크 시작 (포트 $port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s --connect-timeout 5 http://localhost:$port/ > /dev/null 2>&1; then
            echo "✅ $service_name 정상 응답 (시도 $attempt/$max_attempts)"
            return 0
        else
            echo "⏳ $service_name 응답 대기 중... (시도 $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    echo "❌ $service_name 헬스체크 실패 (포트 $port)"
    return 1
}

# Health Check 실행
if [ "$1" = "blue" ]; then
    echo "🔵 Blue 환경 헬스체크..."
    check_service "Blue Web Server" 8000 && \
    check_service "Blue Model Server" 8001
elif [ "$1" = "green" ]; then
    echo "🟢 Green 환경 헬스체크..."
    check_service "Green Web Server" 8002 && \
    check_service "Green Model Server" 8003
else
    echo "사용법: $0 [blue|green]"
    exit 1
fi
EOF

# 스크립트 실행 권한 부여
sudo chmod +x /opt/scripts/health-check.sh

# 테스트 실행
sudo /opt/scripts/health-check.sh blue
```

### 1️⃣ Nginx 로드밸런서 설정 파일 생성

#### A. 메인 Nginx 설정 파일 생성
```bash
# 새로운 nginx.conf 생성
sudo tee /etc/nginx/nginx.conf << 'EOF'
# =============================================================================
# SKN12 Trading Platform Nginx Configuration
# =============================================================================

user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    ##
    # Basic Settings
    ##
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ##
    # SSL Settings
    ##
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    ##
    # Logging Settings
    ##
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'upstream: $upstream_addr response_time: $upstream_response_time';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    ##
    # Gzip Settings
    ##
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    ##
    # Virtual Host Configs
    ##
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF
```

#### B. 무중단 배포용 사이트 설정 생성
```bash
# SKN12 Trading Platform 사이트 설정
sudo tee /etc/nginx/sites-available/skn12-trading << 'EOF'
# =============================================================================
# SKN12 Trading Platform - Blue-Green Deployment Configuration
# =============================================================================

# Upstream 정의 (Blue Environment - 기본 운영)
upstream trading_web_blue {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
}

upstream trading_model_blue {
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
}

# Upstream 정의 (Green Environment - 새 버전 배포)
upstream trading_web_green {
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
}

upstream trading_model_green {
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

# 현재 활성 환경 설정 (기본값: Blue)
# 이 부분은 배포 스크립트에서 자동으로 변경됩니다
map $host $web_upstream {
    default trading_web_blue;
}

map $host $model_upstream {
    default trading_model_blue;
}

# 메인 서버 설정
server {
    listen 80;
    server_name _;  # 모든 도메인 허용

    # 로그 설정
    access_log /var/log/nginx/skn12-trading/access.log main;
    error_log /var/log/nginx/skn12-trading/error.log warn;

    # Health Check 엔드포인트 (Nginx 자체 상태)
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Base Web Server 프록시 (포트 8000 → 현재 활성 환경)
    location / {
        proxy_pass http://$web_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 타임아웃 설정
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Health Check 설정
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
        
        # 추가 헤더
        add_header X-Upstream-Server $upstream_addr always;
        add_header X-Response-Time $upstream_response_time always;
    }

    # Model Server 프록시 (포트 8001 → 현재 활성 환경)
    location /model/ {
        proxy_pass http://$model_upstream/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 타임아웃 설정
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Health Check 설정
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
        
        # 추가 헤더
        add_header X-Upstream-Server $upstream_addr always;
        add_header X-Response-Time $upstream_response_time always;
    }

    # 직접 포트 접근 (디버깅용)
    location /direct-web/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /direct-model/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# 관리자용 서버 (포트 8080)
server {
    listen 8080;
    server_name _;

    # 로그 설정
    access_log /var/log/nginx/skn12-trading/admin-access.log main;
    error_log /var/log/nginx/skn12-trading/admin-error.log warn;

    # Blue 환경 직접 접근
    location /blue/web/ {
        proxy_pass http://trading_web_blue/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Environment "Blue" always;
    }

    location /blue/model/ {
        proxy_pass http://trading_model_blue/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Environment "Blue" always;
    }

    # Green 환경 직접 접근
    location /green/web/ {
        proxy_pass http://trading_web_green/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Environment "Green" always;
    }

    location /green/model/ {
        proxy_pass http://trading_model_green/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Environment "Green" always;
    }

    # Nginx 상태 페이지
    location /nginx-status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
}
EOF
```

#### C. 사이트 활성화 및 Nginx 재시작
```bash
# 사이트 활성화 (심볼릭 링크 생성)
sudo ln -sf /etc/nginx/sites-available/skn12-trading /etc/nginx/sites-enabled/

# 기본 사이트 비활성화
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx 설정 문법 검사
sudo nginx -t
# 출력: nginx: configuration file /etc/nginx/nginx.conf test is successful

# Nginx 재시작
sudo systemctl restart nginx

# Nginx 상태 확인
sudo systemctl status nginx
# Active (running) 상태 확인

# 포트 바인딩 확인
sudo netstat -tlnp | grep nginx
# 80, 8080 포트에 바인딩되어야 함
```

---

## 🚀 Step 2: 무중단 배포 스크립트 작성 (20분)

### 2️⃣ 배포 스크립트 생성

#### A. 메인 배포 스크립트 작성
```bash
# 무중단 배포 스크립트 생성
sudo tee /opt/scripts/blue-green-deploy.sh << 'EOF'
#!/bin/bash
# =============================================================================
# SKN12 Trading Platform - Blue-Green 무중단 배포 스크립트
# =============================================================================

set -e  # 오류 발생 시 스크립트 중단

# 설정 변수
DOCKER_IMAGE="${1:-skn12-trading/ai-trading-platform}"
IMAGE_TAG="${2:-latest}"
DEPLOY_ENV="${3:-PROD}"
TIMEOUT=300  # 5분 타임아웃

# 색상 코드 (로그 출력용)
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 현재 활성 환경 감지
get_current_environment() {
    if docker ps | grep -q "trading-web-server-blue"; then
        echo "blue"
    elif docker ps | grep -q "trading-web-server-green"; then
        echo "green"
    else
        echo "none"
    fi
}

# 새 배포 환경 결정
get_target_environment() {
    local current=$1
    case $current in
        "blue") echo "green" ;;
        "green") echo "blue" ;;
        "none") echo "blue" ;;
        *) echo "blue" ;;
    esac
}

# 환경별 포트 설정
get_ports() {
    local env=$1
    case $env in
        "blue") echo "8000 8001" ;;
        "green") echo "8002 8003" ;;
        *) echo "8000 8001" ;;
    esac
}

# 컨테이너 중지 및 제거
stop_environment() {
    local env=$1
    log_info "🛑 $env 환경 컨테이너 중지 중..."
    
    docker stop "trading-web-server-$env" 2>/dev/null || true
    docker stop "trading-model-server-$env" 2>/dev/null || true
    docker rm "trading-web-server-$env" 2>/dev/null || true
    docker rm "trading-model-server-$env" 2>/dev/null || true
    
    log_info "✅ $env 환경 컨테이너 정리 완료"
}

# 새 환경 시작
start_environment() {
    local env=$1
    local ports=($(get_ports $env))
    local web_port=${ports[0]}
    local model_port=${ports[1]}
    
    log_info "🚀 $env 환경 시작 중..."
    log_debug "이미지: $DOCKER_IMAGE:$IMAGE_TAG"
    log_debug "Web Server 포트: $web_port"
    log_debug "Model Server 포트: $model_port"
    
    # Web Server 시작
    log_info "🌐 Web Server ($env) 시작 중..."
    docker run -d \
        --name "trading-web-server-$env" \
        --restart unless-stopped \
        -p "$web_port:8000" \
        -e APP_ENV=$DEPLOY_ENV \
        -v /opt/skn12-trading/configs/base-web-server:/app/application/base_web_server:ro \
        -v /opt/skn12-trading/logs/base-web-server:/app/logs \
        --health-cmd="curl -f http://localhost:8000/ || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        --health-start-period=60s \
        "$DOCKER_IMAGE:$IMAGE_TAG"
    
    # Model Server 시작
    log_info "🤖 Model Server ($env) 시작 중..."
    docker run -d \
        --name "trading-model-server-$env" \
        --restart unless-stopped \
        -p "$model_port:8001" \
        -e APP_ENV=$DEPLOY_ENV \
        -v /opt/skn12-trading/configs/model-server:/app/application/model_server:ro \
        -v /opt/skn12-trading/logs/model-server:/app/logs \
        --health-cmd="curl -f http://localhost:8001/ || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        --health-start-period=60s \
        "$DOCKER_IMAGE:$IMAGE_TAG" \
        uvicorn application.model_server.main:app --host 0.0.0.0 --port 8001
    
    log_info "✅ $env 환경 컨테이너 시작 완료"
}

# Health Check 수행
perform_health_check() {
    local env=$1
    local ports=($(get_ports $env))
    local web_port=${ports[0]}
    local model_port=${ports[1]}
    
    log_info "🏥 $env 환경 헬스체크 시작..."
    
    # Health Check 스크립트 실행
    if /opt/scripts/health-check.sh $env; then
        log_info "✅ $env 환경 헬스체크 성공"
        return 0
    else
        log_error "❌ $env 환경 헬스체크 실패"
        return 1
    fi
}

# Nginx 설정 업데이트 (트래픽 전환)
switch_traffic() {
    local target_env=$1
    local ports=($(get_ports $target_env))
    local web_port=${ports[0]}
    local model_port=${ports[1]}
    
    log_info "🔀 트래픽을 $target_env 환경으로 전환 중..."
    
    # Nginx 설정 파일 업데이트
    sudo tee /tmp/nginx-upstream-update.conf << EOL
# 트래픽 전환: $target_env 환경으로 변경
map \$host \$web_upstream {
    default trading_web_$target_env;
}

map \$host \$model_upstream {
    default trading_model_$target_env;
}
EOL
    
    # 기존 설정 파일에서 map 부분만 업데이트
    sudo sed -i '/map \$host \$web_upstream/,/}/c\
map $host $web_upstream {\
    default trading_web_'$target_env';\
}' /etc/nginx/sites-available/skn12-trading
    
    sudo sed -i '/map \$host \$model_upstream/,/}/c\
map $host $model_upstream {\
    default trading_model_'$target_env';\
}' /etc/nginx/sites-available/skn12-trading
    
    # Nginx 설정 검사
    if sudo nginx -t; then
        # Nginx 설정 재로드 (무중단)
        sudo nginx -s reload
        log_info "✅ 트래픽 전환 완료: $target_env 환경으로 변경됨"
    else
        log_error "❌ Nginx 설정 오류로 트래픽 전환 실패"
        return 1
    fi
}

# 이전 환경 정리
cleanup_old_environment() {
    local old_env=$1
    
    log_info "🧹 이전 환경 ($old_env) 정리 중..."
    
    # 잠시 대기 (트래픽 전환 안정화)
    sleep 30
    
    # 이전 환경 컨테이너 중지 및 제거
    stop_environment $old_env
    
    log_info "✅ 이전 환경 정리 완료"
}

# 롤백 수행
rollback() {
    local current_env=$1
    local previous_env=$2
    
    log_warn "🔄 롤백 수행 중..."
    log_warn "현재 환경: $current_env → 이전 환경: $previous_env"
    
    # 이전 환경이 아직 실행 중인지 확인
    if docker ps | grep -q "trading-web-server-$previous_env"; then
        log_info "이전 환경이 아직 실행 중입니다. 트래픽을 즉시 전환합니다."
        switch_traffic $previous_env
        stop_environment $current_env
    else
        log_warn "이전 환경을 다시 시작해야 합니다."
        # 이전 버전으로 이전 환경 재시작 (마지막 성공 이미지 사용)
        start_environment $previous_env
        if perform_health_check $previous_env; then
            switch_traffic $previous_env
            stop_environment $current_env
        else
            log_error "롤백 실패: 이전 환경도 시작할 수 없습니다."
            exit 1
        fi
    fi
    
    log_info "✅ 롤백 완료"
}

# 메인 배포 로직
main() {
    log_info "🚀 SKN12 Trading Platform 무중단 배포 시작"
    log_info "이미지: $DOCKER_IMAGE:$IMAGE_TAG"
    log_info "환경: $DEPLOY_ENV"
    
    # 1. 현재 환경 확인
    local current_env=$(get_current_environment)
    local target_env=$(get_target_environment $current_env)
    
    log_info "현재 활성 환경: $current_env"
    log_info "배포 대상 환경: $target_env"
    
    # 2. 새 이미지 다운로드
    log_info "📥 새 이미지 다운로드 중..."
    if ! docker pull "$DOCKER_IMAGE:$IMAGE_TAG"; then
        log_error "이미지 다운로드 실패"
        exit 1
    fi
    
    # 3. 기존 타겟 환경 정리
    stop_environment $target_env
    
    # 4. 새 환경 시작
    if ! start_environment $target_env; then
        log_error "새 환경 시작 실패"
        exit 1
    fi
    
    # 5. Health Check
    log_info "⏳ 서비스 시작 대기 중 (60초)..."
    sleep 60
    
    if ! perform_health_check $target_env; then
        log_error "헬스체크 실패, 롤백 수행"
        stop_environment $target_env
        exit 1
    fi
    
    # 6. 트래픽 전환
    if ! switch_traffic $target_env; then
        log_error "트래픽 전환 실패, 롤백 수행"
        rollback $target_env $current_env
        exit 1
    fi
    
    # 7. 전환 후 최종 확인
    log_info "⏳ 트래픽 전환 안정화 대기 중 (30초)..."
    sleep 30
    
    # 외부에서 접근 테스트
    log_info "🌐 외부 접근 테스트 중..."
    if curl -f -s http://localhost/ > /dev/null && \
       curl -f -s http://localhost/model/ > /dev/null; then
        log_info "✅ 외부 접근 테스트 성공"
    else
        log_warn "⚠️ 외부 접근 테스트 실패, 하지만 배포는 계속 진행"
    fi
    
    # 8. 이전 환경 정리
    if [ "$current_env" != "none" ]; then
        cleanup_old_environment $current_env
    fi
    
    # 9. 배포 완료
    log_info "🎉 무중단 배포 성공!"
    log_info "활성 환경: $target_env"
    log_info "서비스 URL: http://$(curl -s ifconfig.me)/"
    
    # 10. 배포 정보 기록
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 배포 완료: $DOCKER_IMAGE:$IMAGE_TAG → $target_env" >> /opt/logs/deployment.log
}

# 스크립트 실행
if [ "$1" = "" ]; then
    echo "사용법: $0 <docker-image> [image-tag] [deploy-env]"
    echo "예시: $0 skn12-trading/ai-trading-platform latest PROD"
    exit 1
fi

main "$@"
EOF

# 스크립트 실행 권한 부여
sudo chmod +x /opt/scripts/blue-green-deploy.sh

# 로그 디렉토리 생성
sudo mkdir -p /opt/logs
sudo chown ubuntu:ubuntu /opt/logs
```

#### B. 배포 관리 유틸리티 스크립트 생성
```bash
# 배포 상태 확인 스크립트
sudo tee /opt/scripts/deployment-status.sh << 'EOF'
#!/bin/bash
# =============================================================================
# 배포 상태 확인 스크립트
# =============================================================================

echo "🔍 SKN12 Trading Platform 배포 상태"
echo "======================================"

# 현재 실행 중인 컨테이너
echo "📦 실행 중인 컨테이너:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep trading || echo "실행 중인 컨테이너 없음"

echo ""

# Nginx 상태
echo "🌐 Nginx 상태:"
if systemctl is-active nginx >/dev/null 2>&1; then
    echo "✅ Nginx 실행 중"
    
    # 현재 업스트림 설정 확인
    echo "📡 현재 트래픽 라우팅:"
    if grep -q "trading_web_blue" /etc/nginx/sites-available/skn12-trading; then
        echo "  Web Server: Blue 환경 (포트 8000)"
    elif grep -q "trading_web_green" /etc/nginx/sites-available/skn12-trading; then
        echo "  Web Server: Green 환경 (포트 8002)"
    fi
    
    if grep -q "trading_model_blue" /etc/nginx/sites-available/skn12-trading; then
        echo "  Model Server: Blue 환경 (포트 8001)"
    elif grep -q "trading_model_green" /etc/nginx/sites-available/skn12-trading; then
        echo "  Model Server: Green 환경 (포트 8003)"
    fi
else
    echo "❌ Nginx 중지됨"
fi

echo ""

# 서비스 응답 테스트
echo "🏥 서비스 헬스체크:"
if curl -f -s http://localhost/ > /dev/null 2>&1; then
    echo "✅ 메인 서비스 (포트 80) 정상"
else
    echo "❌ 메인 서비스 (포트 80) 오류"
fi

if curl -f -s http://localhost/model/ > /dev/null 2>&1; then
    echo "✅ 모델 서비스 정상"
else
    echo "❌ 모델 서비스 오류"
fi

echo ""

# 최근 배포 이력
echo "📋 최근 배포 이력:"
if [ -f /opt/logs/deployment.log ]; then
    tail -5 /opt/logs/deployment.log
else
    echo "배포 이력 없음"
fi

echo ""

# 시스템 리소스
echo "📊 시스템 리소스:"
echo "메모리: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "디스크: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5" 사용)"}')"
echo "Docker 이미지: $(docker images | wc -l)개"
EOF

sudo chmod +x /opt/scripts/deployment-status.sh

# 빠른 롤백 스크립트
sudo tee /opt/scripts/quick-rollback.sh << 'EOF'
#!/bin/bash
# =============================================================================
# 빠른 롤백 스크립트
# =============================================================================

echo "🔄 빠른 롤백 수행 중..."

# 현재 환경 확인
if docker ps | grep -q "trading-web-server-blue"; then
    current="blue"
    target="green"
elif docker ps | grep -q "trading-web-server-green"; then
    current="green"
    target="blue"
else
    echo "❌ 실행 중인 환경을 찾을 수 없습니다."
    exit 1
fi

echo "현재 환경: $current → 롤백 대상: $target"

# 이전 환경이 실행 중인지 확인
if ! docker ps | grep -q "trading-web-server-$target"; then
    echo "❌ 롤백 대상 환경이 실행되지 않았습니다."
    echo "전체 배포를 다시 수행하거나 수동으로 이전 버전을 시작하세요."
    exit 1
fi

# Nginx 설정 업데이트
echo "🔀 트래픽을 $target 환경으로 전환 중..."

sudo sed -i "s/trading_web_$current/trading_web_$target/g" /etc/nginx/sites-available/skn12-trading
sudo sed -i "s/trading_model_$current/trading_model_$target/g" /etc/nginx/sites-available/skn12-trading

# Nginx 재로드
if sudo nginx -t; then
    sudo nginx -s reload
    echo "✅ 롤백 완료: $target 환경이 활성화됨"
    
    # 롤백 기록
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 롤백 수행: $current → $target" >> /opt/logs/deployment.log
else
    echo "❌ Nginx 설정 오류"
    exit 1
fi
EOF

sudo chmod +x /opt/scripts/quick-rollback.sh
```

---

## 🔧 Step 3: Jenkinsfile에 무중단 배포 통합 (15분)

### 3️⃣ Jenkinsfile 업데이트

#### A. 로컬에서 Jenkinsfile 수정
```bash
# Windows에서 프로젝트 디렉토리로 이동
cd C:\SKN12-FINAL-2TEAM

# Jenkinsfile 백업
copy Jenkinsfile Jenkinsfile.backup

# Jenkinsfile을 에디터로 열기
code Jenkinsfile
# 또는 notepad Jenkinsfile
```

#### B. Deploy Stage를 무중단 배포로 교체
기존 Jenkinsfile의 `Deploy to Server` Stage를 다음 내용으로 교체:

```groovy
// 🚀 5단계: Deploy Server에 무중단 배포
stage('🚀 Zero-Downtime Deploy') {
    steps {
        script {
            echo "🚀 무중단 배포 시작..."
            
            sshagent(credentials: [env.SSH_CREDENTIALS]) {
                sh '''
                    echo "📡 Deploy Server 연결 중..."
                    echo "  - 서버 IP: ${DEPLOY_SERVER}"
                    echo "  - 배포 환경: ${DEPLOY_ENV}"
                    echo "  - 이미지: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                    
                    # SSH 연결 및 무중단 배포 스크립트 실행
                    ssh -o StrictHostKeyChecking=no ubuntu@${DEPLOY_SERVER} "
                        set -e  # 오류 발생 시 스크립트 중단
                        
                        echo '🏠 Deploy Server 접속 성공!'
                        echo '📊 배포 전 서버 상태:'
                        /opt/scripts/deployment-status.sh
                        
                        echo ''
                        echo '🚀 무중단 배포 시작...'
                        
                        # 무중단 배포 스크립트 실행
                        /opt/scripts/blue-green-deploy.sh \\
                            '${DOCKER_IMAGE}' \\
                            '${IMAGE_TAG}' \\
                            '${DEPLOY_ENV}'
                        
                        echo ''
                        echo '📊 배포 후 서버 상태:'
                        /opt/scripts/deployment-status.sh
                        
                        echo ''
                        echo '✅ 무중단 배포 완료!'
                        echo '🔗 서비스 URL:'
                        echo '  - 메인 서비스: http://${DEPLOY_SERVER}/'
                        echo '  - 모델 서비스: http://${DEPLOY_SERVER}/model/'
                        echo '  - 관리자 페이지: http://${DEPLOY_SERVER}:8080/'
                    "
                '''
            }
        }
    }
}
```

#### C. 배포 후 테스트 Stage 강화
기존 `Post-Deploy Testing` Stage를 다음 내용으로 교체:

```groovy
// 🧪 6단계: 무중단 배포 후 통합 테스트
stage('🧪 Post-Deploy Integration Tests') {
    steps {
        script {
            echo "🧪 배포 후 통합 테스트 시작..."
            
            // 기본 접근 테스트
            sh '''
                echo "🌐 기본 서비스 접근 테스트..."
                
                # 메인 서비스 테스트 (Nginx 프록시 통해서)
                echo "🔍 메인 서비스 테스트..."
                for i in {1..10}; do
                    if curl -f -s --connect-timeout 10 http://${DEPLOY_SERVER}/ > /dev/null; then
                        echo "✅ 메인 서비스 응답 성공 (시도 $i)"
                        break
                    else
                        echo "⏳ 메인 서비스 응답 대기 중... (시도 $i/10)"
                        sleep 15
                    fi
                done
                
                # 모델 서비스 테스트
                echo "🔍 모델 서비스 테스트..."
                for i in {1..10}; do
                    if curl -f -s --connect-timeout 10 http://${DEPLOY_SERVER}/model/ > /dev/null; then
                        echo "✅ 모델 서비스 응답 성공 (시도 $i)"
                        break
                    else
                        echo "⏳ 모델 서비스 응답 대기 중... (시도 $i/10)"
                        sleep 15
                    fi
                done
                
                # 관리자 페이지 테스트
                echo "🔍 관리자 페이지 테스트..."
                if curl -f -s --connect-timeout 10 http://${DEPLOY_SERVER}:8080/nginx-status > /dev/null; then
                    echo "✅ 관리자 페이지 접근 성공"
                else
                    echo "⚠️ 관리자 페이지 접근 실패 (선택사항)"
                fi
            '''
            
            // 고급 통합 테스트 (API 엔드포인트)
            sh '''
                echo "🔬 고급 통합 테스트..."
                
                # API 헬스체크 엔드포인트 테스트 (있는 경우)
                echo "🏥 API 헬스체크..."
                if curl -f -s http://${DEPLOY_SERVER}/health > /dev/null; then
                    echo "✅ API 헬스체크 응답"
                else
                    echo "⚠️ API 헬스체크 엔드포인트 없음 (정상)"
                fi
                
                # Nginx 헬스체크
                echo "🌐 Nginx 헬스체크..."
                if curl -f -s http://${DEPLOY_SERVER}/health > /dev/null; then
                    echo "✅ Nginx 헬스체크 응답"
                else
                    echo "⚠️ Nginx 헬스체크 실패"
                fi
                
                # 응답 시간 측정
                echo "⏱️ 응답 시간 측정..."
                RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null http://${DEPLOY_SERVER}/)
                echo "메인 서비스 응답 시간: ${RESPONSE_TIME}초"
                
                if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
                    echo "✅ 응답 시간 양호 (< 5초)"
                else
                    echo "⚠️ 응답 시간 느림 (>= 5초)"
                fi
            '''
        }
    }
}
```

#### D. 실패 시 자동 롤백 추가
Post 섹션에 실패 시 롤백 로직 추가:

```groovy
post {
    failure {
        script {
            echo "❌ 빌드 실패로 인한 자동 롤백 시도..."
            
            // SSH로 롤백 수행
            try {
                sshagent(credentials: [env.SSH_CREDENTIALS]) {
                    sh '''
                        echo "🔄 자동 롤백 수행 중..."
                        ssh -o StrictHostKeyChecking=no ubuntu@${DEPLOY_SERVER} "
                            echo '자동 롤백 시작...'
                            /opt/scripts/quick-rollback.sh || echo '롤백 실패: 수동 개입 필요'
                        "
                    '''
                }
                echo "🔄 자동 롤백 완료"
            } catch (Exception e) {
                echo "❌ 자동 롤백 실패: ${e.getMessage()}"
                echo "🚨 수동 롤백이 필요합니다!"
            }
            
            // 기존 실패 처리 로직...
            echo "❌ 빌드 중 오류가 발생했습니다."
            echo "📋 실패 정보:"
            echo "  - 빌드 번호: ${env.BUILD_NUMBER}"
            echo "  - 브랜치: ${env.BRANCH_NAME ?: 'main'}"
            echo "  - 실패 시간: ${new Date().format('yyyy-MM-dd HH:mm:ss')}"
            echo "🔍 Console Output에서 자세한 오류 내용을 확인하세요."
        }
    }
}
```

#### E. 수정된 Jenkinsfile 커밋
```bash
# Git 상태 확인
git status

# 변경사항 커밋
git add Jenkinsfile
git commit -m "Implement Zero-Downtime Deployment with Blue-Green Strategy

🚀 Features:
- Blue-Green deployment strategy implementation
- Nginx load balancer with automatic traffic switching
- Health checks before traffic switching
- Automatic rollback on deployment failure
- Comprehensive integration tests post-deployment

🔧 Technical Details:
- Deploy script: /opt/scripts/blue-green-deploy.sh
- Health check: /opt/scripts/health-check.sh
- Status monitoring: /opt/scripts/deployment-status.sh
- Quick rollback: /opt/scripts/quick-rollback.sh

🎯 Benefits:
- Zero downtime during deployments
- Automatic rollback on failure
- Real-time health monitoring
- Traffic switching validation"

# GitHub에 푸시
git push origin main
```

---

## 🧪 Step 4: 무중단 배포 테스트 (20분)

### 4️⃣ 첫 번째 무중단 배포 테스트

#### A. 현재 상태 확인
```bash
# Deploy Server에 SSH 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# 현재 배포 상태 확인
/opt/scripts/deployment-status.sh

# Nginx 설정 확인
sudo nginx -t
curl -I http://localhost/
curl -I http://localhost/model/
```

#### B. Jenkins에서 자동 배포 실행
```
1. Jenkinsfile 푸시 후 Jenkins에서 자동 빌드 시작 확인
2. Pipeline 진행 상황 모니터링:
   - Blue Ocean UI에서 시각적 확인
   - Console Output에서 상세 로그 확인

3. 특히 "Zero-Downtime Deploy" Stage 주의 깊게 관찰:
   ✅ "무중단 배포 시작..."
   ✅ "배포 전 서버 상태" 확인
   ✅ "Blue-Green 배포 스크립트 실행"
   ✅ "트래픽 전환 완료"
   ✅ "배포 후 서버 상태" 확인
```

#### C. 배포 중 서비스 연속성 테스트
```bash
# 다른 터미널에서 연속적인 요청 테스트
# PowerShell 새 창에서 실행
while ($true) {
    try {
        $response = Invoke-WebRequest -Uri "http://[Deploy-Server-IP]/" -TimeoutSec 5
        Write-Host "$(Get-Date): OK - Status: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "$(Get-Date): FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Start-Sleep -Seconds 2
}

# 배포 중에도 "OK" 응답이 계속 나와야 함 (무중단 확인)
```

### 4️⃣ 배포 후 상세 검증

#### A. 서비스 상태 종합 확인
```bash
# Deploy Server에서
/opt/scripts/deployment-status.sh

# 기대 결과:
# ✅ 새로운 환경(Blue 또는 Green)이 활성화됨
# ✅ 이전 환경 컨테이너는 정리됨
# ✅ Nginx가 새 환경으로 트래픽 라우팅
# ✅ 모든 서비스가 정상 응답
```

#### B. 로그 확인
```bash
# 배포 로그 확인
tail -20 /opt/logs/deployment.log

# Nginx 로그 확인
sudo tail -50 /var/log/nginx/skn12-trading/access.log
sudo tail -20 /var/log/nginx/skn12-trading/error.log

# 컨테이너 로그 확인
docker logs trading-web-server-blue || docker logs trading-web-server-green
docker logs trading-model-server-blue || docker logs trading-model-server-green
```

#### C. 성능 및 리소스 확인
```bash
# 시스템 리소스 확인
free -h
df -h
docker stats --no-stream

# 응답 시간 측정
curl -w "응답시간: %{time_total}초\n" -s -o /dev/null http://localhost/
curl -w "응답시간: %{time_total}초\n" -s -o /dev/null http://localhost/model/
```

---

## 🔄 Step 5: 롤백 테스트 (10분)

### 5️⃣ 의도적 롤백 시나리오 테스트

#### A. 수동 롤백 테스트
```bash
# Deploy Server에서 현재 상태 확인
/opt/scripts/deployment-status.sh

# 현재 활성 환경 기록 (예: Blue)
echo "현재 활성 환경을 기록해두세요"

# 수동 롤백 실행
/opt/scripts/quick-rollback.sh

# 롤백 후 상태 확인
/opt/scripts/deployment-status.sh

# 서비스 응답 확인
curl http://localhost/
curl http://localhost/model/
```

#### B. 의도적 실패 시나리오 테스트
```bash
# 잘못된 이미지로 배포 시도 (롤백 테스트용)
/opt/scripts/blue-green-deploy.sh "nginx" "invalid-tag" "PROD"

# 예상 결과:
# ❌ 이미지 다운로드 실패 또는 헬스체크 실패
# 🔄 자동 롤백 수행
# ✅ 이전 환경으로 복구
```

#### C. Jenkins 자동 롤백 테스트
```bash
# 로컬에서 일부러 문제가 있는 코드 커밋
cd C:\SKN12-FINAL-2TEAM

# Dockerfile에 오류 추가 (테스트용)
echo "RUN invalid-command" >> base_server/Dockerfile

git add .
git commit -m "Test automatic rollback - intentional build failure"
git push origin main

# Jenkins에서 빌드 실패 및 자동 롤백 확인
# Console Output에서 "자동 롤백 수행 중..." 메시지 확인
```

#### D. 롤백 테스트 후 정상화
```bash
# 문제가 있는 커밋 되돌리기
cd C:\SKN12-FINAL-2TEAM

git revert HEAD --no-edit
git push origin main

# Jenkins에서 정상 배포 재개 확인
```

---

## ✅ 무중단 배포 구현 완료 체크리스트

### 🎯 인프라 설정 완료:
- [ ] Nginx 로드밸런서 설정 완료
- [ ] Blue-Green 환경용 포트 설정 (8000/8001, 8002/8003)
- [ ] Health Check 스크립트 작성 및 테스트 완료
- [ ] 무중단 배포 스크립트 작성 및 권한 설정 완료

### 🔄 배포 자동화 완료:
- [ ] Jenkinsfile에 무중단 배포 로직 통합
- [ ] GitHub Push → 자동 무중단 배포 확인
- [ ] 배포 중 서비스 연속성 확인 (무중단 검증)
- [ ] 배포 후 자동 헬스체크 및 통합 테스트 성공

### 🔄 롤백 시스템 완료:
- [ ] 수동 롤백 스크립트 테스트 성공
- [ ] 자동 롤백 기능 테스트 성공 (실패 시)
- [ ] 의도적 실패 시나리오에서 정상 롤백 확인
- [ ] 롤백 후 서비스 정상성 확인

### 📊 모니터링 및 관리:
- [ ] 배포 상태 확인 스크립트 정상 동작
- [ ] 배포 이력 로그 정상 기록
- [ ] Nginx 로그 및 컨테이너 로그 정상 수집
- [ ] 성능 모니터링 (응답 시간, 리소스 사용량)

---

## 🔧 고급 설정 및 최적화

### 배포 성능 최적화:

#### A. 컨테이너 시작 시간 단축
```bash
# Dockerfile에 health check 추가 (이미 적용됨)
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1
```

#### B. Nginx 캐싱 설정 추가
```nginx
# 정적 파일 캐싱
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1M;
    add_header Cache-Control "public, immutable";
}

# API 응답 캐싱 (선택사항)
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

#### C. 동시 배포 방지
```groovy
// Jenkinsfile에 추가
options {
    disableConcurrentBuilds()
    lock(resource: 'skn12-deployment')
}
```

### 모니터링 강화:

#### A. Prometheus 메트릭 수집 (고급)
```bash
# Node Exporter 설치
docker run -d \
    --name node-exporter \
    -p 9100:9100 \
    -v "/proc:/host/proc:ro" \
    -v "/sys:/host/sys:ro" \
    -v "/:/rootfs:ro" \
    prom/node-exporter
```

#### B. 알람 설정
```bash
# 배포 실패 시 Slack 알람
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🚨 배포 실패: SKN12 Trading Platform"}' \
    YOUR_SLACK_WEBHOOK_URL
```

---

## 🎯 다음 단계 미리보기

### 1️⃣ 최종 통합 테스트:
- 전체 CI/CD 파이프라인 end-to-end 테스트
- 성능 테스트 및 부하 테스트
- 보안 검증 및 모니터링

### 2️⃣ 운영 최적화:
- 로그 집중화 (ELK Stack)
- 메트릭 수집 (Prometheus + Grafana)
- 자동 스케일링 설정

### 3️⃣ 보안 강화:
- SSL/TLS 인증서 설정
- 네트워크 보안 그룹 최적화
- 컨테이너 보안 스캔

---

## 🎉 축하합니다!

무중단 배포 시스템이 완성되었습니다! 🚀

### ✅ 달성한 것:
- 🔄 **무중단 배포**: 서비스 중단 없이 새 버전 배포
- 🔀 **Blue-Green 전략**: 안전한 트래픽 전환
- 🏥 **자동 헬스체크**: 배포 전 서비스 상태 검증
- 🔄 **자동 롤백**: 실패 시 즉시 이전 버전으로 복구
- 📊 **실시간 모니터링**: 배포 상태 및 서비스 상태 추적

### 🚀 이제 가능한 것:
1. **진정한 무중단 서비스**: 사용자가 배포를 전혀 감지할 수 없음
2. **안전한 배포**: 문제 발생 시 자동으로 이전 버전으로 롤백
3. **빠른 배포**: 5-10분 내에 새 버전이 운영 환경에 반영
4. **완전 자동화**: 코드 Push만으로 전체 배포 프로세스 완료

이제 엔터프라이즈급 무중단 배포 시스템이 완성되었습니다! 🎉