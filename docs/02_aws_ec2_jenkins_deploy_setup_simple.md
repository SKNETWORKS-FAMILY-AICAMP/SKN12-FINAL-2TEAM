# 🚀 AWS EC2 Jenkins 초간단 설치 가이드 (초보자용)

> **작성일**: 2025년 1월  
> **소요시간**: 약 2시간  
> **난이도**: ⭐⭐ (초급)

---

## 📌 이 가이드를 선택해야 하는 이유

### 현재 상황
- 코드를 수정할 때마다 수동으로 서버에 올리고 계신가요?
- "내 컴퓨터에선 되는데" 문제로 고민하신 적 있나요?
- 배포할 때마다 실수로 서비스가 중단된 적 있나요?

### 이 가이드를 따라하면
✅ GitHub에 코드 올리면 → 자동으로 배포 완료  
✅ 실수 없는 자동화된 배포  
✅ 24시간 무중단 서비스  

---

## 🎯 최종 목표 시스템

```
[개발자 PC] --push--> [GitHub] --webhook--> [Jenkins] --deploy--> [서비스 서버]
     ↑                                                                    ↓
     └──────────────── 사용자가 서비스 이용 ←─────────────────────────┘
```

---

## 📦 필요한 것들

| 항목 | 설명 | 비용 |
|-----|------|------|
| AWS 계정 | 이미 있으시죠? | - |
| EC2 인스턴스 1개 | Jenkins 서버용 | 월 약 $20 |
| GitHub 계정 | 코드 저장소 | 무료 |
| Docker Hub 계정 | 이미지 저장소 | 무료 |

---

## 🏃 빠른 시작 (30분 완성)

### Step 1: EC2 인스턴스 생성 (5분)

#### 1️⃣ AWS Console 접속
```
https://console.aws.amazon.com
→ EC2 검색 → 인스턴스 시작 클릭
```

#### 2️⃣ 인스턴스 기본 설정
```yaml
이름: jenkins-server
AMI: Ubuntu 22.04 LTS (무료 티어)
인스턴스 유형: t2.medium (최소 사양)
```

#### 3️⃣ 키 페어 생성 (중요!)
```
키 페어 설정:
- 키 페어 이름: jenkins-skn12-keypair
- 키 페어 유형: RSA 선택 (권장)
- 프라이빗 키 파일 형식: .pem 선택 (권장)
  💡 이유: 모든 SSH 클라이언트 지원 + PuTTY 변환 가능

⚠️ 중요: "키 페어 생성" 클릭 후 자동으로 다운로드됩니다!
📁 파일을 안전한 곳에 보관하세요 (다시 다운로드 불가)
```

#### 4️⃣ 네트워크 설정 (쉬운 버전)

**🤔 VPC가 뭔가요?**
- VPC = 가상의 독립적인 네트워크 공간
- 내 서버들만의 안전한 울타리라고 생각하세요

**🎯 우리가 만들 구조:**
```
🌍 인터넷
    ↓
🚪 ALB (로드밸런서) - 외부 접속점
    ↓
🔒 프라이빗 서브넷 - Jenkins/Deploy 서버 (안전한 내부)
    ↓
🌐 NAT Gateway - 내부에서 인터넷으로 나가는 문
```

**Step 4-1: VPC 만들기**
```
EC2 인스턴스 시작 화면에서:

네트워크 설정 섹션:
1. "VPC": 드롭다운 클릭
2. "새 VPC 생성" 선택

VPC 설정:
- VPC 이름: skn12-jenkins-vpc
- IPv4 CIDR: 10.0.0.0/16 (기본값 사용)
```

**Step 4-2: 서브넷 만들기**
```
서브넷 설정:
1. "서브넷": 드롭다운 클릭
2. "새 서브넷 생성" 선택

프라이빗 서브넷 생성:
- 서브넷 이름: skn12-private-subnet
- 가용 영역: ap-northeast-2a (서울)
- IPv4 CIDR: 10.0.10.0/24
- 퍼블릭 IPv4 주소 자동 할당: 비활성화 ✅
```

💡 **왜 프라이빗 서브넷?**
- Jenkins는 민감한 정보 (API 키, 코드 등) 처리
- 외부에서 직접 접근 차단 = 보안 강화
- ALB를 통해서만 접근 가능

#### 5️⃣ 보안 그룹 설정 (방화벽)

**🤔 보안 그룹이 뭔가요?**
- 서버의 방화벽이라고 생각하세요
- 어떤 포트로 누가 들어올 수 있는지 결정

**Step 5-1: 보안 그룹 만들기**
```
보안 그룹 섹션에서:
1. "새 보안 그룹 생성" 선택
2. 보안 그룹 이름: jenkins-security-group
3. 설명: Jenkins server security group
```

