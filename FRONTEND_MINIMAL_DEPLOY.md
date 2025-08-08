# Frontend 최소 배포 가이드

## 🎯 목표: 15MB 프로젝트를 다른 PC에서 실행

---

## 📦 STEP 1: 현재 PC에서 정리 (배포 준비)

### PowerShell 열고 프로젝트로 이동
```powershell
cd C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform
```

### 삭제할 것들 (전부 삭제)
```powershell
# 1. node_modules 삭제 (500MB)
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue

# 2. .next 삭제 (100MB)  
Remove-Item .next -Recurse -Force -ErrorAction SilentlyContinue

# 3. 환경변수 삭제 (보안)
Remove-Item .env -Force -ErrorAction SilentlyContinue
Remove-Item .env.local -Force -ErrorAction SilentlyContinue

# 4. 로그 파일 삭제
Remove-Item *.log -Force -ErrorAction SilentlyContinue
```

### 남은 파일 확인
```powershell
# 폴더 크기 확인 (15MB 정도여야 함)
Get-ChildItem -Recurse | Measure-Object -Property Length -Sum
```

---

## 📁 STEP 2: 필수 파일만 복사

### 복사해야 할 폴더 구조
```
ai-trading-platform/
├── app/                 ✅ 필수
├── components/          ✅ 필수  
├── lib/                 ✅ 필수
├── hooks/               ✅ 필수
├── providers/           ✅ 필수
├── public/              ✅ 필수
├── styles/              ✅ 필수
├── types/               ✅ 필수
├── package.json         ✅ 필수 (절대 삭제 금지!)
├── package-lock.json    ✅ 권장 (버전 고정)
├── next.config.mjs      ✅ 필수
├── tsconfig.json        ✅ 필수
├── tailwind.config.ts   ✅ 필수
├── postcss.config.mjs   ✅ 필수
└── components.json      ✅ 필수
```

### USB나 압축파일로 전달
```powershell
# 압축 (PowerShell 5.0+)
Compress-Archive -Path . -DestinationPath ..\ai-trading-platform.zip
```

---

## 💻 STEP 3: 새 PC에서 설치

### 3.1 Node.js 설치 (5분)
```
1. https://nodejs.org 접속
2. LTS 버전 다운로드 → 설치
3. PC 재시작
```

### 3.2 프로젝트 압축 해제
```powershell
# 예: 바탕화면에 압축 해제
cd C:\Users\[사용자명]\Desktop
Expand-Archive -Path ai-trading-platform.zip -DestinationPath .
cd ai-trading-platform
```

### 3.3 패키지 설치 (5분)
```powershell
# 모든 패키지 자동 설치 (package.json 기반)
npm install
```

**진행 표시:**
```
⸨⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⠂⸩ ⠧ idealTree:ai-trading-platform: sill idealTree buildDeps
```

### 3.4 환경변수 생성 (30초)
```powershell
# .env.local 파일 생성
@"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=10000
"@ | Out-File -FilePath .env.local -Encoding UTF8

# 확인
Get-Content .env.local
```

### 3.5 실행 (10초)
```powershell
npm run dev
```

### 3.6 브라우저 확인
```
http://localhost:3000
```

---

## ✅ 체크포인트

### STEP 1 완료 후
- [ ] node_modules 폴더 없음
- [ ] .next 폴더 없음  
- [ ] package.json 있음 ⭐

### STEP 3.3 완료 후
- [ ] node_modules 폴더 생성됨
- [ ] "added XXX packages" 메시지 확인

### STEP 3.5 완료 후
- [ ] "Ready in XXs" 메시지 확인
- [ ] http://localhost:3000 주소 표시

---

## 🚨 자주 하는 실수

### ❌ 실수 1: package.json 삭제
**결과**: npm install 불가능
**해결**: 원본에서 package.json 복사

### ❌ 실수 2: PowerShell 대신 CMD 사용
**결과**: Remove-Item 명령어 오류
**해결**: PowerShell 사용 또는 CMD 명령어로 변경

### ❌ 실수 3: Node.js 미설치
**결과**: npm: command not found
**해결**: Node.js 설치 → PC 재시작

---

## 📊 용량 비교

| 단계 | 크기 |
|------|------|
| 원본 (node_modules 포함) | 650MB |
| **정리 후 (배포용)** | **15MB** |
| 압축 후 | 3MB |
| 새 PC 설치 후 | 650MB |

---

## ⚡ 빠른 실행 (전체 복사-붙여넣기)

### 배포 준비 (현재 PC)
```powershell
cd C:\SKN12-FINAL-2TEAM\base_server\frontend\ai-trading-platform
Remove-Item node_modules, .next, .env, .env.local -Recurse -Force -ErrorAction SilentlyContinue
Compress-Archive -Path . -DestinationPath ..\ai-trading-platform-deploy.zip
```

### 새 PC 설치
```powershell
# 압축 해제 후
npm install
@"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=10000
"@ | Out-File -FilePath .env.local -Encoding UTF8
npm run dev
```

---

## 📝 최종 확인

**필수 파일 (절대 삭제 금지):**
1. **package.json** - 패키지 목록
2. **next.config.mjs** - Next.js 설정
3. **tsconfig.json** - TypeScript 설정
4. **app/** - 모든 페이지
5. **components/** - UI 컴포넌트

**삭제 가능 (재생성됨):**
1. node_modules/ → `npm install`
2. .next/ → `npm run dev`
3. package-lock.json → `npm install`
4. .env.local → 수동 생성