# 🏗️ Jenkins Docker Compose 설치 및 설정 완전 가이드 (초보자용)

> **목적**: EC2 Jenkins 서버에 Docker Compose를 사용하여 Jenkins를 설치하고, GitHub 및 Docker Hub 연동을 위한 초기 설정을 완료합니다.
>
> **💡 왜 Docker Compose로 Jenkins를 설치하나요?**: 직접 설치보다 관리가 쉽고, 백업/복구가 간단하며, 설정을 코드로 관리할 수 있습니다.

---

## 🏗️ Jenkins 설치 아키텍처 이해하기

```
🖥️ Jenkins Server (EC2)
├── 🐳 Docker Engine (설치 완료)
├── 📁 /opt/jenkins/ (Jenkins 데이터 디렉토리)
│   ├── data/ (Jenkins 홈 - 플러그인, 설정, 작업 등)
│   ├── configs/ (설정 파일들)
│   └── scripts/ (자동화 스크립트들)
└── 🏗️ Jenkins Container (Docker Compose로 실행)
    ├── Jenkins Web UI: http://[Jenkins-IP]:18080
    ├── Docker-in-Docker 지원 (이미지 빌드용)
    ├── Git, Docker CLI 포함
    └── 플러그인: GitHub, Pipeline, Docker 등
```

**Jenkins가 하는 일**:
1. **GitHub에서 코드 가져오기** (git clone)
2. **Docker 이미지 빌드** (docker build)
3. **Docker Hub에 업로드** (docker push)
4. **Deploy 서버에 SSH 접속**하여 배포 명령 실행

---

## 🔐 Step 1: Jenkins Server에 SSH 접속 및 준비 (5분)

### 1️⃣ Jenkins Server 접속

#### A. PowerShell에서 SSH 접속
```powershell
# Windows PowerShell 실행
# Jenkins Server에 접속 (IP를 실제 Elastic IP로 교체)
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-Elastic-IP]

# 예시
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@13.125.123.45
```

#### B. 서버 상태 확인
```bash
# 초기 설정 완료 확인
cat /home/ubuntu/setup-complete.log
# 출력: Jenkins Server 초기 설정 완료: [날짜/시간]

# Docker 설치 확인
docker --version
# 출력: Docker version 24.0.7, build afdd53b

# Docker Compose 확인
docker compose version
# 출력: Docker Compose version v2.21.0

# 현재 사용자가 docker 그룹에 속하는지 확인
groups
# 출력에 "docker"가 포함되어야 함

# 만약 docker 그룹에 없다면 (권한 오류 시)
sudo usermod -aG docker ubuntu
# 로그아웃 후 재접속 필요
```

#### C. 시스템 상태 확인
```bash
# 디스크 용량 확인 (30GB 중 사용량)
df -h
# /dev/xvda1 에서 Available이 25GB 이상이어야 함

# 메모리 확인 (4GB 중 사용량)
free -h
# Available이 3GB 이상이어야 함

# 네트워크 연결 확인
curl -I https://hub.docker.com
# HTTP/2 200 응답이 나와야 함
```

---

## 📁 Step 2: Jenkins 디렉토리 구조 설정 (5분)

### 2️⃣ Jenkins 전용 디렉토리 생성

#### A. 기본 디렉토리 구조 생성
```bash
# Jenkins 관련 모든 파일을 저장할 기본 디렉토리
sudo mkdir -p /opt/jenkins/{data,configs,scripts,backups}

# 세부 디렉토리 설명:
# - data/: Jenkins 홈 디렉토리 (플러그인, 작업, 설정 등)
# - configs/: Docker Compose 및 Jenkins 설정 파일
# - scripts/: 백업, 관리용 스크립트
# - backups/: Jenkins 데이터 백업 파일

# 권한 설정 (ubuntu 사용자가 접근 가능하도록)
sudo chown -R ubuntu:ubuntu /opt/jenkins

# 권한 확인
ls -la /opt/jenkins/
# 출력에서 ubuntu ubuntu로 소유권이 설정되었는지 확인
```

