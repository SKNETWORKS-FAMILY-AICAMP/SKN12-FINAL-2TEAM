# 📁 Account Template

## 📌 개요
Account Template은 사용자 인증, 회원가입, 프로필 관리, API 키 관리 등 계정 관련 모든 기능을 담당하는 시스템입니다. Global DB와 Shard DB를 연동하여 사용자 계정 정보를 관리하고, 보안 인증(OTP, 이메일 인증) 및 투자 프로필 설정을 지원합니다.

## 🏗️ 구조
```
base_server/template/account/
├── account_template_impl.py          # 계정 템플릿 구현체
├── common/                           # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── account_model.py             # 계정 데이터 모델
│   ├── account_protocol.py          # 계정 프로토콜 정의
│   └── account_serialize.py         # 계정 직렬화 클래스
└── README.md                        
```

## 🔧 핵심 기능

### **AccountTemplateImpl 클래스**
- **사용자 인증**: `on_account_login_req()` - 로그인 처리 및 샤드 자동 할당
- **회원가입**: `on_account_signup_req()` - 신규 사용자 등록 및 기본 정보 설정
- **로그아웃**: `on_account_logout_req()` - 세션 종료 및 로그아웃 처리
- **계정 정보**: `on_account_info_req()` - 사용자 계정 정보 조회
- **프로필 관리**: `on_account_profile_setup_req()`, `on_account_profile_get_req()`, `on_account_profile_update_req()` - 투자 프로필 설정/조회/수정
- **이메일 인증**: `on_account_email_verify_req()`, `on_account_email_confirm_req()` - 이메일 인증 코드 전송/확인
- **OTP 인증**: `on_account_otp_setup_req()`, `on_account_otp_verify_req()`, `on_account_otp_login_req()` - 2단계 인증
- **API 키 관리**: `on_account_api_keys_save_req()` - 외부 API 키 저장 및 관리
- **토큰 관리**: `on_account_token_refresh_req()`, `on_account_token_validate_req()` - 액세스 토큰 갱신/검증
- **템플릿 생명주기**: `on_load_data()` - 템플릿 데이터 로딩, `on_client_create()` - 신규 클라이언트 생성, `on_client_update()` - 클라이언트 업데이트

### **주요 메서드**
- `on_account_login_req()`: 플랫폼별 로그인 처리, 샤드 자동 할당, 계정 상태 검증
- `on_account_signup_req()`: 회원가입 처리, 비밀번호 해시화, 기본 정보 저장
- `on_account_profile_setup_req()`: 투자 경험, 위험 성향, 투자 목표, 월 예산 설정
- `on_account_profile_get_req()`: 사용자 프로필 정보 조회 및 반환
- `on_account_profile_update_req()`: 기존 프로필 정보 수정 및 업데이트
- `on_account_api_keys_save_req()`: 한국투자증권 앱키/시크릿, Alpha Vantage, Polygon, Finnhub API 키 저장
- `_initialize_user_portfolio_in_shard()`: 프로필 설정 완료 시 샤드 DB에 포트폴리오 초기화
- `_hash_password()`, `_verify_password()`: bcrypt 기반 비밀번호 해시화 및 검증

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: Global DB 및 Shard DB 연동, 저장 프로시저 호출
- **CacheService**: 세션 정보 캐싱 및 사용자 상태 관리
- **SecurityUtils**: 비밀번호 해시화, SHA-256 호환성 검증
- **DataTableManager**: 아이템 테이블 접근 및 초기 아이템 지급

### **연동 방식 설명**
1. **인증 처리** → DatabaseService를 통한 사용자 정보 조회 및 검증
2. **샤드 관리** → Global DB에서 샤드 정보 조회 및 자동 할당
3. **프로필 관리** → Global DB에 투자 프로필 저장, Shard DB에 포트폴리오 초기화
4. **보안 처리** → SecurityUtils를 통한 비밀번호 해시화 및 검증
5. **세션 관리** → CacheService를 통한 사용자 세션 상태 관리
6. **데이터 검증** → DataTableManager를 통한 초기 아이템 지급 및 검증

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 로그인 요청 (Request)
   ↓
2. AccountTemplateImpl.on_account_login_req()
   ↓
3. DatabaseService.execute_global_query() - 사용자 정보 조회
   ↓
4. 계정 상태 확인 (Normal 상태 검증)
   ↓
5. 비밀번호 검증 (self._verify_password)
   ↓
