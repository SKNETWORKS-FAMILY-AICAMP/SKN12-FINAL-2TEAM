# UML 다이어그램

이 폴더는 SKN12-FINAL-2TEAM 프로젝트의 프론트엔드 UML 다이어그램을 포함합니다.

## 📁 파일 구조

### 유스케이스 다이어그램
- `use-case-as-is.puml` - 현재 구현된 기능들
- `use-case-to-be.puml` - 향후 개선 계획

### 구조 다이어그램
- `package-structure.puml` - 패키지 의존 관계
- `component-diagram.puml` - 컴포넌트 관계

### 시퀀스 다이어그램
- `login-sequence.puml` - 로그인/인증 플로우
- `websocket-sequence.puml` - WebSocket 실시간 시세
- `chat-sse-sequence.puml` - AI 챗봇 SSE 스트리밍
- `tutorial-sequence.puml` - 튜토리얼 진행 플로우

### 상태 머신
- `state-machines.puml` - 주요 상태 머신들 (TypingMessage, WebSocket, Auth, Tutorial)

## 🔄 자동 렌더링

GitHub Actions를 통해 `.puml` 파일이 자동으로 `.svg` 파일로 렌더링됩니다.

### 워크플로우 트리거
- `docs/uml/` 폴더의 `.puml` 파일 변경 시
- 수동 실행 가능 (`workflow_dispatch`)

### 렌더링 결과
- 각 `.puml` 파일이 동일한 이름의 `.svg` 파일로 변환
- SVG 파일이 자동으로 커밋되어 GitHub에서 바로 표시

## 📝 사용법

### 마크다운에서 참조
```markdown
![다이어그램 제목](docs/uml/파일명.svg)
```

### 특정 상태 머신 참조
```markdown
![상태 머신](docs/uml/state-machines.svg#상태명)
```

## 🛠️ 로컬 개발

### PlantUML 설치
```bash
# macOS
brew install plantuml

# Ubuntu/Debian
sudo apt-get install plantuml graphviz
```

### 로컬 렌더링
```bash
# SVG로 렌더링
plantuml -tsvg docs/uml/*.puml

# PNG로 렌더링
plantuml -tpng docs/uml/*.puml
```

## 📋 다이어그램 추가 시

1. `.puml` 파일을 `docs/uml/` 폴더에 추가
2. 마크다운 문서에서 이미지 참조로 변경
3. GitHub에 푸시하면 자동으로 SVG 생성
4. 생성된 SVG가 자동으로 커밋됨

## 🔧 문제 해결

### SVG가 생성되지 않는 경우
- GitHub Actions 로그 확인
- PlantUML 문법 오류 체크
- 파일 확장자가 `.puml` 또는 `.plantuml`인지 확인

### 이미지가 표시되지 않는 경우
- SVG 파일이 `docs/uml/` 폴더에 존재하는지 확인
- 파일 경로가 올바른지 확인
- GitHub Actions가 성공적으로 실행되었는지 확인
