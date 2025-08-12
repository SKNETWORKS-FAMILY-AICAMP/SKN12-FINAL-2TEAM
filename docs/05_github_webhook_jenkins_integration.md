# 🔗 GitHub Webhook 및 Jenkins 통합 완전 가이드 (초보자용)

> **목적**: GitHub 저장소에 코드를 Push할 때 Jenkins가 자동으로 빌드를 시작하도록 Webhook을 설정하고, Jenkins에서 GitHub 저장소를 연동합니다.
>
> **💡 Webhook이란?**: GitHub에서 특정 이벤트(Push, PR 등)가 발생할 때 Jenkins에게 자동으로 알림을 보내는 방법입니다.

---

## 🏗️ GitHub Webhook 동작 원리 이해하기

```
👨‍💻 개발자
    ↓ (git push)
📱 GitHub Repository (SKN12-FINAL-2TEAM)
    ↓ (Webhook 자동 발송)
    📡 HTTP POST → http://[Jenkins-IP]:18080/github-webhook/
    ↓ 
🏗️ Jenkins Server
    ├─ Webhook 수신
    ├─ 자동 빌드 트리거 
    ├─ GitHub에서 코드 다운로드
    ├─ Docker 이미지 빌드
    ├─ Docker Hub 업로드
    └─ Deploy Server에 배포 명령
         ↓
🚀 Deploy Server
    └─ 새 버전 자동 배포
```

**설정해야 할 것들**:
1. **GitHub Webhook**: Push 이벤트를 Jenkins에 알림
2. **Jenkins Job**: Webhook을 받아서 자동 빌드 실행
3. **Pipeline Script**: 실제 빌드/배포 과정 정의

---

## 🔐 Step 1: GitHub Repository Webhook 설정 (10분)

### 1️⃣ GitHub 저장소 Settings 접근

#### A. GitHub 웹사이트에서 저장소 이동
```
1. 웹 브라우저에서 https://github.com 접속
2. 로그인 후 SKN12-FINAL-2TEAM 저장소로 이동
   또는 https://github.com/[사용자명]/SKN12-FINAL-2TEAM
3. 저장소 상단 메뉴에서 "Settings" 탭 클릭
```

#### B. Webhooks 설정 메뉴 접근
```
1. 왼쪽 사이드바에서 "Webhooks" 클릭
2. "Add webhook" 버튼 클릭
3. GitHub 비밀번호 재입력 요구 시 입력
```

### 1️⃣ Webhook 상세 설정

#### A. Webhook URL 설정
```
Payload URL: http://[Jenkins-Public-IP]:18080/github-webhook/

⚠️ 중요한 점들:
- 마지막에 슬래시(/) 반드시 포함
- HTTPS가 아닌 HTTP 사용 (현재 SSL 미설정)
- 포트 18080 포함
- "/github-webhook/" 경로 정확히 입력

예시: http://13.125.123.45:18080/github-webhook/
```

#### B. Content type 설정
```
Content type: application/json (기본값 유지)

왜 JSON인가?
- Jenkins가 JSON 형태의 Webhook 데이터를 선호
- 더 많은 정보를 구조적으로 전달 가능
- GitHub의 표준 권장 방식
```

#### C. Secret 설정 (보안 강화)
```
Secret: skn12-webhook-secret-2025

이 Secret의 역할:
- Webhook이 실제로 GitHub에서 온 것인지 검증
- 악의적인 요청으로부터 Jenkins 보호
- Jenkins에서도 같은 Secret 설정 필요
```

#### D. 이벤트 트리거 설정
```
Which events would you like to trigger this webhook?

선택: "Just the push event" (권장)

이유:
✅ Push event: 코드가 main 브랜치에 푸시될 때만 빌드
❌ Send me everything: 너무 많은 이벤트로 불필요한 빌드 발생
❌ Let me select: 복잡한 설정, 초보자에게 비추천

개별 이벤트 선택 시 권장 이벤트:
- ✅ Pushes (코드 푸시)
- ✅ Pull requests (PR 생성/업데이트)  
- ❌ Issues (이슈는 빌드와 무관)
- ❌ Wiki (위키 변경은 빌드와 무관)
```