#### B. Docker Compose 작업 디렉토리 이동
```bash
# Jenkins 설정 디렉토리로 이동
cd /opt/jenkins/configs

# 현재 위치 확인
pwd
# 출력: /opt/jenkins/configs
```

#### C. 환경 변수 파일 생성
```bash
# Jenkins 환경 설정 파일 생성
cat > .env << 'EOF'
# =============================================================================
# Jenkins Docker Compose 환경 변수 설정
# =============================================================================

# Jenkins 컨테이너 설정
JENKINS_VERSION=lts
JENKINS_PORT=18080
JENKINS_AGENT_PORT=50000

# Jenkins 홈 디렉토리 (호스트 경로)
JENKINS_HOME=/opt/jenkins/data

# Jenkins 관리자 설정 (초기 설정용)
JENKINS_ADMIN_USER=admin
JENKINS_ADMIN_PASSWORD=skn12-jenkins-2025!

# 시간대 설정
TZ=Asia/Seoul

# Docker 소켓 마운트 (Docker-in-Docker용)
DOCKER_SOCK=/var/run/docker.sock

# 로그 설정
JENKINS_LOG_LEVEL=INFO
EOF

# 환경 변수 파일 내용 확인
cat .env
```

---

## 🐳 Step 3: Docker Compose 파일 작성 (10분)

### 3️⃣ Jenkins Docker Compose 설정

#### A. docker-compose.yml 파일 생성
```bash
# Jenkins Docker Compose 설정 파일 생성
cat > docker-compose.yml << 'EOF'
# =============================================================================
# Jenkins CI/CD Server Docker Compose 설정
# =============================================================================
# 이 파일은 Jenkins를 Docker 컨테이너로 실행하기 위한 설정입니다.
# Docker-in-Docker 지원으로 Jenkins에서 Docker 이미지를 빌드할 수 있습니다.

version: '3.8'

services:
  # 🏗️ Jenkins Master (CI/CD 메인 서버)
  jenkins:
    image: jenkins/jenkins:${JENKINS_VERSION:-lts}
    container_name: jenkins-master
    restart: unless-stopped
    
    # 포트 설정
    ports:
      - "${JENKINS_PORT:-18080}:8080"     # Jenkins 웹 UI
      - "${JENKINS_AGENT_PORT:-50000}:50000"  # Jenkins 에이전트 통신용 (선택사항)
    
    # 환경 변수
    environment:
      - TZ=${TZ:-Asia/Seoul}
      - JENKINS_OPTS=--httpPort=8080
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Xmx2g -Xms1g
      
    # 볼륨 마운트 (데이터 영속성)
    volumes:
      # Jenkins 홈 디렉토리 (플러그인, 작업, 설정 등 저장)
      - "${JENKINS_HOME:-/opt/jenkins/data}:/var/jenkins_home"
      
      # Docker 소켓 마운트 (Docker-in-Docker 지원)
      # Jenkins에서 호스트의 Docker를 사용하여 이미지 빌드 가능
      - "${DOCKER_SOCK:-/var/run/docker.sock}:/var/run/docker.sock"
      
      # Docker 바이너리 마운트 (Jenkins에서 docker 명령어 사용)
      - "/usr/bin/docker:/usr/bin/docker:ro"
      
      # 시간 동기화
      - "/etc/localtime:/etc/localtime:ro"
    
    # 네트워크 설정
    networks:
      - jenkins-network
    
    # 헬스체크 설정
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    # 사용자 설정 (docker 그룹 권한 필요)
    user: "1000:999"  # ubuntu:docker 그룹 ID
    
    # 메모리 제한 설정
    deploy:
      resources:
        limits:
          memory: 3G
        reservations:
          memory: 2G

# 🌐 네트워크 설정
networks:
  jenkins-network:
    driver: bridge
    name: jenkins-net

# 📦 볼륨 설정 (명시적 볼륨 정의)
volumes:
  jenkins-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/jenkins/data
      o: bind
EOF

# Docker Compose 파일 내용 확인
cat docker-compose.yml
```

