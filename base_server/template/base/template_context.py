from threading import Lock
from typing import Dict
from .template_type import TemplateType
from .base_template import BaseTemplate

class TemplateContext:
    _templates: Dict[TemplateType, BaseTemplate] = {}
    _lock = Lock()

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._templates.clear()


    @classmethod
    def add_template(cls, key: TemplateType, value):
        with cls._lock:
            if key in cls._templates:
                return False
            cls._templates[key] = value
            return True
        
    @classmethod
    def get_template(cls, key: TemplateType):
        with cls._lock:
            return cls._templates.get(key, None)

    @classmethod
    def remove_template(cls, key: TemplateType):
        with cls._lock:
            if key in cls._templates:
                del cls._templates[key]

 
    @classmethod
    def init_template(cls, config):
        with cls._lock:
            for t in cls._templates.values():
                t.init(config)

    @classmethod
    def load_data_table(cls, config):
        """모든 템플릿의 데이터 테이블 로드"""
        with cls._lock:
            for template_type, template in cls._templates.items():
                try:
                    template.on_load_data(config)
                    from service.core.logger import Logger
                    Logger.info(f"템플릿 데이터 로드 완료: {template_type.name}")
                except Exception as e:
                    from service.core.logger import Logger
                    Logger.error(f"템플릿 데이터 로드 실패: {template_type.name} - {e}")

    @classmethod
    def create_client(cls, db_client, client_session):
        for t in cls._templates.values():
            t.on_client_create(db_client, client_session)

    @classmethod
    def update_client(cls, db_client, client_session):
        for t in cls._templates.values():
            t.on_client_update(db_client, client_session)

    @classmethod
    def delete_client(cls, db_client, user_id):
        for t in cls._templates.values():
            t.on_client_delete(db_client, user_id) 