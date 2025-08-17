# 🔗 GitHub 자동 빌드 설정 가이드 (5분 완성)

> **소요시간**: 5분  
> **난이도**: ⭐ (매우 쉬움)

---

## 🤔 GitHub 자동 빌드가 뭔가요?

**간단히 말하면**: 코드를 GitHub에 올리면 Jenkins가 자동으로 알아채고 빌드를 시작하는 마법입니다.

```
코드 수정 → GitHub에 올림 → Jenkins가 자동으로:
📥 코드 다운로드
🏗️ Docker 이미지 만들기
📤 Docker Hub에 업로드
🚀 서버에 배포
```

### 왜 필요한가요?
- **수동 작업 제거**: "빌드하기" 버튼 누르는 것도 귀찮아요
- **즉시 반영**: 코드 수정하자마자 자동으로 적용
- **실수 방지**: 빌드 깜빡하는 일 없음!

---

## 🔗 Step 1: GitHub에서 Webhook 설정 (2분)

### 1️⃣ GitHub 저장소에서 설정하기
```
GitHub.com → SKN12-FINAL-2TEAM 저장소 
→ Settings → Webhooks → Add webhook
```

### 2️⃣ Webhook 정보 입력
```
Payload URL: http://[Jenkins서버IP]:8080/github-webhook/
예시: http://13.125.123.45:8080/github-webhook/

⚠️ 중요: 마지막에 슬래시(/) 꼭 써주세요!

Content type: application/json
Secret: (비워둠)
Events: Just the push event 선택
Active: ✅ 체크
```

### 3️⃣ Webhook 생성
```
Add webhook 클릭 → 완료!
```

---

## 🏗️ Step 2: Jenkins에서 Job 생성 (3분)

### 1️⃣ 새 작업 만들기
```
Jenkins → New Item
→ 이름: auto-build
→ Pipeline 선택 → OK
```

### 2️⃣ 자동 빌드 설정
```
Build Triggers 섹션에서:
✅ GitHub hook trigger for GITScm polling 체크
```

### 3️⃣ 간단한 파이프라인 코드 입력
Pipeline Script에 다음 코드 붙여넣기:

```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'your-dockerhub-id/my-app'
        DOCKER_CREDS = 'dockerhub-creds'
    }
    
    stages {
        stage('GitHub에서 코드 가져오기') {
            steps {
                checkout scm
                echo '✅ 코드 다운로드 완료!'
            }
        }
        
        stage('Docker 이미지 만들기') {
            steps {
                dir('base_server') {
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                        docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                        echo '✅ Docker 이미지 빌드 완료!'
                    '''
                }
            }
        }
        
        stage('Docker Hub에 업로드') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: '${DOCKER_CREDS}',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest
                        echo '✅ Docker Hub 업로드 완료!'
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 자동 빌드 성공!'
        }
        failure {
            echo '❌ 빌드 실패! 로그를 확인하세요.'
        }
    }
}
```

**중요**: `your-dockerhub-id`를 실제 Docker Hub 아이디로 바꿔주세요!

---

## ✅ Step 3: 테스트해보기 (1분)

### 1️⃣ 수동 테스트
```
Save → Build Now 클릭
→ 빌드가 성공하면 OK!
```

### 2️⃣ 자동 테스트 
```bash
# 로컬에서 간단한 파일 수정
echo "테스트" > test.txt
git add test.txt
git commit -m "자동 빌드 테스트"
git push origin main
```

### 3️⃣ 자동 빌드 확인
```
GitHub에 올린 후 Jenkins를 보면
자동으로 새 빌드가 시작됩니다!
```

---

## 🚨 자주 묻는 질문

### Q: Webhook 연결이 안 되요!
**A**: 보안 그룹 확인
```
AWS Console → EC2 → Security Groups
→ 8080 포트가 0.0.0.0/0으로 열려있나 확인
```

### Q: 자동 빌드가 시작 안 되요!
**A**: 체크리스트
- [ ] GitHub Webhook URL 정확한가요? (마지막 슬래시 포함)
- [ ] Jenkins에서 "GitHub hook trigger" 체크했나요?
- [ ] GitHub에 코드를 올렸나요? (push 했나요?)

### Q: Docker Hub 업로드 실패해요!
**A**: Credentials 확인
```
Jenkins → Manage Jenkins → Credentials
→ dockerhub-creds가 정확히 설정되었나 확인
```

### Q: 빌드는 되는데 에러가 나요!
**A**: 코드 문제일 수 있습니다
```
Console Output에서 에러 메시지 확인
→ 대부분 Python 패키지나 Docker 파일 문제
```

---

## 💡 활용 팁

### 더 빠른 빌드
```groovy
// 이전 이미지를 캐시로 사용
sh 'docker build --cache-from ${DOCKER_IMAGE}:latest -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .'
```

### Slack 알림 연동
```groovy
post {
    success {
        slackSend color: 'good', message: '✅ 빌드 성공!'
    }
    failure {
        slackSend color: 'danger', message: '❌ 빌드 실패!'
    }
}
```

### 특정 브랜치만 빌드
```groovy
when {
    branch 'main'  // main 브랜치만 빌드
}
```

---

## 🎯 다음 단계

✅ GitHub 자동 빌드 완료  
→ **다음**: 완전한 CI/CD 파이프라인 만들기 (06번 문서)

---

## 🎉 완료!

이제 코드를 GitHub에 올리기만 하면 자동으로 빌드됩니다! 🔗

**소요 시간**: 5분  
**다음 문서**: 완전한 Jenkinsfile 작성

더 이상 수동으로 빌드할 필요가 없어요! 🚀