#### B. Jenkins 설정 디렉토리 초기화
```bash
# Jenkins 홈 디렉토리 권한 설정
sudo mkdir -p /opt/jenkins/data
sudo chown -R 1000:999 /opt/jenkins/data

# Docker 그룹 ID 확인 (999여야 함)
grep docker /etc/group
# 출력: docker:x:999:ubuntu

# 권한 확인
ls -la /opt/jenkins/
# data 디렉토리가 1000:999 (jenkins:docker) 소유권이어야 함
```

#### C. 초기 Jenkins 설정 스크립트 생성
```bash
# Jenkins 초기 설정 자동화 스크립트
cat > setup-jenkins.sh << 'EOF'
#!/bin/bash
# =============================================================================
# Jenkins 초기 설정 자동화 스크립트
# =============================================================================

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 Jenkins 설정 시작..."

# Jenkins 홈 디렉토리 확인
JENKINS_HOME="/opt/jenkins/data"
if [ ! -d "$JENKINS_HOME" ]; then
    echo "❌ Jenkins 홈 디렉토리가 없습니다: $JENKINS_HOME"
    exit 1
fi

# Docker Compose 파일 존재 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 파일이 없습니다"
    exit 1
fi

# Jenkins 컨테이너가 실행 중인지 확인
if docker ps | grep -q jenkins-master; then
    echo "⚠️ Jenkins 컨테이너가 이미 실행 중입니다"
    echo "중지하고 다시 시작하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🛑 기존 Jenkins 컨테이너 중지 중..."
        docker compose down
    else
        echo "❌ 설정을 중단합니다"
        exit 1
    fi
fi

echo "📦 Jenkins 컨테이너 시작 중..."
docker compose up -d

echo "⏰ Jenkins 시작 대기 중 (약 2-3분 소요)..."
for i in {1..60}; do
    if docker logs jenkins-master 2>/dev/null | grep -q "Jenkins is fully up and running"; then
        echo "✅ Jenkins가 성공적으로 시작되었습니다!"
        break
    fi
    echo -n "."
    sleep 5
done

echo ""
echo "🔑 Jenkins 초기 관리자 비밀번호 확인 중..."
if docker exec jenkins-master test -f /var/jenkins_home/secrets/initialAdminPassword; then
    echo "📋 초기 관리자 비밀번호:"
    docker exec jenkins-master cat /var/jenkins_home/secrets/initialAdminPassword
else
    echo "⚠️ 초기 비밀번호 파일을 찾을 수 없습니다. Jenkins 로그를 확인하세요."
fi

echo ""
echo "🌐 Jenkins 접속 정보:"
echo "URL: http://$(curl -s ifconfig.me):18080"
echo "사용자명: admin"
echo "비밀번호: 위의 초기 관리자 비밀번호 사용"

echo ""
echo "📊 Jenkins 컨테이너 상태:"
docker ps | grep jenkins-master

echo ""
echo "✅ Jenkins 설정이 완료되었습니다!"
echo "웹 브라우저에서 Jenkins에 접속하여 초기 설정을 완료하세요."
EOF

# 스크립트 실행 권한 부여
chmod +x setup-jenkins.sh
```

---

## 🚀 Step 4: Jenkins 컨테이너 실행 (10분)

### 4️⃣ Jenkins 시작하기

#### A. Docker Compose로 Jenkins 실행
```bash
# 현재 디렉토리 확인 (/opt/jenkins/configs 여야 함)
pwd

# Jenkins 설정 스크립트 실행
./setup-jenkins.sh

# 또는 수동으로 실행하려면:
# docker compose up -d
```

#### B. Jenkins 시작 과정 모니터링
```bash
# Jenkins 컨테이너 상태 확인
docker ps
# jenkins-master 컨테이너가 "Up" 상태여야 함

# Jenkins 시작 로그 확인 (실시간)
docker logs -f jenkins-master

# 다음 메시지가 나올 때까지 대기:
# "Jenkins is fully up and running"
# Ctrl+C로 로그 모니터링 종료
```

#### C. Jenkins 웹 접속 확인
```bash
# 외부 IP 주소 확인
curl -s ifconfig.me
# 출력: [Jenkins Server의 Public IP]

# Jenkins 웹 서버 응답 확인
curl -I http://localhost:18080
# HTTP/1.1 200 OK 응답이 나와야 함

echo "🌐 Jenkins 접속 URL: http://$(curl -s ifconfig.me):18080"
```

