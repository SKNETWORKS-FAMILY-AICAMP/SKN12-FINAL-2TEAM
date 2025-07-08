from abc import ABC, abstractmethod

class BaseTemplate(ABC):
    def init(self, config):
        """템플릿별 초기화"""
        pass

    def on_load_data(self, config):
        """데이터 로딩(예: csv, json, db 등)"""
        pass

    def on_client_create(self, db_client, client_session):
        """클라이언트 생성 시 콜백"""
        pass

    def on_client_update(self, db_client, client_session):
        """클라이언트 업데이트 시 콜백"""
        pass

    def on_client_delete(self, db_client, user_id):
        """클라이언트 삭제 시 콜백"""
        pass