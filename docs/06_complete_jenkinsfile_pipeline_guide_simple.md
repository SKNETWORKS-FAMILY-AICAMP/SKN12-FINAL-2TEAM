# 🏗️ 완전한 CI/CD 파이프라인 만들기 (15분 완성)

> **소요시간**: 15분  
> **난이도**: ⭐⭐ (쉬움)

---

## 🤔 완전한 CI/CD가 뭔가요?

**간단히 말하면**: 코드 올리면 자동으로 모든 게 되는 마법입니다.

```
코드 수정 → GitHub 올림 → 자동으로:
📥 코드 다운로드
🧪 코드 품질 검사
🏗️ Docker 이미지 만들기
📤 Docker Hub 업로드
🚀 서버에 배포
✅ 서비스 동작 확인
```

### 왜 필요한가요?
- **완전 자동화**: 손 하나 까딱 안 해도 배포 완료
- **품질 보장**: 문제 있는 코드는 자동으로 차단
- **즉시 반영**: 코드 수정 → 5분 후 서비스 업데이트!

---

## 📁 Step 1: Jenkinsfile 만들기 (5분)

### 1️⃣ 프로젝트에 Jenkinsfile 추가
```bash
# 프로젝트 폴더로 이동
cd C:\SKN12-FINAL-2TEAM

# 메모장으로 Jenkinsfile 만들기
notepad Jenkinsfile
```

### 2️⃣ Jenkinsfile 내용 복사해서 붙여넣기
```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'your-dockerhub-id/ai-trading-platform'
        DOCKER_CREDS = 'dockerhub-creds'
        GITHUB_CREDS = 'github-token'
        DEPLOY_SERVER = 'your-deploy-server-ip'
        SSH_CREDS = 'deploy-server-ssh-key'
    }
    
    stages {
        stage('📥 코드 가져오기') {
            steps {
                checkout scm
                echo '✅ GitHub에서 코드 다운로드 완료!'
            }
        }
        
        stage('🧪 코드 품질 검사') {
            steps {
                echo '🔍 코드 품질 검사 중...'
                dir('base_server') {
                    sh '''
                        # Python 파일 존재 확인
                        if [ -f "requirements.txt" ]; then
                            echo "✅ requirements.txt 존재"
                        else
                            echo "❌ requirements.txt 없음"
                            exit 1
                        fi
                        
                        # Dockerfile 존재 확인
                        if [ -f "Dockerfile" ]; then
                            echo "✅ Dockerfile 존재"
                        else
                            echo "❌ Dockerfile 없음"
                            exit 1
                        fi
                    '''
                }
                echo '✅ 코드 품질 검사 완료!'
            }
        }
        
        stage('🏗️ Docker 이미지 만들기') {
            steps {
                echo '🐳 Docker 이미지 빌드 중...'
                dir('base_server') {
                    script {
                        def imageTag = "build-${BUILD_NUMBER}"
                        env.IMAGE_TAG = imageTag
                        
                        sh '''
                            # 이전 이미지를 캐시로 사용해서 빠르게 빌드
                            docker build --cache-from ${DOCKER_IMAGE}:latest -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                            docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest
                            
                            echo "✅ Docker 이미지 빌드 완료!"
                            docker images | grep ${DOCKER_IMAGE}
                        '''
                    }
                }
            }
        }
        
        stage('📤 Docker Hub 업로드') {
            steps {
                echo '🚀 Docker Hub에 업로드 중...'
                withCredentials([usernamePassword(
                    credentialsId: env.DOCKER_CREDS,
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh '''
                        # Docker Hub 로그인
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        
                        # 이미지 업로드
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        
                        echo "✅ Docker Hub 업로드 완료!"
                        docker logout
                    '''
                }
            }
        }
        
        stage('🚀 서버에 배포') {
            steps {
                echo '📡 서버에 배포 중...'
                sshagent([env.SSH_CREDS]) {
                    sh '''
                        echo "🔗 Deploy Server 연결 중..."
                        
                        ssh -o StrictHostKeyChecking=no ubuntu@${DEPLOY_SERVER} "
                            echo '📥 새 이미지 다운로드 중...'
                            docker pull ${DOCKER_IMAGE}:latest
                            
                            echo '🛑 기존 컨테이너 중지 중...'
                            docker stop ai-trading-app || true
                            docker rm ai-trading-app || true
                            
                            echo '🚀 새 컨테이너 시작 중...'
                            docker run -d \
                                --name ai-trading-app \
                                -p 8000:8000 \
                                -e APP_ENV=PROD \
                                ${DOCKER_IMAGE}:latest
                            
                            echo '✅ 배포 완료!'
                        "
                    '''
                }
            }
        }
        
        stage('🧪 서비스 동작 확인') {
            steps {
                echo '🔍 서비스 동작 확인 중...'
                script {
                    // 서비스 시작 대기
                    sleep(time: 30, unit: 'SECONDS')
                    
                    sh '''
                        echo "🌐 웹 서비스 접속 테스트..."
                        
                        # 서비스 응답 확인
                        if curl -f -s http://${DEPLOY_SERVER}:8000/health > /dev/null; then
                            echo "✅ 웹 서비스 정상 동작!"
                        else
                            echo "❌ 웹 서비스 응답 없음"
                            exit 1
                        fi
                    '''
                }
                echo '✅ 모든 서비스 정상 동작 확인!'
            }
        }
    }
    
    post {
        always {
            echo '🧹 정리 작업 중...'
            sh '''
                # 오래된 이미지 정리 (디스크 공간 절약)
                docker image prune -f || true
            '''
        }
        success {
            echo '🎉 배포 성공! 서비스가 정상 업데이트되었습니다!'
            echo "🌐 서비스 주소: http://${DEPLOY_SERVER}:8000"
        }
        failure {
            echo '❌ 배포 실패! 로그를 확인하세요.'
        }
    }
}
```

