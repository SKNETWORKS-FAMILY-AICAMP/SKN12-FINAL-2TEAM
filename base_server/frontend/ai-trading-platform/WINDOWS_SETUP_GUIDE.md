# Windows 환경 프론트엔드 설치 및 실행 가이드

## 📋 사전 요구사항

### 1. Node.js 설치
- **Node.js 18.17.0 이상** 필요
- [Node.js 공식 사이트](https://nodejs.org/)에서 LTS 버전 다운로드
- 설치 시 "Add to PATH" 옵션 체크 필수

### 2. Git 설치
- [Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치
- 설치 시 기본 옵션으로 진행

### 3. 코드 에디터 설치 (권장)
- **Visual Studio Code** 설치
- [VS Code 다운로드](https://code.visualstudio.com/)

## 🚀 프로젝트 설치 및 실행

### 1단계: 프로젝트 클론
```bash
# 원하는 폴더로 이동 (예: C:\Projects)
cd C:\Projects

# 프로젝트 클론
git clone [프로젝트_URL]
cd SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform
```

### 2단계: 의존성 설치
```bash
# npm 캐시 정리 (선택사항)
npm cache clean --force

# 의존성 설치
npm install

# 설치 확인
npm --version
node --version
```

### 3단계: 환경 변수 설정
```bash
# .env.local 파일 생성
copy .env.example .env.local
```

**또는 수동으로 `.env.local` 파일 생성:**
```env
# .env.local 파일 내용
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000
```

### 4단계: 개발 서버 실행
```bash
# 개발 서버 시작
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

## 🔧 문제 해결

### Node.js 버전 문제
```bash
# Node.js 버전 확인
node --version

# 버전이 낮은 경우 Node.js 재설치
```

### npm 설치 오류
```bash
# npm 캐시 정리
npm cache clean --force

# node_modules 삭제 후 재설치
rmdir /s node_modules
del package-lock.json
npm install
```

### 포트 충돌 문제
```bash
# 포트 3000 사용 중인 프로세스 확인
netstat -ano | findstr :3000

# 프로세스 종료 (PID는 위 명령어로 확인)
taskkill /PID [프로세스ID] /F
```

### 권한 문제
- 명령 프롬프트를 **관리자 권한**으로 실행
- 또는 PowerShell을 관리자 권한으로 실행

## 📦 추가 도구 설치 (권장)

### 1. Git Bash 설치
- Git 설치 시 함께 설치됨
- Unix 스타일 명령어 사용 가능

### 2. Windows Terminal 설치
- [Microsoft Store](https://apps.microsoft.com/detail/9n0dx20hk701)에서 설치
- 더 나은 터미널 경험 제공

### 3. VS Code 확장 프로그램
```bash
# VS Code에서 다음 확장 프로그램 설치:
# - ESLint
# - Prettier
# - TypeScript Importer
# - Tailwind CSS IntelliSense
# - Auto Rename Tag
```

## 🛠️ 개발 도구 설정

### VS Code 설정
1. **프로젝트 열기**
   ```bash
   code .
   ```

2. **추천 확장 프로그램 설치**
   - VS Code에서 `Ctrl+Shift+X`로 확장 프로그램 탭 열기
   - 다음 확장 프로그램 검색 및 설치:
     - ESLint
     - Prettier
     - TypeScript Importer
     - Tailwind CSS IntelliSense

3. **설정 파일 생성**
   ```json
   // .vscode/settings.json
   {
     "editor.formatOnSave": true,
     "editor.defaultFormatter": "esbenp.prettier-vscode",
     "typescript.preferences.importModuleSpecifier": "relative"
   }
   ```

### Git 설정
```bash
# Git 사용자 정보 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 기본 브랜치 설정
git config --global init.defaultBranch main
```

## 📋 팀 개발 가이드라인

### 브랜치 전략
```bash
# 메인 브랜치에서 개발 브랜치 생성
git checkout -b feature/your-feature-name

# 작업 완료 후
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 코드 스타일
- **ESLint** 규칙 준수
- **Prettier** 자동 포맷팅 사용
- **TypeScript** 타입 정의 필수

### 커밋 메시지 규칙
```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드 프로세스 또는 보조 도구 변경
```

## 🔍 디버깅 도구

### 브라우저 개발자 도구
- **F12** 키로 개발자 도구 열기
- **Console** 탭에서 에러 확인
- **Network** 탭에서 API 요청 확인

### React Developer Tools
- Chrome/Firefox 확장 프로그램 설치
- 컴포넌트 상태 및 props 확인

### Redux DevTools
- Chrome 확장 프로그램 설치
- Redux 상태 변화 추적

## 📱 모바일 테스트

### Chrome DevTools
1. F12로 개발자 도구 열기
2. **Toggle device toolbar** 클릭 (Ctrl+Shift+M)
3. 다양한 디바이스 크기로 테스트

### 실제 모바일 테스트
```bash
# 로컬 IP 확인
ipconfig

# 개발 서버를 모든 IP에서 접근 가능하도록 실행
npm run dev -- --hostname 0.0.0.0
```

## 🚀 배포 준비

### 프로덕션 빌드
```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 확인
npm start
```

### 환경 변수 설정 (프로덕션)
```env
# .env.production
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_WS_URL=wss://your-api-domain.com
NEXTAUTH_SECRET=your-production-secret
NEXTAUTH_URL=https://your-domain.com
```

## 📞 문제 발생 시 연락처

### 기술적 문제
- **프로젝트 리더**: [이름] - [이메일]
- **프론트엔드 담당**: [이름] - [이메일]

### 일반적인 문제 해결
1. **Node.js 재설치**
2. **npm 캐시 정리**
3. **node_modules 삭제 후 재설치**
4. **관리자 권한으로 실행**

## 📚 추가 학습 자료

- [Next.js 공식 문서](https://nextjs.org/docs)
- [React 공식 문서](https://react.dev/)
- [TypeScript 핸드북](https://www.typescriptlang.org/docs/)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)

---

**⚠️ 주의사항**
- Node.js 버전은 18.17.0 이상 사용
- 관리자 권한이 필요한 경우 명령 프롬프트를 관리자 권한으로 실행
- 방화벽이나 백신 프로그램이 포트를 차단할 수 있으니 확인 필요 