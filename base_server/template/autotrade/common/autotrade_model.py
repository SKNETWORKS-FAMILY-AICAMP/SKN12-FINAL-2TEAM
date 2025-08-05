from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SignalAlarmInfo(BaseModel):
    """시그널 알림 정보 - UI 표시용"""
    alarm_id: str = ""                       # 알림 고유 ID
    symbol: str = ""                         # 종목 코드 (TSLA, AAPL 등)
    company_name: str = ""                   # 기업명 (Tesla, Inc.)
    current_price: float = 0.0               # 등록 시점 가격
    exchange: str = "NASDAQ"                 # 거래소
    currency: str = "USD"                    # 통화
    note: str = ""                           # 사용자 메모
    
    # 알림 상태 관리
    is_active: bool = True                   # 알림 활성화 여부 (ON/OFF 스위치)
    
    # 성과 통계 (table_signal_history에서 집계)
    signal_count: int = 0                    # 총 시그널 발생 횟수
    win_rate: float = 0.0                    # 승률 (%) - 1% 이상 움직임 기준
    profit_rate: float = 0.0                 # 평균 수익률 (%)
    
    created_at: str = ""                     # 알림 등록 시간

class SignalHistoryItem(BaseModel):
    """시그널 히스토리 정보"""
    signal_id: str = ""                      # 시그널 ID
    alarm_id: str = ""                       # 연결된 알림 ID
    symbol: str = ""                         # 종목 코드
    signal_type: str = ""                    # BUY/SELL
    signal_price: float = 0.0                # 시그널 발생 가격
    volume: int = 0                          # 거래량
    triggered_at: str = ""                   # 발생 시간
    
    # 1일 후 성과 평가
    price_after_1d: Optional[float] = None   # 1일 후 가격
    profit_rate: Optional[float] = None      # 수익률 (%)
    is_win: Optional[bool] = None            # 1% 이상 움직임 여부
    evaluated_at: Optional[str] = None       # 평가 시간