**Step 5-2: 인바운드 규칙 (들어오는 트래픽)**
```
인바운드 규칙 추가:

1️⃣ SSH 접속용:
   - 유형: SSH
   - 포트: 22
   - 소스: 내 IP (자동 감지됨)
   - 설명: SSH access from my IP

2️⃣ Jenkins 웹 UI용:
   - 유형: 사용자 지정 TCP
   - 포트: 8080
   - 소스: 내 IP
   - 설명: Jenkins web UI access

3️⃣ 웹 서비스용 (나중에 ALB에서 사용):
   - 유형: HTTP
   - 포트: 80
   - 소스: 0.0.0.0/0 (모든 곳)
   - 설명: Web service via ALB
```

💡 **내 IP 확인하는 법**: 구글에서 "내 IP 주소" 검색

#### 6️⃣ 스토리지 설정

**🤔 스토리지가 왜 중요한가요?**
- Jenkins 빌드 파일, 로그, 플러그인 저장 공간
- 부족하면 빌드 실패할 수 있음

```
스토리지 구성:
1. 루트 볼륨 설정:
   - 크기: 30 GiB
   - 볼륨 유형: gp3 (빠르고 저렴)
   - IOPS: 3000 (기본값)
   - 처리량: 125 MiB/s (기본값)

2. 고급 설정:
   - 암호화: 활성화 ✅ (보안 강화)
   - 종료 시 삭제: 비활성화 ✅ (데이터 보호)
```

#### 7️⃣ 고급 세부 정보 (선택사항)

**IAM 인스턴스 프로파일:**
```
나중에 필요하면 설정:
- Docker Hub 접근용
- S3 백업용
- CloudWatch 로그용

지금은 "없음"으로 두고 시작 ✅
```

**사용자 데이터 (부팅 시 자동 실행 스크립트):**
```
고급 세부 정보 → 사용자 데이터에 입력:

#!/bin/bash
echo "SKN12 Jenkins Server 초기화 시작" > /home/ubuntu/server-init.log
date >> /home/ubuntu/server-init.log

# 기본 패키지 업데이트
apt-get update -y
apt-get upgrade -y

# 필수 패키지 설치
apt-get install -y curl wget git htop

# 시간대 설정
timedatectl set-timezone Asia/Seoul

echo "서버 초기화 완료" >> /home/ubuntu/server-init.log
```

#### 8️⃣ 인스턴스 시작 및 확인

**Step 8-1: 인스턴스 시작**
```
1. 모든 설정 확인:
   ✅ 이름: jenkins-server
   ✅ AMI: Ubuntu 22.04 LTS
   ✅ 인스턴스 유형: t2.medium
   ✅ 키 페어: jenkins-skn12-keypair.pem
   ✅ VPC: skn12-jenkins-vpc
   ✅ 서브넷: skn12-private-subnet
   ✅ 보안 그룹: jenkins-security-group
   ✅ 스토리지: 30GB gp3

2. "인스턴스 시작" 클릭
3. 키 페어 다운로드 확인
```

**Step 8-2: 인스턴스 상태 확인**
```
EC2 콘솔에서 확인:
1. 인스턴스 상태: running ✅
2. 상태 검사: 2/2 검사 통과 ✅ (2-3분 소요)
3. 프라이빗 IP 주소: 10.0.10.xxx 확인
```

**Step 8-3: 프라이빗 IP 접속 준비**
```
⚠️ 중요: 프라이빗 서브넷이므로 직접 SSH 불가능!

해결 방법들:
1. 같은 VPC에 점프 서버 (추가 비용)
2. VPN 연결 (복잡)
3. Session Manager 사용 (권장)
```

---

### Step 2: 서버 접속 및 필수 프로그램 설치 (10분)

#### 1️⃣ 프라이빗 서브넷 서버 접속 방법

**🤔 왜 직접 SSH가 안 되나요?**
- 프라이빗 서브넷 = 외부 인터넷에서 직접 접근 불가
- 보안을 위해 의도적으로 막아둔 것
- AWS Session Manager로 안전하게 접속!

##### A. Session Manager 접속 (권장)
```
1. EC2 콘솔에서 jenkins-server 인스턴스 선택
2. "연결" 버튼 클릭
3. "Session Manager" 탭 선택
4. "연결" 클릭

→ 브라우저에서 터미널이 열립니다! 🎉
```

**Session Manager 설정이 안 된다면:**
```
1. EC2 콘솔 → 인스턴스 선택 → 작업 → 보안 → IAM 역할 수정
2. 새 IAM 역할 생성:
   - 역할 이름: EC2-SSM-Role  
   - 정책: AmazonSSMManagedInstanceCore 연결
3. 인스턴스 재시작
```

##### B. 점프 서버 방식 (대안)
```bash
# 퍼블릭 서브넷에 작은 인스턴스 생성 → 점프 서버로 사용
# 비용이 추가로 발생하므로 권장하지 않음

# 점프 서버 접속 후
ssh -i key.pem ubuntu@[프라이빗-IP]
```

