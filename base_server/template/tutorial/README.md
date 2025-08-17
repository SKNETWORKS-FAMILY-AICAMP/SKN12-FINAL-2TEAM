# 📁 Tutorial Template

## 📌 개요
Tutorial Template은 AI 기반 금융 거래 플랫폼의 사용자 튜토리얼 진행 상태 관리 핵심 비즈니스 로직을 담당하는 템플릿입니다. 사용자가 플랫폼의 다양한 기능을 단계별로 학습할 수 있도록 진행 상태를 추적하고 저장합니다. tutorial_type별로 개별 로우를 유지하며, GREATEST 함수를 통해 스텝 역행을 방지하는 안전한 진행 상태 관리 시스템을 제공합니다.

## 🏗️ 구조
```
base_server/template/tutorial/
├── tutorial_template_impl.py              # 튜토리얼 템플릿 구현체
├── common/                               # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── tutorial_model.py                 # 튜토리얼 데이터 모델
│   ├── tutorial_protocol.py              # 튜토리얼 프로토콜 정의
│   └── tutorial_serialize.py             # 튜토리얼 직렬화 클래스
└── README.md                            
```

## 🔧 핵심 기능

### **TutorialTemplateImpl 클래스**
- **튜토리얼 초기화**: `init(config)` - 템플릿 초기화 및 로깅
- **데이터 로딩**: `on_load_data(config)` - 튜토리얼 데이터 로딩 (현재 미구현)
- **스텝 완료 저장**: `on_tutorial_complete_step_req()` - 튜토리얼 스텝 완료 상태 저장 (UPSERT 방식)
- **진행 상태 조회**: `on_tutorial_get_progress_req()` - 사용자의 모든 튜토리얼 타입별 진행 상태 조회

### **핵심 비즈니스 로직**
- **스텝 역행 방지**: GREATEST 함수를 사용하여 이전 스텝으로 되돌아가는 것을 방지
- **tutorial_type별 개별 관리**: OVERVIEW, PORTFOLIO, SIGNALS, CHAT, SETTINGS 등 각 튜토리얼 타입별로 독립적인 진행 상태 관리
- **샤드 DB 연동**: 사용자별로 적절한 샤드 DB에 진행 상태 저장
- **에러 처리**: 입력값 검증, DB 오류 처리, 상세한 로깅

### **데이터 모델**
- **TutorialProgress**: 튜토리얼 진행 상태 (tutorial_type, completed_step, updated_at)
- **TutorialCompleteStepRequest**: 스텝 완료 요청 (tutorial_type, step_number)
- **TutorialGetProgressRequest**: 진행 상태 조회 요청 (세션 기반 사용자 정보)
- **TutorialCompleteStepResponse**: 스텝 완료 응답
- **TutorialGetProgressResponse**: 진행 상태 응답 (progress_list 포함)

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출 (call_shard_procedure)

### **연동 방식 설명**
1. **데이터베이스 연동** → ServiceContainer.get_database_service()로 DatabaseService 획득, fp_tutorial_complete_step, fp_tutorial_get_progress 프로시저 호출
2. **샤드 DB 선택** → client_session.session.shard_id를 통한 사용자별 샤드 DB 선택
3. **세션 관리** → client_session.session.account_db_key를 통한 사용자 식별

## 📊 데이터 흐름

### **튜토리얼 스텝 완료 플로우**
```
1. 스텝 완료 요청 (tutorial_type, step_number)
   ↓
2. 입력값 검증 (tutorial_type 존재, step_number >= 0)
   ↓
3. 사용자 정보 추출 (account_db_key, shard_id)
   ↓
4. fp_tutorial_complete_step 프로시저 호출 (UPSERT 방식)
   ↓
5. 결과 확인 및 응답 반환
   ↓
6. 로깅 (성공/실패)
```

### **튜토리얼 진행 상태 조회 플로우**
```
1. 진행 상태 조회 요청
   ↓
2. 사용자 검증 (account_db_key > 0)
   ↓
3. fp_tutorial_get_progress 프로시저 호출
   ↓
4. 모든 튜토리얼 타입별 진행 상태 파싱
   ↓
5. TutorialProgress 객체 리스트 생성
   ↓
6. TutorialGetProgressResponse 반환
```

### **데이터베이스 스키마**
- **테이블**: `table_tutorial_progress` (샤드 DB)
- **구조**: account_db_key, tutorial_type, completed_step, created_at, updated_at
- **인덱스**: (account_db_key, tutorial_type) 복합 PK, account_db_key, tutorial_type, updated_at

## 🚀 사용 예제

### **튜토리얼 스텝 완료 예제**
```python
async def on_tutorial_complete_step_req(self, client_session, request: TutorialCompleteStepRequest):
    """튜토리얼 스텝 완료 저장"""
    response = TutorialCompleteStepResponse()
    response.sequence = request.sequence
    
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        
        # 입력값 검증
        if not request.tutorial_type or request.step_number < 0:
            response.errorCode = 400
            Logger.error(f"Invalid tutorial request: type='{request.tutorial_type}', step={request.step_number}")
            return response
        
        # DB에 튜토리얼 상태 저장 (UPSERT 방식)
        database_service = ServiceContainer.get_database_service()
        result = await database_service.call_shard_procedure(
            shard_id,
            'fp_tutorial_complete_step',
            (account_db_key, request.tutorial_type, request.step_number)
        )
        
        if result and result[0].get('result') == 'SUCCESS':
            response.errorCode = 0
            Logger.info(f"Tutorial progress updated: user={account_db_key}, type='{request.tutorial_type}', step={request.step_number}")
        else:
            response.errorCode = 500
            Logger.error(f"Tutorial step save failed: {result}")
        
    except Exception as e:
        response.errorCode = 500
        Logger.error(f"Tutorial step complete error: {e}")
    
    return response
```

