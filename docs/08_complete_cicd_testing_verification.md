# 🧪 완전한 CI/CD 파이프라인 테스트 및 검증 가이드

> **목적**: 구축한 전체 CI/CD 파이프라인이 정상적으로 동작하는지 종합적으로 테스트하고 검증합니다. 실제 운영 환경에서 발생할 수 있는 다양한 시나리오를 테스트합니다.
>
> **💡 이 가이드의 범위**: 개발자 코드 작성부터 운영 서비스 배포까지 전체 과정을 검증합니다.

---

## 🏗️ 전체 CI/CD 파이프라인 아키텍처 검증

### 구축된 시스템 전체 구조

```
👨‍💻 개발자 (Windows)
    ↓ (git push)
📱 GitHub Repository
    ↓ (Webhook)
🏗️ Jenkins Server (EC2)
    ├─ 📥 소스코드 체크아웃
    ├─ 🧪 코드 품질 검사
    ├─ 🐳 Docker 이미지 빌드
    ├─ 📤 Docker Hub 업로드
    └─ 🚀 무중단 배포 실행
         ↓
🚀 Deploy Server (EC2)
    ├─ 🔵 Blue Environment (현재 운영)
    ├─ 🟢 Green Environment (새 배포)
    ├─ 📡 Nginx Load Balancer
    └─ 🏥 Health Check & 트래픽 전환
         ↓
👥 실제 사용자들
```

### 검증할 주요 구성 요소

| 구성 요소 | 상태 | 검증 방법 |
|----------|------|-----------|
| **GitHub Webhook** | ✅ | Push 이벤트 → Jenkins 자동 트리거 |
| **Jenkins Pipeline** | ✅ | 6단계 Pipeline 정상 실행 |
| **Docker Hub 연동** | ✅ | 이미지 자동 업로드/다운로드 |
| **무중단 배포** | ✅ | Blue-Green 전환 무중단 확인 |
| **자동 롤백** | ✅ | 실패 시 자동 이전 버전 복구 |
| **모니터링** | ✅ | 실시간 상태 확인 및 로그 수집 |

---

## 📋 Step 1: 전체 시스템 상태 점검 (15분)

### 1️⃣ 인프라 상태 종합 확인

#### A. AWS EC2 인스턴스 상태 확인
```bash
# Windows PowerShell에서 각 서버 접속 테스트

# Jenkins Server 상태 확인
echo "🔍 Jenkins Server 상태 확인..."
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-Server-IP] "
    echo '📊 Jenkins Server 시스템 정보:'
    echo '  - 호스트명:' \$(hostname)
    echo '  - 업타임:' \$(uptime | cut -d',' -f1)
    echo '  - 메모리:' \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')
    echo '  - 디스크:' \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2\" (\"\$5\" 사용)\"}')
    echo ''
    echo '🐳 Docker 상태:'
    docker --version
    docker ps | grep jenkins-master || echo '❌ Jenkins 컨테이너 없음'
    echo ''
    echo '🌐 네트워크 연결:'
    curl -I -s --connect-timeout 5 https://github.com | head -1 || echo '❌ GitHub 연결 실패'
    curl -I -s --connect-timeout 5 https://hub.docker.com | head -1 || echo '❌ Docker Hub 연결 실패'
"

echo ""

# Deploy Server 상태 확인  
echo "🔍 Deploy Server 상태 확인..."
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP] "
    echo '📊 Deploy Server 시스템 정보:'
    echo '  - 호스트명:' \$(hostname)
    echo '  - 업타임:' \$(uptime | cut -d',' -f1)
    echo '  - 메모리:' \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')
    echo '  - 디스크:' \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2\" (\"\$5\" 사용)\"}')
    echo ''
    echo '🐳 Docker 상태:'
    docker --version
    docker ps | grep trading || echo '⚠️ 실행 중인 애플리케이션 컨테이너 없음'
    echo ''
    echo '🌐 Nginx 상태:'
    systemctl is-active nginx && echo '✅ Nginx 실행 중' || echo '❌ Nginx 중지됨'
    curl -I -s http://localhost/ | head -1 || echo '❌ 로컬 웹 서버 응답 없음'
"
```

