# ☁️ AWS EC2 Jenkins + Deploy 서버 구축 완전 가이드 (초보자용)

> **목적**: 기존 AWS 서비스(S3, OpenSearch, Bedrock 등)가 설정된 상태에서 EC2 인스턴스 2개를 생성하여 Jenkins CI/CD 서버와 애플리케이션 배포 서버를 구축합니다.
>
> **💡 이 가이드는 AWS를 처음 사용하는 초보자도 따라할 수 있도록 모든 단계를 스크린샷과 함께 상세히 설명합니다.**

---

## 🏗️ 전체 아키텍처 이해하기

```
🏠 개발자 PC (Windows)
    ↓ (코드 작성 후 git push)
📱 GitHub Repository (소스코드 저장소)
    ↓ (Webhook으로 자동 알림)
📦 Jenkins Server (EC2-1) 
    ├─ GitHub에서 코드 다운로드
    ├─ Docker 이미지 빌드
    ├─ Docker Hub에 이미지 업로드
    └─ Deploy 서버에 배포 명령 전송
         ↓ (SSH 접속)
🚀 Deploy Server (EC2-2)
    ├─ Docker Hub에서 이미지 다운로드
    ├─ 컨테이너 실행 (Base Web Server:8000, Model Server:8001)
    └─ 사용자에게 서비스 제공
         ↓
👥 실제 사용자들 (웹 브라우저로 접속)
```

**이미 설정된 AWS 서비스들**:
- ✅ **S3**: 파일 저장소 (로그, 백업용)
- ✅ **OpenSearch**: 검색 엔진 서비스
- ✅ **Bedrock**: AI 모델 서비스  
- ✅ **SES/SNS**: 이메일/SMS 알림 서비스
- ✅ **IAM**: 권한 관리 (기존 설정 활용)

---

## 📋 필요한 EC2 인스턴스 계획

| 서버 이름 | 역할 | 컴퓨터 사양 | 월 예상 비용 | 열어야 할 포트 |
|----------|------|-------------|-------------|---------------|
| **Jenkins Server** | 코드 빌드 + 배포 자동화 | t3.medium (CPU 2개, RAM 4GB) | 약 $30 | 22(SSH), 18080(Jenkins) |
| **Deploy Server** | 실제 앱 서비스 제공 | t3.small (CPU 2개, RAM 2GB) | 약 $15 | 22(SSH), 80(웹), 8000, 8001 |

**💰 총 예상 비용**: 월 약 $45 (기존 AWS 서비스 비용 별도)

---

## 🔐 Step 1: SSH 접속용 키 페어 생성 (5분)

> **💡 키 페어란?**: EC2 서버에 SSH로 안전하게 접속하기 위한 암호화 키입니다. 
> 열쇠와 같은 역할로, 이 키가 없으면 서버에 접속할 수 없습니다.

### 1️⃣ AWS Management Console 접속
```
1. 웹 브라우저에서 https://aws.amazon.com/console/ 접속
2. 기존에 생성한 IAM 사용자로 로그인
   - 사용자명: skn12-finance-master
   - 패스워드: [설정한 패스워드]
3. 우측 상단에서 리전이 "아시아 태평양(서울) ap-northeast-2"인지 확인
```

### 2️⃣ EC2 서비스로 이동
```
1. AWS Console 상단 검색창에 "EC2" 입력
2. "EC2" 서비스 클릭
3. EC2 Dashboard가 열리면 성공
```

### 3️⃣ 키 페어 생성하기
```
1. EC2 Dashboard 왼쪽 메뉴에서 "네트워크 및 보안" 클릭
2. "키 페어" 클릭
3. 우측 상단 "키 페어 생성" 버튼 클릭
4. 키 페어 생성 설정:
   - 이름: skn12-trading-keypair
   - 키 페어 유형: RSA (기본값 유지)
   - 프라이빗 키 파일 형식: .pem (Linux/macOS/Windows용)
5. "키 페어 생성" 버튼 클릭
6. 자동으로 .pem 파일이 다운로드됨 (절대 잃어버리면 안 됨!)
```

### 4️⃣ 다운로드된 키 파일 보안 설정 (중요!)
```bash
# 1. 다운로드된 키 파일을 안전한 위치로 이동
# Windows 탐색기에서 다음 폴더 생성
mkdir C:\aws-keys

# 2. Downloads 폴더에서 키 파일을 C:\aws-keys\로 이동
# skn12-trading-keypair.pem 파일을 잘라내기 → 붙여넣기

# 3. 파일 보안 설정 (매우 중요!)
# C:\aws-keys\skn12-trading-keypair.pem 파일 우클릭
# → "속성" 클릭
# → "보안" 탭 클릭  
# → "고급" 버튼 클릭
# → "상속 사용 안함" 클릭
# → "이 개체에서 상속된 사용 권한을 모두 제거합니다" 선택
# → "추가" 버튼 클릭
# → "보안 주체 선택" 클릭
# → "고급" → "지금 찾기" → 현재 사용자 계정 선택
# → "모든 권한" 체크박스 선택
# → "확인" → "확인" → "확인"
```

