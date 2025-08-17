# 🐳 Docker Hub 초간단 설정 가이드 (3분 완성)

> **소요시간**: 3분  
> **난이도**: ⭐ (매우 쉬움)

---

## 🤔 Docker Hub가 뭔가요?

**간단히 말하면**: 우리가 만든 앱을 담는 상자(Docker 이미지)를 저장하는 창고입니다.

```
GitHub = 코드 저장소 📝
Docker Hub = 앱 상자 저장소 📦
```

### 왜 필요한가요?
1. **Jenkins**에서 앱을 빌드 → **Docker Hub**에 저장
2. **서버**에서 **Docker Hub**에서 다운로드 → 실행

---

## 🚀 Step 1: 계정 만들기 (1분)

### 1️⃣ 사이트 접속
```
https://hub.docker.com 
→ "Sign Up" 클릭
```

### 2️⃣ 정보 입력
```
Username: [영문으로 간단하게, 예: skn12team]
Email: [자주 쓰는 이메일]
Password: [강력한 비밀번호]
```

### 3️⃣ 이메일 인증
- 이메일 확인 → 인증 링크 클릭 → 완료!

---

## 🔑 Step 2: Jenkins용 토큰 만들기 (1분)

### 왜 토큰이 필요한가요?
비밀번호 대신 사용하는 안전한 열쇠입니다. Jenkins가 자동으로 Docker Hub에 접근할 수 있게 해줍니다.

### 1️⃣ 토큰 생성
```
로그인 후 → 우측 상단 프로필 → Account Settings
→ Security → Personal access tokens 
→ "Generate new token" 클릭
```

### 2️⃣ 토큰 설정
```
Token description: Jenkins-CI-CD
Access permissions: Read, Write, Delete
→ "Generate" 클릭
```

### 3️⃣ 토큰 복사 (중요!)
```
⚠️ 생성된 토큰을 반드시 복사해서 메모장에 저장!
   (한 번만 보여주고 다시 볼 수 없음)

예시: dckr_pat_1234567890abcdef...
```

---

## 🔗 Step 3: Jenkins에 등록하기 (1분)

### 1️⃣ Jenkins 접속
```
http://[서버IP]:8080
→ Jenkins 관리 → Credentials
```

### 2️⃣ 새 인증 정보 추가
```
Add Credentials 클릭

Kind: Username with password
Username: [Docker Hub 아이디]
Password: [복사한 토큰] ← 비밀번호가 아님!
ID: dockerhub-creds
Description: Docker Hub Access Token

→ Create 클릭
```

---

## ✅ 연동 테스트

### Jenkins Pipeline에서 사용 예시
```groovy
stage('Push to Docker Hub') {
    steps {
        withCredentials([usernamePassword(
            credentialsId: 'dockerhub-creds',
            usernameVariable: 'DOCKER_USER',
            passwordVariable: 'DOCKER_PASS'
        )]) {
            sh '''
                echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                docker push your-dockerhub-id/your-app:latest
            '''
        }
    }
}
```

---

## 🏷️ 이미지 태그 관리 팁

### 좋은 태그 예시
```bash
# 최신 버전 (항상 최신으로 업데이트)
your-app:latest

# 빌드 번호 (Jenkins에서 자동 생성)
your-app:build-123

# 버전 태그 (릴리스용)
your-app:v1.0.0
your-app:v1.1.0

# 환경별 태그
your-app:dev
your-app:staging
your-app:prod
```

### Jenkins에서 자동 태그 설정
```groovy
environment {
    DOCKER_IMAGE = 'your-dockerhub-id/your-app'
    DOCKER_TAG = "${BUILD_NUMBER}"
}

stages {
    stage('Build & Tag') {
        steps {
            sh '''
                # 빌드 번호와 latest 태그 동시 생성
                docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                
                # 둘 다 업로드
                docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                docker push ${DOCKER_IMAGE}:latest
            '''
        }
    }
}
```

---

## 🚨 자주 묻는 질문

### Q: 토큰을 잃어버렸어요!
**A**: 새로 만들면 됩니다. 보안상 한 번만 보여줍니다.

### Q: Jenkins에서 로그인 실패 에러가 나요
**A**: 체크 리스트
- [ ] Username이 정확한가요?
- [ ] 토큰(비밀번호 아님!)을 입력했나요?
- [ ] 토큰에 Read, Write 권한이 있나요?

### Q: 무료 계정 제한은?
**A**: 
- Private 저장소: 1개 무료
- Public 저장소: 무제한 무료
- 대역폭: 충분함 (개인 프로젝트용)

### Q: 이미지 크기를 줄이고 싶어요
**A**: 
```dockerfile
# 작은 베이스 이미지 사용
FROM python:3.11-slim  # slim 버전 사용

# 멀티 스테이지 빌드
FROM python:3.11 AS builder
# 빌드 과정...

FROM python:3.11-slim
# 최종 실행 이미지는 작게
```

---

## 💡 보안 팁

### 1. 정기적인 토큰 갱신
```
3개월마다 토큰을 새로 발급받아 보안 강화
```

### 2. 최소 권한 원칙
```
Jenkins용 토큰: Read, Write만
개발자용 토큰: Read만
```

### 3. Private 저장소 사용
```
민감한 내용이 포함된 이미지는 Private 저장소 사용
(월 $5 for unlimited private repos)
```

---

## 🎯 다음 단계

✅ Docker Hub 계정 생성 완료  
✅ Jenkins 연동 완료  
→ **다음**: Jenkins Pipeline 설정 (04번 문서)

---

## 📞 문제 해결

### 접속 관련
```bash
# Docker Hub 접속 테스트
curl -s https://hub.docker.com/health

# 로컬에서 로그인 테스트
docker login
```

### 용량 관리
```bash
# 오래된 이미지 삭제 (Docker Hub 웹에서)
# 로컬 정리
docker system prune -a
```

---

## 🎉 완료!

이제 Jenkins에서 자동으로 Docker Hub에 이미지를 업로드할 수 있습니다!

**소요 시간**: 3분  
**다음 문서**: Jenkins Docker Compose 설정