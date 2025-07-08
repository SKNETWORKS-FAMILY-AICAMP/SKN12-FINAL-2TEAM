from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

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

class UserProfile(BaseModel):
    """User profile model"""
    account_db_key: int = 0
    platform_type: int = 1
    account_id: str = ""
    nickname: str = ""
    email: str = ""
    account_level: int = 1
    shard_id: int = 0