**🚨 중요**: 이 키 파일을 잃어버리면 서버에 접속할 수 없습니다! 반드시 안전한 곳에 백업하세요.

---

## 🛡️ Step 2: 보안 그룹 생성 (방화벽 규칙 설정) (10분)

> **💡 보안 그룹이란?**: AWS의 가상 방화벽입니다. 어떤 포트를 열고 닫을지, 어디서 접속을 허용할지 설정합니다.

### 1️⃣ Jenkins Server용 보안 그룹 생성

#### A. 보안 그룹 생성 시작
```
1. EC2 Dashboard → 왼쪽 메뉴 "네트워크 및 보안" → "보안 그룹" 클릭
2. 우측 상단 "보안 그룹 생성" 버튼 클릭
```

#### B. 기본 정보 입력
```
보안 그룹 이름: skn12-jenkins-sg
설명: SKN12 Jenkins CI/CD Server Security Group
VPC: vpc-xxxxxxxx (기본값 유지 - 기본 VPC)
```

#### C. 인바운드 규칙 설정 (들어오는 트래픽 허용)
```
"인바운드 규칙" 탭에서 "규칙 추가" 버튼을 3번 클릭하여 다음 규칙들 추가:

규칙 1 - SSH 접속 (관리자용):
- 유형: SSH (자동으로 TCP 프로토콜, 포트 22 설정됨)
- 소스: 내 IP (자동으로 현재 접속 IP가 설정됨, 예: 123.456.789.012/32)
- 설명: SSH access for administrators

규칙 2 - Jenkins 웹 UI:
- 유형: 사용자 지정 TCP
- 포트 범위: 18080
- 소스: 0.0.0.0/0 (모든 IP에서 접속 허용)
- 설명: Jenkins web interface

규칙 3 - HTTPS (향후 SSL 적용용):
- 유형: HTTPS (자동으로 TCP 프로토콜, 포트 443 설정됨)
- 소스: 0.0.0.0/0
- 설명: HTTPS for future SSL setup
```

#### D. 아웃바운드 규칙 (나가는 트래픽)
```
기본값 유지 (모든 트래픽 허용)
- 이미 설정된 "모든 트래픽" 규칙을 그대로 두세요
```

#### E. 보안 그룹 생성 완료
```
"보안 그룹 생성" 버튼 클릭
→ "보안 그룹 skn12-jenkins-sg이(가) 생성되었습니다" 메시지 확인
```

### 2️⃣ Deploy Server용 보안 그룹 생성

#### A. 두 번째 보안 그룹 생성 시작
```
다시 "보안 그룹 생성" 버튼 클릭
```

#### B. 기본 정보 입력
```
보안 그룹 이름: skn12-deploy-sg
설명: SKN12 Application Deploy Server Security Group  
VPC: vpc-xxxxxxxx (기본값 유지)
```

#### C. 인바운드 규칙 설정 (총 5개 규칙)
```
"규칙 추가" 버튼을 5번 클릭하여 다음 규칙들 추가:

규칙 1 - Jenkins에서 SSH 접속:
- 유형: SSH
- 소스: 사용자 지정 → skn12-jenkins-sg 선택 (보안 그룹 이름으로 검색)
- 설명: SSH access from Jenkins server

규칙 2 - 관리자 SSH 접속:
- 유형: SSH  
- 소스: 내 IP (자동 설정)
- 설명: SSH access for administrators

규칙 3 - 웹 서비스 (Nginx):
- 유형: HTTP (포트 80)
- 소스: 0.0.0.0/0
- 설명: Web service via Nginx proxy

규칙 4 - Base Web Server:
- 유형: 사용자 지정 TCP
- 포트 범위: 8000
- 소스: 0.0.0.0/0  
- 설명: Base Web Server direct access

규칙 5 - Model Server:
- 유형: 사용자 지정 TCP
- 포트 범위: 8001
- 소스: 0.0.0.0/0
- 설명: Model Server direct access
```

#### D. Deploy 보안 그룹 생성 완료
```
"보안 그룹 생성" 버튼 클릭
```

---

## 🖥️ Step 3: Jenkins Server EC2 인스턴스 생성 (15분)

> **💡 EC2 인스턴스란?**: AWS의 가상 서버입니다. 실제 컴퓨터를 클라우드에서 빌려쓰는 것과 같습니다.

### 3️⃣ 인스턴스 시작하기

#### A. 인스턴스 생성 시작
```
1. EC2 Dashboard 메인 화면에서 "인스턴스 시작" 버튼 클릭
2. 또는 왼쪽 메뉴 "인스턴스" → "인스턴스" → "인스턴스 시작"
```

