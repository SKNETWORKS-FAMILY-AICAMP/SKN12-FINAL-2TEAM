# 🏗️ Jenkins 초간단 설치 가이드 (30분 완성)

> **소요시간**: 30분  
> **난이도**: ⭐⭐ (쉬움)

---

## 🤔 Jenkins가 뭔가요?

**간단히 말하면**: 코드를 자동으로 빌드하고 배포해주는 로봇입니다.

```
개발자가 코드 수정 → GitHub에 올림 → Jenkins가 자동으로:
1. 코드 다운로드 📥
2. Docker 이미지 빌드 🏗️
3. 테스트 실행 🧪
4. Docker Hub에 업로드 📤
5. 서버에 배포 🚀
```

### 왜 필요한가요?
- **수동 작업 제거**: "빌드하고 → 테스트하고 → 배포하고" 반복 작업 자동화
- **실수 방지**: 사람이 하면 실수하지만 Jenkins는 정확히 실행
- **시간 절약**: 배포가 5초 만에 완료!

---

## 🚀 Step 1: Jenkins 서버 접속 (2분)

### 1️⃣ SSH로 서버 접속
```bash
# PowerShell에서 실행
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins서버IP]

# 예시
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@13.125.123.45
```

### 2️⃣ Docker 동작 확인
```bash
# Docker 버전 확인
docker --version

# 결과: Docker version 24.0.7
```

---

## 🐳 Step 2: Jenkins 설치 (5분)

### 1️⃣ Jenkins 폴더 만들기
```bash
# Jenkins 전용 폴더 생성
sudo mkdir -p /opt/jenkins
sudo chown ubuntu:ubuntu /opt/jenkins
cd /opt/jenkins
```

### 2️⃣ docker-compose.yml 파일 생성
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    restart: unless-stopped
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_data:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker
    environment:
      - JAVA_OPTS=-Xmx2048m
      - TZ=Asia/Seoul

volumes:
  jenkins_data:
EOF
```

### 3️⃣ Jenkins 시작
```bash
# Jenkins 컨테이너 실행
docker compose up -d

# 시작 확인 (2-3분 대기)
docker logs -f jenkins
```

성공하면 이런 메시지가 나옵니다:
```
Jenkins is fully up and running
```

---

## 🔑 Step 3: 초기 비밀번호 확인 (1분)

### 1️⃣ 관리자 비밀번호 찾기
```bash
# 초기 비밀번호 확인
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 결과 예시: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
# 이 비밀번호를 메모장에 복사해두세요!
```

### 2️⃣ 외부 접속 주소 확인
```bash
# 서버 IP 주소 확인
curl -s ifconfig.me

# 결과: 13.125.123.45 (예시)
# Jenkins 접속 주소: http://13.125.123.45:8080
```

---

## 🌐 Step 4: 웹에서 Jenkins 설정 (10분)

### 1️⃣ 브라우저에서 Jenkins 접속
```
주소창에 입력: http://[서버IP]:8080
예시: http://13.125.123.45:8080
```

### 2️⃣ 초기 설정 완료
```
1. "Unlock Jenkins" 페이지:
   → 위에서 복사한 비밀번호 입력 → Continue

2. "Customize Jenkins" 페이지:
   → "Install suggested plugins" 클릭 (5분 대기)

3. "Create First Admin User" 페이지:
   사용자명: admin
   비밀번호: admin1234!
   이름: Admin
   이메일: admin@example.com
   → Save and Continue

4. "Instance Configuration":
   → Save and Finish

5. "Start using Jenkins" 클릭!
```

---

## 🔐 Step 5: GitHub 연동 (5분)

### 1️⃣ GitHub 토큰 생성
```
GitHub.com → 우측 상단 프로필 → Settings 
→ Developer settings → Personal access tokens → Tokens (classic)
→ Generate new token (classic)

설정:
- Note: Jenkins-Token
- 권한: repo, admin:repo_hook 체크
→ Generate token
→ 토큰 복사 (ghp_xxx...)
```

### 2️⃣ Jenkins에 GitHub 토큰 등록
```
Jenkins → Manage Jenkins → Credentials 
→ System → Global credentials → Add Credentials

설정:
Kind: Secret text
Secret: [복사한 GitHub 토큰]
ID: github-token
→ Create
```

---

## 🐳 Step 6: Docker Hub 연동 (3분)

### 1️⃣ Jenkins에 Docker Hub 계정 등록
```
Jenkins → Credentials → Add Credentials

설정:
Kind: Username with password
Username: [Docker Hub 아이디]
Password: [Docker Hub 토큰] ← 비밀번호가 아님!
ID: dockerhub-creds
→ Create
```

---

## ✅ Step 7: 연동 테스트 (5분)

### 1️⃣ 테스트 파이프라인 생성
```
Jenkins 대시보드 → New Item
→ 이름: connection-test
→ Pipeline 선택 → OK
```

### 2️⃣ 테스트 스크립트 입력
Pipeline Script에 다음 코드 입력:

```groovy
pipeline {
    agent any
    stages {
        stage('GitHub Test') {
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'TOKEN')]) {
                    sh 'echo "GitHub 연결 테스트 성공!"'
                }
            }
        }
        stage('Docker Hub Test') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        echo "Docker Hub 로그인 성공!"
                        docker logout
                    '''
                }
            }
        }
    }
}
```

### 3️⃣ 테스트 실행
```
Save → Build Now 클릭
→ Build History에서 #1 클릭
→ Console Output 확인

성공하면:
✅ GitHub 연결 테스트 성공!
✅ Docker Hub 로그인 성공!
✅ Finished: SUCCESS
```

---

## 🚨 자주 묻는 질문

### Q: Jenkins 웹페이지가 안 열려요!
**A**: 보안 그룹 확인
```
AWS Console → EC2 → Security Groups 
→ jenkins 보안 그룹 선택
→ Inbound rules에 8080 포트가 0.0.0.0/0으로 열려있나 확인
```

### Q: Docker 권한 오류가 나요
**A**: 
```bash
# SSH에서 실행
sudo chmod 666 /var/run/docker.sock
docker compose restart jenkins
```

### Q: Jenkins가 느려요
**A**: 메모리 부족일 수 있습니다
```bash
# 메모리 확인
free -h
# Available이 1GB 이하면 인스턴스 크기 증가 필요
```

### Q: GitHub 토큰이 만료되었어요
**A**: 
```
GitHub에서 토큰 재생성 → Jenkins Credentials에서 github-token 업데이트
```

---

## 💡 관리 팁

### Jenkins 재시작
```bash
cd /opt/jenkins
docker compose restart jenkins
```

### 로그 확인
```bash
docker logs jenkins
```

### 백업
```bash
# Jenkins 데이터 백업
docker run --rm -v jenkins_jenkins_data:/data -v $(pwd):/backup alpine tar czf /backup/jenkins-backup.tar.gz -C /data .
```

---

## 🎯 다음 단계

✅ Jenkins 설치 완료  
✅ GitHub, Docker Hub 연동 완료  
→ **다음**: GitHub Webhook 설정 (05번 문서)

---

## 🎉 완료!

Jenkins CI/CD 서버가 준비되었습니다! 🏗️

**소요 시간**: 30분  
**다음 문서**: GitHub Webhook 자동 빌드 설정

이제 코드를 GitHub에 올리면 자동으로 빌드되는 시스템을 만들어봅시다! 🚀