#### E. Webhook 활성화 설정
```
Active: ✅ 체크 (활성화)

활성화 상태:
- 체크: Webhook이 즉시 작동
- 미체크: Webhook 설정은 저장하지만 비활성화
```

#### F. Webhook 생성 완료
```
1. "Add webhook" 버튼 클릭
2. "Webhooks" 페이지로 리다이렉트
3. 생성된 Webhook 확인:
   - URL: http://[Jenkins-IP]:18080/github-webhook/
   - Events: push
   - Active: ✅
```

---

## 🔍 Step 2: Webhook 연결 테스트 (5분)

### 2️⃣ Webhook 즉시 테스트

#### A. GitHub에서 Webhook 테스트
```
1. Webhooks 목록에서 방금 생성한 Webhook 클릭
2. 하단 "Recent Deliveries" 섹션 확인
3. "Redeliver" 버튼 클릭하여 테스트 전송
4. 응답 상태 확인:
   - ✅ 200 OK: Jenkins가 정상적으로 Webhook 수신
   - ❌ Connection timeout: Jenkins 서버 접근 불가
   - ❌ 404 Not Found: Webhook URL 오류
```

#### B. 연결 실패 시 문제 해결
```
❌ Connection timeout 오류:
1. EC2 보안 그룹에서 포트 18080 확인
2. Jenkins 컨테이너 실행 상태 확인:
   docker ps | grep jenkins-master
3. Jenkins 웹 UI 직접 접속 테스트:
   http://[Jenkins-IP]:18080

❌ 404 Not Found 오류:
1. Webhook URL 재확인 (특히 마지막 슬래시)
2. Jenkins에서 GitHub Integration Plugin 설치 확인
3. Jenkins 설정에서 GitHub Webhook 수신 활성화 확인
```

#### C. Jenkins 로그에서 Webhook 수신 확인
```bash
# SSH에서 Jenkins 로그 확인
docker logs jenkins-master | grep -i github
docker logs jenkins-master | grep -i webhook

# 실시간 로그 모니터링
docker logs -f jenkins-master
# GitHub에서 "Redeliver" 클릭 후 로그 확인
```

---

## 🏗️ Step 3: Jenkins에서 GitHub 프로젝트 연동 (15분)

### 3️⃣ 새 Jenkins Job 생성

#### A. Jenkins Dashboard에서 새 작업 생성
```
1. Jenkins 웹 UI 접속: http://[Jenkins-IP]:18080
2. 관리자 로그인: admin / skn12-jenkins-2025!
3. "New Item" 클릭
4. Job 설정:
   - Enter an item name: SKN12-Trading-Platform-CI
   - 프로젝트 유형: "Pipeline" 선택
   - "OK" 클릭
```

#### B. General 설정
```
Job 기본 정보:
- Description: SKN12 Final Project CI/CD Pipeline - Automated build and deployment
- ✅ GitHub project: 체크
  - Project url: https://github.com/[사용자명]/SKN12-FINAL-2TEAM/
- ✅ This project is parameterized: 체크하지 않음 (초보자용 단순화)
```

#### C. Build Triggers 설정
```
빌드 트리거 설정:
✅ GitHub hook trigger for GITScm polling

이 옵션의 의미:
- GitHub Webhook이 도착하면 자동으로 빌드 시작
- 수동 "Build Now" 클릭 없이 자동화
- Git 저장소 변경사항 자동 감지

추가 옵션들 (체크하지 않음):
❌ Build after other projects are built
❌ Build periodically  
❌ Poll SCM
```

### 3️⃣ Pipeline 설정

#### A. Pipeline Definition 설정
```
Pipeline 섹션:
- Definition: Pipeline script from SCM (권장)
  
  또는
  
- Definition: Pipeline script (직접 작성)

초보자 권장: "Pipeline script" 선택 (먼저 테스트용)
```

