from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .autotrade_model import SignalAlarmInfo, SignalHistoryItem

# Yahoo Finance API 요청/응답 모델 (기존 유지)
class AutoTradeYahooSearchRequest(BaseRequest):
    """야후 파이낸스 검색 요청"""
    query: str

class AutoTradeYahooSearchResponse(BaseResponse):
    """야후 파이낸스 검색 응답"""
    results: List[Dict[str, Any]] = []

class AutoTradeYahooDetailRequest(BaseRequest):
    """야후 파이낸스 상세정보 요청"""
    symbol: str

class AutoTradeYahooDetailResponse(BaseResponse):
    """야후 파이낸스 상세정보 응답"""
    price_data: Dict[str, Any] = {}

# ============================================================================
# 시그널 알림 관리 API
# is_active: 알림 수신 ON/OFF (화면에는 계속 표시)
# is_deleted: 화면에서 완전 제거 (soft delete)
# ============================================================================

class SignalAlarmCreateRequest(BaseRequest):
    """시그널 알림 등록 요청"""
    symbol: str                              # 종목 코드 (필수)
    company_name: Optional[str] = None       # 기업명
    current_price: Optional[float] = None    # 현재 가격
    exchange: str = "NASDAQ"                 # 거래소
    currency: str = "USD"                    # 통화
    note: Optional[str] = None               # 사용자 메모

class SignalAlarmCreateResponse(BaseResponse):
    """시그널 알림 등록 응답"""
    alarm_id: str = ""                       # 생성된 알림 ID
    alarm_info: Optional[SignalAlarmInfo] = None  # 생성된 알림 정보

class SignalAlarmListRequest(BaseRequest):
    """시그널 알림 목록 조회 요청 (is_deleted=0만 조회)"""
    pass

class SignalAlarmListResponse(BaseResponse):
    """시그널 알림 목록 조회 응답"""
    alarms: List[SignalAlarmInfo] = []       # 알림 목록 (활성/비활성 모두 포함)
    total_count: int = 0                     # 총 알림 개수
    active_count: int = 0                    # 알림 수신 활성화된 개수

class SignalAlarmToggleRequest(BaseRequest):
    """시그널 알림 수신 ON/OFF 요청 (is_active 토글)"""
    alarm_id: str                            # 알림 ID (필수)

class SignalAlarmToggleResponse(BaseResponse):
    """시그널 알림 수신 ON/OFF 응답"""
    alarm_id: str = ""                       # 알림 ID
    is_active: bool = False                  # 변경된 알림 수신 상태

class SignalAlarmDeleteRequest(BaseRequest):
    """시그널 알림 삭제 요청 (화면에서 완전 제거, is_deleted=1)"""
    alarm_id: str                            # 알림 ID (필수)

class SignalAlarmDeleteResponse(BaseResponse):
    """시그널 알림 삭제 응답"""
    alarm_id: str = ""                       # 삭제된 알림 ID

class SignalHistoryRequest(BaseRequest):
    """시그널 히스토리 조회 요청"""
    alarm_id: Optional[str] = None           # 특정 알림만 조회 (선택)
    symbol: Optional[str] = None             # 특정 종목만 조회 (선택)
    signal_type: Optional[str] = None        # BUY/SELL 필터 (선택)
    limit: int = 50                          # 조회 개수 제한

class SignalHistoryResponse(BaseResponse):
    """시그널 히스토리 조회 응답"""
    signals: List[SignalHistoryItem] = []    # 시그널 히스토리 목록
    total_count: int = 0                     # 총 시그널 개수