#### D. 웹 브라우저에서 Jenkins 접속
```
1. 웹 브라우저 열기
2. 주소창에 입력: http://[Jenkins-Public-IP]:18080
3. "Unlock Jenkins" 페이지가 표시되면 성공!
```

---

## 🔐 Step 5: Jenkins 초기 설정 (15분)

### 5️⃣ Jenkins 웹 UI 초기 설정

#### A. 초기 관리자 비밀번호 확인
```bash
# SSH에서 초기 비밀번호 확인
docker exec jenkins-master cat /var/jenkins_home/secrets/initialAdminPassword

# 출력 예시: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
# 이 비밀번호를 복사하여 웹 브라우저에 입력
```

#### B. 웹 브라우저에서 Jenkins 설정
```
1. "Unlock Jenkins" 페이지에서:
   - Administrator password 필드에 위의 비밀번호 붙여넣기
   - "Continue" 버튼 클릭

2. "Customize Jenkins" 페이지에서:
   - "Install suggested plugins" 선택 (권장)
   - 플러그인 설치 진행 (약 5분 소요)

3. "Create First Admin User" 페이지에서:
   - Username: admin
   - Password: skn12-jenkins-2025!
   - Password confirm: skn12-jenkins-2025!
   - Full name: SKN12 Jenkins Admin
   - E-mail address: admin@skn12-trading.com
   - "Save and Continue" 클릭

4. "Instance Configuration" 페이지에서:
   - Jenkins URL: http://[Jenkins-Public-IP]:18080/
   - 주소가 정확한지 확인 후 "Save and Finish" 클릭

5. "Jenkins is ready!" 페이지에서:
   - "Start using Jenkins" 클릭
```

#### C. Jenkins Dashboard 확인
```
Jenkins 메인 화면이 표시되면 설정 완료!

확인 항목:
✅ 왼쪽 메뉴: New Item, People, Build History 등
✅ 상단: 사용자명 "admin" 표시
✅ 메인 영역: "Welcome to Jenkins!" 메시지
```

---

## 🔧 Step 6: 필수 플러그인 설치 (10분)

### 6️⃣ CI/CD에 필요한 추가 플러그인 설치

#### A. Plugin Manager 접속
```
1. Jenkins Dashboard → 왼쪽 메뉴 "Manage Jenkins" 클릭
2. "Plugins" 클릭 (또는 "Manage Plugins")
3. "Available plugins" 탭 클릭
```

#### B. 필수 플러그인 검색 및 설치
```
검색창에서 다음 플러그인들을 하나씩 검색하여 체크박스 선택:

🔍 검색어 → 선택할 플러그인:

"docker" → 
  ✅ Docker Pipeline
  ✅ Docker plugin

"github" →
  ✅ GitHub Integration Plugin
  ✅ GitHub Pull Request Builder

"ssh" →
  ✅ SSH Agent Plugin
  ✅ SSH Build Agents plugin

"pipeline" →
  ✅ Pipeline: Stage View Plugin
  ✅ Blue Ocean (시각적 파이프라인 UI)

"credential" →
  ✅ Credentials Binding Plugin

"workspace" →
  ✅ Workspace Cleanup Plugin

총 선택한 플러그인 수: 10-12개
```

#### C. 플러그인 설치 실행
```
1. 모든 플러그인 선택 완료 후 페이지 하단 "Install" 버튼 클릭
2. "Installing Plugins/Upgrades" 페이지에서 설치 진행 상황 확인
3. 모든 플러그인 설치 완료 시 "Success" 표시 확인
4. "Restart Jenkins when installation is complete and no jobs are running" 체크박스 선택
5. Jenkins 자동 재시작 대기 (약 2-3분)
```