##### C. 로컬 개발용 - 퍼블릭 IP 임시 할당
```
⚠️ 개발 중에만 사용!

1. EC2 콘솔 → 인스턴스 선택 → 작업 → 네트워킹 → 퍼블릭 IP 주소 연결
2. 탄력적 IP 할당 및 연결
3. SSH 접속:
   ssh -i "C:\aws-keys\jenkins-skn12-keypair.pem" ubuntu@[퍼블릭IP]
4. 작업 완료 후 퍼블릭 IP 해제 (보안)
```

#### 2️⃣ NAT Gateway 설정 (인터넷 접속용)

**🤔 NAT Gateway가 왜 필요한가요?**
- 프라이빗 서브넷 → 인터넷 연결 불가
- Jenkins가 Docker Hub, GitHub 접속 필요
- NAT Gateway = 내부→외부 일방향 연결

**Step 2-1: NAT Gateway 생성**
```
1. VPC 콘솔 → NAT Gateway → "NAT Gateway 생성"

NAT Gateway 설정:
- 이름: skn12-nat-gateway
- 서브넷: 퍼블릭 서브넷 선택 (새로 만들어야 함)
- 연결 유형: 퍼블릭
- 탄력적 IP 할당: 새 탄력적 IP 할당
```

**Step 2-2: 퍼블릭 서브넷 생성 (NAT Gateway용)**
```
VPC 콘솔 → 서브넷 → "서브넷 생성"

퍼블릭 서브넷 설정:
- VPC: skn12-jenkins-vpc 선택
- 서브넷 이름: skn12-public-subnet
- 가용 영역: ap-northeast-2a (동일한 AZ)
- IPv4 CIDR: 10.0.1.0/24
```

**Step 2-3: 인터넷 게이트웨이 연결**
```
1. VPC 콘솔 → 인터넷 게이트웨이 → "인터넷 게이트웨이 생성"
   - 이름: skn12-internet-gateway

2. 생성 후 → 작업 → VPC에 연결
   - VPC: skn12-jenkins-vpc 선택
```

**Step 2-4: 라우팅 테이블 설정**
```
퍼블릭 서브넷 라우팅:
1. VPC 콘솔 → 라우팅 테이블 → "라우팅 테이블 생성"
   - 이름: skn12-public-route-table
   - VPC: skn12-jenkins-vpc

2. 라우팅 추가:
   - 대상: 0.0.0.0/0
   - 타겟: 인터넷 게이트웨이 (skn12-internet-gateway)

3. 서브넷 연결:
   - 서브넷 연결 탭 → 서브넷 연결 편집
   - skn12-public-subnet 선택

프라이빗 서브넷 라우팅:
1. 라우팅 테이블 생성:
   - 이름: skn12-private-route-table
   - VPC: skn12-jenkins-vpc

2. 라우팅 추가:
   - 대상: 0.0.0.0/0
   - 타겟: NAT 게이트웨이 (skn12-nat-gateway)

3. 서브넷 연결:
   - skn12-private-subnet 선택
```

#### 3️⃣ Docker 설치 및 환경 설정

**Step 3-1: 인터넷 연결 확인**
```bash
# Session Manager에서 실행
# 인터넷 연결 테스트
ping -c 3 8.8.8.8

# 결과:
# ✅ 성공: NAT Gateway 정상 작동
# ❌ 실패: NAT Gateway 또는 라우팅 문제
```

**Step 3-2: Docker 설치 (복사해서 붙여넣기)**
```bash
# 시스템 업데이트
sudo apt-get update -y

# Docker 설치 (한 번에 복사해서 실행)
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker 권한 설정
sudo usermod -aG docker ubuntu

# 시스템 재시작 (권한 적용)
sudo reboot
```

**Step 3-3: 재접속 및 확인**
```bash
# 재부팅 후 Session Manager로 다시 접속 (2-3분 후)
# EC2 콘솔 → 인스턴스 선택 → 연결 → Session Manager

# Docker 동작 확인
docker --version
docker compose version

# 네트워크 상태 확인
ip addr show  # 프라이빗 IP 확인: 10.0.10.xxx
curl -s ifconfig.me  # 퍼블릭 IP 확인: NAT Gateway IP
```

---

### Step 3: ALB 설정 (외부 접속용) (10분)

**🤔 ALB가 왜 필요한가요?**
- Application Load Balancer = 외부에서 안전하게 접속하는 문
- 프라이빗 서브넷의 Jenkins에 외부에서 접속 가능
- HTTPS 인증서 연결 가능 (나중에)
- 여러 서버로 트래픽 분산 가능

#### 1️⃣ ALB용 보안 그룹 생성
```
EC2 콘솔 → 보안 그룹 → "보안 그룹 생성"

ALB 보안 그룹 설정:
- 보안 그룹 이름: skn12-alb-security-group
- 설명: ALB for Jenkins access
- VPC: skn12-jenkins-vpc 선택

인바운드 규칙:
1️⃣ HTTP 접속:
   - 유형: HTTP
   - 포트: 80
   - 소스: 0.0.0.0/0 (전체 인터넷)
   - 설명: Public web access

2️⃣ HTTPS 접속 (나중에 사용):
   - 유형: HTTPS
   - 포트: 443
   - 소스: 0.0.0.0/0
   - 설명: Public HTTPS access
```

