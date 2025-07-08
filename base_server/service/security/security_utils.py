import bcrypt
import secrets
import hashlib
from typing import Optional
from datetime import datetime, timedelta

class SecurityUtils:
    """보안 관련 유틸리티 클래스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """bcrypt를 사용한 안전한 비밀번호 해싱"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """안전한 토큰 생성"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_token() -> str:
        """세션 토큰 생성"""
        return secrets.token_urlsafe(32)
    
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
    
    @staticmethod
    def hash_for_legacy_compatibility(password: str) -> str:
        """기존 SHA-256 해싱과의 호환성을 위한 메소드 (마이그레이션용)"""
        return hashlib.sha256(password.encode()).hexdigest()