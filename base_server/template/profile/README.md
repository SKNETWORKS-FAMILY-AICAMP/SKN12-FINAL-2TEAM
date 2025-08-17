# 📁 Profile Template

## 📌 개요
Profile Template은 AI 기반 금융 거래 플랫폼의 사용자 프로필 관리 핵심 비즈니스 로직을 담당하는 템플릿입니다. 사용자 기본 정보, 알림 설정, 비밀번호 관리, 결제 플랜, API 키 관리 등 종합적인 프로필 기능을 제공합니다. Account Template과 연동하여 보안을 유지하면서 사용자 설정을 체계적으로 관리합니다.

## 🏗️ 구조
```
base_server/template/profile/
├── profile_template_impl.py              # 프로필 템플릿 구현체
├── common/                              # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── profile_model.py                 # 프로필 데이터 모델
│   ├── profile_protocol.py              # 프로필 프로토콜 정의
│   └── profile_serialize.py             # 프로필 직렬화 클래스
└── README.md                            
```

## 🔧 핵심 기능

### **ProfileTemplateImpl 클래스**
- **프로필 조회**: `on_profile_get_req()` - 사용자 프로필 설정 전체 조회
- **전체 프로필 업데이트**: `on_profile_update_all_req()` - 마이페이지에서 모든 설정을 한번에 저장 (트랜잭션 처리)
- **기본 프로필 업데이트**: `on_profile_update_basic_req()` - 닉네임, 이메일, 전화번호 업데이트
- **알림 설정 업데이트**: `on_profile_update_notification_req()` - 이메일, SMS, 푸시, 알림 종류별 설정
- **비밀번호 변경**: `on_profile_change_password_req()` - 현재 비밀번호 검증 후 새 비밀번호 설정
- **결제 플랜 조회**: `on_profile_get_payment_plan_req()` - 현재 플랜 정보 및 만료일 조회
- **결제 플랜 변경**: `on_profile_change_plan_req()` - 플랜 업그레이드/다운그레이드 (결제 처리)
- **API 키 저장**: `on_profile_save_api_keys_req()` - 한국투자증권, Alpha Vantage, Polygon, Finnhub API 키 저장
- **API 키 조회**: `on_profile_get_api_keys_req()` - 저장된 API 키 조회 (시크릿 키 마스킹)

### **보안 유틸리티 메서드**
- **`_hash_password()`**: bcrypt를 사용한 비밀번호 해싱 (Account Template과 동일)
- **`_verify_password()`**: 비밀번호 검증 (SHA-256 레거시 호환성 포함)
- **`_mask_secret()`**: API 시크릿 키 마스킹 (앞4자리****뒤4자리)

### **데이터 모델**
- **ProfileSettings**: 기본 프로필, 알림 설정, 결제 정보를 포함한 통합 프로필 설정
- **ApiKeyInfo**: 다양한 금융 API 키 정보 (시크릿 키는 마스킹)
- **PaymentPlanInfo**: 결제 플랜 정보 (플랜명, 가격, 만료일, 자동갱신)

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 글로벌 DB 연동 및 저장 프로시저 호출 (call_global_procedure, execute_global_query)
- **SecurityService**: SecurityUtils를 통한 비밀번호 해싱 및 검증

### **연동 방식 설명**
1. **데이터베이스 연동** → ServiceContainer.get_database_service()로 DatabaseService 획득, fp_get_user_profile_settings, fp_update_profile_all, fp_update_basic_profile, fp_update_notification_settings, fp_change_password, fp_get_payment_plan, fp_save_api_keys, fp_get_api_keys 프로시저 호출
2. **보안 연동** → SecurityUtils.hash_password(), SecurityUtils.verify_password()를 통한 비밀번호 해싱 및 검증
3. **세션 관리** → client_session.session.account_db_key를 통한 사용자 식별

## 📊 데이터 흐름

### **프로필 조회 플로우**
```
1. 프로필 조회 요청
   ↓
2. fp_get_user_profile_settings 프로시저 호출 (account_db_key)
   ↓
3. 프로필 데이터 파싱 및 ProfileSettings 모델 생성
   ↓
4. ProfileGetResponse 반환
```

### **전체 프로필 업데이트 플로우**
```
1. 전체 프로필 업데이트 요청
   ↓
2. fp_update_profile_all 프로시저 호출 (트랜잭션으로 한번에 처리)
   ↓
3. 업데이트 결과 확인 (비밀번호 변경, API 키 저장 여부)
   ↓
4. 업데이트된 프로필 재조회
   ↓
5. ProfileUpdateAllResponse 반환 (재로그인 필요 여부 포함)
```

### **비밀번호 변경 플로우**
```
1. 비밀번호 변경 요청
   ↓
2. table_accountid에서 현재 저장된 비밀번호 해시 조회
   ↓
3. 현재 비밀번호 검증 (_verify_password)
   ↓
4. 새 비밀번호 해싱 (_hash_password)
   ↓
5. fp_change_password 프로시저 호출
   ↓
6. ProfileChangePasswordResponse 반환 (재로그인 필요)
```