#### 2️⃣ Jenkins 보안 그룹 수정 (ALB에서만 접속 허용)
```
EC2 콘솔 → 보안 그룹 → jenkins-security-group 선택 → 편집

기존 Jenkins 웹 UI 규칙 제거:
❌ 포트 8080 규칙 삭제 (직접 접속 차단)

새 규칙 추가:
✅ Jenkins ALB 접속:
   - 유형: 사용자 지정 TCP
   - 포트: 8080
   - 소스: skn12-alb-security-group (ALB에서만 접속)
   - 설명: Jenkins via ALB only
```

#### 3️⃣ Application Load Balancer 생성
```
EC2 콘솔 → 로드 밸런서 → "Load Balancer 생성"

ALB 기본 설정:
1. 로드 밸런서 유형: Application Load Balancer 선택
2. 로드 밸런서 이름: skn12-jenkins-alb
3. 체계: 인터넷 경계 (Internet-facing)
4. IP 주소 유형: IPv4
```

#### 4️⃣ ALB 네트워크 매핑
```
VPC: skn12-jenkins-vpc 선택

매핑:
✅ ap-northeast-2a: skn12-public-subnet 선택
✅ ap-northeast-2c: 새 퍼블릭 서브넷 생성 필요

💡 ALB는 최소 2개 AZ 필요!
```

**Step 4-1: 추가 퍼블릭 서브넷 생성**
```
새 창에서 VPC 콘솔 → 서브넷 → "서브넷 생성"

추가 퍼블릭 서브넷:
- VPC: skn12-jenkins-vpc
- 서브넷 이름: skn12-public-subnet-2c
- 가용 영역: ap-northeast-2c
- IPv4 CIDR: 10.0.2.0/24

라우팅 테이블 연결:
- 라우팅 테이블: skn12-public-route-table
- 서브넷 연결 편집 → skn12-public-subnet-2c 추가
```

#### 5️⃣ ALB 보안 그룹 및 리스너 설정
```
보안 그룹: skn12-alb-security-group 선택

리스너 및 라우팅:
1. 프로토콜: HTTP
2. 포트: 80
3. 기본 작업: "새 대상 그룹 생성" 클릭
```

#### 6️⃣ 대상 그룹 생성
```
대상 그룹 기본 구성:
- 대상 유형: 인스턴스
- 대상 그룹 이름: jenkins-target-group
- 프로토콜: HTTP
- 포트: 8080
- VPC: skn12-jenkins-vpc

상태 확인:
- 상태 확인 프로토콜: HTTP
- 상태 확인 경로: /login
- 포트: 트래픽 포트
- 정상 임계값: 2
- 비정상 임계값: 2
- 제한 시간: 5초
- 간격: 30초

대상 등록:
- 인스턴스: jenkins-server 선택
- 포트: 8080
- "대기 중인 것으로 포함" 클릭
```

#### 7️⃣ ALB 생성 완료
```
"로드 밸런서 생성" 클릭

⏱️ 프로비저닝: 2-3분 소요
✅ 상태: Active 확인
✅ 대상 상태: Healthy 확인
```

---

### Step 4: Jenkins 설치 (10분)

#### 1️⃣ docker-compose.yml 파일 생성
```bash
# Session Manager 또는 SSH로 jenkins-server 접속

# 홈 디렉토리에서 작업
cd /home/ubuntu

# docker-compose.yml 파일 생성
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    user: root
    ports:
      - "8080:8080"  # ALB에서 접속
      - "50000:50000"  # Jenkins 에이전트용
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker
    environment:
      - JAVA_OPTS=-Xmx2048m -Djenkins.install.runSetupWizard=false
    restart: unless-stopped

volumes:
  jenkins_home:
EOF
```

#### 2️⃣ Jenkins 시작
```bash
# Jenkins 실행
docker compose up -d

# 컨테이너 상태 확인
docker ps

# Jenkins 로그 확인 (시작되는지 확인)
docker logs jenkins --follow

# 초기 비밀번호 확인 (중요! 복사해두세요)
sleep 30  # Jenkins 완전 시작 대기
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

#### 3️⃣ ALB DNS로 Jenkins 접속
```
EC2 콘솔 → 로드 밸런서 → skn12-jenkins-alb 선택
→ DNS 이름 복사: skn12-jenkins-alb-xxxxx.ap-northeast-2.elb.amazonaws.com

브라우저에서 접속:
http://[ALB-DNS-주소]

예: http://skn12-jenkins-alb-1234567890.ap-northeast-2.elb.amazonaws.com