#### B. 이름과 태그 설정
```
이름: skn12-jenkins-server

추가 태그 (선택사항, 하지만 권장):
키: Project, 값: SKN12-FINAL-2TEAM
키: Environment, 값: Production
키: Role, 값: Jenkins-CI-CD
```

#### C. 운영체제(AMI) 선택
```
"Amazon Machine Image (AMI)" 섹션에서:

1. "빠른 시작" 탭 선택 (기본값)
2. "Ubuntu" 클릭
3. "Ubuntu Server 22.04 LTS (HVM), SSD Volume Type" 선택
   - 64비트 (x86) 아키텍처 확인
   - "프리 티어 사용 가능" 라벨 확인
4. AMI ID: ami-xxxxxxxx (자동 설정, 변경 안 함)
```

**💡 Ubuntu를 선택하는 이유**:
- 무료 티어 지원
- Docker 설치가 쉬움  
- 커뮤니티 지원이 풍부함
- 안정적인 LTS(장기지원) 버전

#### D. 인스턴스 유형 선택
```
"인스턴스 유형" 섹션에서:

1. 인스턴스 유형: t3.medium 선택
   - vCPU: 2개
   - 메모리: 4.0 GiB
   - 네트워크 성능: 최대 5 Gigabit

2. 무료 티어 경고 메시지 무시 (Jenkins는 최소 4GB RAM 필요)
```

**💡 t3.medium을 선택하는 이유**:
- Jenkins + Docker 빌드에 최소 4GB RAM 필요
- CPU 2개로 병렬 빌드 가능
- 월 $30 정도의 합리적인 비용

#### E. 키 페어 설정
```
"키 페어(로그인)" 섹션에서:

1. "기존 키 페어 선택" 선택
2. 키 페어 이름: skn12-trading-keypair (앞서 생성한 키)
3. 체크박스 확인: "선택한 프라이빗 키 파일(.pem)에 액세스할 수 있음을 확인합니다..."
```

#### F. 네트워크 설정
```
"네트워크 설정" 섹션에서 "편집" 버튼 클릭:

VPC: vpc-xxxxxxxx (기본 VPC 유지)
서브넷: subnet-xxxxxxxx (기본 서브넷 유지, 가용 영역 무관)
퍼블릭 IP 자동 할당: 활성화 (Enable) ✅
방화벽(보안 그룹): 기존 보안 그룹 선택
   → "기존 보안 그룹 선택" 라디오 버튼 선택
   → 일반 보안 그룹: skn12-jenkins-sg 체크박스 선택
```

#### G. 스토리지 구성
```
"스토리지 구성" 섹션:

1. 볼륨 1(루트) 설정:
   - 크기: 30 GiB로 변경 (기본 8GB에서 증가)
   - 볼륨 유형: gp3 (범용 SSD) 유지
   - IOPS: 3000 (기본값 유지)
   - 처리량: 125 MB/s (기본값 유지)
   - 종료 시 삭제: 체크 유지 (인스턴스 삭제 시 저장소도 함께 삭제)

2. "볼륨 추가" 버튼은 클릭하지 않음 (루트 볼륨만 사용)
```

**💡 30GB를 선택하는 이유**:
- Ubuntu OS: ~5GB
- Jenkins 홈 디렉토리: ~10GB
- Docker 이미지 캐시: ~15GB

#### H. 고급 세부 정보 (자동 설정 스크립트)
```
"고급 세부 정보" 섹션 확장 (맨 아래):

1. "종료 보호 활성화" 체크 (실수로 인스턴스 삭제 방지)
2. "상세 CloudWatch 모니터링 활성화" 체크 (성능 모니터링)
3. "사용자 데이터" 텍스트 박스에 다음 스크립트 입력:
```

