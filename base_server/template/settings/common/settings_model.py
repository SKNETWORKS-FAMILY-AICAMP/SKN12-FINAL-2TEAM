from pydantic import BaseModel
from typing import Optional, Dict, Any

class UserSettings(BaseModel):
    """사용자 설정"""
    # 프로필 설정
    investment_experience: str = "BEGINNER"
    risk_tolerance: str = "MODERATE" 
    investment_goal: str = "GROWTH"
    monthly_budget: float = 0.0
    
    # 알림 설정
    price_alerts: bool = True
    news_alerts: bool = True
    portfolio_alerts: bool = False
    trade_alerts: bool = True
    
    # 보안 설정
    otp_enabled: bool = False
    biometric_enabled: bool = False
    session_timeout: int = 30  # 분
    login_alerts: bool = True
    
    # 화면 설정
    theme: str = "DARK"  # DARK, LIGHT
    language: str = "KO"  # KO, EN
    currency: str = "KRW"  # KRW, USD
    chart_style: str = "CANDLE"  # CANDLE, BAR
    
    # 거래 설정
    auto_trading_enabled: bool = False
    max_position_size: float = 0.1
    stop_loss_default: float = -0.05
    take_profit_default: float = 0.15

class NotificationSettings(BaseModel):
    """알림 설정 상세"""
    price_change_threshold: float = 0.05  # 5% 변동시 알림
    news_keywords: list[str] = []
    portfolio_rebalance_alerts: bool = True
    daily_summary: bool = True
    weekly_report: bool = True

class SecuritySettings(BaseModel):
    """보안 설정 상세"""
    password_change_required: bool = False
    last_password_change: str = ""
    failed_login_attempts: int = 0
    device_trust_enabled: bool = True
    ip_whitelist: list[str] = []