#### B. Jenkins 웹 UI 접근 테스트
```bash
# Jenkins 웹 UI 접근성 확인
echo "🔍 Jenkins 웹 UI 접근 테스트..."

# PowerShell에서 HTTP 요청 테스트
$jenkinsUrl = "http://[Jenkins-Server-IP]:18080"
try {
    $response = Invoke-WebRequest -Uri $jenkinsUrl -TimeoutSec 10
    Write-Host "✅ Jenkins 웹 UI 접근 성공 (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Jenkins 웹 UI 접근 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# Deploy Server 웹 서비스 접근 테스트
$deployUrl = "http://[Deploy-Server-IP]"
try {
    $response = Invoke-WebRequest -Uri $deployUrl -TimeoutSec 10
    Write-Host "✅ Deploy Server 웹 서비스 접근 성공 (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Deploy Server 웹 서비스 접근 실패: $($_.Exception.Message)" -ForegroundColor Red
}
```

#### C. GitHub 저장소 및 Webhook 상태 확인
```
1. 웹 브라우저에서 GitHub 저장소 접속
2. Settings → Webhooks → 생성한 Webhook 클릭
3. "Recent Deliveries" 섹션에서 최근 전송 기록 확인:
   - ✅ 최근 전송이 성공적이어야 함 (200 응답)
   - ❌ 실패가 계속되면 URL이나 Jenkins 상태 점검 필요
```

### 1️⃣ Jenkins Credentials 및 설정 확인

#### A. Jenkins 로그인 및 Credentials 확인
```
1. Jenkins 웹 UI 접속: http://[Jenkins-Server-IP]:18080
2. 로그인: admin / skn12-jenkins-2025!
3. "Manage Jenkins" → "Credentials" → "System" → "Global credentials"
4. 등록된 Credentials 확인:
   ✅ github-token (Secret text)
   ✅ dockerhub-credentials (Username with password)
   ✅ deploy-server-ssh-key (SSH Username with private key)
```

#### B. Job 설정 확인
```
1. Jenkins Dashboard → "SKN12-Trading-Platform-CI" Job 클릭
2. "Configure" 클릭하여 설정 확인:
   ✅ Pipeline script from SCM 설정
   ✅ GitHub 저장소 URL 정확성
   ✅ Credentials 올바른 선택
   ✅ Branches to build: */main
   ✅ Script Path: Jenkinsfile
```

---

## 🧪 Step 2: 기본 CI/CD 파이프라인 테스트 (20분)

### 2️⃣ 단순 변경사항으로 전체 파이프라인 테스트

#### A. 테스트용 코드 변경 생성
```bash
# 프로젝트 디렉토리로 이동
cd C:\SKN12-FINAL-2TEAM

# 현재 Git 상태 확인
git status
git log --oneline -5

# 간단한 테스트 파일 생성
$testContent = @"
# CI/CD 파이프라인 테스트 로그

## 테스트 정보
- 테스트 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 테스트 목적: 전체 CI/CD 파이프라인 검증
- 테스트 버전: v1.0.$(Get-Random -Minimum 100 -Maximum 999)

## 변경 사항
- 파이프라인 테스트용 파일 추가
- 무중단 배포 검증
- 자동 롤백 시스템 확인

## 기대 결과
1. GitHub Webhook 자동 트리거 ✅
2. Jenkins Pipeline 6단계 모두 성공 ✅
3. Docker Hub 이미지 업로드 성공 ✅
4. 무중단 배포 수행 ✅
5. 서비스 정상 응답 확인 ✅
"@

$testContent | Out-File -FilePath "pipeline-test-$(Get-Date -Format 'MMdd-HHmm').md" -Encoding UTF8

# README 파일에 테스트 배지 추가
$readmeUpdate = @"

---

## 🚀 CI/CD Pipeline Status

**Last Updated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

### Pipeline Stages
- [x] 📥 Checkout & Environment Setup
- [x] 🔍 Code Quality Check
- [x] 🐳 Build Docker Image  
- [x] 📤 Push to Docker Hub
- [x] 🚀 Zero-Downtime Deploy
- [x] 🧪 Post-Deploy Integration Tests

### Service Endpoints
- **Main Service**: http://[Deploy-Server-IP]/
- **Model Service**: http://[Deploy-Server-IP]/model/
- **Admin Panel**: http://[Deploy-Server-IP]:8080/
- **Jenkins**: http://[Jenkins-Server-IP]:18080/

### Deployment Info
- **Image Repository**: https://hub.docker.com/r/[사용자명]/ai-trading-platform
- **Deployment Strategy**: Blue-Green with Zero Downtime
- **Auto Rollback**: Enabled on failure
- **Health Checks**: Automated pre and post deployment
"@

$readmeUpdate | Add-Content -Path "README.md"
```