🎉 Jenkins 로그인 화면이 나오면 성공!
```

#### 4️⃣ Jenkins 초기 설정
```
1. 초기 비밀번호 입력 (위에서 복사한 값)
2. "Install suggested plugins" 클릭 (5분 대기)
   ✅ 플러그인 설치 완료 기다리기

3. 관리자 계정 생성:
   - Username: admin
   - Password: skn12admin! (복잡한 비밀번호)
   - Full name: SKN12 Admin
   - Email: admin@skn12.com

4. Jenkins URL 확인:
   - Jenkins URL: http://[ALB-DNS-주소]/
   - "Save and Continue" 클릭

5. "Start using Jenkins" 클릭
```

#### 5️⃣ Deploy Server용 추가 EC2 인스턴스 생성
```
동일한 설정으로 Deploy 서버 생성:

EC2 인스턴스 시작:
- 이름: deploy-server
- AMI: Ubuntu 22.04 LTS
- 인스턴스 유형: t2.small (최소 사양)
- 키 페어: jenkins-skn12-keypair (동일한 키 사용)
- VPC: skn12-jenkins-vpc
- 서브넷: skn12-private-subnet (같은 프라이빗 서브넷)
- 보안 그룹: 새로 생성

Deploy 서버 보안 그룹:
- 이름: deploy-security-group
- 인바운드 규칙:
  1️⃣ SSH (Jenkins에서만):
     - 유형: SSH, 포트: 22
     - 소스: jenkins-security-group
  2️⃣ 웹 서비스 (ALB에서만):
     - 유형: HTTP, 포트: 80
     - 소스: skn12-alb-security-group
  3️⃣ API 서비스 (ALB에서만):
     - 유형: 사용자 지정 TCP, 포트: 8000
     - 소스: skn12-alb-security-group
```

---

### Step 5: RDS MySQL 데이터베이스 설정 (15분)

**🤔 왜 RDS를 사용하나요?**
- 관리형 MySQL 서비스 = 백업, 패치, 모니터링 자동화
- 고가용성과 자동 장애 조치
- 프라이빗 서브넷에서 안전하게 운영
- 확장과 성능 튜닝 쉬움

#### 1️⃣ DB 서브넷 그룹 생성
```
RDS 콘솔 → 서브넷 그룹 → "DB 서브넷 그룹 생성"

DB 서브넷 그룹 설정:
- 이름: skn12-db-subnet-group
- 설명: SKN12 Database subnet group
- VPC: skn12-jenkins-vpc 선택

서브넷 추가:
✅ ap-northeast-2a: skn12-private-subnet (10.0.10.0/24)
✅ ap-northeast-2c: 새 프라이빗 서브넷 생성 필요
```

**Step 5-1: 추가 프라이빗 서브넷 생성 (RDS용)**
```
VPC 콘솔 → 서브넷 → "서브넷 생성"

추가 프라이빗 서브넷:
- VPC: skn12-jenkins-vpc
- 서브넷 이름: skn12-private-subnet-2c-db
- 가용 영역: ap-northeast-2c
- IPv4 CIDR: 10.0.20.0/24

라우팅 테이블 연결:
- 라우팅 테이블: skn12-private-route-table
- 서브넷 연결 편집 → skn12-private-subnet-2c-db 추가
```

#### 2️⃣ RDS 보안 그룹 생성
```
EC2 콘솔 → 보안 그룹 → "보안 그룹 생성"

RDS 보안 그룹 설정:
- 보안 그룹 이름: skn12-rds-security-group
- 설명: RDS MySQL security group
- VPC: skn12-jenkins-vpc

인바운드 규칙:
1️⃣ MySQL/Aurora (Jenkins에서 접근):
   - 유형: MySQL/Aurora
   - 포트: 3306
   - 소스: jenkins-security-group
   - 설명: MySQL access from Jenkins

2️⃣ MySQL/Aurora (Deploy서버에서 접근):
   - 유형: MySQL/Aurora
   - 포트: 3306
   - 소스: deploy-security-group
   - 설명: MySQL access from Deploy server
```

#### 3️⃣ RDS MySQL 인스턴스 생성
```
RDS 콘솔 → "데이터베이스 생성"

엔진 설정:
- 엔진 유형: MySQL
- 버전: MySQL 8.0.35 (최신 안정 버전)
- 템플릿: 프리 티어 (개발용) 또는 프로덕션 (운영용)

인스턴스 설정:
- DB 인스턴스 식별자: skn12-mysql
- 마스터 사용자 이름: admin
- 마스터 암호: SKN12mysql!2024 (복잡한 암호)
- 암호 확인: SKN12mysql!2024

인스턴스 구성:
- DB 인스턴스 클래스: 
  * 프리 티어: db.t3.micro
  * 운영용: db.t3.small 이상
