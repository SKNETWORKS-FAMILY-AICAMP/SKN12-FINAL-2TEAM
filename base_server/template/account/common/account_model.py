from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserInfo(BaseModel):
    """사용자 기본 정보 - Global DB table_accountid 기반"""
    user_id: str = ""                        # account_db_key를 문자열로 표현
    email: str = ""                          # email 컬럼 (varchar(100))
    nickname: str = ""                       # nickname 컬럼 (varchar(50))
    name: str = ""                           # 실명 (회원가입 시 선택 입력)
    birth_date: str = ""                     # birth_year/month/day 조합
    gender: str = ""                         # gender 컬럼 (M/F/OTHER)
    created_at: str = ""                     # create_time 컬럼
    status: str = "ACTIVE"                   # account_status 컬럼 (Normal/Blocked/Withdrawn)

class OTPInfo(BaseModel):
    """OTP 인증 정보"""
    secret_key: str = ""                     # OTP 시크릿 키 (16자리)
    qr_code_url: str = ""                    # QR코드 생성용 URL
    backup_codes: list[str] = []             # 백업 코드 목록 (6자리 x 10개)
    is_enabled: bool = False                 # OTP 활성화 여부

class UserProfile(BaseModel):
    """사용자 투자 프로필 - Global DB table_user_profiles 기반"""
    account_id: str = ""                     # account_id 컬럼 (varchar(100)) - 로그인 ID
    nickname: str = ""                       # nickname 컬럼 (varchar(50)) - 화면 표시명
    email: str = ""                          # email 컬럼 (varchar(100)) - 연락처
    investment_experience: str = "BEGINNER"  # investment_experience 컬럼 (ENUM: BEGINNER/INTERMEDIATE/EXPERT)
    risk_tolerance: str = "MODERATE"         # risk_tolerance 컬럼 (ENUM: CONSERVATIVE/MODERATE/AGGRESSIVE)
    investment_goal: str = "GROWTH"          # investment_goal 컬럼 (ENUM: GROWTH/INCOME/PRESERVATION)
    monthly_budget: float = 0.0              # monthly_budget 컬럼 (DECIMAL(15,2)) - 원화 기준
    birth_year: Optional[int] = None         # birth_year 컬럼 (INT) - 1900~현재년도
    birth_month: Optional[int] = None        # birth_month 컬럼 (INT) - 1~12
    birth_day: Optional[int] = None          # birth_day 컬럼 (INT) - 1~31
    gender: Optional[str] = None             # gender 컬럼 (ENUM: M/F/OTHER)
    profile_completed: bool = False          # profile_completed 컬럼 (BIT(1)) - 설정 완료 여부

class AccountInfo(BaseModel):
    """투자 계좌 정보 - Shard DB table_user_accounts 기반"""
    account_number: str = ""                 # account_number 컬럼 (varchar(20)) - 유니크 계좌번호
    balance: float = 0.0                     # balance 컬럼 (DECIMAL(15,2)) - 계좌 잔고
    account_type: str = ""                   # account_type 컬럼 (ENUM: checking/savings/investment)
    account_status: str = ""                 # account_status 컬럼 (ENUM: active/suspended/closed)
    currency_code: str = ""                  # currency_code 컬럼 (varchar(3)) - KRW/USD/EUR
    created_at: str = ""                     # created_at 컬럼

class PortfolioInfo(BaseModel):
    """포트폴리오 보유 종목 정보 - Shard DB table_user_portfolios 기반"""
    portfolio_id: int = 0                    # portfolio_id 컬럼 (BIGINT AUTO_INCREMENT)
    asset_code: str = ""                     # asset_code 컬럼 (varchar(10)) - 종목코드 (KRW/005930/AAPL)
    asset_type: str = ""                     # asset_type 추론 (CASH/STOCK/ETF/CRYPTO)
    quantity: float = 0.0                    # quantity 컬럼 (DECIMAL(15,6)) - 보유수량
    average_cost: float = 0.0                # average_cost 컬럼 (DECIMAL(15,2)) - 평균단가
    current_value: float = 0.0               # current_value 컬럼 (DECIMAL(15,2)) - 현재가치
    last_updated: str = ""                   # last_updated 컬럼

class TransactionInfo(BaseModel):
    """거래 내역 정보 - Shard DB table_transactions 기반"""
    transaction_id: str = ""                 # transaction_id 컬럼 (varchar(32)) - 거래 고유ID
    account_number: str = ""                 # account_number 컬럼 (varchar(20))
    amount: float = 0.0                      # amount 컬럼 (DECIMAL(15,2)) - 거래금액
    transaction_type: str = ""               # transaction_type 컬럼 (ENUM: deposit/withdrawal/transfer_in/transfer_out/fee)
    description: str = ""                    # description 컬럼 (TEXT) - 거래 설명
    reference_id: str = ""                   # reference_id 컬럼 (varchar(50)) - 참조번호
    status: str = ""                         # status 컬럼 (ENUM: pending/completed/failed/cancelled)
    created_at: str = ""                     # created_at 컬럼

class AccountApiKeysSaveRequest(BaseModel):
    """API 키 저장 요청"""
    korea_investment_app_key: str = ""
    korea_investment_app_secret: str = ""
    alpha_vantage_key: str = ""
    polygon_key: str = ""
    finnhub_key: str = ""

class AccountApiKeysSaveResponse(BaseModel):
    """API 키 저장 응답"""
    message: str = ""