```bash
#!/bin/bash
# =============================================================================
# Jenkins Server 자동 설정 스크립트
# =============================================================================
# 이 스크립트는 EC2 인스턴스가 처음 시작될 때 자동으로 실행됩니다.
# Docker, 기본 패키지, 시간대 설정 등을 자동으로 처리합니다.

echo "🚀 Jenkins Server 초기 설정 시작: $(date)" > /var/log/user-data.log

# -----------------------------------------------------------------------------
# 1. 시스템 업데이트 (보안 패치 포함)
# -----------------------------------------------------------------------------
echo "📦 시스템 패키지 업데이트 중..." >> /var/log/user-data.log
apt-get update -y
apt-get upgrade -y

# -----------------------------------------------------------------------------  
# 2. Docker 설치 (공식 저장소 사용)
# -----------------------------------------------------------------------------
echo "🐳 Docker 설치 중..." >> /var/log/user-data.log

# Docker 공식 GPG 키 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker 저장소 추가
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 패키지 목록 업데이트 후 Docker 설치
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작 및 부팅 시 자동 시작 설정
systemctl start docker
systemctl enable docker

# ubuntu 사용자를 docker 그룹에 추가 (sudo 없이 docker 명령어 사용 가능)
usermod -aG docker ubuntu

# -----------------------------------------------------------------------------
# 3. 기본 개발 도구 설치
# -----------------------------------------------------------------------------
echo "🛠️ 기본 도구 설치 중..." >> /var/log/user-data.log
apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    htop \
    tree \
    vim \
    net-tools \
    jq

# -----------------------------------------------------------------------------
# 4. 시간대 설정 (한국 시간)
# -----------------------------------------------------------------------------
echo "🕐 시간대 설정 중..." >> /var/log/user-data.log
timedatectl set-timezone Asia/Seoul

# -----------------------------------------------------------------------------
# 5. Jenkins 데이터 디렉토리 준비
# -----------------------------------------------------------------------------
echo "📁 디렉토리 구조 생성 중..." >> /var/log/user-data.log
mkdir -p /opt/jenkins/{data,configs,scripts}
chown -R ubuntu:ubuntu /opt/jenkins

# -----------------------------------------------------------------------------
# 6. Git 전역 설정 (Jenkins용)
# -----------------------------------------------------------------------------
echo "🔧 Git 설정 중..." >> /var/log/user-data.log
sudo -u ubuntu git config --global user.name "Jenkins CI"
sudo -u ubuntu git config --global user.email "jenkins@skn12-trading.com"
sudo -u ubuntu git config --global init.defaultBranch main

# -----------------------------------------------------------------------------
# 7. 완료 신호 파일 생성
# -----------------------------------------------------------------------------
echo "✅ Jenkins Server 초기 설정 완료: $(date)" >> /var/log/user-data.log
echo "Jenkins Server 초기 설정 완료: $(date)" > /home/ubuntu/setup-complete.log
chown ubuntu:ubuntu /home/ubuntu/setup-complete.log

echo "🎉 모든 설정이 완료되었습니다!" >> /var/log/user-data.log
```

#### I. 요약 및 인스턴스 시작
```
1. "요약" 섹션에서 설정 내용 최종 확인:
   - 이름: skn12-jenkins-server
   - AMI: Ubuntu Server 22.04 LTS
   - 인스턴스 유형: t3.medium
   - 키 페어: skn12-trading-keypair
   - 보안 그룹: skn12-jenkins-sg
   - 스토리지: 30 GiB gp3

2. "인스턴스 시작" 버튼 클릭

3. "인스턴스 시작 중" 페이지가 나타나면 성공
   - "모든 인스턴스 보기" 버튼 클릭하여 인스턴스 목록으로 이동
```

---

## 🚀 Step 4: Deploy Server EC2 인스턴스 생성 (10분)

> **💡 두 번째 서버 생성**: 실제 애플리케이션이 실행될 서버를 만듭니다.

### 4️⃣ Deploy Server 생성하기

#### A. 두 번째 인스턴스 생성 시작
```
1. 인스턴스 목록 화면에서 다시 "인스턴스 시작" 버튼 클릭
```

#### B. 이름과 태그 설정
```
이름: skn12-deploy-server

추가 태그:
키: Project, 값: SKN12-FINAL-2TEAM
키: Environment, 값: Production  
키: Role, 값: Application-Server
```

#### C. AMI 및 인스턴스 유형 선택
```
AMI: Ubuntu Server 22.04 LTS (Jenkins와 동일)
인스턴스 유형: t3.small (Jenkins보다 작은 사양)
   - vCPU: 2개
   - 메모리: 2.0 GiB
   - 예상 월 비용: ~$15
```

**💡 t3.small을 선택하는 이유**:
- 애플리케이션 실행에는 2GB RAM으로 충분
- Jenkins처럼 빌드 작업을 하지 않아서 더 적은 자원 필요
- 비용 절약

#### D. 키 페어 및 네트워크 설정
```
키 페어: skn12-trading-keypair (같은 키 사용)

네트워크 설정 → "편집":
- VPC: 기본 VPC 유지
- 퍼블릭 IP 자동 할당: 활성화 ✅
- 방화벽: 기존 보안 그룹 선택 → skn12-deploy-sg
```

#### E. 스토리지 설정
```
볼륨 크기: 20 GiB (Jenkins보다 작게)
- Ubuntu OS: ~5GB
- 애플리케이션 + Docker 이미지: ~10GB  
- 로그 및 데이터: ~5GB

볼륨 유형: gp3 유지
```