6. 샤드 정보 조회 및 자동 할당
   ↓
7. 로그인 시간 업데이트 및 성공 응답 (Response)
```

### **회원가입 및 프로필 설정 플로우**
```
1. 회원가입 요청
   ↓
2. 비밀번호 해시화 (self._hash_password)
   ↓
3. Global DB에 사용자 정보 저장 (fp_user_signup)
   ↓
4. 프로필 설정 요청
   ↓
5. 투자 프로필 정보 저장 (fp_profile_setup)
   ↓
6. Shard DB에 포트폴리오 초기화 (_initialize_user_portfolio_in_shard)
   ↓
7. 프로필 설정 완료 응답
```

### **샤드 DB 연동 플로우**
```
1. 사용자 계정 정보 조회
   ↓
2. Global DB에서 샤드 매핑 정보 확인
   ↓
3. 샤드 정보가 없으면 자동 할당 (account_db_key % active_count + 1)
   ↓
4. Shard DB에 계좌 생성 (fp_create_account)
   ↓
5. 포트폴리오 테이블에 초기 현금 설정
   ↓
6. 샤드별 데이터 접근 준비 완료
```

## 🚀 사용 예제

### **로그인 처리 예제**
```python
# 로그인 요청 처리
async def on_account_login_req(self, client_session, request: AccountLoginRequest):
    """로그인 요청 처리"""
    response = AccountLoginResponse()
    response.sequence = request.sequence
    
    try:
        db_service = ServiceContainer.get_database_service()
        
        # 1. 사용자 정보 및 프로필 완료 상태 조회
        user_query = """
        SELECT a.account_db_key, a.password_hash, a.nickname, a.account_level, a.account_status,
               COALESCE(p.profile_completed, 0) as profile_completed
        FROM table_accountid a
        LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
        WHERE a.platform_type = %s AND a.account_id = %s
        """
        user_result = await db_service.execute_global_query(user_query, (request.platform_type, request.account_id))
        
        # 2. 계정 상태 확인
        if user_result[0].get('account_status') != 'Normal':
            response.errorCode = 1003  # 계정 블록
            return response
        
        # 3. 비밀번호 검증
        stored_hash = user_result[0].get('password_hash', '')
        if not self._verify_password(request.password, stored_hash):
            response.errorCode = 1001  # 로그인 실패
            return response
        
        # 4. 샤드 정보 조회 및 자동 할당
        account_db_key = user_result[0].get('account_db_key')
        # 샤드 정보 조회 및 자동 할당 로직은 on_account_login_req 메서드 내부에 직접 구현됨
        shard_id = 1  # 기본값 (실제로는 샤드 할당 로직 수행)
        
        # 5. 성공 응답 설정
        response.errorCode = 0
        response.nickname = user_result[0].get('nickname', '')
        response.profile_completed = bool(user_result[0].get('profile_completed', 0))
        
    except Exception as e:
        response.errorCode = 1000  # 서버 오류
        Logger.error(f"Login error: {e}")
    
    return response
```

### **프로필 설정 예제**
```python
# 프로필 설정 요청 처리
async def on_account_profile_setup_req(self, client_session, request: AccountProfileSetupRequest):
    """프로필 설정"""
    response = AccountProfileSetupResponse()
    response.sequence = request.sequence
    
    try:
        # 1. 세션에서 사용자 정보 가져오기
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        
        # 2. 입력값 검증
        if not all([request.investment_experience, request.risk_tolerance, 
                   request.investment_goal]) or request.monthly_budget < 0:
            response.errorCode = 2004
            response.message = "필수 입력값이 누락되었거나 잘못되었습니다"
            return response
        
        db_service = ServiceContainer.get_database_service()
        
        # 3. DB에 프로필 정보 저장
        profile_result = await db_service.call_global_procedure(
            "fp_profile_setup",
            (account_db_key, request.investment_experience, request.risk_tolerance, 
             request.investment_goal, request.monthly_budget)
        )
        
        # 4. 포트폴리오 초기화
        shard_id = getattr(client_session.session, 'shard_id', 1)
        await self._initialize_user_portfolio_in_shard(db_service, account_db_key, shard_id, request.monthly_budget)
        
        response.errorCode = 0
        response.message = "프로필 설정 완료"
        response.next_step = "TUTORIAL"
        
    except Exception as e:
        response.errorCode = 1000
        response.message = "프로필 설정 중 오류가 발생했습니다"
        Logger.error(f"Profile setup error: {e}")
    
    return response