#### B. 간단한 테스트 Pipeline Script 작성
```groovy
pipeline {
    agent any
    
    // 환경 변수 정의
    environment {
        DOCKER_IMAGE = '[Docker-Hub-사용자명]/ai-trading-platform'
        DOCKER_CREDENTIALS = 'dockerhub-credentials'
        GITHUB_CREDENTIALS = 'github-token'
        DEPLOY_SERVER = '[Deploy-Server-IP]'
        SSH_CREDENTIALS = 'deploy-server-ssh-key'
    }
    
    stages {
        // 1단계: GitHub에서 소스코드 다운로드
        stage('📥 Checkout Source Code') {
            steps {
                echo '🔍 GitHub에서 소스코드 체크아웃 중...'
                
                // GitHub 저장소에서 코드 가져오기
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/[사용자명]/SKN12-FINAL-2TEAM.git',
                        credentialsId: env.GITHUB_CREDENTIALS
                    ]]
                ])
                
                echo '✅ 소스코드 체크아웃 완료'
                
                // 코드 정보 출력
                sh '''
                    echo "📊 Git 정보:"
                    git log --oneline -5
                    echo "📁 프로젝트 구조:"
                    ls -la
                '''
            }
        }
        
        // 2단계: 환경 정보 확인
        stage('🔍 Environment Check') {
            steps {
                echo '🔧 빌드 환경 정보 확인 중...'
                
                sh '''
                    echo "🐳 Docker 정보:"
                    docker --version
                    docker compose version
                    
                    echo "📂 작업 디렉토리:"
                    pwd
                    ls -la
                    
                    echo "🖥️ 시스템 정보:"
                    uname -a
                    free -h
                    df -h
                '''
            }
        }
        
        // 3단계: Docker 이미지 빌드 테스트
        stage('🏗️ Build Docker Image') {
            steps {
                echo '🐳 Docker 이미지 빌드 중...'
                
                dir('base_server') {
                    script {
                        // 이미지 태그 생성 (빌드 번호 + Git 커밋 해시)
                        def imageTag = "build-${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
                        env.IMAGE_TAG = imageTag
                        
                        sh '''
                            echo "🏷️ 이미지 태그: ${IMAGE_TAG}"
                            
                            # Docker 이미지 빌드
                            docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                            docker build -t ${DOCKER_IMAGE}:latest .
                            
                            echo "✅ Docker 이미지 빌드 완료"
                            docker images | grep ${DOCKER_IMAGE}
                        '''
                    }
                }
            }
        }
        
        // 4단계: Docker Hub 업로드 (현재는 테스트만)
        stage('📤 Push to Docker Hub') {
            steps {
                echo '🚀 Docker Hub에 이미지 업로드 중...'
                
                withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDENTIALS, 
                                                usernameVariable: 'DOCKER_USER', 
                                                passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        # Docker Hub 로그인
                        echo "$DOCKER_PASS" | docker login --username "$DOCKER_USER" --password-stdin
                        
                        # 이미지 푸시
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        
                        # 로그아웃
                        docker logout
                        
                        echo "✅ Docker Hub 업로드 완료"
                    '''
                }
            }
        }
        
        // 5단계: Deploy Server 연결 테스트
        stage('🚀 Deploy Test') {
            steps {
                echo '🔗 Deploy Server 연결 테스트 중...'
                
                sshagent(credentials: [env.SSH_CREDENTIALS]) {
                    sh '''
                        echo "📡 Deploy Server 연결 중..."
                        
                        ssh -o StrictHostKeyChecking=no ubuntu@${DEPLOY_SERVER} "
                            echo '✅ Deploy Server 연결 성공!'
                            echo '서버 정보:'
                            hostname
                            uptime
                            docker --version
                            
                            echo '현재 실행 중인 컨테이너:'
                            docker ps
                        "
                    '''
                }
            }
        }
    }
    
    // 빌드 완료 후 처리
    post {
        always {
            echo '🧹 빌드 후 정리 작업 중...'
            
            // 작업 공간 정리
            cleanWs()
            
            // 로컬 Docker 이미지 정리 (선택사항)
            sh '''
                echo "🗑️ 임시 Docker 이미지 정리 중..."
                docker image prune -f || true
            '''
        }
        
        success {
            echo '🎉 빌드가 성공적으로 완료되었습니다!'
            echo "📦 빌드 결과: ${env.DOCKER_IMAGE}:${env.IMAGE_TAG}"
        }
        
        failure {
            echo '❌ 빌드 중 오류가 발생했습니다.'
            echo '📋 로그를 확인하여 문제를 해결하세요.'
        }
    }
}
```

#### C. Pipeline Script 저장
```
1. 위 스크립트를 Pipeline Script 텍스트 상자에 붙여넣기
2. [사용자명], [Deploy-Server-IP] 등을 실제 값으로 교체
3. "Save" 버튼 클릭
```