#### F. 사용자 데이터 스크립트
```bash
#!/bin/bash
# =============================================================================
# Deploy Server 자동 설정 스크립트
# =============================================================================
# 실제 애플리케이션이 실행될 서버의 초기 설정을 담당합니다.

echo "🚀 Deploy Server 초기 설정 시작: $(date)" > /var/log/user-data.log

# -----------------------------------------------------------------------------
# 1. 시스템 업데이트
# -----------------------------------------------------------------------------
echo "📦 시스템 패키지 업데이트 중..." >> /var/log/user-data.log
apt-get update -y
apt-get upgrade -y

# -----------------------------------------------------------------------------
# 2. Docker 설치 (Jenkins Server와 동일한 방법)
# -----------------------------------------------------------------------------
echo "🐳 Docker 설치 중..." >> /var/log/user-data.log

# Docker 공식 GPG 키 및 저장소 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 설정
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# -----------------------------------------------------------------------------
# 3. Nginx 설치 (리버스 프록시 및 로드밸런서용)
# -----------------------------------------------------------------------------
echo "🌐 Nginx 설치 중..." >> /var/log/user-data.log
apt-get install -y nginx

# Nginx 서비스 시작 및 자동 시작 설정
systemctl start nginx
systemctl enable nginx

# 기본 Nginx 설정 백업
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# -----------------------------------------------------------------------------
# 4. 기본 도구 설치
# -----------------------------------------------------------------------------
echo "🛠️ 기본 도구 설치 중..." >> /var/log/user-data.log
apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    htop \
    tree \
    vim \
    net-tools \
    jq \
    certbot \
    python3-certbot-nginx

# -----------------------------------------------------------------------------
# 5. 애플리케이션 디렉토리 구조 생성
# -----------------------------------------------------------------------------
echo "📁 애플리케이션 디렉토리 생성 중..." >> /var/log/user-data.log
mkdir -p /opt/skn12-trading/{configs,logs,backups,ssl}
mkdir -p /opt/skn12-trading/configs/{base-web-server,model-server}
mkdir -p /opt/skn12-trading/logs/{base-web-server,model-server,nginx}

# 소유권 설정 (ubuntu 사용자가 접근 가능하도록)
chown -R ubuntu:ubuntu /opt/skn12-trading

# 로그 디렉토리 권한 설정 (웹 서버가 쓸 수 있도록)
chmod -R 755 /opt/skn12-trading/logs

# -----------------------------------------------------------------------------
# 6. 시간대 설정
# -----------------------------------------------------------------------------
echo "🕐 시간대 설정 중..." >> /var/log/user-data.log
timedatectl set-timezone Asia/Seoul

# -----------------------------------------------------------------------------
# 7. 방화벽 기본 설정 (UFW)
# -----------------------------------------------------------------------------
echo "🔥 방화벽 기본 설정 중..." >> /var/log/user-data.log
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 8000
ufw allow 8001

# -----------------------------------------------------------------------------
# 8. 시스템 모니터링 도구 설치
# -----------------------------------------------------------------------------
echo "📊 모니터링 도구 설치 중..." >> /var/log/user-data.log
apt-get install -y htop iotop iftop ncdu

# -----------------------------------------------------------------------------
# 9. 완료 신호
# -----------------------------------------------------------------------------
echo "✅ Deploy Server 초기 설정 완료: $(date)" >> /var/log/user-data.log
echo "Deploy Server 초기 설정 완료: $(date)" > /home/ubuntu/setup-complete.log
chown ubuntu:ubuntu /home/ubuntu/setup-complete.log

# 디스크 사용량 체크
df -h >> /home/ubuntu/setup-complete.log
echo "🎉 모든 설정이 완료되었습니다!" >> /var/log/user-data.log
```

#### G. Deploy Server 인스턴스 시작
```
"인스턴스 시작" 버튼 클릭
```

---

## 🌐 Step 5: Elastic IP 할당 (고정 IP 설정) (10분)

> **💡 Elastic IP란?**: 인스턴스를 재시작해도 변하지 않는 고정 IP 주소입니다. 
> 웹사이트 도메인 연결이나 Jenkins Webhook URL 설정에 필요합니다.

### 5️⃣ Jenkins Server용 Elastic IP 생성

#### A. Elastic IP 생성
```
1. EC2 Dashboard → 왼쪽 메뉴 "네트워크 및 보안" → "Elastic IP" 클릭
2. 우측 상단 "Elastic IP 주소 할당" 버튼 클릭
3. 설정:
   - 네트워크 경계 그룹: ap-northeast-2 (서울 리전)
   - 퍼블릭 IPv4 주소 풀: Amazon의 IPv4 주소 풀 (기본값)
   - 태그 추가 (선택사항):
     * 키: Name, 값: skn12-jenkins-eip  
     * 키: Project, 값: SKN12-FINAL-2TEAM
4. "할당" 버튼 클릭
```

#### B. Jenkins Server에 Elastic IP 연결
```
1. 방금 생성된 Elastic IP 주소 선택 (체크박스 클릭)
2. "작업" 드롭다운 → "Elastic IP 주소 연결" 클릭  
3. 연결 설정:
   - 리소스 유형: 인스턴스 (기본값)
   - 인스턴스: skn12-jenkins-server 선택
   - 프라이빗 IP 주소: (자동 선택됨)
4. "연결" 버튼 클릭
5. "Elastic IP 주소가 성공적으로 연결되었습니다" 메시지 확인
```