```

## ⚙️ 설정

### 1. 필수 서비스 (ServiceContainer)
- **DatabaseService**  
  - 글로벌/샤드 DB 연결이 정상이어야 합니다.  
  - 사용되는 프로시저/쿼리:
    - `fp_user_signup`, `fp_user_logout`, `fp_get_account_info`, `fp_create_account`, `fp_profile_setup`, `fp_profile_get`
    - `SELECT ... FROM table_accountid / table_user_profiles / table_user_shard_mapping / table_shard_config`
- **CacheService (Redis)**  
  - 이메일 인증코드/인증완료 플래그를 저장·조회합니다.

> 구현상 별도의 JWT/SMTP 환경변수는 **직접 사용되지 않습니다.**  
> (이메일은 현재 **코드 생성·저장 및 로그 출력**까지만 구현되어 있으며 실제 발송은 미구현)

---

### 2. Redis 키 & TTL (구현값)
- **이메일 인증코드**  
  - Key: `email_verify:{email}`  
  - Value: 6자리 코드(문자열)  
  - TTL: **300초**
- **이메일 인증 완료 플래그**  
  - Key: `email_verified:{email}`  
  - Value: `"true"`  
  - TTL: **3600초**

---

### 3. DB 의존 객체 (테이블/프로시저)
- **글로벌 DB**
  - `table_accountid`, `table_user_profiles`, `table_user_shard_mapping`, `table_shard_config`, `table_user_api_keys`
  - 프로시저:  
    - `fp_user_signup(platform_type, account_id, password_hash, email, nickname, birth_y, birth_m, birth_d, gender)`  
    - `fp_user_logout(account_db_key)`  
    - `fp_profile_setup(account_db_key, investment_experience, risk_tolerance, investment_goal, monthly_budget)`  
    - `fp_profile_get(account_db_key)`
- **샤드 DB**
  - `table_user_accounts`, `table_user_portfolios`  
  - 프로시저:  
    - `fp_get_account_info(account_db_key)`  
    - `fp_create_account(account_db_key, account_type)`

---

### 4. 보안/암호 (구현 기준)
- **비밀번호 해시**: `SecurityUtils.hash_password()` 사용 (bcrypt)  
  - 레거시 호환: 저장 해시 길이가 64인 경우 **SHA-256 호환 검증** 분기
- **OTP**: 예시용 **고정 시크릿 키**로 QR URL 생성 (실제 검증/발송은 미구현)  
  - `otpauth://totp/Investment Platform:{account_id}?secret={SECRET}&issuer=Investment Platform`

---

### 5. 기타 동작 상수/로직
- **회원가입 결과 처리**: `SUCCESS` / `DUPLICATE_ID` 분기 처리
- **샤드 자동할당**: `table_user_shard_mapping`에 없으면  
  - `table_shard_config`의 `active` 개수 기반으로 `shard_id = (account_db_key % active_count) + 1` 계산 후 매핑 저장
- **포트폴리오 초기화**: 프로필 설정 완료 시 샤드 DB에 계정/현금 포지션 초기화  
  - 초기 현금: `max(monthly_budget * 12, 1000000.0)`

---

### 6. 설정 체크리스트
- [ ] Redis 연결 (인증코드 키 TTL 동작 확인)  
- [ ] 글로벌/샤드 DB 연결 및 **필수 테이블/프로시저 배포**  
- [ ] `SecurityUtils`(bcrypt) 사용 가능 여부  
- [ ] 이메일 발송이 필요한 경우: **별도 SMTP 연동 구현 필요(현재 미구현)**

## 🔗 연관 폴더

### **의존성 관계**
- **`service.service_container`**: ServiceContainer - 서비스 컨테이너 및 DatabaseService 접근
- **`service.cache.cache_service`**: CacheService - 사용자 세션 정보 캐싱 및 상태 관리
- **`service.security.security_utils`**: SecurityUtils - 비밀번호 해시화, 보안 유틸리티
- **`service.data.data_table_manager`**: DataTableManager - 데이터 테이블 관리 및 초기 아이템 지급

### **기본 템플릿 연관**
- **`template.base.template.account_template`**: AccountTemplate - 계정 템플릿 기본 클래스
- **`template.base.template_context`**: TemplateContext - 템플릿 컨텍스트 관리
- **`template.base.template_type`**: TemplateType - 템플릿 타입 정의

---