### **결제 플랜 변경 플로우**
```
1. 플랜 변경 요청
   ↓
2. 현재 플랜 조회 (fp_get_payment_plan)
   ↓
3. FREE 플랜 다운그레이드 시 즉시 변경
   ↓
4. 유료 플랜 업그레이드 시 결제 URL 생성 (임시)
   ↓
5. ProfileChangePlanResponse 반환 (결제 필요 여부 포함)
```

### **API 키 관리 플로우**
```
1. API 키 저장 요청
   ↓
2. fp_save_api_keys 프로시저 호출 (다양한 API 키들)
   ↓
3. 저장 결과 확인
   ↓
4. ProfileSaveApiKeysResponse 반환
```

## 🚀 사용 예제

### **프로필 조회 예제**
```python
async def on_profile_get_req(self, client_session, request: ProfileGetRequest):
    """프로필 설정 조회"""
    response = ProfileGetResponse()
    
    try:
        account_db_key = client_session.session.account_db_key
        
        db_service = ServiceContainer.get_database_service()
        
        # 프로필 설정 조회 (Global DB)
        profile_result = await db_service.call_global_procedure(
            "fp_get_user_profile_settings",
            (account_db_key,)
        )
        
        if not profile_result:
            response.errorCode = 9001
            response.profile = None
            return response
        
        profile_data = profile_result[0]
        
        # ProfileSettings 객체 생성
        response.profile = ProfileSettings(
            account_id=profile_data.get('account_id', ''),
            nickname=profile_data.get('nickname', ''),
            email=profile_data.get('email', ''),
            phone_number=profile_data.get('phone_number'),
            email_verified=bool(profile_data.get('email_verified', False)),
            phone_verified=bool(profile_data.get('phone_verified', False)),
            email_notifications_enabled=bool(profile_data.get('email_notifications_enabled', True)),
            sms_notifications_enabled=bool(profile_data.get('sms_notifications_enabled', False)),
            push_notifications_enabled=bool(profile_data.get('push_notifications_enabled', True)),
            price_alert_enabled=bool(profile_data.get('price_alert_enabled', True)),
            news_alert_enabled=bool(profile_data.get('news_alert_enabled', True)),
            portfolio_alert_enabled=bool(profile_data.get('portfolio_alert_enabled', False)),
            trade_alert_enabled=bool(profile_data.get('trade_alert_enabled', True)),
            payment_plan=profile_data.get('payment_plan', 'FREE'),
            plan_expires_at=str(profile_data.get('plan_expires_at')) if profile_data.get('plan_expires_at') else None,
            created_at=str(profile_data.get('created_at', '')),
            updated_at=str(profile_data.get('updated_at', ''))
        )
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
        response.profile = None
        Logger.error(f"Profile get error: {e}")
    
    return response
```

### **전체 프로필 업데이트 예제**
```python
async def on_profile_update_all_req(self, client_session, request: ProfileUpdateAllRequest):
    """전체 프로필 설정 업데이트 (트랜잭션으로 한번에 처리)"""
    response = ProfileUpdateAllResponse()
    
    try:
        account_db_key = client_session.session.account_db_key
        db_service = ServiceContainer.get_database_service()
        
        # 통합 업데이트 프로시저 호출 (트랜잭션 처리)
        result = await db_service.call_global_procedure(
            "fp_update_profile_all",
            (
                account_db_key,
                # 기본 프로필
                request.nickname, request.email, request.phone_number,
                # 알림 설정
                request.email_notifications_enabled, request.sms_notifications_enabled,
                request.push_notifications_enabled, request.price_alert_enabled,
                request.news_alert_enabled, request.portfolio_alert_enabled,
                request.trade_alert_enabled,
                # 비밀번호 변경 (선택사항)
                request.current_password, request.new_password,
                # API 키 (선택사항)
                request.korea_investment_app_key, request.korea_investment_app_secret,
                request.alpha_vantage_key, request.polygon_key, request.finnhub_key
            )
        )
        
        if not result or result[0].get('result') != 'SUCCESS':
            response.errorCode = 9002
            response.message = result[0].get('message', '프로필 업데이트 실패') if result else '프로필 업데이트 실패'
            return response
        
        # 결과 정보 설정
        result_data = result[0]
        response.password_changed = bool(result_data.get('password_changed', False))
        response.api_keys_saved = bool(result_data.get('api_keys_saved', False))
        response.require_relogin = response.password_changed  # 비밀번호 변경 시 재로그인 필요
        
        response.message = "프로필 설정이 업데이트되었습니다"
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
        response.message = "프로필 설정 업데이트 실패"
        Logger.error(f"Profile update all error: {e}")
    
    return response
```

