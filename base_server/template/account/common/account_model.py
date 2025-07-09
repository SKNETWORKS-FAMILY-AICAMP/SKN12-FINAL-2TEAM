from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserInfo(BaseModel):
    """사용자 기본 정보"""
    user_id: str = ""
    email: str = ""
    nickname: str = ""
    name: str = ""
    birth_date: str = ""
    gender: str = ""
    created_at: str = ""
    status: str = "ACTIVE"

class OTPInfo(BaseModel):
    """OTP 인증 정보"""
    secret_key: str = ""
    qr_code_url: str = ""
    backup_codes: list[str] = []
    is_enabled: bool = False

class UserProfile(BaseModel):
    """사용자 투자 프로필"""
    account_db_key: int = 0
    platform_type: int = 1
    account_id: str = ""
    nickname: str = ""
    email: str = ""
    account_level: int = 1
    shard_id: int = 0
    investment_experience: str = "BEGINNER"  # BEGINNER, INTERMEDIATE, EXPERT
    risk_tolerance: str = "MODERATE"         # CONSERVATIVE, MODERATE, AGGRESSIVE  
    investment_goal: str = "GROWTH"          # GROWTH, INCOME, PRESERVATION
    monthly_budget: float = 0.0
    profile_completed: bool = False

class AccountInfo(BaseModel):
    """Account information model"""
    account_number: str = ""
    balance: float = 0.0
    account_type: str = ""
    account_status: str = ""
    currency_code: str = ""
    created_at: str = ""

class TransactionInfo(BaseModel):
    """Transaction information model"""
    transaction_id: str = ""
    amount: float = 0.0
    transaction_type: str = ""
    description: str = ""
    status: str = ""
    created_at: str = ""