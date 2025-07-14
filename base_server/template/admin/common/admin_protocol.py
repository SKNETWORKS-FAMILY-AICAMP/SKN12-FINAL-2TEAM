from .admin_model import (
    HealthCheckRequest, ServerStatusRequest, SessionCountRequest,
    QueueStatsRequest, QuickTestRequest
)

class AdminProtocol:
    def __init__(self):
        self.message_controllers = {}
        # 콜백 속성
        self.on_health_check_req_callback = None
        self.on_server_status_req_callback = None
        self.on_session_count_req_callback = None
        self.on_queue_stats_req_callback = None
        self.on_quick_test_req_callback = None
        self._register_controllers()

    def _register_controllers(self):
        # 각 패킷별 컨트롤러 등록
        # ProtocolId는 실제로는 상수로 정의되어 있어야 함
        self.message_controllers[getattr(HealthCheckRequest, 'ProtocolId', 101)] = self.health_check_req_controller
        self.message_controllers[getattr(ServerStatusRequest, 'ProtocolId', 102)] = self.server_status_req_controller
        self.message_controllers[getattr(SessionCountRequest, 'ProtocolId', 103)] = self.session_count_req_controller
        self.message_controllers[getattr(QueueStatsRequest, 'ProtocolId', 104)] = self.queue_stats_req_controller
        self.message_controllers[getattr(QuickTestRequest, 'ProtocolId', 105)] = self.quick_test_req_controller

    def health_check_req_controller(self, session, msg: bytes, length: int):
        # msg를 HealthCheckRequest로 역직렬화
        # 콜백 호출
        request = HealthCheckRequest.model_validate_json(msg)
        if self.on_health_check_req_callback:
            return self.on_health_check_req_callback(session, request)
        raise NotImplementedError('on_health_check_req_callback is not set')

    def server_status_req_controller(self, session, msg: bytes, length: int):
        request = ServerStatusRequest.model_validate_json(msg)
        if self.on_server_status_req_callback:
            return self.on_server_status_req_callback(session, request)
        raise NotImplementedError('on_server_status_req_callback is not set')

    def session_count_req_controller(self, session, msg: bytes, length: int):
        request = SessionCountRequest.model_validate_json(msg)
        if self.on_session_count_req_callback:
            return self.on_session_count_req_callback(session, request)
        raise NotImplementedError('on_session_count_req_callback is not set')

    def queue_stats_req_controller(self, session, msg: bytes, length: int):
        request = QueueStatsRequest.model_validate_json(msg)
        if self.on_queue_stats_req_callback:
            return self.on_queue_stats_req_callback(session, request)
        raise NotImplementedError('on_queue_stats_req_callback is not set')

    def quick_test_req_controller(self, session, msg: bytes, length: int):
        request = QuickTestRequest.model_validate_json(msg)
        if self.on_quick_test_req_callback:
            return self.on_quick_test_req_callback(session, request)
        raise NotImplementedError('on_quick_test_req_callback is not set')