### **비밀번호 변경 예제**
```python
async def on_profile_change_password_req(self, client_session, request: ProfileChangePasswordRequest):
    """비밀번호 변경"""
    response = ProfileChangePasswordResponse()
    
    try:
        account_db_key = client_session.session.account_db_key
        db_service = ServiceContainer.get_database_service()
        
        # IP 주소 가져오기 (client_session에서 또는 기본값 사용)
        client_ip = getattr(client_session, 'ip_address', '127.0.0.1')
        
        # 현재 저장된 비밀번호 해시 조회
        password_query = "SELECT password_hash FROM table_accountid WHERE account_db_key = %s"
        password_result = await db_service.execute_global_query(password_query, (account_db_key,))
        
        if not password_result:
            response.errorCode = 9004
            response.message = "계정 정보를 찾을 수 없습니다"
            return response
        
        stored_hash = password_result[0].get('password_hash', '')
        
        # 현재 비밀번호 검증 (Account와 동일한 방식)
        if not self._verify_password(request.current_password, stored_hash):
            response.errorCode = 9004
            response.message = "현재 비밀번호가 일치하지 않습니다"
            return response
        
        # 새 비밀번호 해싱 (Account와 동일한 방식)
        new_password_hash = self._hash_password(request.new_password)
        
        # 비밀번호 변경
        result = await db_service.call_global_procedure(
            "fp_change_password",
            (account_db_key, new_password_hash, client_ip)
        )
        
        if not result or result[0].get('result') != 'SUCCESS':
            response.errorCode = 9004
            response.message = "비밀번호 변경 실패"
            return response
        
        response.message = "비밀번호가 변경되었습니다"
        response.require_relogin = True
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
        response.message = "비밀번호 변경 실패"
        Logger.error(f"Profile change password error: {e}")
    
    return response
```

### **보안 유틸리티 예제**
```python
def _hash_password(self, password: str) -> str:
    """패스워드 해시화 - bcrypt 사용 (Account와 동일)"""
    return SecurityUtils.hash_password(password)

def _verify_password(self, password: str, hashed_password: str) -> bool:
    """비밀번호 검증 (Account와 동일)"""
    # 기존 SHA-256 해시와의 호환성 검사
    if len(hashed_password) == 64:  # SHA-256 해시 길이
        legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
        return legacy_hash == hashed_password
    # bcrypt 검증
    return SecurityUtils.verify_password(password, hashed_password)

def _mask_secret(self, secret: str) -> str:
    """시크릿 키 마스킹"""
    if not secret or len(secret) < 8:
        return "****"
    return f"{secret[:4]}****{secret[-4:]}"
```

## ⚙️ 설정

### **데이터베이스 프로시저 설정**
- **fp_get_user_profile_settings**: 사용자 프로필 설정 조회 (account_db_key)
- **fp_update_profile_all**: 전체 프로필 설정 통합 업데이트 (트랜잭션 처리)
- **fp_update_basic_profile**: 기본 프로필 업데이트 (닉네임, 이메일, 전화번호)
- **fp_update_notification_settings**: 알림 설정 업데이트 (7개 알림 옵션)
- **fp_change_password**: 비밀번호 변경 (해시, IP 주소)
- **fp_get_payment_plan**: 결제 플랜 정보 조회
- **fp_save_api_keys**: API 키 저장 (5개 서비스)
- **fp_get_api_keys**: API 키 조회

### **보안 설정**
- **비밀번호 해싱**: bcrypt 사용 (Account Template과 동일)
- **레거시 호환성**: SHA-256 해시 길이(64) 감지 시 호환성 검증
- **시크릿 마스킹**: API 시크릿 키 앞4자리****뒤4자리

### **알림 설정 기본값**
- **이메일 알림**: 기본 활성화 (True)
- **SMS 알림**: 기본 비활성화 (False)
- **푸시 알림**: 기본 활성화 (True)
- **가격 알림**: 기본 활성화 (True)
- **뉴스 알림**: 기본 활성화 (True)
- **포트폴리오 알림**: 기본 비활성화 (False)
- **거래 알림**: 기본 활성화 (True)

### **결제 플랜 설정**
- **기본 플랜**: FREE
- **플랜 변경**: FREE 다운그레이드 시 즉시 변경, 유료 업그레이드 시 결제 필요
- **결제 URL**: 임시 URL 생성 (실제 PG사 연동 미구현)

### **API 키 관리 설정**
- **지원 서비스**: 한국투자증권, Alpha Vantage, Polygon, Finnhub
- **시크릿 마스킹**: 8자리 미만 시 "****", 8자리 이상 시 "앞4자리****뒤4자리"

## 🔗 연관 폴더

### **의존성 관계**
- **`service.db.database_service`**: DatabaseService - 글로벌 DB 연동 및 저장 프로시저 호출
- **`service.security.security_utils`**: SecurityUtils - 비밀번호 해싱 및 검증

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 상속
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리

### **계정 시스템 연관**
- **`template.account.account_template`**: AccountTemplate - 비밀번호 해싱 방식 동일, 계정 정보 조회
- **`table_accountid`**: 비밀번호 해시 조회를 위한 글로벌 DB 테이블

---
