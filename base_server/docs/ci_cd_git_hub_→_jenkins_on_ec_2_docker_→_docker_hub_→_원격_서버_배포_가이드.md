# CI/CD 전체 요약 및 스텝-바이-스텝 가이드

> **목표**: GitHub에 푸시하면 Jenkins가 자동으로 도커 이미지를 빌드해 Docker Hub로 푸시하고, 원격 서버(EC2)로 SSH 접속해 새 이미지를 배포(단일 컨테이너 혹은 docker compose)하는 파이프라인 구축.

---

## 0. 전체 구조 개요

```
GitHub (repo)
  └─ Webhook → Jenkins on EC2 (Docker 컨테이너)
         ├─ Docker build & push → Docker Hub
         └─ SSH → 배포 서버(EC2, Docker/Compose 설치)
                        └─ docker pull & run/compose up -d
```

- Jenkins: CI 서버(빌드/테스트/이미지 푸시)
- CD: Jenkins가 SSH로 배포 서버에서 컨테이너 재기동
- Kubernetes 배포를 원하면 Deploy 단계에서 kubectl/Helm 사용

---

## 1. 사전 준비 체크리스트

-

> 보안 팁: Jenkins 포트(18080)는 특정 IP만 허용하거나, 프록시+HTTPS(예: Nginx+Let’s Encrypt) 권장.

---

## 2. Jenkins 서버를 Docker로 띄우기

### 2.1 `docker-compose.yml` (Jenkins 호스팅)

```yaml
version: "3.8"
services:
  jenkins:
    build:
      context: .
      dockerfile: Dockerfile.jenkins
    user: root
    ports:
      - "18080:8080"    # Jenkins UI
      - "50000:50000"   # (옵션) 에이전트
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock  # host docker 사용
    restart: unless-stopped

volumes:
  jenkins_home:
```

### 2.2 `Dockerfile.jenkins` (컨테이너에 docker CLI 설치)

```dockerfile
FROM jenkins/jenkins:lts-jdk17
USER root
RUN apt-get update && apt-get install -y docker.io git \
    && rm -rf /var/lib/apt/lists/*
USER jenkins
```

### 2.3 실행 및 초기 설정

```bash
# EC2(Jenkins)에서
docker compose up -d
# 초기 관리자 비밀번호 확인
docker exec -it <jenkins_container> cat /var/jenkins_home/secrets/initialAdminPassword
```

- Jenkins 플러그인: **Git, GitHub, Pipeline, SSH Agent, Docker Pipeline** 등 설치
- **Manage Jenkins → System → Jenkins URL**: `http://<EC2-PublicDNS>:18080/` 로 정확히 설정

---

## 3. GitHub Webhook 연결

1. GitHub Repo → **Settings → Webhooks → Add webhook**

   - **Payload URL**: `http://<EC2-PublicDNS>:18080/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: Just the push event (필요 시 PR 등 추가)
   - Webhook 테스트 Deliveries에서 200 OK 확인

2. Jenkins가 코드 클론할 수 있도록 **GitHub PAT** 준비

   - 권장 스코프: `repo`, `admin:repo_hook`(필요 시)

---

## 4. Jenkins Credentials 등록

- **GitHub PAT**: *Kind* → **Secret text** (ID 예: `github-pat`)
- **Docker Hub**: *Kind* → **Username with password** (ID 예: `dockerhub-cred`)
- **배포 SSH Key**: *Kind* → **SSH Username with private key** (ID 예: `deploy-ssh-key`)

### 4.1 Jenkins 컨테이너 안에서 SSH 키 생성

```bash
docker exec -u jenkins -it <jenkins_container> bash
ssh-keygen -t ed25519 -C "jenkins-deploy" -N "" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

- 출력된 공개키를 **배포 서버**의 `~/.ssh/authorized_keys`에 추가
- Jenkins Credentials에 **Private Key** 등록 (Username: 배포 서버의 사용자, 예: `ec2-user`/`ubuntu`)

---

## 5. 애플리케이션 리포지토리 준비

### 5.1 `Dockerfile` (예: Node.js)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### 5.2 `Jenkinsfile` (단일 컨테이너 배포 예시)

```groovy
pipeline {
  agent any

  environment {
    REGISTRY = "docker.io"
    IMAGE    = "<DOCKERHUB_USERNAME>/<APP_NAME>"
    DOCKERHUB_CRED = "dockerhub-cred"
    SSH_CRED = "deploy-ssh-key"
    DEPLOY_HOST = "ec2-user@<REMOTE_SERVER_IP_OR_DNS>"
    TAG = "${env.GIT_COMMIT.take(7)}"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build image') {
      steps {
        sh """
          docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .
        """
      }
    }

    stage('Push image') {
      steps {
        withCredentials([usernamePassword(credentialsId: DOCKERHUB_CRED, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh """
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin ${REGISTRY}
            docker push ${IMAGE}:${TAG}
            docker push ${IMAGE}:latest
          """
        }
      }
    }

    stage('Deploy (SSH)') {
      steps {
        sshagent (credentials: [SSH_CRED]) {
          sh """
            ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} '
              docker pull ${IMAGE}:${TAG} &&
              docker stop app || true &&
              docker rm app || true &&
              docker run -d --name app -p 80:3000 ${IMAGE}:${TAG}
            '
          """
        }
      }
    }
  }

  post {
    always { cleanWs() }
  }
}
```

