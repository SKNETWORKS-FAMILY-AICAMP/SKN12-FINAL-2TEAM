# AI Trading Platform — Security Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Security 서비스입니다. 비밀번호 해싱, 토큰 생성, 보안 검증을 담당하는 정적 클래스 시스템입니다. bcrypt를 사용한 안전한 비밀번호 관리와 보안 토큰 생성을 제공합니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
security/
├── __init__.py                    # 패키지 초기화
└── security_utils.py              # 보안 유틸리티 클래스 (정적 메서드)
```

---

## 🔧 핵심 기능

### 1. **비밀번호 보안 (Password Security)**
- **bcrypt 해싱**: `hash_password()` 메서드로 안전한 비밀번호 해싱 (12 rounds)
- **비밀번호 검증**: `verify_password()` 메서드로 해시된 비밀번호 검증
- **레거시 호환성**: `hash_for_legacy_compatibility()` 메서드로 SHA-256 호환성 지원
- **강도 검증**: `validate_password_strength()` 메서드로 비밀번호 복잡도 검증

### 2. **토큰 생성 (Token Generation)**
- **보안 토큰**: `generate_secure_token()` 메서드로 안전한 URL-safe 토큰 생성
- **세션 토큰**: `generate_session_token()` 메서드로 32자 세션 토큰 생성
- **cryptographically secure**: `secrets` 모듈을 사용한 암호학적 안전성

### 3. **보안 검증 (Security Validation)**
- **비밀번호 정책**: 최소 8자, 대문자/소문자/숫자/특수문자 포함
- **에러 처리**: 예외 상황에서 안전한 실패 처리

---

## 📚 사용된 라이브러리

### **보안 & 암호화**
- **bcrypt**: 안전한 비밀번호 해싱 (12 rounds)
- **secrets**: 암호학적으로 안전한 토큰 생성
- **hashlib**: SHA-256 해시 (레거시 호환성)

### **개발 도구**
- **typing**: 타입 힌트 및 타입 안전성 (Optional 사용)

---

## 🪝 핵심 클래스 및 메서드

### **SecurityUtils - 보안 유틸리티 클래스**

```python
class SecurityUtils:
    """보안 관련 유틸리티 클래스 (정적 메서드)"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """bcrypt를 사용한 안전한 비밀번호 해싱"""
        # 12 rounds의 salt로 비밀번호 해싱
        # UTF-8 인코딩 지원
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        # bcrypt 검증 및 예외 처리
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """안전한 토큰 생성"""
        # secrets.token_urlsafe 사용
    
    @staticmethod
    def generate_session_token() -> str:
        """세션 토큰 생성"""
        # 32자 URL-safe 토큰
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """비밀번호 강도 검증"""
        # 복잡도 요구사항 검증
    
    @staticmethod
    def hash_for_legacy_compatibility(password: str) -> str:
        """기존 SHA-256 해싱과의 호환성"""
        # 마이그레이션 지원
```

**동작 방식**:
- 모든 메서드가 정적 메서드로 구현
- 인스턴스 생성 없이 직접 호출 가능
- bcrypt를 통한 안전한 비밀번호 관리
- 레거시 시스템과의 호환성 보장

---

## 🌐 API 연동 방식

### **비밀번호 해싱 및 검증**

```python
from service.security.security_utils import SecurityUtils

# 비밀번호 해싱
password = "MySecurePassword123!"
hashed_password = SecurityUtils.hash_password(password)
# 결과: bcrypt 해시된 문자열

# 비밀번호 검증
is_valid = SecurityUtils.verify_password(password, hashed_password)
# 결과: True/False

# 레거시 SHA-256 호환성
legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
# 결과: SHA-256 해시 문자열
```

### **토큰 생성**

```python
# 보안 토큰 생성
secure_token = SecurityUtils.generate_secure_token(64)
# 결과: 64자 URL-safe 토큰

# 세션 토큰 생성
session_token = SecurityUtils.generate_session_token()
# 결과: 32자 세션 토큰
```

### **비밀번호 강도 검증**

```python
# 비밀번호 강도 검증
is_strong, message = SecurityUtils.validate_password_strength("WeakPass")
# 결과: (False, "비밀번호는 대문자, 소문자, 숫자, 특수문자를 모두 포함해야 합니다")

is_strong, message = SecurityUtils.validate_password_strength("StrongPass123!")
# 결과: (True, "안전한 비밀번호입니다")
```

---

## 🔄 보안 서비스 전체 흐름

### **1. 비밀번호 해싱 플로우**
```
1. 사용자 비밀번호 입력
2. bcrypt.gensalt(rounds=12)로 salt 생성
3. bcrypt.hashpw()로 비밀번호 해싱
4. UTF-8 디코딩하여 문자열 반환
5. 데이터베이스에 해시된 비밀번호 저장
```

### **2. 비밀번호 검증 플로우**
```
1. 사용자 입력 비밀번호와 저장된 해시
2. bcrypt.checkpw()로 비밀번호 검증
3. 예외 발생 시 False 반환
4. 검증 결과 반환 (True/False)
```

### **3. 토큰 생성 플로우**
```
1. 토큰 길이 설정 (기본값: 32)
2. secrets.token_urlsafe() 호출
3. 암호학적으로 안전한 랜덤 바이트 생성
4. URL-safe base64 인코딩
5. 안전한 토큰 문자열 반환
```

---

## 🔌 보안 시스템 구현 상세

### **bcrypt 비밀번호 해싱**

```python
@staticmethod
def hash_password(password: str) -> str:
    """bcrypt를 사용한 안전한 비밀번호 해싱"""
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds의 salt
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
```

**보안 특징**:
- **12 rounds**: 계산 비용과 보안성의 균형
- **자동 salt**: 매번 다른 salt로 동일 비밀번호도 다른 해시
- **UTF-8 지원**: 다국어 비밀번호 지원

### **비밀번호 강도 검증**

```python
@staticmethod
def validate_password_strength(password: str) -> tuple[bool, str]:
    """비밀번호 강도 검증"""
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        return False, "비밀번호는 대문자, 소문자, 숫자, 특수문자를 모두 포함해야 합니다"
    
    return True, "안전한 비밀번호입니다"
```

**검증 기준**:
- **길이**: 최소 8자 이상
- **복잡도**: 대문자, 소문자, 숫자, 특수문자 모두 포함
- **피드백**: 구체적인 개선 방향 제시

### **레거시 호환성 지원**

```python
@staticmethod
def hash_for_legacy_compatibility(password: str) -> str:
    """기존 SHA-256 해싱과의 호환성을 위한 메소드 (마이그레이션용)"""
    return hashlib.sha256(password.encode()).hexdigest()
```

**기능**:
- **SHA-256**: SHA-256 해시 생성
- **hexdigest**: 16진수 문자열로 반환

---

## 🔬 고급 기능 심층 분석: 보안 시스템 아키텍처

보안 서비스의 핵심은 **bcrypt 기반 비밀번호 보안**과 **레거시 시스템 호환성**입니다.

### **1. 개요**
이 시스템은 **현대적인 보안 표준**과 **기존 시스템과의 호환성**을 동시에 제공합니다. 단순한 해싱을 넘어서 **salt 기반 보안**, **점진적 마이그레이션**, **강도 검증**을 통해 시스템의 보안성을 향상시킵니다.

### **2. 핵심 아키텍처 및 보안 플로우**

#### **2.1 bcrypt 보안 메커니즘**
```python
# bcrypt 해싱 과정
salt = bcrypt.gensalt(rounds=12)  # 2^12 = 4,096 iterations
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

# 검증 과정
is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed)
```

**보안 특징**:
- **Adaptive Hashing**: 하드웨어 성능 향상에 따른 자동 조정
- **Salt Protection**: Rainbow Table 공격 방지
- **Time Cost**: 무차별 대입 공격에 대한 저항성

#### **2.2 레거시 호환성 지원**
```python
# SecurityUtils는 SHA-256 해시 생성만 제공
legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
# 실제 레거시 호환성 로직은 사용하는 쪽에서 구현해야 함
```

**제공 기능**:
- **SHA-256 해시 생성**: hash_for_legacy_compatibility() 메서드
- **사용자 구현 필요**: 레거시 호환성 검증 로직

### **3. 실제 구현된 동작 과정**

#### **3.1 비밀번호 해싱 과정**
```
1. 사용자 비밀번호 입력 (UTF-8 문자열)
2. bcrypt.gensalt(rounds=12)로 4,096 iterations salt 생성
3. bcrypt.hashpw()로 salt + password 해싱
4. 바이트 배열을 UTF-8 문자열로 디코딩
5. 데이터베이스에 해시 저장
```

#### **3.2 비밀번호 검증 과정**
```
1. 사용자 입력 비밀번호와 저장된 해시
2. bcrypt.checkpw()로 비밀번호 검증
3. 예외 발생 시 False 반환
4. 검증 결과 반환
```

### **4. 보안 최적화 효과**

#### **4.1 bcrypt 보안 강화**
```
rounds=12의 효과:
- 2^12 = 4,096 iterations
- 2010년 기준 권장값
- 하드웨어 발전에 따른 자동 조정
- 무차별 대입 공격 저항성
```

#### **4.2 SHA-256 지원**
```
제공 기능:
- SHA-256 해시 생성
- 기존 시스템과의 호환성
- 사용자 구현 필요: 마이그레이션 로직
```

### **5. 에러 처리 및 복구**

#### **5.1 예외 상황 처리**
```python
@staticmethod
def verify_password(password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False  # 안전한 실패 처리
```

**에러 처리 전략**:
- **예외 캐치**: 모든 예외 상황 처리
- **안전한 실패**: False 반환으로 인증 실패

#### **5.2 SHA-256 지원**
```python
# SHA-256 해시 생성 (사용자가 구현해야 함)
legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
# 실제 마이그레이션 로직은 사용하는 쪽에서 구현
```

**제공 기능**:
- **SHA-256 해시 생성**: hash_for_legacy_compatibility() 메서드
- **사용자 구현 필요**: 마이그레이션 및 업그레이드 로직

### **6. 사용 예시**

#### **6.1 기본 사용법**
```python
# SecurityUtils 직접 사용
from service.security.security_utils import SecurityUtils

# 비밀번호 해싱
hashed = SecurityUtils.hash_password("mypassword")

# 비밀번호 검증
is_valid = SecurityUtils.verify_password("mypassword", hashed)

# 토큰 생성
token = SecurityUtils.generate_secure_token(32)
```

#### **6.2 SHA-256 지원**
```python
# SHA-256 해시 생성
legacy_hash = SecurityUtils.hash_for_legacy_compatibility("oldpassword")

# 실제 레거시 호환성 검증은 사용자가 구현해야 함
# SecurityUtils는 SHA-256 해시 생성만 제공
```

### **7. 핵심 특징 및 장점**

#### **7.1 보안성 및 신뢰성**
- **bcrypt 표준**: 업계 표준 해싱 알고리즘
- **Salt 보호**: Rainbow Table 공격 방지
- **적응형 해싱**: 하드웨어 성능에 따른 자동 조정
- **예외 처리**: 모든 예외 상황에 대한 안전한 처리

#### **7.2 호환성 및 확장성**
- **SHA-256 지원**: SHA-256 해시 생성 메서드 제공
- **사용자 구현**: 레거시 호환성 로직은 사용자가 구현
- **확장 가능**: 새로운 해시 방식 추가 용이

#### **7.3 성능 및 사용성**
- **정적 메서드**: 인스턴스 생성 없이 직접 호출
- **타입 안전성**: Python 타입 힌트 지원
- **에러 처리**: 안전한 실패 처리로 시스템 안정성

이 시스템은 **현대적인 보안 표준**과 **SHA-256 지원**을 제공하는 보안 유틸리티입니다.

---

## 📊 사용 예제

### **기본 비밀번호 관리**

```python
from service.security.security_utils import SecurityUtils

# 비밀번호 해싱
password = "MySecurePassword123!"
hashed_password = SecurityUtils.hash_password(password)
print(f"해시된 비밀번호: {hashed_password}")
# 출력: $2b$12$... (bcrypt 해시)

# 비밀번호 검증
is_valid = SecurityUtils.verify_password(password, hashed_password)
print(f"비밀번호 검증: {is_valid}")
# 출력: True
```

### **비밀번호 강도 검증**

```python
# 약한 비밀번호 검증
weak_password = "password"
is_strong, message = SecurityUtils.validate_password_strength(weak_password)
print(f"강도 검증: {is_strong}")
print(f"메시지: {message}")
# 출력: False, "비밀번호는 대문자, 소문자, 숫자, 특수문자를 모두 포함해야 합니다"

# 강한 비밀번호 검증
strong_password = "StrongPass123!"
is_strong, message = SecurityUtils.validate_password_strength(strong_password)
print(f"강도 검증: {is_strong}")
print(f"메시지: {message}")
# 출력: True, "안전한 비밀번호입니다"
```

### **토큰 생성**

```python
# 보안 토큰 생성
secure_token = SecurityUtils.generate_secure_token(64)
print(f"보안 토큰: {secure_token}")
# 출력: 64자 URL-safe 토큰

# 세션 토큰 생성
session_token = SecurityUtils.generate_session_token()
print(f"세션 토큰: {session_token}")
# 출력: 32자 세션 토큰
```

### **SHA-256 해시 생성**

```python
# SHA-256 해시 생성
legacy_hash = SecurityUtils.hash_for_legacy_compatibility("oldpassword")
print(f"SHA-256 해시: {legacy_hash}")
# 출력: 64자 SHA-256 해시

# 참고: SecurityUtils는 SHA-256 해시 생성만 제공
# 실제 검증 로직은 사용자가 구현해야 함
```

---

## ⚙️ 설정

### **bcrypt 설정**

```python
# bcrypt rounds 설정 (security_utils.py에서)
salt = bcrypt.gensalt(rounds=12)  # 2^12 = 4,096 iterations

# 권장값:
# - 2010년: rounds=12 (4,096 iterations)
# - 2020년: rounds=14 (16,384 iterations)
# - 2030년: rounds=16 (65,536 iterations)
```

### **토큰 설정**

```python
# 기본 토큰 길이
DEFAULT_TOKEN_LENGTH = 32

# 세션 토큰 길이
SESSION_TOKEN_LENGTH = 32

# 보안 토큰 길이 (사용자 정의 가능)
secure_token = SecurityUtils.generate_secure_token(64)
```

### **비밀번호 정책**

```python
# validate_password_strength() 메서드 내부에 하드코딩된 정책
# - 최소 길이: 8자
# - 대문자, 소문자, 숫자, 특수문자 모두 포함
# - 특수문자: !@#$%^&*()_+-=[]{}|;:,.<>?

# 실제 구현에서는 상수로 정의되지 않음
```

---

## 🔗 연관 폴더

### **의존성 관계**
- **bcrypt**: 비밀번호 해싱 및 검증
- **secrets**: 암호학적으로 안전한 토큰 생성
- **hashlib**: SHA-256 해시 (레거시 호환성)

---

## 📚 외부 시스템

### **bcrypt**
- **비밀번호 해싱**: 12 rounds의 salt 기반 해싱
- **보안 표준**: 업계 표준 비밀번호 보안
- **적응형 해싱**: 하드웨어 성능에 따른 자동 조정

### **secrets**
- **토큰 생성**: 암호학적으로 안전한 랜덤 생성
- **URL-safe**: 웹 환경에서 안전한 사용
- **Python 표준**: Python 3.6+ 표준 라이브러리

### **hashlib**
- **SHA-256**: SHA-256 해시 생성
- **표준 해시**: Python 표준 해시 라이브러리

---
