from template.base.base_template import BaseTemplate
from template.autotrade.common.autotrade_serialize import (
    AutoTradeYahooSearchRequest, AutoTradeYahooSearchResponse,
    AutoTradeYahooDetailRequest, AutoTradeYahooDetailResponse,
    SignalAlarmCreateRequest, SignalAlarmCreateResponse,
    SignalAlarmListRequest, SignalAlarmListResponse,
    SignalAlarmToggleRequest, SignalAlarmToggleResponse,
    SignalAlarmDeleteRequest, SignalAlarmDeleteResponse,
    SignalHistoryRequest, SignalHistoryResponse
)
from template.autotrade.common.autotrade_model import SignalAlarmInfo, SignalHistoryItem
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.external.yahoo_finance_client import YahooFinanceClient
import uuid
from datetime import datetime

class AutoTradeTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()

    async def on_autotrade_yahoo_search_req(self, client_session, request: AutoTradeYahooSearchRequest):
        """야후 파이낸스 주식 검색"""
        response = AutoTradeYahooSearchResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Yahoo Finance search request: query={request.query}")
        
        try:
            cache_service = ServiceContainer.get_cache_service()
            async with YahooFinanceClient(cache_service) as client:
                result = await client.search_stocks(request.query)
                
                response.errorCode = result.get('errorCode', 0)
                response.results = result.get('results', [])
                
                if response.errorCode != 0:
                    response.message = result.get('message', '검색 중 오류가 발생했습니다')
                
        except Exception as e:
            Logger.error(f"Yahoo Finance search error: {e}")
            response.errorCode = 1
            response.results = []
            response.message = f"검색 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_autotrade_yahoo_detail_req(self, client_session, request: AutoTradeYahooDetailRequest):
        """야후 파이낸스 주식 상세 정보"""
        response = AutoTradeYahooDetailResponse()
        response.sequence = request.sequence
        
        # symbol 유효성 검사
        if not request.symbol or not isinstance(request.symbol, str) or not request.symbol.strip():
            response.errorCode = 1
            response.price_data = {}
            response.message = f"유효하지 않은 symbol: {request.symbol}"
            return response
        
        Logger.info(f"Yahoo Finance detail request: symbol={request.symbol}")
        
        try:
            cache_service = ServiceContainer.get_cache_service()
            async with YahooFinanceClient(cache_service) as client:
                result = await client.get_stock_detail(request.symbol)
                
                if result is None:
                    # None 대신 유효한 응답 구조 반환
                    response.errorCode = 1
                    response.price_data = {
                        request.symbol: {
                            "symbol": request.symbol,
                            "current_price": 0.0,
                            "close_price": 0.0,
                            "open_price": 0.0,
                            "high_price": 0.0,
                            "low_price": 0.0,
                            "volume": 0,
                            "change_amount": 0.0,
                            "change_percent": 0.0,
                            "currency": "USD",
                            "exchange": "NASDAQ"
                        }
                    }
                    response.message = f"상세 정보를 가져올 수 없습니다: {request.symbol}"
                else:
                    # 성공 시에도 프론트엔드가 기대하는 형태로 변환
                    response.errorCode = 0
                    response.price_data = {
                        request.symbol: {
                            "symbol": result.symbol,
                            "name": result.name,
                            "current_price": result.current_price,
                            "close_price": result.current_price,  # current_price를 close_price로도 사용
                            "open_price": result.open_price,
                            "high_price": result.high_price,
                            "low_price": result.low_price,
                            "volume": result.volume,
                            "change_amount": result.change_amount,
                            "change_percent": result.change_percent,
                            "currency": result.currency,
                            "exchange": result.exchange
                        }
                    }
                    response.message = "상세 정보 조회 성공"
                    
        except Exception as e:
            Logger.error(f"Yahoo Finance detail error: {e}")
            response.errorCode = 1
            response.price_data = {}
            response.message = f"상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_signal_alarm_create_req(self, client_session, request: SignalAlarmCreateRequest):
        """시그널 알림 등록"""
        response = SignalAlarmCreateResponse()
        response.sequence = request.sequence
        
        try:
            # 세션 정보 조회
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            if account_db_key == 0:
                response.errorCode = 1001
                response.message = "유효하지 않은 세션입니다"
                return response
            
            # Yahoo Finance에서 종목 정보 조회
            cache_service = ServiceContainer.get_cache_service()
            async with YahooFinanceClient(cache_service) as client:
                stock_detail = await client.get_stock_detail(request.symbol)
                
                if stock_detail is None:
                    response.errorCode = 1004
                    response.message = f"종목 정보를 찾을 수 없습니다: {request.symbol}"
                    return response
            
            # UUID 생성
            alarm_id = str(uuid.uuid4())
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로시저 호출 - 전체 파라미터 전달
            result = await db_service.execute_shard_procedure(
                account_db_key,
                "fp_signal_alarm_create",
                (
                    alarm_id,
                    account_db_key,
                    request.symbol,
                    stock_detail.name if stock_detail.name else request.symbol,
                    stock_detail.current_price,
                    stock_detail.exchange if stock_detail.exchange else "NASDAQ",
                    stock_detail.currency if stock_detail.currency else "USD",
                    ""  # note (빈 문자열)
                )
            )
            
            if not result:
                response.errorCode = 1002
                response.message = "알림 등록 중 오류가 발생했습니다"
                return response
            
            proc_result = result[0]
            error_code = proc_result.get('ErrorCode', 1)
            error_message = proc_result.get('ErrorMessage', '')
            
            response.errorCode = error_code
            if error_code == 0:
                response.message = "알림이 성공적으로 등록되었습니다"
                Logger.info(f"Signal alarm created: user={account_db_key}, symbol={request.symbol}, alarm_id={alarm_id}")
            else:
                response.message = error_message
                Logger.warning(f"Signal alarm creation failed: {error_message}")
                
        except Exception as e:
            Logger.error(f"Signal alarm create error: {e}")
            response.errorCode = 1003
            response.message = f"알림 등록 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_signal_alarm_list_req(self, client_session, request: SignalAlarmListRequest):
        """시그널 알림 목록 조회"""
        response = SignalAlarmListResponse()
        response.sequence = request.sequence
        response.alarms = []
        
        try:
            # 세션 정보 조회
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            if account_db_key == 0:
                response.errorCode = 1001
                response.message = "유효하지 않은 세션입니다"
                return response
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로시저 호출 - 통계 정보 포함
            result = await db_service.execute_shard_procedure(
                account_db_key,
                "fp_signal_alarms_get_with_stats",
                (account_db_key,)
            )
            
            if not result:
                response.errorCode = 1002
                response.message = "알림 목록 조회 중 오류가 발생했습니다"
                return response
            
            # 첫 번째 결과는 프로시저 상태
            proc_result = result[0]
            error_code = proc_result.get('ErrorCode', 1)
            error_message = proc_result.get('ErrorMessage', '')
            
            response.errorCode = error_code
            if error_code == 0:
                # 두 번째부터는 알림 데이터
                for alarm_data in result[1:]:
                    alarm_info = SignalAlarmInfo(
                        alarm_id=alarm_data.get('alarm_id', ''),
                        symbol=alarm_data.get('symbol', ''),
                        company_name=alarm_data.get('company_name', ''),
                        current_price=float(alarm_data.get('current_price', 0.0)),
                        is_active=bool(alarm_data.get('is_active', True)),
                        signal_count=int(alarm_data.get('signal_count', 0)),
                        win_rate=float(alarm_data.get('win_rate', 0.0)),
                        profit_rate=float(alarm_data.get('profit_rate', 0.0))
                    )
                    response.alarms.append(alarm_info)
                
                response.message = f"{len(response.alarms)}개의 알림을 조회했습니다"
                Logger.info(f"Signal alarms retrieved: user={account_db_key}, count={len(response.alarms)}")
            else:
                response.message = error_message
                Logger.warning(f"Signal alarm list failed: {error_message}")
                
        except Exception as e:
            Logger.error(f"Signal alarm list error: {e}")
            response.errorCode = 1003
            response.message = f"알림 목록 조회 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_signal_alarm_toggle_req(self, client_session, request: SignalAlarmToggleRequest):
        """시그널 알림 ON/OFF 토글"""
        response = SignalAlarmToggleResponse()
        response.sequence = request.sequence
        
        try:
            # 세션 정보 조회
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            if account_db_key == 0:
                response.errorCode = 1001
                response.message = "유효하지 않은 세션입니다"
                return response
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로시저 호출 - 알림 토글
            result = await db_service.execute_shard_procedure(
                account_db_key,
                "fp_signal_alarm_toggle",
                (request.alarm_id, account_db_key)
            )
            
            if not result:
                response.errorCode = 1002
                response.message = "알림 설정 변경 중 오류가 발생했습니다"
                return response
            
            proc_result = result[0]
            error_code = proc_result.get('ErrorCode', 1)
            error_message = proc_result.get('ErrorMessage', '')
            
            response.errorCode = error_code
            if error_code == 0:
                new_status = proc_result.get('new_status', True)
                status_text = "활성화" if new_status else "비활성화"
                response.message = f"알림이 {status_text}되었습니다"
                Logger.info(f"Signal alarm toggled: user={account_db_key}, alarm_id={request.alarm_id}, active={new_status}")
            else:
                response.message = error_message
                Logger.warning(f"Signal alarm toggle failed: {error_message}")
                
        except Exception as e:
            Logger.error(f"Signal alarm toggle error: {e}")
            response.errorCode = 1003
            response.message = f"알림 설정 변경 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_signal_alarm_delete_req(self, client_session, request: SignalAlarmDeleteRequest):
        """시그널 알림 삭제"""
        response = SignalAlarmDeleteResponse()
        response.sequence = request.sequence
        
        try:
            # 세션 정보 조회
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            if account_db_key == 0:
                response.errorCode = 1001
                response.message = "유효하지 않은 세션입니다"
                return response
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로시저 호출 - 소프트 삭제
            result = await db_service.execute_shard_procedure(
                account_db_key,
                "fp_signal_alarm_soft_delete",
                (request.alarm_id, account_db_key)
            )
            
            if not result:
                response.errorCode = 1002
                response.message = "알림 삭제 중 오류가 발생했습니다"
                return response
            
            proc_result = result[0]
            error_code = proc_result.get('ErrorCode', 1)
            error_message = proc_result.get('ErrorMessage', '')
            
            response.errorCode = error_code
            if error_code == 0:
                response.message = "알림이 성공적으로 삭제되었습니다"
                Logger.info(f"Signal alarm deleted: user={account_db_key}, alarm_id={request.alarm_id}")
            else:
                response.message = error_message
                Logger.warning(f"Signal alarm deletion failed: {error_message}")
                
        except Exception as e:
            Logger.error(f"Signal alarm delete error: {e}")
            response.errorCode = 1003
            response.message = f"알림 삭제 중 오류가 발생했습니다: {str(e)}"
        
        return response

    async def on_signal_history_req(self, client_session, request: SignalHistoryRequest):
        """시그널 히스토리 조회"""
        response = SignalHistoryResponse()
        response.sequence = request.sequence
        response.history = []
        
        try:
            # 세션 정보 조회
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            if account_db_key == 0:
                response.errorCode = 1001
                response.message = "유효하지 않은 세션입니다"
                return response
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로시저 호출 - 히스토리 조회
            result = await db_service.execute_shard_procedure(
                account_db_key,
                "fp_signal_history_get",
                (account_db_key, request.alarm_id, request.limit, request.offset)
            )
            
            if not result:
                response.errorCode = 1002
                response.message = "히스토리 조회 중 오류가 발생했습니다"
                return response
            
            # 첫 번째 결과는 프로시저 상태
            proc_result = result[0]
            error_code = proc_result.get('ErrorCode', 1)
            error_message = proc_result.get('ErrorMessage', '')
            
            response.errorCode = error_code
            if error_code == 0:
                # 두 번째부터는 히스토리 데이터
                for history_data in result[1:]:
                    history_item = SignalHistoryItem(
                        signal_id=history_data.get('signal_id', ''),
                        signal_type=history_data.get('signal_type', ''),
                        signal_price=float(history_data.get('signal_price', 0.0)),
                        profit_rate=history_data.get('profit_rate'),
                        is_win=history_data.get('is_win')
                    )
                    response.history.append(history_item)
                
                response.message = f"{len(response.history)}개의 히스토리를 조회했습니다"
                Logger.info(f"Signal history retrieved: user={account_db_key}, alarm_id={request.alarm_id}, count={len(response.history)}")
            else:
                response.message = error_message
                Logger.warning(f"Signal history failed: {error_message}")
                
        except Exception as e:
            Logger.error(f"Signal history error: {e}")
            response.errorCode = 1003
            response.message = f"히스토리 조회 중 오류가 발생했습니다: {str(e)}"
        
        return response