#### B. 변경사항 커밋 및 자동 빌드 트리거
```bash
# Git 변경사항 확인
git status

# 모든 변경사항 스테이징
git add .

# 의미있는 커밋 메시지로 커밋
git commit -m "Complete CI/CD Pipeline End-to-End Test

🧪 Testing Scope:
- Full pipeline automation (GitHub → Jenkins → Docker Hub → Deploy)
- Zero-downtime deployment verification
- Blue-green deployment strategy validation
- Auto-rollback system testing
- Service health monitoring

🎯 Validation Points:
- GitHub webhook automatic triggering
- Jenkins 6-stage pipeline execution
- Docker image build and registry push
- Automated deployment with traffic switching
- Post-deployment health checks and monitoring

📊 Expected Results:
- Complete pipeline execution in 5-10 minutes
- Zero service downtime during deployment
- Automatic rollback on any failure
- All services responding normally post-deployment

Test ID: CICD-TEST-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# GitHub에 푸시 (자동 빌드 트리거)
git push origin main

echo "✅ 변경사항 푸시 완료 - Jenkins에서 자동 빌드가 시작됩니다"
echo "🔗 Jenkins 모니터링: http://[Jenkins-Server-IP]:18080/job/SKN12-Trading-Platform-CI/"
```

### 2️⃣ 파이프라인 실행 모니터링

#### A. Jenkins 빌드 진행 상황 실시간 모니터링
```
1. Jenkins 웹 UI에서 "SKN12-Trading-Platform-CI" Job 페이지 접속
2. Build History에서 새로 시작된 빌드 번호 클릭 (예: #15)
3. Blue Ocean UI로 시각적 모니터링:
   - "Open Blue Ocean" 클릭
   - 파이프라인 각 Stage의 진행 상황 실시간 확인

모니터링할 Stage별 세부 사항:

Stage 1 - 📥 Checkout & Environment Setup (1-2분):
✅ GitHub에서 소스코드 체크아웃 성공
✅ 환경 변수 및 빌드 정보 출력
✅ 프로젝트 구조 확인

Stage 2 - 🔍 Code Quality Check (1-2분):
✅ Python 파일 문법 검사 (병렬 처리)
✅ Docker 관련 파일 존재 확인
✅ 코드 품질 기준 통과

Stage 3 - 🐳 Build Docker Image (3-5분):
✅ Docker 이미지 빌드 시작
✅ 빌드 시간 측정 및 출력
✅ 이미지 크기 및 레이어 정보 확인
✅ 컨테이너 실행 테스트 성공

Stage 4 - 📤 Push to Docker Hub (2-3분):
✅ Docker Hub 로그인 성공
✅ 이미지 태그 생성 (빌드번호-커밋해시)
✅ latest 태그와 버전 태그 모두 업로드
✅ 업로드 시간 측정 및 완료 확인

Stage 5 - 🚀 Zero-Downtime Deploy (3-4분):
✅ Deploy Server SSH 연결 성공
✅ 무중단 배포 스크립트 실행
✅ Blue-Green 환경 전환
✅ Health Check 통과
✅ 트래픽 전환 완료

Stage 6 - 🧪 Post-Deploy Integration Tests (1-2분):
✅ 외부에서 서비스 접근 테스트
✅ API 엔드포인트 응답 확인
✅ 응답 시간 측정 (< 5초)
✅ 통합 테스트 성공
```