- 스토리지 유형: 범용 SSD (gp3)
- 할당된 스토리지: 20 GiB
- 스토리지 자동 조정: 활성화
```

#### 4️⃣ RDS 네트워크 및 보안 설정
```
연결 설정:
- Virtual Private Cloud (VPC): skn12-jenkins-vpc
- DB 서브넷 그룹: skn12-db-subnet-group
- 퍼블릭 액세스: 아니요 ✅ (프라이빗 접근만)
- VPC 보안 그룹: skn12-rds-security-group
- 가용 영역: ap-northeast-2a (기본값)
- 포트: 3306

추가 구성:
- 초기 데이터베이스 이름: finance_global
- DB 파라미터 그룹: default.mysql8.0
- 백업 보존 기간: 7일
- 백업 기간: 03:00-04:00 (한국시간)
- 유지 관리 기간: 일요일 04:00-05:00
- 삭제 방지: 활성화 ✅
```

#### 5️⃣ RDS 생성 완료 및 확인
```
"데이터베이스 생성" 클릭

⏱️ 생성 시간: 5-10분 소요
✅ 상태: 사용 가능 확인
📝 엔드포인트 복사: skn12-mysql.xxxxx.ap-northeast-2.rds.amazonaws.com
```

---

### Step 6: ElastiCache Redis 설정 (10분)

**🤔 왜 ElastiCache Redis가 필요한가요?**
- 세션 관리: 사용자 로그인 상태 저장
- 캐싱: API 응답 캐싱으로 성능 향상
- 실시간 데이터: WebSocket 연결 관리
- 분산 락: 동시성 제어

#### 1️⃣ Redis 서브넷 그룹 생성
```
ElastiCache 콘솔 → 서브넷 그룹 → "서브넷 그룹 생성"

Redis 서브넷 그룹 설정:
- 이름: skn12-redis-subnet-group
- 설명: SKN12 Redis subnet group
- VPC: skn12-jenkins-vpc

서브넷 추가:
✅ ap-northeast-2a: skn12-private-subnet
✅ ap-northeast-2c: skn12-private-subnet-2c-db
```

#### 2️⃣ Redis 보안 그룹 생성
```
EC2 콘솔 → 보안 그룹 → "보안 그룹 생성"

Redis 보안 그룹 설정:
- 보안 그룹 이름: skn12-redis-security-group
- 설명: ElastiCache Redis security group
- VPC: skn12-jenkins-vpc

인바운드 규칙:
1️⃣ Redis (Jenkins에서 접근):
   - 유형: 사용자 지정 TCP
   - 포트: 6379
   - 소스: jenkins-security-group
   - 설명: Redis access from Jenkins

2️⃣ Redis (Deploy서버에서 접근):
   - 유형: 사용자 지정 TCP
   - 포트: 6379
   - 소스: deploy-security-group
   - 설명: Redis access from Deploy server
```

#### 3️⃣ ElastiCache Redis 클러스터 생성
```
ElastiCache 콘솔 → Redis OSS → "Redis 클러스터 생성"

클러스터 설정:
- 클러스터 이름: skn12-redis
- 설명: SKN12 Redis cluster
- 노드 유형: cache.t3.micro (프리 티어) 또는 cache.t3.small
- 복제본 수: 0 (단일 노드, 개발용)

연결 설정:
- 서브넷 그룹: skn12-redis-subnet-group
- 보안 그룹: skn12-redis-security-group
- 암호화: 전송 중 암호화 활성화 ✅
- 저장 시 암호화: 활성화 ✅

백업 설정:
- 자동 백업: 활성화
- 백업 보존 기간: 5일
- 백업 기간: 05:00-06:00 (한국시간)
```

#### 4️⃣ Redis 생성 완료 및 확인
```
"Redis 클러스터 생성" 클릭

⏱️ 생성 시간: 3-5분 소요
✅ 상태: 사용 가능 확인
📝 기본 엔드포인트 복사: skn12-redis.xxxxx.cache.amazonaws.com:6379
```

---

### Step 7: GitHub 연동 (5분)

#### 1️⃣ GitHub Personal Access Token 생성
```
GitHub.com 로그인 → Settings → Developer settings 
→ Personal access tokens → Tokens (classic) 
→ Generate new token (classic)

설정:
- Note: Jenkins CI/CD
- 체크 항목: repo, admin:repo_hook
- Generate token 클릭
- 토큰 복사 (한 번만 보여짐!)
```

#### 2️⃣ Jenkins에 GitHub 토큰 등록
```
Jenkins 관리 → Credentials → System → Global credentials 
→ Add Credentials

Kind: Username with password
Username: [GitHub 아이디]
Password: [복사한 토큰]
ID: github-creds
```

---

### Step 8: Docker Hub 연동 (3분)

#### 1️⃣ Docker Hub Access Token 생성
```
hub.docker.com 로그인 → Account Settings 
→ Security → New Access Token

Token Description: Jenkins
Access permissions: Read, Write, Delete
→ Generate → 토큰 복사
```

#### 2️⃣ Jenkins에 Docker Hub 토큰 등록
```
Jenkins 관리 → Credentials → Add Credentials