### 5️⃣ Deploy Server용 Elastic IP 생성

#### A. 두 번째 Elastic IP 생성
```
다시 "Elastic IP 주소 할당" 버튼 클릭

설정:
- 네트워크 경계 그룹: ap-northeast-2
- 태그:
  * 키: Name, 값: skn12-deploy-eip
  * 키: Project, 값: SKN12-FINAL-2TEAM
```

#### B. Deploy Server에 연결
```
생성된 Elastic IP를 skn12-deploy-server에 연결
(Jenkins와 동일한 과정)
```

### 5️⃣ IP 주소 기록하기
```
1. "Elastic IP" 페이지에서 할당된 IP 주소들 확인
2. 메모장에 기록:

Jenkins Server IP: [예: 13.125.123.45]
Deploy Server IP: [예: 52.79.234.56]

3. 이 IP들은 앞으로 계속 사용됩니다!
```

**💰 비용 안내**: 
- Elastic IP를 인스턴스에 연결한 상태에서는 무료
- 인스턴스에 연결하지 않고 보유만 하면 시간당 요금 발생

---

## 🔗 Step 6: 인스턴스 상태 확인 및 SSH 접속 테스트 (10분)

> **💡 이 단계에서는**: 생성한 서버들이 정상적으로 실행되고 접속 가능한지 확인합니다.

### 6️⃣ 인스턴스 상태 확인

#### A. 인스턴스 목록 확인
```
1. EC2 Dashboard → 왼쪽 메뉴 "인스턴스" → "인스턴스" 클릭
2. 생성한 인스턴스들 확인:

skn12-jenkins-server:
- 인스턴스 상태: ✅ running (녹색)
- 상태 검사: ✅ 2/2 checks passed 
- 퍼블릭 IPv4 주소: [Jenkins Elastic IP]
- 프라이빗 IPv4 주소: 172.31.x.x

skn12-deploy-server:
- 인스턴스 상태: ✅ running (녹색)  
- 상태 검사: ✅ 2/2 checks passed
- 퍼블릭 IPv4 주소: [Deploy Elastic IP]
- 프라이빗 IPv4 주소: 172.31.x.x
```

#### B. 상태 검사 대기
```
⏰ 상태 검사가 "2/2 checks passed"가 될 때까지 대기 (약 2-3분)

만약 "상태 검사" 칸에 "초기화 중" 또는 "1/2 checks passed"가 표시되면:
- 2-3분 더 기다리기
- 페이지 새로고침 (F5)
- 두 검사 모두 통과할 때까지 기다린 후 다음 단계 진행
```

### 6️⃣ SSH 접속 테스트 

#### A. Windows PowerShell 준비
```
1. 시작 버튼 → "PowerShell" 검색 → "Windows PowerShell" 실행
2. 또는 Win + R → "powershell" 입력 → Enter
```

#### B. Jenkins Server SSH 접속 테스트
```powershell
# 키 파일 경로와 서버 IP로 SSH 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-Elastic-IP]

# 예시 (실제 IP로 교체하세요)
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@13.125.123.45
```

#### C. 첫 접속 시 호스트 키 확인
```
첫 번째 접속 시 다음 메시지가 표시됩니다:

The authenticity of host '13.125.123.45 (13.125.123.45)' can't be established.
ECDSA key fingerprint is SHA256:abcd1234...
Are you sure you want to continue connecting (yes/no/[fingerprint])?

→ "yes" 입력 후 Enter
```

#### D. 성공적인 접속 확인
```
성공적으로 접속되면 다음과 같은 화면이 나타납니다:

Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-1015-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

Last login: [날짜/시간]
ubuntu@ip-172-31-xx-xx:~$
```

#### E. 자동 설정 스크립트 완료 확인
```bash
# 설정 완료 파일 확인
cat /home/ubuntu/setup-complete.log

# 예상 출력:
# Jenkins Server 초기 설정 완료: Wed Aug 12 14:23:45 KST 2025

# Docker 설치 확인
docker --version
# 예상 출력: Docker version 24.0.7, build afdd53b

# Docker Compose 확인  
docker compose version
# 예상 출력: Docker Compose version v2.21.0

# 설치된 패키지 확인
git --version
curl --version
```

#### F. Jenkins 서버에서 로그아웃
```bash
# SSH 연결 종료
exit

# 또는 Ctrl + D
```

### 6️⃣ Deploy Server SSH 접속 테스트

#### A. Deploy Server 접속
```powershell
# PowerShell에서 Deploy Server에 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-Elastic-IP]

# 예시
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@52.79.234.56
```

#### B. Deploy Server 설정 확인
```bash
# 설정 완료 확인
cat /home/ubuntu/setup-complete.log

# Docker 확인
docker --version

# Nginx 확인
nginx -v
systemctl status nginx

# 애플리케이션 디렉토리 확인
ls -la /opt/skn12-trading/
tree /opt/skn12-trading/

# 예상 출력:
# /opt/skn12-trading/
# ├── configs/
# │   ├── base-web-server/
# │   └── model-server/
# ├── logs/
# │   ├── base-web-server/
# │   ├── model-server/
# │   └── nginx/
# ├── backups/
# └── ssl/

# 방화벽 상태 확인
ufw status

# 디스크 사용량 확인
df -h
```