#### B. 동시에 서비스 연속성 모니터링
```powershell
# 별도 PowerShell 창에서 서비스 연속성 테스트 실행
# 배포 중에도 서비스가 중단되지 않는지 확인

$deployServerIP = "[Deploy-Server-IP]"
$testDuration = 900  # 15분간 테스트
$startTime = Get-Date

Write-Host "🔄 서비스 연속성 모니터링 시작 (15분간)" -ForegroundColor Yellow
Write-Host "배포 중에도 서비스가 중단되지 않아야 합니다." -ForegroundColor Yellow

while ((Get-Date) -lt $startTime.AddSeconds($testDuration)) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    try {
        # 메인 서비스 테스트
        $response = Invoke-WebRequest -Uri "http://$deployServerIP/" -TimeoutSec 5 -UseBasicParsing
        $status = "✅ OK"
        $color = "Green"
    }
    catch {
        $status = "❌ FAIL"
        $color = "Red"
    }
    
    Write-Host "$timestamp - $status (Status: $($response.StatusCode))" -ForegroundColor $color
    Start-Sleep -Seconds 5
}

Write-Host "📊 서비스 연속성 테스트 완료" -ForegroundColor Green
```

#### C. 배포 완료 후 상태 확인
```bash
# Deploy Server에 접속하여 배포 결과 확인
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# 배포 상태 종합 확인
/opt/scripts/deployment-status.sh

# 기대 결과:
# ✅ 새로운 환경(Blue 또는 Green)이 활성화됨
# ✅ 새 이미지가 정상적으로 실행됨  
# ✅ Nginx가 새 환경으로 트래픽 라우팅
# ✅ 모든 서비스가 정상 응답

# 배포 로그 확인
tail -10 /opt/logs/deployment.log

# 서비스 응답 시간 측정
echo "🔍 서비스 응답 시간 측정:"
curl -w "메인 서비스: %{time_total}초\n" -s -o /dev/null http://localhost/
curl -w "모델 서비스: %{time_total}초\n" -s -o /dev/null http://localhost/model/

# 컨테이너 리소스 사용량 확인
echo "📊 컨테이너 리소스 사용량:"
docker stats --no-stream | grep trading
```

---

## 🚨 Step 3: 실패 시나리오 테스트 (자동 롤백 검증) (15분)

### 3️⃣ 의도적 실패 시나리오 생성

#### A. 빌드 실패 시나리오 테스트
```bash
# 프로젝트 디렉토리에서
cd C:\SKN12-FINAL-2TEAM

# Dockerfile에 의도적 오류 추가
$dockerfilePath = "base_server\Dockerfile"
$errorLine = "`n# 의도적 빌드 실패 테스트`nRUN this-command-does-not-exist`n"
Add-Content -Path $dockerfilePath -Value $errorLine

# 변경사항 커밋
git add .
git commit -m "Test Case: Intentional Build Failure for Rollback Testing

🧪 Test Scenario:
- Added invalid RUN command to Dockerfile
- Expected behavior: Build should fail at Stage 3 (Docker Build)
- Auto-rollback: Jenkins should attempt automatic rollback
- Service continuity: Previous version should remain running

⚠️ This is a test commit and will be reverted immediately"

git push origin main

echo "❌ 의도적 빌드 실패 커밋 푸시 완료"
echo "Jenkins에서 빌드 실패 및 롤백 과정을 모니터링하세요"
```

#### B. 빌드 실패 모니터링
```
1. Jenkins에서 새 빌드 시작 확인
2. Console Output에서 실패 지점 확인:
   - Stage 3 (Build Docker Image)에서 실패 예상
   - "RUN this-command-does-not-exist" 오류 메시지 확인
3. Post 섹션에서 자동 롤백 시도 확인:
   - "❌ 빌드 실패로 인한 자동 롤백 시도..."
   - "🔄 자동 롤백 수행 중..."
   - 롤백 성공/실패 메시지 확인