### **튜토리얼 진행 상태 조회 예제**
```python
async def on_tutorial_get_progress_req(self, client_session, request: TutorialGetProgressRequest):
    """튜토리얼 진행 상태 조회"""
    response = TutorialGetProgressResponse()
    response.sequence = request.sequence
    
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        
        # 사용자 검증
        if account_db_key <= 0:
            response.errorCode = 400
            response.progress_list = []
            Logger.error(f"Invalid account_db_key: {account_db_key}")
            return response
        
        database_service = ServiceContainer.get_database_service()
        result = await database_service.call_shard_procedure(
            shard_id,
            'fp_tutorial_get_progress',
            (account_db_key,)
        )
        
        # 사용자의 모든 튜토리얼 상태 반환
        progress_list = []
        if result and len(result) > 0:
            for row in result:
                progress = TutorialProgress(
                    tutorial_type=row.get('tutorial_type', ''),
                    completed_step=row.get('completed_step', 0),
                    updated_at=str(row.get('updated_at', ''))
                )
                progress_list.append(progress)
            Logger.debug(f"Tutorial progress found: user={account_db_key}, count={len(progress_list)}")
        else:
            Logger.debug(f"No tutorial progress found for user: {account_db_key}")
        
        response.progress_list = progress_list
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 500
        response.progress_list = []
        Logger.error(f"Tutorial get progress error: {e}")
    
    return response
```

### **프론트엔드 연동 예제**
```typescript
// use-tutorial.ts 훅에서 백엔드 연동
const completeStep = useCallback(async (tutorialType: string, stepNumber: number) => {
  try {
    const response = await fetch('/complete/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tutorial_type: tutorialType, step_number: stepNumber })
    });
    
    if (response.ok) {
      console.log('✅ Tutorial step completed:', stepNumber);
      return true;
    } else {
      console.error('❌ Tutorial step completion failed');
      return false;
    }
  } catch (error) {
      console.error('❌ Tutorial step completion error:', error);
      return false;
  }
}, []);
```

## ⚙️ 설정

### **데이터베이스 프로시저 설정**
- **fp_tutorial_complete_step**: 튜토리얼 스텝 완료 저장 (account_db_key, tutorial_type, step_number)
- **fp_tutorial_get_progress**: 사용자의 모든 튜토리얼 진행 상태 조회 (account_db_key)

### **데이터베이스 테이블 설정**
- **테이블명**: `table_tutorial_progress`
- **샤드 DB**: finance_shard_1, finance_shard_2
- **스키마**: account_db_key (BIGINT), tutorial_type (VARCHAR(50)), completed_step (INT), created_at (DATETIME), updated_at (DATETIME)
- **인덱스**: 복합 PK (account_db_key, tutorial_type), 단일 인덱스 (account_db_key, tutorial_type, updated_at)

### **튜토리얼 타입 설정**
- **지원 타입**: OVERVIEW, PORTFOLIO, SIGNALS, CHAT, SETTINGS
- **스텝 번호**: 0 (시작 안함), N (N번째 스텝까지 완료)
- **진행 상태**: tutorial_type별로 개별 로우 유지

### **에러 코드 설정**
- **400**: 잘못된 요청 (tutorial_type 누락, step_number < 0)
- **500**: 서버 오류 (DB 저장 실패, 예외 발생)
- **0**: 성공

### **로깅 설정**
- **정보 로그**: 템플릿 초기화, 스텝 완료 성공
- **에러 로그**: 초기화 실패, 입력값 검증 실패, DB 저장 실패, 예외 발생
- **디버그 로그**: 진행 상태 조회 결과

## 🔗 연관 폴더

### **의존성 관계**
- **`service.db.database_service`**: DatabaseService - 샤드 DB 연동 및 저장 프로시저 호출
- **`service.core.logger`**: Logger - 로깅 서비스

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 상속
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리

### **API 라우터 연관**
- **`application.base_web_server.routers.tutorial`**: TutorialRouter - 튜토리얼 API 엔드포인트
- **`/complete/step`**: 스텝 완료 API
- **`/progress`**: 진행 상태 조회 API

### **프론트엔드 연관**
- **`frontend.ai-trading-platform.hooks.use-tutorial`**: 튜토리얼 상태 관리 훅
- **프론트엔드 상태 관리**: 즉시 업데이트로 사용자 경험 향상
- **백그라운드 저장**: 백엔드 저장 실패 시에도 프론트엔드는 정상 작동

### **데이터베이스 스크립트 연관**
- **`db_scripts.extend_finance_shard_tutorial.sql`**: 튜토리얼 테이블 및 프로시저 생성 스크립트
- **샤드 DB 설정**: finance_shard_1, finance_shard_2에 동일한 스키마 적용

---