Kind: Username with password  
Username: [Docker Hub 아이디]
Password: [복사한 토큰]
ID: dockerhub-creds
```

---

### Step 9: 환경별 설정 파일 생성 (5분)

#### 1️⃣ Jenkins 서버에 설정 파일 생성
```bash
# Session Manager로 jenkins-server 접속

# 설정 파일 디렉토리 생성
sudo mkdir -p /opt/skn12/config
sudo chown ubuntu:ubuntu /opt/skn12/config

# 프로덕션 환경 설정 파일 생성
cat > /opt/skn12/config/base_web_server-config.json << 'EOF'
{
  "templateConfig": {
    "appId": "finance_app",
    "env": "PROD",
    "skipAwsTests": false
  },
  "databaseConfig": {
    "type": "mysql",
    "host": "skn12-mysql.xxxxx.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "database": "finance_global",
    "username": "admin",
    "password": "SKN12mysql!2024",
    "pool_size": 10,
    "max_overflow": 20
  },
  "cacheConfig": {
    "host": "skn12-redis.xxxxx.cache.amazonaws.com",
    "port": 6379,
    "session_expire_seconds": 3600,
    "max_connections": 10
  },
  "llmConfig": {
    "default_provider": "openai",
    "providers": {
      "openai": {
        "api_key": "sk-your-openai-key",
        "model": "gpt-4"
      }
    }
  }
}
EOF

# 파일 권한 설정
chmod 600 /opt/skn12/config/base_web_server-config.json
```

#### 2️⃣ Deploy 서버에도 동일한 설정 복사
```bash
# Deploy 서버에도 Session Manager로 접속 후 동일한 작업 수행
# 또는 Jenkins에서 배포 시 자동으로 복사하도록 설정
```

---

### Step 10: ALB에 API 리스너 추가 (외부 API 접속용) (10분)

**🤔 왜 API도 ALB로 접속하나요?**
- 외부에서 우리 API 호출 가능 (모바일 앱, 다른 서비스)
- HTTPS 인증서 적용 가능
- 트래픽 분산과 헬스체크
- 보안 그룹으로 세밀한 접근 제어

#### 1️⃣ API용 대상 그룹 생성
```
EC2 콘솔 → 대상 그룹 → "대상 그룹 생성"

API 대상 그룹 설정:
- 대상 유형: 인스턴스
- 대상 그룹 이름: api-target-group
- 프로토콜: HTTP
- 포트: 8000 (FastAPI 기본 포트)
- VPC: skn12-jenkins-vpc

상태 확인:
- 상태 확인 프로토콜: HTTP
- 상태 확인 경로: /health
- 포트: 트래픽 포트
- 정상 임계값: 2
- 비정상 임계값: 2
- 제한 시간: 5초
- 간격: 30초

대상 등록:
- 인스턴스: deploy-server 선택
- 포트: 8000
- "대기 중인 것으로 포함" 클릭
```

#### 2️⃣ ALB에 API 리스너 추가
```
EC2 콘솔 → 로드 밸런서 → skn12-jenkins-alb 선택 → 리스너 탭

"리스너 추가" 클릭:
- 프로토콜: HTTP
- 포트: 8000
- 기본 작업: api-target-group으로 전달

"추가" 클릭
```

#### 3️⃣ ALB 보안 그룹에 API 포트 추가
```
EC2 콘솔 → 보안 그룹 → skn12-alb-security-group 편집

새 인바운드 규칙 추가:
- 유형: 사용자 지정 TCP
- 포트: 8000
- 소스: 0.0.0.0/0 (모든 곳에서 API 접속 허용)
- 설명: Public API access
```

#### 4️⃣ API 접속 테스트
```
# ALB DNS 주소로 API 테스트
curl http://[ALB-DNS-주소]:8000/health
curl http://[ALB-DNS-주소]:8000/

# 예시
curl http://skn12-jenkins-alb-1234567890.ap-northeast-2.elb.amazonaws.com:8000/health
```

---

### Step 11: 첫 번째 파이프라인 생성 (5분)

#### 1️⃣ 새 파이프라인 생성
```
Jenkins 대시보드 → 새로운 Item 
→ 이름: my-first-pipeline
→ Pipeline 선택 → OK
```

#### 2️⃣ 파이프라인 설정
```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'your-dockerhub-id/my-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-creds',
                    url: 'https://github.com/your-id/your-repo.git'
            }
        }
        
        stage('Build') {
            steps {
                sh '''
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }
        
        stage('Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                sh '''
                    # Deploy 서버에 SSH로 배포
                    ssh -o StrictHostKeyChecking=no ubuntu@[DEPLOY-SERVER-PRIVATE-IP] "
                        docker stop my-app || true
                        docker rm my-app || true
                        docker pull ${DOCKER_IMAGE}:latest
                        docker run -d --name my-app \
                            -p 8000:8000 \
                            -v /opt/skn12/config:/app/config \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE}:latest
                    "
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ 배포 성공!'
        }
        failure {
            echo '❌ 배포 실패!'
        }
    }
}
```

#### 3️⃣ 저장 → Build Now 클릭

---

### Step 12: GitHub Webhook 설정 (자동 배포) (2분)

#### 1️⃣ Jenkins에서 Webhook 활성화
```
파이프라인 설정 → Build Triggers 
→ ✅ GitHub hook trigger for GITScm polling 체크
```

#### 2️⃣ GitHub에서 Webhook 추가
```
GitHub 저장소 → Settings → Webhooks → Add webhook