#### C. Deploy 서버에서 로그아웃
```bash
exit
```

### 6️⃣ 접속 문제 해결

#### 문제 1: "Permission denied (publickey)"
```
원인: 키 파일 권한 문제

해결책:
1. 키 파일 권한 재설정:
   - C:\aws-keys\skn12-trading-keypair.pem 우클릭
   - 속성 → 보안 → 고급 → 상속 사용 안함
   - 소유자만 "모든 권한" 부여

2. 다른 SSH 클라이언트 시도:
   - Git Bash
   - Windows Subsystem for Linux (WSL)
   - MobaXterm
   - PuTTY (.ppk 파일 필요)
```

#### 문제 2: "Connection timed out"  
```
원인: 네트워크 또는 보안 그룹 문제

해결책:
1. 보안 그룹 확인:
   - EC2 → 보안 그룹 → skn12-jenkins-sg 클릭
   - 인바운드 규칙에서 SSH (포트 22) 규칙 확인
   - 소스가 "내 IP"로 올바르게 설정되었는지 확인

2. 내 IP 주소 변경 확인:
   - whatismyipaddress.com에서 현재 IP 확인
   - 보안 그룹에서 IP 업데이트

3. 인스턴스 상태 확인:
   - 인스턴스가 "running" 상태인지 확인
   - 상태 검사가 "2/2 checks passed"인지 확인
```

#### 문제 3: "Host key verification failed"
```
원인: 이전에 같은 IP로 다른 서버에 접속한 적이 있음

해결책:
# known_hosts 파일에서 해당 IP 제거
ssh-keygen -R [서버-IP-주소]

# 또는 호스트 키 확인 건너뛰기 (임시)
ssh -o StrictHostKeyChecking=no -i "키파일" ubuntu@서버IP
```

---

## 📝 Step 7: 서버 정보 정리 및 문서화 (5분)

### 7️⃣ 접속 정보 정리

#### A. 서버 정보 요약표 작성
```
=== SKN12 Trading Platform 서버 정보 ===

Jenkins Server (CI/CD):
- 이름: skn12-jenkins-server
- Public IP: [Jenkins-Elastic-IP]
- SSH 접속: ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-IP]
- Jenkins URL: http://[Jenkins-IP]:18080 (Jenkins 설치 후)
- 사양: t3.medium (2 vCPU, 4GB RAM, 30GB SSD)
- 월 예상 비용: ~$30

Deploy Server (Application):
- 이름: skn12-deploy-server  
- Public IP: [Deploy-Elastic-IP]
- SSH 접속: ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-IP]
- App URLs: 
  * Base Web Server: http://[Deploy-IP]:8000 (배포 후)
  * Model Server: http://[Deploy-IP]:8001 (배포 후)
  * Nginx Proxy: http://[Deploy-IP] (설정 후)
- 사양: t3.small (2 vCPU, 2GB RAM, 20GB SSD)  
- 월 예상 비용: ~$15

AWS 리소스:
- 키 페어: skn12-trading-keypair
- 보안 그룹: skn12-jenkins-sg, skn12-deploy-sg
- Elastic IP: 2개 (각 서버당 1개)
- 리전: ap-northeast-2 (서울)

총 월 예상 비용: ~$45 (EC2만, 기존 AWS 서비스 별도)
```

#### B. 메모장에 저장
```
1. 메모장 실행 (시작 → "메모장" 검색)
2. 위 정보를 복사하여 붙여넣기
3. 파일 저장:
   - 파일명: SKN12_서버정보.txt
   - 위치: C:\aws-keys\ (키 파일과 같은 폴더)
```

### 7️⃣ 네트워크 연결 테스트

#### A. Jenkins Server에서 외부 연결 테스트
```bash
# Jenkins Server에 SSH 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-IP]

# 외부 서비스 연결 테스트
curl -I https://hub.docker.com
# 응답: HTTP/2 200 (정상)

curl -I https://github.com  
# 응답: HTTP/2 200 (정상)

curl -I https://google.com
# 응답: HTTP/2 200 (정상)

# AWS 서비스 연결 테스트 (기존 설정 확인)
curl -I https://s3.ap-northeast-2.amazonaws.com
# 응답: HTTP/1.1 200 OK (정상)

exit
```

#### B. Deploy Server에서 연결 테스트
```bash
# Deploy Server에 SSH 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Deploy-IP]

# Docker Hub 연결 테스트
curl -I https://hub.docker.com

# GitHub 연결 테스트  
curl -I https://github.com

# Nginx 웹서버 동작 확인
curl http://localhost
# 응답: HTML 페이지 (Nginx 기본 페이지)

# 또는 브라우저에서 확인:
# http://[Deploy-IP] 접속 → "Welcome to nginx!" 페이지 표시

exit
```