### 3️⃣ 실제 값으로 수정하기
```
your-dockerhub-id → 실제 Docker Hub 아이디
your-deploy-server-ip → 실제 Deploy 서버 IP

예시:
DOCKER_IMAGE = 'skn12trading/ai-trading-platform'
DEPLOY_SERVER = '52.79.234.56'
```

---

## 🔧 Step 2: Jenkins 설정 변경 (3분)

### 1️⃣ Jenkins에서 Pipeline 방식 변경
```
Jenkins → SKN12-Trading-Platform-CI → Configure

Pipeline 섹션에서:
❌ Definition: Pipeline script
↓
✅ Definition: Pipeline script from SCM

SCM: Git
Repository URL: https://github.com/your-id/SKN12-FINAL-2TEAM.git
Credentials: github-token
Branch: */main
Script Path: Jenkinsfile
```

### 2️⃣ 설정 저장
```
Save 클릭 → 완료!
```

---

## 📤 Step 3: GitHub에 올리기 (2분)

### 1️⃣ Jenkinsfile을 Git에 추가
```bash
# Jenkinsfile 추가
git add Jenkinsfile

# 커밋
git commit -m "완전한 CI/CD 파이프라인 추가

✨ 기능:
- 자동 코드 품질 검사
- Docker 이미지 자동 빌드
- Docker Hub 자동 업로드  
- 서버 자동 배포
- 서비스 동작 자동 확인"

# GitHub에 올리기
git push origin main
```

---

## ✅ Step 4: 자동 빌드 확인 (5분)

### 1️⃣ Jenkins에서 자동 빌드 시작 확인
```
GitHub에 올린 후 Jenkins 확인
→ 새 빌드가 자동으로 시작됩니다!
```

### 2️⃣ 각 단계별 진행 상황 확인
```
Jenkins → Build History → 최신 빌드 클릭 → Console Output

확인할 내용:
✅ 📥 코드 가져오기 - "코드 다운로드 완료!"
✅ 🧪 코드 품질 검사 - "코드 품질 검사 완료!"
✅ 🏗️ Docker 이미지 만들기 - "Docker 이미지 빌드 완료!"
✅ 📤 Docker Hub 업로드 - "Docker Hub 업로드 완료!"
✅ 🚀 서버에 배포 - "배포 완료!"
✅ 🧪 서비스 동작 확인 - "모든 서비스 정상 동작 확인!"
```

### 3️⃣ 실제 서비스 접속 확인
```
브라우저에서 접속:
http://[Deploy-Server-IP]:8000

정상 응답이 나오면 성공! 🎉
```

---

## 🚨 자주 묻는 질문

### Q: "Jenkinsfile not found" 에러가 나요!
**A**: 
```bash
# GitHub에 Jenkinsfile이 올라갔는지 확인
# 파일명이 정확히 "Jenkinsfile"인지 확인 (대소문자 구분!)
```

### Q: Docker 빌드가 실패해요!
**A**: 
```bash
# base_server 폴더에 Dockerfile이 있는지 확인
# requirements.txt가 있는지 확인
```

### Q: Docker Hub 업로드가 실패해요!
**A**: 
```
Jenkins → Credentials → dockerhub-creds 다시 확인
토큰이 유효한지 확인
```

### Q: 서버 배포가 실패해요!
**A**: 
```
Deploy Server가 실행 중인지 확인
SSH 키가 올바른지 확인
```

### Q: 서비스 접속이 안 되요!
**A**: 
```
Deploy Server 보안 그룹에서 8000 포트 열려있나 확인
Docker 컨테이너가 실행 중인지 확인: docker ps
```

---

## 💡 고급 활용 팁

### 더 빠른 빌드
```groovy
// Docker 빌드 캐시 최적화
sh 'docker build --cache-from ${DOCKER_IMAGE}:latest --build-arg BUILDKIT_INLINE_CACHE=1 -t ${DOCKER_IMAGE}:${IMAGE_TAG} .'
```

### 브랜치별 다른 배포
```groovy
stage('배포') {
    when { branch 'main' }  // main 브랜치만 운영 배포
    steps {
        // 운영 서버 배포
    }
}
```

### 롤백 기능 추가
```groovy
stage('롤백 준비') {
    steps {
        sh '''
            # 이전 이미지 백업
            docker tag ${DOCKER_IMAGE}:latest ${DOCKER_IMAGE}:backup
        '''
    }
}
```

---

## 🎯 다음 단계

✅ 완전한 CI/CD 파이프라인 완료  
→ **다음**: 모니터링 및 알림 설정

---

## 🎉 완료!

진정한 DevOps 환경이 완성되었습니다! 🏗️

**이제 할 수 있는 것:**
- 코드 수정 → GitHub 올림 → 5분 후 서비스 업데이트 완료!
- 문제 있는 코드는 자동으로 차단
- 품질 검사부터 배포까지 완전 자동화
- 서비스 동작까지 자동으로 확인

**소요 시간**: 15분  
**결과**: 완전 자동화된 CI/CD 시스템

더 이상 수동 배포는 없습니다! 🚀