#### D. 재시작 후 Jenkins 상태 확인
```bash
# SSH에서 Jenkins 컨테이너 상태 확인
docker ps | grep jenkins-master
# 컨테이너가 정상 실행 중이어야 함

# Jenkins 로그 확인
docker logs --tail 20 jenkins-master
# "Jenkins is fully up and running" 메시지 확인

# 웹 브라우저에서 Jenkins 재접속
# http://[Jenkins-Public-IP]:18080
# 로그인 화면이 나타나면 admin / skn12-jenkins-2025! 로 로그인
```

---

## 🔑 Step 7: Credentials 설정 (GitHub & Docker Hub) (15분)

### 7️⃣ GitHub Personal Access Token 생성

#### A. GitHub에서 Personal Access Token 생성
```
1. GitHub 웹사이트 (https://github.com) 로그인
2. 우측 상단 프로필 이미지 클릭 → "Settings"
3. 왼쪽 메뉴 맨 아래 "Developer settings" 클릭
4. "Personal access tokens" → "Tokens (classic)" 클릭
5. "Generate new token" → "Generate new token (classic)" 선택

Token 설정:
- Note: Jenkins-CI-CD-Token
- Expiration: 90 days (또는 No expiration)
- Select scopes:
  ✅ repo (Full control of private repositories)
  ✅ workflow (Update GitHub Action workflows)
  ✅ admin:repo_hook (Admin repo hooks)

6. "Generate token" 클릭
7. 생성된 토큰 복사 (한 번만 표시됨!)
   예: ghp_1234567890abcdefghijklmnopqrstuvwxyz
```

#### B. Jenkins에 GitHub Credentials 등록
```
1. Jenkins Dashboard → "Manage Jenkins" → "Credentials"
2. "System" → "Global credentials (unrestricted)" 클릭
3. 왼쪽 "Add Credentials" 클릭

GitHub Token 설정:
- Kind: Secret text
- Scope: Global
- Secret: [위에서 복사한 GitHub Token]
- ID: github-token
- Description: GitHub Personal Access Token for SKN12 Trading Platform

4. "Create" 버튼 클릭
```

### 7️⃣ Docker Hub Credentials 설정

#### A. Jenkins에 Docker Hub Credentials 등록
```
1. 다시 "Add Credentials" 클릭

Docker Hub 설정:
- Kind: Username with password
- Scope: Global  
- Username: [Docker Hub 사용자명]
- Password: [Docker Hub Access Token] (비밀번호 아님!)
- ID: dockerhub-credentials
- Description: Docker Hub access for image push/pull

2. "Create" 버튼 클릭
```

#### B. SSH Key for Deploy Server 생성
```bash
# SSH에서 Jenkins용 SSH 키 생성
docker exec -it jenkins-master bash

# Jenkins 컨테이너 내부에서 실행
ssh-keygen -t ed25519 -C "jenkins-deploy-key" -f ~/.ssh/id_ed25519 -N ""

# 공개키 확인 (Deploy Server에 등록할 키)
cat ~/.ssh/id_ed25519.pub

# 개인키 확인 (Jenkins Credentials에 등록할 키)
cat ~/.ssh/id_ed25519

# Jenkins 컨테이너에서 나가기
exit
```

#### C. Deploy Server에 공개키 등록
```bash
# 새 터미널/SSH 세션에서 Deploy Server에 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Server-IP]

# authorized_keys 파일에 Jenkins 공개키 추가
mkdir -p ~/.ssh
echo "[위에서 복사한 공개키 전체]" >> ~/.ssh/authorized_keys

# 권한 설정
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Deploy Server에서 나가기
exit
```

#### D. Jenkins에 SSH Credentials 등록
```
1. Jenkins에서 다시 "Add Credentials" 클릭

SSH Key 설정:
- Kind: SSH Username with private key
- Scope: Global
- ID: deploy-server-ssh-key
- Description: SSH key for Deploy Server access
- Username: ubuntu
- Private Key: Enter directly
- Key: [위에서 확인한 개인키 전체 내용 붙여넣기]
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
  -----END OPENSSH PRIVATE KEY-----

2. "Create" 버튼 클릭
```

---

## 🧪 Step 8: Jenkins 설정 테스트 및 검증 (10분)

### 8️⃣ 설정된 Credentials 테스트

