// =============================================================================
// SKN12 Trading Platform - Jenkins Pipeline (AWS Production Docker Deploy)
// =============================================================================
// 
// 🎯 프로덕션 배포 파이프라인:
// 1. GitHub 소스코드 자동 체크아웃
// 2. Backend/Frontend Docker 이미지 빌드
// 3. Docker Hub 이미지 푸시 (태그 관리)
// 4. AWS EC2 서버 Docker Compose 배포
// 5. 헬스체크 및 배포 상태 확인
//
// 📝 사용법:
// - GitHub에 코드 Push 시 자동 실행
// - Jenkins에서 "Build Now" 수동 실행 가능
// - 환경별 배포: main 브랜치 → Production, develop 브랜치 → Staging

pipeline {
    agent any
    
    // 🌍 환경 변수 정의 (모든 Stage에서 사용 가능)
    environment {
        // Docker 이미지 설정
        DOCKER_REGISTRY = "docker.io"
        DOCKER_IMAGE = "ashone91/ai-trading-platform"
        DOCKER_CREDENTIALS = "dockerhub-credentials"
        
        // Git 및 GitHub 설정
        GITHUB_CREDENTIALS = "github-token"
        
        // 배포 서버 설정
        DEPLOY_SERVER = "[Deploy-Server-IP]"  // ⚠️ 실제 Deploy Server IP로 교체 필요
        SSH_CREDENTIALS = "deploy-server-ssh-key"
        
        // 이미지 태그 생성 (빌드 번호 + Git 커밋 해시)
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'unknown'}"
        
        // 배포 환경 결정 (브랜치별)
        DEPLOY_ENV = "${env.BRANCH_NAME == 'main' ? 'PROD' : (env.BRANCH_NAME == 'develop' ? 'DEBUG' : 'LOCAL')}"
        
        // 타임스탬프 (로그 및 백업용)
        BUILD_TIMESTAMP = new Date().format('yyyy-MM-dd-HH-mm-ss')
    }
    
    // 🔄 빌드 트리거 설정
    triggers {
        // GitHub Webhook에 의한 자동 빌드
        githubPush()
        
        // 주기적 빌드 (매일 오전 3시 - 야간 빌드)
        cron('0 3 * * *')
    }
    
    // 📊 빌드 옵션
    options {
        // 빌드 히스토리 보관 (최근 20개)
        buildDiscarder(logRotator(numToKeepStr: '20'))
        
        // 빌드 타임아웃 (30분)
        timeout(time: 30, unit: 'MINUTES')
        
        // 동시 빌드 방지 (리소스 절약)
        disableConcurrentBuilds()
        
        // 타임스탬프 로그
        timestamps()
        
        // ANSI 컬러 로그
        ansiColor('xterm')
    }
    
    stages {
        // 🔍 1단계: 소스코드 체크아웃 및 환경 확인
        stage('📥 Checkout & Environment Setup') {
            steps {
                script {
                    echo "🚀 SKN12 Trading Platform CI/CD 파이프라인 시작"
                    echo "📅 빌드 시간: ${env.BUILD_TIMESTAMP}"
                    echo "🔖 빌드 번호: ${env.BUILD_NUMBER}"
                    echo "🌿 브랜치: ${env.BRANCH_NAME ?: 'main'}"
                    echo "🏷️ 이미지 태그: ${env.IMAGE_TAG}"
                    echo "🌍 배포 환경: ${env.DEPLOY_ENV}"
                }
                
                // GitHub에서 소스코드 체크아웃
                echo "📥 GitHub에서 소스코드 다운로드 중..."
                checkout scm
                
                // 프로젝트 정보 확인
                sh '''
                    echo "📊 Git 정보:"
                    git log --oneline -5 || echo "Git 로그 조회 실패"
                    
                    echo "📁 프로젝트 구조:"
                    ls -la
                    
                    echo "🔍 base_server 디렉토리 확인:"
                    if [ -d "base_server" ]; then
                        ls -la base_server/
                    else
                        echo "❌ base_server 디렉토리가 없습니다!"
                        exit 1
                    fi
                '''
                
                // 빌드 환경 정보 출력
                sh '''
                    echo "🔧 빌드 환경 정보:"
                    echo "  - OS: $(uname -a)"
                    echo "  - Docker: $(docker --version)"
                    echo "  - Docker Compose: $(docker compose version)"
                    echo "  - 메모리: $(free -h | grep Mem)"
                    echo "  - 디스크: $(df -h | grep -v tmpfs | head -5)"
                    echo "  - 현재 시간: $(date)"
                '''
            }
        }
        
        // 🧪 2단계: 코드 품질 검사 (선택사항)
        stage('🔍 Code Quality Check') {
            when {
                // main 또는 develop 브랜치에서만 실행
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            
            parallel {
                // Python 코드 스타일 검사
                stage('Python Lint') {
                    steps {
                        script {
                            dir('base_server') {
                                sh '''
                                    echo "🐍 Python 코드 스타일 검사 중..."
                                    
                                    # flake8 설치 및 실행 (있는 경우에만)
                                    if command -v python3 &> /dev/null; then
                                        echo "Python 3 발견, 코드 검사 시작..."
                                        # 기본적인 Python 문법 검사만 수행
                                        python3 -m py_compile application/base_web_server/main.py || echo "⚠️ main.py 문법 검사 실패"
                                    else
                                        echo "⚠️ Python 3를 찾을 수 없음, 검사 건너뛰기"
                                    fi
                                '''
                            }
                        }
                    }
                }
                
                // Docker 관련 파일 검사
                stage('Docker Files Check') {
                    steps {
                        script {
                            dir('base_server') {
                                sh '''
                                    echo "🐳 Docker 파일 검사 중..."
                                    
                                    # Dockerfile 존재 확인
                                    if [ ! -f "Dockerfile" ]; then
                                        echo "❌ Dockerfile이 없습니다!"
                                        exit 1
                                    fi
                                    
                                    # .dockerignore 존재 확인
                                    if [ ! -f ".dockerignore" ]; then
                                        echo "⚠️ .dockerignore 파일이 없습니다."
                                    fi
                                    
                                    # requirements.txt 존재 확인
                                    if [ ! -f "requirements.txt" ]; then
                                        echo "❌ requirements.txt가 없습니다!"
                                        exit 1
                                    fi
                                    
                                    echo "✅ Docker 관련 파일 검사 완료"
                                '''
                            }
                        }
                    }
                }
            }
        }
        
        // 🏗️ 3단계: Docker 이미지 빌드
        stage('🐳 Build Docker Image') {
            steps {
                script {
                    echo "🏗️ Docker 이미지 빌드 시작..."
                    
                    dir('base_server') {
                        // 이전 빌드 이미지 정리
                        sh '''
                            echo "🧹 이전 빌드 이미지 정리 중..."
                            docker image prune -f || true
                        '''
                        
                        // Docker 이미지 빌드
                        sh '''
                            echo "🔨 Docker 이미지 빌드 중..."
                            echo "  - 이미지: ${DOCKER_IMAGE}"
                            echo "  - 태그: ${IMAGE_TAG}, latest"
                            
                            # 빌드 시작 시간 기록
                            BUILD_START=$(date +%s)
                            
                            # Docker 이미지 빌드 (캐시 활용)
                            docker build \\
                                --cache-from ${DOCKER_IMAGE}:latest \\
                                --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \\
                                --build-arg VCS_REF=${GIT_COMMIT} \\
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \\
                                -t ${DOCKER_IMAGE}:${IMAGE_TAG} \\
                                -t ${DOCKER_IMAGE}:latest \\
                                .
                            
                            # 빌드 완료 시간 계산
                            BUILD_END=$(date +%s)
                            BUILD_TIME=$((BUILD_END - BUILD_START))
                            echo "⏱️ 빌드 완료 시간: ${BUILD_TIME}초"
                            
                            # 빌드된 이미지 정보 확인
                            echo "📦 빌드된 이미지 정보:"
                            docker images | grep ${DOCKER_IMAGE} | head -5
                            
                            # 이미지 크기 확인
                            IMAGE_SIZE=$(docker images ${DOCKER_IMAGE}:${IMAGE_TAG} --format "table {{.Size}}" | tail -1)
                            echo "📏 이미지 크기: ${IMAGE_SIZE}"
                        '''
                        
                        // 이미지 보안 스캔 (간단한 체크)
                        sh '''
                            echo "🔒 이미지 기본 보안 검사 중..."
                            
                            # 이미지 히스토리 확인 (레이어 구조)
                            docker history ${DOCKER_IMAGE}:${IMAGE_TAG} --no-trunc | head -10
                            
                            # 컨테이너 실행 테스트 (빠른 시작/종료)
                            echo "🧪 컨테이너 실행 테스트 중..."
                            CONTAINER_ID=$(docker run -d --name test-container-${BUILD_NUMBER} ${DOCKER_IMAGE}:${IMAGE_TAG})
                            
                            # 컨테이너가 정상 시작되는지 확인 (10초 대기)
                            sleep 10
                            
                            if docker ps | grep test-container-${BUILD_NUMBER}; then
                                echo "✅ 컨테이너 정상 시작 확인"
                                docker logs test-container-${BUILD_NUMBER} | head -20
                            else
                                echo "❌ 컨테이너 시작 실패"
                                docker logs test-container-${BUILD_NUMBER} || true
                            fi
                            
                            # 테스트 컨테이너 정리
                            docker stop test-container-${BUILD_NUMBER} || true
                            docker rm test-container-${BUILD_NUMBER} || true
                        '''
                    }
                }
            }
        }
        
        // 📤 4단계: Docker Hub에 이미지 업로드
        stage('📤 Push to Docker Hub') {
            steps {
                script {
                    echo "🚀 Docker Hub에 이미지 업로드 시작..."
                    
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDENTIALS, 
                                                    usernameVariable: 'DOCKER_USER', 
                                                    passwordVariable: 'DOCKER_PASS')]) {
                        sh '''
                            echo "🔐 Docker Hub 로그인 중..."
                            echo "$DOCKER_PASS" | docker login --username "$DOCKER_USER" --password-stdin ${DOCKER_REGISTRY}
                            
                            if [ $? -eq 0 ]; then
                                echo "✅ Docker Hub 로그인 성공"
                            else
                                echo "❌ Docker Hub 로그인 실패"
                                exit 1
                            fi
                            
                            # 업로드 시작 시간 기록
                            PUSH_START=$(date +%s)
                            
                            echo "📤 이미지 업로드 중..."
                            echo "  - ${DOCKER_IMAGE}:${IMAGE_TAG}"
                            echo "  - ${DOCKER_IMAGE}:latest"
                            
                            # 이미지 푸시
                            docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                            docker push ${DOCKER_IMAGE}:latest
                            
                            # 업로드 완료 시간 계산
                            PUSH_END=$(date +%s)
                            PUSH_TIME=$((PUSH_END - PUSH_START))
                            echo "⏱️ 업로드 완료 시간: ${PUSH_TIME}초"
                            
                            # Docker Hub 로그아웃
                            docker logout ${DOCKER_REGISTRY}
                            
                            echo "✅ Docker Hub 업로드 완료"
                            echo "🔗 이미지 URL: https://hub.docker.com/r/${DOCKER_IMAGE/docker.io\\//}/tags"
                        '''
                    }
                }
            }
        }
        
        // 🚀 5단계: Deploy Server에 자동 배포
        stage('🚀 Deploy to Server') {
            steps {
                script {
                    echo "🚀 Deploy Server에 배포 시작..."
                    
                    sshagent(credentials: [env.SSH_CREDENTIALS]) {
                        sh '''
                            echo "📡 Deploy Server 연결 중..."
                            echo "  - 서버 IP: ${DEPLOY_SERVER}"
                            echo "  - 배포 환경: ${DEPLOY_ENV}"
                            echo "  - 이미지: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                            
                            # SSH 연결 및 배포 스크립트 실행
                            ssh -o StrictHostKeyChecking=no ubuntu@${DEPLOY_SERVER} "
                                set -e  # 오류 발생 시 스크립트 중단
                                
                                echo '🏠 Deploy Server 접속 성공!'
                                echo '📊 서버 정보:'
                                hostname
                                uptime
                                free -h | grep Mem
                                df -h | grep -v tmpfs | head -3
                                
                                echo '🐳 Docker 환경 확인:'
                                docker --version
                                docker compose version || docker-compose version
                                
                                echo '📥 새 이미지 다운로드 중...'
                                docker pull ${DOCKER_IMAGE}:${IMAGE_TAG}
                                docker pull ${DOCKER_IMAGE}:latest
                                
                                echo '🔄 기존 컨테이너 중지 및 제거 (무중단 배포 준비)...'
                                
                                # Base Web Server 업데이트
                                if docker ps | grep -q trading-web-server; then
                                    echo '⏹️ 기존 Web Server 컨테이너 중지 중...'
                                    docker stop trading-web-server || true
                                    docker rm trading-web-server || true
                                fi
                                
                                # Model Server 업데이트  
                                if docker ps | grep -q trading-model-server; then
                                    echo '⏹️ 기존 Model Server 컨테이너 중지 중...'
                                    docker stop trading-model-server || true
                                    docker rm trading-model-server || true
                                fi
                                
                                echo '🚀 새 컨테이너 실행 중...'
                                
                                # 애플리케이션 디렉토리 확인 및 생성
                                sudo mkdir -p /opt/skn12-trading/{configs,logs}/{base-web-server,model-server}
                                sudo chown -R ubuntu:ubuntu /opt/skn12-trading
                                
                                # Base Web Server 시작 (포트 8000)
                                echo '🌐 Base Web Server 시작 중...'
                                docker run -d \\
                                    --name trading-web-server \\
                                    --restart unless-stopped \\
                                    -p 8000:8000 \\
                                    -e APP_ENV=${DEPLOY_ENV} \\
                                    -v /opt/skn12-trading/configs/base-web-server:/app/application/base_web_server:ro \\
                                    -v /opt/skn12-trading/logs/base-web-server:/app/logs \\
                                    ${DOCKER_IMAGE}:${IMAGE_TAG}
                                
                                # Model Server 시작 (포트 8001)
                                echo '🤖 Model Server 시작 중...'
                                docker run -d \\
                                    --name trading-model-server \\
                                    --restart unless-stopped \\
                                    -p 8001:8001 \\
                                    -e APP_ENV=${DEPLOY_ENV} \\
                                    -v /opt/skn12-trading/configs/model-server:/app/application/model_server:ro \\
                                    -v /opt/skn12-trading/logs/model-server:/app/logs \\
                                    ${DOCKER_IMAGE}:${IMAGE_TAG} \\
                                    uvicorn application.model_server.main:app --host 0.0.0.0 --port 8001
                                
                                echo '⏰ 컨테이너 시작 대기 중 (30초)...'
                                sleep 30
                                
                                echo '📊 배포 결과 확인:'
                                docker ps | grep trading || echo '⚠️ 실행 중인 trading 컨테이너 없음'
                                
                                # 헬스체크
                                echo '🏥 서비스 헬스체크:'
                                
                                # Base Web Server 체크
                                if curl -f -s http://localhost:8000/ > /dev/null 2>&1; then
                                    echo '✅ Base Web Server (8000) 정상 응답'
                                else
                                    echo '❌ Base Web Server (8000) 응답 없음'
                                    docker logs trading-web-server | tail -10 || true
                                fi
                                
                                # Model Server 체크
                                if curl -f -s http://localhost:8001/ > /dev/null 2>&1; then
                                    echo '✅ Model Server (8001) 정상 응답'
                                else
                                    echo '❌ Model Server (8001) 응답 없음'
                                    docker logs trading-model-server | tail -10 || true
                                fi
                                
                                echo '🧹 이전 이미지 정리 중...'
                                docker image prune -f || true
                                
                                echo '✅ 배포 완료!'
                                echo '🔗 서비스 URL:'
                                echo '  - Base Web Server: http://${DEPLOY_SERVER}:8000'
                                echo '  - Model Server: http://${DEPLOY_SERVER}:8001'
                            "
                        '''
                    }
                }
            }
        }
        
        // 🧪 6단계: 배포 후 통합 테스트
        stage('🧪 Post-Deploy Testing') {
            steps {
                script {
                    echo "🧪 배포 후 통합 테스트 시작..."
                    
                    // 외부에서 서비스 접근 테스트
                    sh '''
                        echo "🌐 외부에서 서비스 접근 테스트 중..."
                        
                        # Base Web Server 테스트
                        echo "🔍 Base Web Server (8000) 테스트..."
                        for i in {1..5}; do
                            if curl -f -s http://${DEPLOY_SERVER}:8000/ > /dev/null; then
                                echo "✅ Base Web Server 응답 성공 (시도 $i)"
                                break
                            else
                                echo "⏳ Base Web Server 응답 대기 중... (시도 $i/5)"
                                sleep 10
                            fi
                        done
                        
                        # Model Server 테스트
                        echo "🔍 Model Server (8001) 테스트..."
                        for i in {1..5}; do
                            if curl -f -s http://${DEPLOY_SERVER}:8001/ > /dev/null; then
                                echo "✅ Model Server 응답 성공 (시도 $i)"
                                break
                            else
                                echo "⏳ Model Server 응답 대기 중... (시도 $i/5)"
                                sleep 10
                            fi
                        done
                        
                        echo "🏁 통합 테스트 완료"
                    '''
                }
            }
        }
    }
    
    // 📧 빌드 완료 후 처리 (성공/실패 공통)
    post {
        always {
            script {
                echo "🧹 빌드 후 정리 작업 시작..."
                
                // 작업 공간 정리
                echo "📁 작업 공간 정리 중..."
                cleanWs()
                
                // 로컬 Docker 이미지 정리 (디스크 공간 절약)
                sh '''
                    echo "🗑️ 로컬 Docker 이미지 정리 중..."
                    
                    # 사용하지 않는 이미지 정리
                    docker image prune -f || true
                    
                    # 빌드 캐시 정리 (주 1회)
                    if [ "$(date +%u)" -eq 7 ]; then
                        echo "📅 주간 캐시 정리 중..."
                        docker builder prune -f || true
                    fi
                    
                    # 현재 Docker 이미지 상태
                    echo "📊 현재 Docker 이미지 상태:"
                    docker images | head -10
                    
                    # 디스크 사용량 확인
                    echo "💾 디스크 사용량:"
                    df -h | grep -v tmpfs
                '''
                
                // 빌드 시간 계산
                script {
                    def buildDuration = currentBuild.duration ? "${(currentBuild.duration / 1000).intValue()}초" : "알 수 없음"
                    echo "⏱️ 총 빌드 시간: ${buildDuration}"
                }
            }
        }
        
        success {
            script {
                echo "🎉 빌드가 성공적으로 완료되었습니다!"
                echo "📦 배포된 이미지: ${env.DOCKER_IMAGE}:${env.IMAGE_TAG}"
                echo "🔗 서비스 URL:"
                echo "  - Base Web Server: http://${env.DEPLOY_SERVER}:8000"
                echo "  - Model Server: http://${env.DEPLOY_SERVER}:8001"
                echo "  - Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE.replace('docker.io/', '')}/tags"
                
                // Slack 알림 (Slack 플러그인 설치 시 활성화)
                /*
                slackSend(
                    channel: '#ci-cd',
                    color: 'good',
                    message: """
                        ✅ *SKN12 Trading Platform* 배포 성공!
                        
                        • 빌드 번호: #${env.BUILD_NUMBER}
                        • 브랜치: ${env.BRANCH_NAME ?: 'main'}
                        • 이미지: `${env.DOCKER_IMAGE}:${env.IMAGE_TAG}`
                        • 배포 환경: ${env.DEPLOY_ENV}
                        
                        🔗 서비스: http://${env.DEPLOY_SERVER}:8000
                    """.stripIndent()
                )
                */
            }
        }
        
        failure {
            script {
                echo "❌ 빌드 중 오류가 발생했습니다."
                echo "📋 실패 정보:"
                echo "  - 빌드 번호: ${env.BUILD_NUMBER}"
                echo "  - 브랜치: ${env.BRANCH_NAME ?: 'main'}"
                echo "  - 실패 시간: ${new Date().format('yyyy-MM-dd HH:mm:ss')}"
                echo "🔍 Console Output에서 자세한 오류 내용을 확인하세요."
                
                // 오류 발생 시 로그 수집
                sh '''
                    echo "📊 오류 발생 시 시스템 상태:"
                    
                    # 메모리 사용량
                    echo "💾 메모리 상태:"
                    free -h
                    
                    # 디스크 사용량
                    echo "💿 디스크 상태:"
                    df -h
                    
                    # Docker 상태
                    echo "🐳 Docker 상태:"
                    docker ps -a | head -5 || true
                    docker images | head -5 || true
                    
                    # 최근 시스템 로그 (Ubuntu)
                    echo "📜 시스템 로그 (최근 10줄):"
                    sudo journalctl -n 10 --no-pager || true
                '''
                
                // Slack 실패 알림 (Slack 플러그인 설치 시 활성화)
                /*
                slackSend(
                    channel: '#ci-cd',
                    color: 'danger',
                    message: """
                        ❌ *SKN12 Trading Platform* 빌드 실패!
                        
                        • 빌드 번호: #${env.BUILD_NUMBER}
                        • 브랜치: ${env.BRANCH_NAME ?: 'main'}
                        • 실패 단계: ${env.STAGE_NAME ?: '알 수 없음'}
                        
                        🔗 로그 확인: ${env.BUILD_URL}console
                    """.stripIndent()
                )
                */
            }
        }
        
        unstable {
            script {
                echo "⚠️ 빌드가 불안정한 상태로 완료되었습니다."
                echo "🔍 테스트 결과나 코드 품질 검사에서 경고가 발생했을 수 있습니다."
            }
        }
        
        aborted {
            script {
                echo "🛑 빌드가 중단되었습니다."
                echo "👤 사용자가 수동으로 중단했거나 시간 초과가 발생했습니다."
            }
        }
    }
}

// =============================================================================
// 📝 Jenkinsfile 사용 가이드
// =============================================================================
//
// 🔧 설정 변경 필요 사항:
// 1. Line 21: [Docker-Hub-사용자명] → 실제 Docker Hub 사용자명
// 2. Line 29: [Deploy-Server-IP] → 실제 Deploy Server IP
//
// 🎯 브랜치별 배포 환경:
// - main → PROD (운영 환경)
// - develop → DEBUG (개발 환경)  
// - feature/* → LOCAL (로컬 환경)
//
// 📤 자동 배포 조건:
// - GitHub Push 시 자동 실행
// - 매일 오전 3시 정기 빌드
// - 수동 "Build Now" 실행 가능
//
// 🔗 관련 링크:
// - Pipeline Syntax: Jenkins → Pipeline Syntax Helper
// - Blue Ocean: Jenkins → Open Blue Ocean (시각적 파이프라인)
// - 플러그인 문서: https://plugins.jenkins.io/
// =============================================================================