> 포트 매핑(`-p 80:3000`)은 앱 포트에 맞게 조정.

---

## 6. docker compose로 배포하는 경우

- 배포 서버에 `docker-compose.yml`이 존재한다고 가정(예: `/opt/yourapp/docker-compose.yml`)

### 6.1 배포 서버의 `docker-compose.yml` 예시

```yaml
version: "3.8"
services:
  app:
    image: <DOCKERHUB_USERNAME>/<APP_NAME>:latest
    container_name: app
    ports:
      - "80:3000"
    restart: unless-stopped
    env_file:
      - .env
```

### 6.2 Jenkinsfile Deploy 단계 (compose)

```groovy
stage('Deploy (Compose)') {
  steps {
    sshagent (credentials: [SSH_CRED]) {
      sh """
        ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} '
          cd /opt/yourapp &&
          docker compose pull &&
          docker compose up -d &&
          docker image prune -f
        '
      """
    }
  }
}
```

---

## 7. (옵션) Kubernetes로 배포하는 경우

- Jenkins Credentials에 **Kubeconfig**를 Secret file로 등록(ID 예: `kubeconfig-prod`)
- 배포 단계 예시:

```groovy
stage('Deploy (Kubernetes)') {
  steps {
    withCredentials([file(credentialsId: 'kubeconfig-prod', variable: 'KUBECONFIG')]) {
      sh """
        kubectl set image deployment/your-deploy your-container=${IMAGE}:${TAG} -n prod
        kubectl rollout status deployment/your-deploy -n prod
      """
    }
  }
}
```

---

## 8. 트러블슈팅 체크리스트

- **Webhook 403/timeout**: Jenkins URL 오설정, 18080 방화벽, 퍼블릭 접근 불가
- \`\`: Jenkins 컨테이너에 docker CLI 미설치 → `Dockerfile.jenkins` 확인
- \`\`: 소켓 마운트/권한 문제 → compose yml의 소켓 마운트와 `user: root` 확인
- **비공개 Repo 클론 실패**: GitHub PAT 누락/권한 부족(`repo` 권한 필요)
- **Docker Hub 푸시 실패**: Credentials 불일치 또는 rate limit
- **SSH 호스트키 확인**: `-o StrictHostKeyChecking=no` 임시 사용 또는 known\_hosts 사전 등록
- **포트 충돌**: 기존 컨테이너/프로세스가 점유 → `docker ps`, `lsof -i :PORT` 확인

---

## 9. 운영 팁

- **브랜치 전략**: `main`→프로덕션, `develop`→스테이징. 멀티브랜치 파이프라인으로 분리 배포
- **태깅**: `${GIT_COMMIT:0:7}` + 날짜 등으로 이미지 추적성 확보
- **롤백**: compose/K8s 모두 이전 태그로 빠르게 재기동 스크립트 준비
- **로그/모니터링**: CloudWatch/Elastic/Grafana 등 연계
- **보안**: Jenkins 보안 업데이트/백업, HTTPS, 최소 권한 원칙

---

## 10. 빠른 실행 스니펫 모음

```bash
# Jenkins 초기 비번
docker exec -it <jenkins_container> cat /var/jenkins_home/secrets/initialAdminPassword

# Jenkins 컨테이너 셸 접속
docker exec -u jenkins -it <jenkins_container> bash

# Jenkins 컨테이너에서 SSH 키 생성
ssh-keygen -t ed25519 -C "jenkins-deploy" -N "" -f ~/.ssh/id_ed25519

# 배포 서버에서 수동 테스트(이미지 교체)
docker pull <DOCKERHUB_USERNAME>/<APP_NAME>:latest
docker stop app || true && docker rm app || true
docker run -d --name app -p 80:3000 <DOCKERHUB_USERNAME>/<APP_NAME>:latest
```

---

### 끝. 필요한 변수만 본인 환경으로 치환해 그대로 적용하면 됩니다.

- `<DOCKERHUB_USERNAME>`, `<APP_NAME>`, `<REMOTE_SERVER_IP_OR_DNS>` 등
- 포트, 환경변수, 볼륨, 헬스체크, 브랜치 분기(Prod/Staging)도 요청 주시면 추가 템플릿 제공 가능합니다.