#### A. GitHub 연결 테스트
```
1. Jenkins Dashboard → "New Item" 클릭
2. Item name: test-github-connection
3. "Pipeline" 선택 → "OK" 클릭
4. "Pipeline" 섹션에서:
   - Definition: Pipeline script
   - Script:
```

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test GitHub Connection') {
            steps {
                script {
                    // GitHub Token을 사용하여 저장소 정보 가져오기
                    withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                        sh '''
                            echo "🔍 GitHub 연결 테스트 중..."
                            curl -H "Authorization: token $GITHUB_TOKEN" \
                                 https://api.github.com/user | jq '.login' || echo "GitHub API 호출 실패"
                        '''
                    }
                }
            }
        }
        
        stage('Test Docker Hub Connection') {
            steps {
                script {
                    // Docker Hub 로그인 테스트
                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', 
                                                    usernameVariable: 'DOCKER_USER', 
                                                    passwordVariable: 'DOCKER_PASS')]) {
                        sh '''
                            echo "🐳 Docker Hub 로그인 테스트 중..."
                            echo "$DOCKER_PASS" | docker login --username "$DOCKER_USER" --password-stdin
                            if [ $? -eq 0 ]; then
                                echo "✅ Docker Hub 로그인 성공!"
                                docker logout
                            else
                                echo "❌ Docker Hub 로그인 실패!"
                                exit 1
                            fi
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "🧹 테스트 정리 중..."
            cleanWs()
        }
        success {
            echo "✅ 모든 연결 테스트가 성공했습니다!"
        }
        failure {
            echo "❌ 연결 테스트 중 오류가 발생했습니다."
        }
    }
}
```

#### B. 테스트 파이프라인 실행
```
1. "Save" 버튼 클릭
2. 왼쪽 "Build Now" 클릭
3. Build History에서 "#1" 클릭
4. "Console Output" 클릭하여 실행 결과 확인

기대 결과:
✅ GitHub 연결: 사용자명이 출력됨
✅ Docker Hub 연결: "Docker Hub 로그인 성공!" 메시지
✅ 전체 파이프라인: "Finished: SUCCESS"
```

#### C. SSH 연결 테스트 (Deploy Server)
```
1. "New Item" → "test-ssh-connection" → "Pipeline" 생성
2. Pipeline Script:
```

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test SSH Connection') {
            steps {
                sshagent(credentials: ['deploy-server-ssh-key']) {
                    sh '''
                        echo "🔐 Deploy Server SSH 연결 테스트 중..."
                        
                        # Deploy Server IP (실제 IP로 변경)
                        DEPLOY_SERVER="[Deploy-Server-IP]"
                        
                        # SSH 연결 테스트
                        ssh -o StrictHostKeyChecking=no ubuntu@$DEPLOY_SERVER '
                            echo "✅ SSH 연결 성공!"
                            echo "서버 정보:"
                            hostname
                            uptime
                            docker --version
                        '
                    '''
                }
            }
        }
    }
}
```

#### D. 전체 시스템 상태 확인
```bash
# SSH에서 Jenkins 시스템 상태 확인
cd /opt/jenkins/configs

# 실행 중인 컨테이너 확인
docker ps
# jenkins-master가 "Up" 상태이고 18080 포트가 매핑되어야 함

# Jenkins 데이터 디렉토리 확인
ls -la /opt/jenkins/data/
# plugins, jobs, users 등의 디렉토리가 생성되어야 함

# 시스템 리소스 사용량 확인
free -h  # 메모리 사용량
df -h    # 디스크 사용량

# Jenkins 컨테이너 리소스 사용량
docker stats jenkins-master --no-stream
```

---

## ✅ Jenkins 설치 완료 체크리스트

### 🎯 기본 설치 완료:
- [ ] Jenkins Docker 컨테이너 정상 실행 (docker ps 확인)
- [ ] Jenkins 웹 UI 접속 가능 (http://Jenkins-IP:18080)
- [ ] 관리자 계정 생성 완료 (admin / skn12-jenkins-2025!)
- [ ] 기본 플러그인 설치 완료
- [ ] 추가 필수 플러그인 설치 완료 (Docker, GitHub, SSH 등)

### 🔐 Credentials 설정 완료:
- [ ] GitHub Personal Access Token 등록 (github-token)
- [ ] Docker Hub Access Token 등록 (dockerhub-credentials)  
- [ ] Deploy Server SSH Key 등록 (deploy-server-ssh-key)
- [ ] 모든 Credentials 연결 테스트 성공

### 📁 디렉토리 구조 확인:
- [ ] `/opt/jenkins/data/` - Jenkins 홈 디렉토리
- [ ] `/opt/jenkins/configs/` - Docker Compose 설정
- [ ] Jenkins 데이터 영속성 확인 (컨테이너 재시작 후에도 설정 유지)

### 🌐 네트워크 연결 확인:
- [ ] GitHub API 연결 성공
- [ ] Docker Hub 로그인 성공
- [ ] Deploy Server SSH 연결 성공
- [ ] 외부 인터넷 연결 정상

---

## 🔧 문제 해결 및 유지 관리

### Jenkins 컨테이너 관리 명령어:
```bash
# Jenkins 컨테이너 상태 확인
docker ps | grep jenkins

# Jenkins 로그 확인
docker logs jenkins-master

# Jenkins 컨테이너 재시작
cd /opt/jenkins/configs
docker compose restart jenkins

# Jenkins 컨테이너 중지/시작
docker compose down
docker compose up -d

# Jenkins 백업 (데이터 디렉토리 압축)
tar -czf /opt/jenkins/backups/jenkins-backup-$(date +%Y%m%d).tar.gz -C /opt/jenkins data/
```

### 자주 발생하는 문제 해결:

#### 문제 1: "Permission denied" Docker 오류
```bash
# Docker 그룹 권한 확인
groups ubuntu
# docker가 포함되어야 함

# 권한 재설정
sudo usermod -aG docker ubuntu
sudo systemctl restart docker

# Jenkins 컨테이너 재시작
cd /opt/jenkins/configs
docker compose restart jenkins
```

#### 문제 2: Jenkins 웹 UI 접속 불가
```bash
# 포트 확인
netstat -tulpn | grep 18080

# 방화벽 확인 (EC2 보안 그룹)
# AWS Console에서 skn12-jenkins-sg 보안 그룹 확인
# 포트 18080이 0.0.0.0/0에 열려있는지 확인

# Jenkins 컨테이너 상태 확인
docker logs jenkins-master | tail -20
```

#### 문제 3: 메모리 부족 오류
```bash
# 메모리 사용량 확인
free -h
docker stats jenkins-master --no-stream

# Jenkins JVM 설정 조정 (docker-compose.yml에서)
# JAVA_OPTS=-Xmx1g -Xms512m (메모리 줄이기)
```

---

## 🎯 다음 단계 미리보기

### 1️⃣ GitHub Webhook 설정:
- GitHub 저장소에 Webhook URL 추가
- Push 이벤트 시 Jenkins 자동 빌드 트리거

### 2️⃣ Jenkinsfile 작성:
- Pipeline as Code 구현
- GitHub → Docker Build → Docker Hub Push → Deploy

### 3️⃣ 자동 배포 설정:
- Deploy Server에서 이미지 자동 다운로드
- 무중단 배포 구현

---

## 🎉 축하합니다!

Jenkins CI/CD 서버 설치가 완료되었습니다! 🏗️

### ✅ 지금까지 구축한 것:
- 🐳 **Jenkins Container**: Docker Compose로 안정적 실행
- 🔐 **Credentials**: GitHub, Docker Hub, SSH 연동 완료
- 🔧 **Plugins**: CI/CD에 필요한 모든 플러그인 설치
- 🧪 **연결 테스트**: 모든 외부 서비스 연동 검증

### 🚀 다음 할 일:
1. **GitHub Webhook** 설정으로 자동 빌드 트리거
2. **Jenkinsfile** 작성으로 Pipeline as Code 구현
3. **자동 배포** 설정으로 완전한 CI/CD 구축

Jenkins가 준비되었습니다. 이제 완전 자동화된 CI/CD 파이프라인을 만들어봅시다! 🚀