Payload URL: http://[ALB-DNS-주소]/github-webhook/
Content type: application/json
Events: Just the push event
→ Add webhook

💡 중요: 서버 IP 대신 ALB DNS 주소 사용!
```

---

## ✅ 동작 테스트

### 1. 프로젝트에 Dockerfile 추가
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### 2. GitHub에 Push
```bash
git add .
git commit -m "Test CI/CD"
git push origin main
```

### 3. 자동 배포 확인
- Jenkins 대시보드에서 자동 빌드 시작 확인
- 빌드 완료 후 http://[ALB-DNS-주소] 접속해서 서비스 확인

---

## 🚨 자주 발생하는 문제 해결

### 1. "Permission denied" 에러
```bash
# Docker 권한 문제 해결
sudo chmod 666 /var/run/docker.sock
```

### 2. Jenkins 빌드 실패
```bash
# 로그 확인
docker logs jenkins

# Jenkins 재시작
docker restart jenkins
```

### 3. 포트가 이미 사용 중
```bash
# 기존 컨테이너 정리
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

### 4. 메모리 부족
```bash
# Swap 메모리 추가
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 💡 유용한 팁

### Jenkins 플러그인 추천
1. **Blue Ocean**: 예쁜 UI
2. **Slack Notification**: 배포 알림
3. **GitHub Integration**: GitHub 연동 강화

### 보안 강화
```bash
# 1. Jenkins 보안 설정
Jenkins 관리 → Configure Global Security
→ Security Realm: Jenkins' own user database
→ Authorization: Logged-in users can do anything

# 2. 방화벽 설정 (Jenkins는 내 IP만)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow from [내IP] to any port 8080
sudo ufw enable
```

---

## 📊 비용 절감 팁

### 1. 사용하지 않을 때 인스턴스 중지
```
AWS Console → EC2 → 인스턴스 선택 → 인스턴스 상태 → 중지
# 중지하면 과금 안 됨 (스토리지 비용만 발생)
```

### 2. 프리 티어 활용
- t2.micro 인스턴스는 매월 750시간 무료
- 신규 계정은 1년간 프리 티어 혜택

---

## 🎯 다음 단계

1. **HTTPS 설정**: ACM 인증서로 SSL 적용
2. **도메인 연결**: Route 53으로 도메인 설정
3. **모니터링**: CloudWatch 대시보드 구성
4. **CI/CD 고도화**: 블루-그린 배포, 카나리 배포
5. **백업 전략**: RDS 스냅샷, 코드 백업 S3
6. **성능 최적화**: CloudFront CDN, 캐싱 전략

---

## 📞 도움말

### 더 자세한 정보가 필요하면
- [Jenkins 공식 문서](https://www.jenkins.io/doc/)
- [Docker 공식 문서](https://docs.docker.com/)
- [AWS EC2 가이드](https://docs.aws.amazon.com/ec2/)

### 막히는 부분이 있다면
1. 에러 메시지를 구글에 검색
2. ChatGPT에게 물어보기
3. Stack Overflow 검색

---

## 🎉 축하합니다!

이제 GitHub에 코드를 푸시하면 자동으로 배포되는 CI/CD 파이프라인이 완성되었습니다!

**총 소요 시간**: 약 3시간  
**월 비용**: 약 $60 (t2.medium + t2.small + ALB + NAT Gateway + RDS + ElastiCache)  
**얻은 것**: 완전한 운영급 자동화 배포 시스템 ✨

**🔒 보안 강화 포인트:**
- ✅ 프라이빗 서브넷으로 서버 보호
- ✅ ALB를 통한 안전한 외부 접속
- ✅ 보안 그룹으로 세밀한 트래픽 제어
- ✅ Session Manager로 안전한 서버 관리
- ✅ Jenkins와 Deploy 서버 분리
- ✅ RDS MySQL 프라이빗 서브넷 배치
- ✅ ElastiCache Redis 암호화 및 프라이빗 접근
- ✅ 데이터베이스 백업 및 자동 패치

**🌍 외부 접속 가능:**
- ✅ Jenkins UI: http://[ALB-DNS]/
- ✅ API 서비스: http://[ALB-DNS]:8000/
- ✅ 웹 서비스: http://[ALB-DNS] (포트 80)
- ✅ HTTPS 확장 가능 (ACM 인증서 연결)