---

## 🧪 Step 4: 수동 빌드 테스트 (10분)

### 4️⃣ Jenkins Job 수동 실행

#### A. 첫 번째 빌드 실행
```
1. Jenkins Job 페이지에서 "Build Now" 클릭
2. Build History에서 "#1" 클릭
3. "Console Output" 클릭하여 실시간 로그 확인
```

#### B. 빌드 과정 모니터링
```
Console Output에서 확인할 내용:

✅ Stage 1 - Checkout: 
   "✅ 소스코드 체크아웃 완료" 메시지

✅ Stage 2 - Environment Check:
   Docker 버전 정보 출력

✅ Stage 3 - Build Docker Image:
   "✅ Docker 이미지 빌드 완료" 메시지

✅ Stage 4 - Push to Docker Hub:
   "✅ Docker Hub 업로드 완료" 메시지

✅ Stage 5 - Deploy Test:
   "✅ Deploy Server 연결 성공!" 메시지

✅ Post Actions:
   "🎉 빌드가 성공적으로 완료되었습니다!" 메시지
```

#### C. 빌드 결과 확인
```
빌드 성공 시:
- Build History에서 파란색 공 표시
- "Finished: SUCCESS" 메시지
- 각 Stage가 녹색으로 표시

빌드 실패 시:
- Build History에서 빨간색 공 표시  
- "Finished: FAILURE" 메시지
- 실패한 Stage가 빨간색으로 표시
- Console Output에서 오류 메시지 확인
```

---

## 🔄 Step 5: 자동 빌드 테스트 (GitHub Push) (10분)

### 5️⃣ 실제 GitHub Push로 자동 빌드 테스트

#### A. 로컬에서 간단한 변경사항 만들기
```bash
# Windows PowerShell에서 프로젝트 디렉토리로 이동
cd C:\SKN12-FINAL-2TEAM

# 간단한 테스트 파일 생성
echo "Jenkins CI/CD 테스트 - $(Get-Date)" > build-test.txt

# Git 변경사항 확인
git status

# 변경사항 커밋
git add build-test.txt
git commit -m "Jenkins CI/CD 자동 빌드 테스트

- build-test.txt 파일 추가
- GitHub Webhook → Jenkins 자동 빌드 테스트용
- 빌드 트리거 검증"

# GitHub에 푸시
git push origin main
```

#### B. Jenkins에서 자동 빌드 시작 확인
```
1. GitHub Push 후 즉시 Jenkins 웹 UI로 이동
2. Jenkins Dashboard에서 "SKN12-Trading-Platform-CI" Job 확인
3. Build History에서 새로운 빌드(#2)가 자동으로 시작되는지 확인
4. 빌드가 자동으로 시작되면 Webhook 연동 성공!
```

#### C. GitHub Webhook 전송 로그 확인
```
1. GitHub 저장소 → Settings → Webhooks
2. 생성한 Webhook 클릭
3. "Recent Deliveries" 섹션에서 최근 전송 기록 확인:
   - Request: POST 요청 정보
   - Response: Jenkins 응답 (200 OK여야 함)
   - Delivery: Successful/Failed 상태
```

#### D. 자동 빌드 실패 시 문제 해결
```
❌ Webhook은 전송되지만 Jenkins 빌드가 시작되지 않는 경우:

1. Jenkins Job 설정 확인:
   - Build Triggers에서 "GitHub hook trigger for GITScm polling" 체크 확인
   
2. GitHub URL 설정 확인:
   - General 섹션의 "GitHub project" URL이 정확한지 확인
   
3. Credentials 설정 확인:
   - github-token이 올바르게 설정되었는지 확인

❌ Webhook 전송 자체가 실패하는 경우:
1. 보안 그룹에서 포트 18080 개방 확인
2. Jenkins 컨테이너 실행 상태 확인
3. Webhook URL 정확성 재확인
```

---

## 🎛️ Step 6: Jenkins GitHub Integration 고급 설정 (10분)

### 6️⃣ GitHub Integration Plugin 세부 설정