---

## ✅ EC2 설정 완료 체크리스트

### 🎯 기본 인프라 확인:
- [ ] Jenkins Server EC2 생성 및 running 상태
- [ ] Deploy Server EC2 생성 및 running 상태  
- [ ] 키 페어 생성 및 안전한 보관 (C:\aws-keys\)
- [ ] 보안 그룹 생성 (skn12-jenkins-sg, skn12-deploy-sg)
- [ ] Elastic IP 할당 및 연결 (2개)
- [ ] SSH 접속 테스트 성공 (양쪽 서버 모두)

### 🛠️ 소프트웨어 설치 확인:
- [ ] Jenkins Server: Docker, Docker Compose 설치 완료
- [ ] Deploy Server: Docker, Nginx 설치 완료
- [ ] 시스템 업데이트 및 기본 패키지 설치 완료
- [ ] 시간대 설정 (Asia/Seoul) 완료
- [ ] Git 설정 완료

### 📁 디렉토리 구조 확인:
- [ ] `/opt/skn12-trading/configs/` 존재
- [ ] `/opt/skn12-trading/logs/` 존재  
- [ ] `/opt/skn12-trading/backups/` 존재
- [ ] 적절한 권한 설정 (ubuntu 사용자 소유)

### 🌐 네트워크 연결 확인:
- [ ] Jenkins Server → 외부 인터넷 연결 정상
- [ ] Deploy Server → 외부 인터넷 연결 정상
- [ ] Nginx 웹서버 정상 동작 (Deploy Server)
- [ ] AWS 서비스 연결 정상 (기존 설정 활용)

### 📝 문서화 완료:
- [ ] 서버 접속 정보 정리 및 저장
- [ ] IP 주소 기록 및 보관
- [ ] SSH 접속 명령어 확인

---

## 🎯 다음 단계 미리보기

### 1️⃣ Jenkins 설치 및 설정 (다음 가이드):
- Docker Compose로 Jenkins 컨테이너 실행
- Jenkins 초기 설정 및 플러그인 설치
- GitHub, Docker Hub 연동 설정

### 2️⃣ CI/CD 파이프라인 구축:
- GitHub Webhook 설정
- Jenkinsfile 작성
- 자동 빌드 및 배포 테스트

### 3️⃣ 애플리케이션 배포:
- Docker 이미지 빌드 및 푸시
- Deploy Server에서 컨테이너 실행
- 실제 서비스 접속 테스트

---

## 💰 비용 관리 팁

### 개발 중 비용 절약하기:
```bash
# PowerShell에서 AWS CLI 설치 후 (선택사항)
# 개발하지 않을 때 인스턴스 중지
aws ec2 stop-instances --instance-ids i-jenkins123 i-deploy456

# 다시 시작할 때  
aws ec2 start-instances --instance-ids i-jenkins123 i-deploy456

# 💡 인스턴스를 중지하면 컴퓨팅 비용은 0이 되고, 
#    저장소(EBS) 비용만 발생합니다 (월 $1-2 정도)
```

### CloudWatch 비용 알림 설정:
```
1. AWS Console → CloudWatch → 청구 알림
2. 임계값: $50/월 설정
3. 이메일 알림 활성화
4. 예상 비용 초과 시 즉시 알림 수신
```

---

## 🔒 보안 강화 (선택사항)

### 추가 보안 조치:
```bash
# SSH 포트 변경 (22 → 다른 포트)
sudo vim /etc/ssh/sshd_config
# Port 2222 (또는 다른 포트)
sudo systemctl restart ssh

# fail2ban 설치 (무차별 대입 공격 방지)
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 자동 보안 업데이트 활성화
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### Jenkins HTTPS 설정 (향후):
```bash
# Let's Encrypt SSL 인증서 설치
sudo certbot --nginx -d jenkins.yourdomain.com
```

---

## 🎉 축하합니다!

AWS EC2 기반 CI/CD 인프라 구축의 기초 단계가 완료되었습니다!

### ✅ 지금까지 구축한 것:
- 🖥️ **Jenkins Server**: 코드 빌드 및 배포 자동화
- 🚀 **Deploy Server**: 실제 애플리케이션 운영
- 🔐 **보안**: 적절한 방화벽 및 접근 제어
- 🌐 **네트워크**: 고정 IP 및 외부 연결

### 🚀 다음 할 일:
1. **Jenkins 컨테이너 설치** (docker-compose 사용)
2. **Docker Hub 계정 연동**
3. **GitHub Webhook 설정**  
4. **CI/CD 파이프라인 구성**
5. **실제 애플리케이션 배포**

모든 준비가 완료되었습니다. 이제 본격적인 DevOps 자동화를 시작해봅시다! 🚀