```

#### C. 서비스 연속성 확인
```bash
# 빌드 실패 중에도 서비스가 계속 실행되는지 확인
# PowerShell에서
$deployServerIP = "[Deploy-Server-IP]"

for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://$deployServerIP/" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ 서비스 정상 (시도 $i): Status $($response.StatusCode)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 서비스 오류 (시도 $i): $($_.Exception.Message)" -ForegroundColor Red
    }
    Start-Sleep -Seconds 3
}
```

#### D. 실패 테스트 정리 (정상화)
```bash
# 의도적 오류 제거 (커밋 되돌리기)
cd C:\SKN12-FINAL-2TEAM

git revert HEAD --no-edit
git push origin main

echo "✅ 의도적 실패 테스트 완료 - 정상 코드로 복구됨"
echo "Jenkins에서 정상 빌드 및 배포 재개를 확인하세요"
```

### 3️⃣ 수동 롤백 테스트

#### A. 현재 배포 상태 확인
```bash
# Deploy Server에 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# 현재 활성 환경 확인
echo "🔍 수동 롤백 테스트 전 상태:"
/opt/scripts/deployment-status.sh

# 현재 활성 환경 기록 (Blue 또는 Green)
echo "현재 환경을 기록해두세요 (예: Blue)"
```

#### B. 수동 롤백 실행
```bash
# 수동 롤백 스크립트 실행
echo "🔄 수동 롤백 테스트 시작..."
/opt/scripts/quick-rollback.sh

# 롤백 후 상태 확인
echo "📊 롤백 후 상태:"
/opt/scripts/deployment-status.sh

# 서비스 응답 확인
echo "🏥 롤백 후 서비스 헬스체크:"
curl -f http://localhost/ && echo "✅ 메인 서비스 정상"
curl -f http://localhost/model/ && echo "✅ 모델 서비스 정상"
```

#### C. 롤백 후 정상 배포로 복원
```bash
# 다시 정상 배포로 되돌리기
echo "🔄 정상 배포로 복원..."
# 최신 이미지로 재배포 (예시)
/opt/scripts/blue-green-deploy.sh "skn12-trading/ai-trading-platform" "latest" "PROD"

# 최종 상태 확인
/opt/scripts/deployment-status.sh
```

---

## 🎯 Step 4: 성능 및 부하 테스트 (선택사항) (20분)

### 4️⃣ 기본 성능 테스트

#### A. 응답 시간 측정
```bash
# Deploy Server에서 성능 측정
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# Apache Bench 설치 (간단한 부하 테스트용)
sudo apt install -y apache2-utils

# 기본 응답 시간 측정
echo "📊 단일 요청 응답 시간 측정:"
curl -w @- -s -o /dev/null http://localhost/ << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF

echo ""
echo "📊 모델 서비스 응답 시간:"
curl -w "모델 서비스 응답시간: %{time_total}초\n" -s -o /dev/null http://localhost/model/
```

#### B. 동시 요청 부하 테스트
```bash
# 가벼운 부하 테스트 (10명 동시 사용자, 100개 요청)
echo "🔥 부하 테스트 시작 (10 concurrent users, 100 requests):"

# 메인 서비스 부하 테스트
ab -n 100 -c 10 http://localhost/ > /tmp/load_test_main.txt
echo "메인 서비스 부하 테스트 결과:"
grep -E "(Requests per second|Time per request|Transfer rate)" /tmp/load_test_main.txt

echo ""

# 모델 서비스 부하 테스트 (더 가벼운 테스트)
ab -n 50 -c 5 http://localhost/model/ > /tmp/load_test_model.txt 2>/dev/null || echo "모델 서비스 부하 테스트 스킵 (404 정상)"

# 시스템 리소스 확인
echo "📊 부하 테스트 중 시스템 리소스:"
echo "메모리 사용량:"
free -h | grep Mem
echo "CPU 사용량 (5초간):"
top -bn1 | head -5
echo "Docker 컨테이너 리소스:"
docker stats --no-stream | grep trading
```

#### C. 연결 안정성 테스트
```bash
# 장시간 연결 안정성 테스트 (5분간)
echo "🔄 연결 안정성 테스트 시작 (5분간)..."