#### A. Global GitHub 설정
```
1. Jenkins Dashboard → "Manage Jenkins" → "System"
2. "GitHub" 섹션 찾기
3. GitHub Server 설정:
   - Name: GitHub.com (기본값)
   - API URL: https://api.github.com (기본값)
   - Credentials: github-token 선택
   - ✅ Manage hooks: 체크 (Jenkins가 자동으로 Webhook 관리)
   - ✅ Test connection: 클릭하여 연결 테스트
```

#### B. Webhook Secret 설정 (보안 강화)
```
1. Job 설정으로 돌아가기: SKN12-Trading-Platform-CI → "Configure"
2. "Build Triggers" 섹션
3. "GitHub hook trigger for GITScm polling" 아래 "Advanced" 클릭
4. Secret 설정:
   - ✅ Use GitHub hook secret: 체크
   - Secret: skn12-webhook-secret-2025 (GitHub Webhook에서 설정한 것과 동일)
```

#### C. Branch 제한 설정 (선택사항)
```
Pipeline Script에서 특정 브랜치만 빌드하도록 설정:

checkout([
    $class: 'GitSCM',
    branches: [[name: '*/main']],  // main 브랜치만
    // 또는 여러 브랜치: [[name: '*/main'], [name: '*/develop']]
    userRemoteConfigs: [[
        url: 'https://github.com/[사용자명]/SKN12-FINAL-2TEAM.git',
        credentialsId: env.GITHUB_CREDENTIALS
    ]]
])
```

---

## 📊 Step 7: Pipeline 시각화 및 모니터링 설정 (5분)

### 7️⃣ Blue Ocean UI 설정 (시각적 파이프라인)

#### A. Blue Ocean 플러그인 확인
```
1. Jenkins → "Manage Jenkins" → "Plugins"
2. "Installed plugins"에서 "Blue Ocean" 검색
3. 설치되지 않았다면 "Available plugins"에서 설치
```

#### B. Blue Ocean으로 파이프라인 보기
```
1. Jenkins Dashboard 왼쪽 메뉴에서 "Open Blue Ocean" 클릭
2. SKN12-Trading-Platform-CI 파이프라인 클릭
3. 시각적 파이프라인 뷰 확인:
   - 각 Stage가 박스로 표시
   - 성공/실패 상태가 색깔로 구분
   - 실행 시간 및 로그 확인 가능
```

### 7️⃣ 빌드 알림 설정 (선택사항)

#### A. 이메일 알림 설정
```
1. "Manage Jenkins" → "System"
2. "E-mail Notification" 섹션:
   - SMTP server: smtp.gmail.com
   - Default user e-mail suffix: @gmail.com
   - 사용할 이메일 계정 설정
```

#### B. Pipeline에 알림 추가
```groovy
post {
    success {
        echo '🎉 빌드가 성공적으로 완료되었습니다!'
        // 이메일 알림 (선택사항)
        emailext (
            subject: "✅ Jenkins 빌드 성공: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "빌드가 성공적으로 완료되었습니다.\n\n빌드 URL: ${env.BUILD_URL}",
            to: "admin@skn12-trading.com"
        )
    }
    
    failure {
        echo '❌ 빌드 중 오류가 발생했습니다.'
        // 실패 알림 (선택사항)
        emailext (
            subject: "❌ Jenkins 빌드 실패: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "빌드가 실패했습니다.\n\n오류 로그: ${env.BUILD_URL}console",
            to: "admin@skn12-trading.com"
        )
    }
}
```

---

## ✅ GitHub Webhook 연동 완료 체크리스트

### 🎯 GitHub 설정 완료:
- [ ] GitHub 저장소에 Webhook 생성 완료
- [ ] Webhook URL 정확히 설정 (http://Jenkins-IP:18080/github-webhook/)
- [ ] Secret 설정 완료 (skn12-webhook-secret-2025)
- [ ] Push 이벤트 트리거 설정 완료
- [ ] Webhook 테스트 전송 성공 (200 OK 응답)

### 🏗️ Jenkins 설정 완료:
- [ ] Jenkins Job 생성 완료 (SKN12-Trading-Platform-CI)
- [ ] GitHub hook trigger 설정 완료
- [ ] Pipeline script 작성 및 테스트 완료
- [ ] 모든 Credentials 연동 확인 (GitHub, Docker Hub, SSH)

### 🔄 자동화 테스트 완료:
- [ ] 수동 빌드 테스트 성공 ("Build Now")
- [ ] 자동 빌드 테스트 성공 (GitHub Push 후 자동 시작)
- [ ] 모든 Pipeline Stage 성공 (Checkout → Build → Push → Deploy Test)
- [ ] Docker Hub에 이미지 업로드 성공

### 📊 모니터링 설정 완료:
- [ ] Blue Ocean UI로 시각적 파이프라인 확인
- [ ] Build History 정상 기록
- [ ] Console Output 로그 정상 확인

---

## 🔧 문제 해결 및 최적화

### 자주 발생하는 문제들:

#### 문제 1: Webhook은 전송되지만 빌드가 시작되지 않음
```bash
해결 방법:
1. Jenkins 로그 확인:
   docker logs jenkins-master | grep -i webhook

2. Job 설정 재확인:
   - Build Triggers에서 "GitHub hook trigger" 체크
   - GitHub project URL 정확성 확인

3. Webhook Secret 일치 확인:
   - GitHub Webhook Secret
   - Jenkins Job의 Hook Secret
```

#### 문제 2: Docker 이미지 빌드 실패
```bash
해결 방법:
1. 작업 디렉토리 확인:
   dir('base_server') { ... } 에서 경로 정확성 확인

2. Docker 권한 확인:
   docker ps (Jenkins 컨테이너에서 Docker 명령어 실행 가능한지)

3. 메모리 부족 확인:
   free -h (빌드 시 메모리 사용량 확인)
```

#### 문제 3: Docker Hub 업로드 실패
```bash
해결 방법:
1. Credentials 재확인:
   - Docker Hub Access Token 유효성
   - Username 정확성

2. 네트워크 연결 확인:
   curl -I https://hub.docker.com

3. 이미지 태그 형식 확인:
   [사용자명]/ai-trading-platform:latest 형식 정확성
```

### 성능 최적화 팁:

#### 빌드 속도 향상:
```groovy
// Docker 빌드 캐시 활용
sh '''
    docker build --cache-from ${DOCKER_IMAGE}:latest \
                 -t ${DOCKER_IMAGE}:${IMAGE_TAG} \
                 -t ${DOCKER_IMAGE}:latest .
'''

// 병렬 처리 활용
parallel {
    stage('Unit Tests') {
        steps { sh 'pytest tests/unit/' }
    }
    stage('Lint Check') {
        steps { sh 'flake8 .' }
    }
}
```

#### 리소스 사용량 최적화:
```groovy
// 빌드 후 정리
post {
    always {
        sh '''
            # 사용하지 않는 Docker 이미지 정리
            docker image prune -f
            
            # 빌드 캐시 정리 (주간 1회)
            docker builder prune -f
        '''
    }
}
```

---

## 🎯 다음 단계 미리보기

### 1️⃣ 완전한 Jenkinsfile 작성:
- Pipeline as Code로 모든 설정을 코드화
- 다양한 환경별 빌드 설정 (dev, staging, prod)
- 테스트 자동화 단계 추가

### 2️⃣ 자동 배포 구현:
- Deploy Server에서 무중단 배포
- 롤백 기능 구현
- 배포 상태 모니터링

### 3️⃣ 고급 CI/CD 기능:
- Multi-branch Pipeline
- Pull Request 자동 빌드
- 성능 테스트 자동화

---

## 🎉 축하합니다!

GitHub Webhook과 Jenkins가 완전히 연동되었습니다! 🔗

### ✅ 지금까지 구축한 것:
- 🔗 **GitHub Webhook**: Push 이벤트 자동 감지
- 🏗️ **Jenkins Pipeline**: 완전 자동화된 빌드 프로세스
- 🐳 **Docker 통합**: 이미지 빌드 및 Docker Hub 업로드
- 🚀 **배포 준비**: Deploy Server 연결 및 배포 테스트

### 🚀 다음 할 일:
1. **완전한 Jenkinsfile** 작성으로 Pipeline as Code 구현
2. **자동 배포** 설정으로 Deploy Server에 실제 배포
3. **모니터링 및 알림** 설정으로 운영 안정성 확보

이제 코드를 Push만 하면 자동으로 빌드되고 배포되는 완전 자동화된 CI/CD 파이프라인이 거의 완성되었습니다! 🚀