for i in {1..60}; do
    timestamp=$(date '+%H:%M:%S')
    if curl -f -s --max-time 5 http://localhost/ > /dev/null; then
        echo "$timestamp - ✅ OK ($i/60)"
    else
        echo "$timestamp - ❌ FAIL ($i/60)"
    fi
    sleep 5
done

echo "✅ 연결 안정성 테스트 완료"
```

### 4️⃣ 외부 접근 테스트

#### A. 인터넷에서 접근 테스트
```powershell
# Windows PowerShell에서 외부 접근 테스트
$deployServerIP = "[Deploy-Server-IP]"

Write-Host "🌐 외부에서 서비스 접근 테스트" -ForegroundColor Yellow

# 다양한 방법으로 접근 테스트
$urls = @(
    "http://$deployServerIP/",
    "http://$deployServerIP/model/",
    "http://$deployServerIP/health",
    "http://$deployServerIP:8080/nginx-status"
)

foreach ($url in $urls) {
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        Write-Host "✅ $url - OK (Status: $($response.StatusCode))" -ForegroundColor Green
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "⚠️ $url - Not Found (404) - 정상 (엔드포인트 없음)" -ForegroundColor Yellow
        }
        else {
            Write-Host "❌ $url - FAIL: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
```

#### B. 다양한 디바이스에서 접근 테스트
```
📱 모바일 접근 테스트:
1. 스마트폰 브라우저에서 http://[Deploy-Server-IP]/ 접속
2. 응답 시간 및 화면 표시 확인

💻 다른 컴퓨터에서 접근 테스트:
1. 다른 PC나 노트북에서 브라우저로 접속
2. 네트워크가 다른 환경에서도 접근 확인

🌍 온라인 서비스로 접근 테스트:
1. https://www.site24x7.com/tools/website-ping-test/ 접속
2. Deploy Server IP 입력하여 전 세계에서 접근 테스트
```

---

## 📊 Step 5: 모니터링 및 로그 검증 (10분)

### 5️⃣ 로그 수집 및 분석

#### A. Jenkins 빌드 로그 분석
```bash
# Jenkins Server에 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-Server-IP]

# Jenkins 컨테이너 로그 확인
echo "📋 최근 Jenkins 로그 (마지막 100줄):"
docker logs --tail 100 jenkins-master | grep -E "(SUCCESS|FAILURE|ERROR|WARN)"

# 빌드 통계 확인
echo "📊 Jenkins 빌드 통계:"
echo "전체 빌드 수: $(docker exec jenkins-master find /var/jenkins_home/jobs/SKN12-Trading-Platform-CI/builds -type d | wc -l)"

# 디스크 사용량 확인
echo "💾 Jenkins 디스크 사용량:"
docker exec jenkins-master du -sh /var/jenkins_home
```

#### B. Deploy Server 로그 분석
```bash
# Deploy Server에 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

echo "📋 배포 로그 분석:"

# 배포 이력 확인
echo "🔄 배포 이력 (최근 10건):"
tail -10 /opt/logs/deployment.log 2>/dev/null || echo "배포 로그 없음"

# Nginx 로그 분석
echo "🌐 Nginx 액세스 로그 (최근 20줄):"
sudo tail -20 /var/log/nginx/skn12-trading/access.log 2>/dev/null || echo "Nginx 로그 없음"

echo "❌ Nginx 에러 로그:"
sudo tail -10 /var/log/nginx/skn12-trading/error.log 2>/dev/null || echo "에러 로그 없음 (정상)"

# 컨테이너 로그 확인
echo "🐳 실행 중인 컨테이너 로그:"
for container in $(docker ps --format "{{.Names}}" | grep trading); do
    echo "--- $container 로그 (마지막 10줄) ---"
    docker logs --tail 10 $container
    echo ""
done

# 시스템 로그 확인
echo "📊 시스템 상태:"
echo "메모리: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "디스크: $(df -h / | tail -1 | awk '{print $3"/"$2}')"
echo "업타임: $(uptime | cut -d',' -f1)"
```

#### C. Docker Hub 이미지 현황 확인
```bash
# 로컬에서 Docker Hub API 확인 (선택사항)
# PowerShell에서 실행

$dockerUser = "[Docker-Hub-사용자명]"
$repo = "ai-trading-platform"

try {
    $apiUrl = "https://hub.docker.com/v2/repositories/$dockerUser/$repo/tags/"
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get
    
    Write-Host "🐳 Docker Hub 이미지 태그 현황:" -ForegroundColor Green
    $response.results | Select-Object -First 10 | ForEach-Object {
        Write-Host "  - $($_.name) (크기: $([math]::Round($_.full_size/1MB, 1))MB, 업데이트: $($_.last_updated.Substring(0,10)))"
    }
}
catch {
    Write-Host "⚠️ Docker Hub API 접근 실패 (정상 - 권한 제한)" -ForegroundColor Yellow
}
```

### 5️⃣ 성능 메트릭 수집

#### A. 응답 시간 통계
```bash
# Deploy Server에서 성능 측정 스크립트 실행
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# 응답 시간 통계 수집
echo "📊 서비스 응답 시간 통계 (10회 측정):"
for i in {1..10}; do
    main_time=$(curl -w "%{time_total}" -s -o /dev/null http://localhost/)
    model_time=$(curl -w "%{time_total}" -s -o /dev/null http://localhost/model/ 2>/dev/null || echo "0")
    echo "측정 $i: 메인=${main_time}s, 모델=${model_time}s"
    sleep 1
done

# 평균 계산 (간단한 방법)
echo "📈 성능 요약:"
echo "- 목표 응답 시간: < 3초"
echo "- 허용 가능한 응답 시간: < 5초"
echo "- 경고 임계값: >= 5초"
```

#### B. 리소스 사용량 모니터링
```bash
# 종합적인 시스템 상태 보고서 생성
echo "📊 시스템 종합 상태 보고서 생성 중..."

cat > /tmp/system-report.txt << 'EOF'
# SKN12 Trading Platform 시스템 상태 보고서
Generated: $(date)

## 시스템 정보
- 호스트명: $(hostname)
- 운영체제: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
- 커널: $(uname -r)
- 업타임: $(uptime)

## 리소스 사용량
### 메모리
$(free -h)

### 디스크
$(df -h)

### CPU (현재)
$(top -bn1 | head -10)

## Docker 상태
### 실행 중인 컨테이너
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

### 이미지 목록
$(docker images | head -10)

### 컨테이너 리소스
$(docker stats --no-stream)

## 네트워크 상태
### 포트 바인딩
$(netstat -tlnp | grep -E "(nginx|docker)")

### 서비스 응답 테스트
메인 서비스: $(curl -f -s http://localhost/ && echo "OK" || echo "FAIL")
모델 서비스: $(curl -f -s http://localhost/model/ && echo "OK" || echo "FAIL")

## Nginx 상태
$(systemctl status nginx --no-pager -l)

## 최근 배포 이력
$(tail -5 /opt/logs/deployment.log 2>/dev/null || echo "배포 이력 없음")
EOF

# 보고서 출력
cat /tmp/system-report.txt
echo ""
echo "💾 상세 보고서 저장 위치: /tmp/system-report.txt"
```

---

## ✅ 전체 CI/CD 파이프라인 검증 완료 체크리스트

### 🎯 기본 파이프라인 검증:
- [ ] GitHub Webhook 자동 트리거 정상 동작
- [ ] Jenkins 6단계 Pipeline 모두 성공적으로 완료
- [ ] Docker Hub 이미지 자동 업로드 성공
- [ ] 무중단 배포 정상 실행 (Blue-Green 전환)
- [ ] 배포 후 통합 테스트 모두 통과

### 🔄 장애 복구 시스템 검증:
- [ ] 빌드 실패 시 자동 롤백 정상 동작
- [ ] 수동 롤백 스크립트 정상 동작
- [ ] 롤백 후 서비스 정상성 확인
- [ ] 실패 시나리오에서 서비스 연속성 유지

### 📊 성능 및 안정성 검증:
- [ ] 서비스 응답 시간 < 5초 (목표: < 3초)
- [ ] 부하 테스트 통과 (동시 사용자 10명)
- [ ] 연결 안정성 테스트 통과 (5분간 무중단)
- [ ] 외부 접근 테스트 성공 (다양한 네트워크)

### 🔍 모니터링 및 로그 검증:
- [ ] Jenkins 빌드 로그 정상 수집
- [ ] Deploy Server 배포 로그 정상 기록
- [ ] Nginx 액세스/에러 로그 정상 수집
- [ ] 컨테이너 로그 정상 확인

### 🌐 운영 준비성 검증:
- [ ] 모든 서비스 외부 접근 가능
- [ ] 관리자 페이지 접근 가능
- [ ] 시스템 리소스 사용량 적정 수준
- [ ] 보안 설정 기본 요구사항 충족

---

## 🎖️ 성능 벤치마크 및 권장 기준

### 📊 성능 기준값

| 메트릭 | 목표값 | 허용값 | 경고값 |
|--------|--------|--------|--------|
| **응답 시간** | < 1초 | < 3초 | >= 5초 |
| **처리량** | > 50 req/sec | > 20 req/sec | < 10 req/sec |
| **메모리 사용량** | < 70% | < 85% | >= 90% |
| **디스크 사용량** | < 60% | < 80% | >= 90% |
| **빌드 시간** | < 5분 | < 10분 | >= 15분 |
| **배포 시간** | < 3분 | < 5분 | >= 10분 |

### 🚀 최적화 권장사항

#### 성능 향상:
1. **Docker 이미지 최적화**
   - Multi-stage build 활용
   - 불필요한 패키지 제거
   - 베이스 이미지 Alpine 사용 고려

2. **빌드 캐시 최적화**
   - Jenkins 빌드 캐시 활용
   - Docker layer 캐싱 개선
   - 의존성 캐싱 강화

3. **네트워크 최적화**
   - CDN 적용 고려
   - Nginx 압축 설정
   - Keep-alive 연결 최적화

#### 확장성 개선:
1. **Auto Scaling**
   - AWS Auto Scaling Group 설정
   - Load Balancer 다중화
   - 컨테이너 오케스트레이션 (K8s)

2. **데이터베이스 최적화**
   - 읽기 전용 복제본
   - 연결 풀링
   - 쿼리 최적화

3. **모니터링 강화**
   - Prometheus + Grafana
   - ELK Stack 로그 분석
   - APM 도구 통합

---

## 🎉 최종 검증 완료!

### ✅ 구축 완료된 시스템:

1. **완전 자동화된 CI/CD 파이프라인**
   - GitHub Push → Jenkins → Docker Hub → Deploy (완전 자동)
   - 5-10분 내 전체 배포 완료
   - 사람 개입 없는 완전 무인 자동화

2. **무중단 배포 시스템**
   - Blue-Green 배포 전략
   - 서비스 중단 시간 0초
   - 자동 헬스체크 및 트래픽 전환

3. **자동 장애 복구**
   - 실패 시 즉시 자동 롤백
   - 이전 버전으로 완전 복구
   - 서비스 연속성 100% 보장

4. **종합 모니터링 시스템**
   - 실시간 배포 상태 추적
   - 성능 메트릭 수집
   - 로그 중앙 집중 관리

### 🚀 이제 가능한 것:

- **1초 코드 변경** → **10분 내 운영 반영**
- **완전 무중단 서비스** (배포 중에도 사용자 이용 가능)
- **자동 품질 보장** (테스트 실패 시 배포 중단)
- **즉시 롤백** (문제 발생 시 1분 내 이전 버전 복구)

**🎯 최종 결과: 엔터프라이즈급 DevOps 파이프라인 완성!**

이제 진정한 DevOps 환경에서 안전하고 빠른 소프트웨어 배포가 가능합니다! 🚀🎉