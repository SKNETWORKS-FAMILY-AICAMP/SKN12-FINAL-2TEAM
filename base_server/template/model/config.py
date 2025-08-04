"""
설정 관리 모듈
환경 변수와 데이터베이스 연결 설정 관리
"""

import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    
    def __init__(self):
        # MySQL 설정
        self.mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        self.mysql_port = os.getenv('MYSQL_PORT', '3306')
        self.mysql_user = os.getenv('MYSQL_USER', 'stockuser')
        self.mysql_password = os.getenv('MYSQL_PASSWORD', 'stockpass')
        self.mysql_database = os.getenv('MYSQL_DATABASE', 'stock_predictions')
        
        # API 설정
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        
        # 모델 설정 (RunPod 환경 고려)
        if self._is_runpod_environment():
            # RunPod 환경: /workspace 경로 사용 (영구 저장)
            self.model_path = os.getenv('MODEL_PATH', '/workspace/models/final_model.pth')
            self.preprocessor_path = os.getenv('PREPROCESSOR_PATH', '/workspace/models/preprocessor.pkl')
            self.log_dir = os.getenv('LOG_DIR', '/workspace/logs')
        else:
            # 로컬/Docker 환경: 상대 경로 사용
            self.model_path = os.getenv('MODEL_PATH', 'models/final_model.pth')
            self.preprocessor_path = os.getenv('PREPROCESSOR_PATH', 'models/preprocessor.pkl')
            self.log_dir = os.getenv('LOG_DIR', 'logs')
        
        # 로깅 설정
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def _is_runpod_environment(self) -> bool:
        """RunPod 환경 여부 확인"""
        return (os.getenv('RUNPOD_POD_ID') is not None or 
                os.getenv('RUNPOD_API_KEY') is not None or
                os.path.exists('/workspace'))
    
    @property
    def mysql_connection_string(self) -> str:
        """MySQL 연결 문자열 생성"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def mysql_connection_dict(self) -> dict:
        """MySQL 연결 딕셔너리 반환"""
        return {
            'host': self.mysql_host,
            'port': int(self.mysql_port),
            'user': self.mysql_user,
            'password': self.mysql_password,
            'database': self.mysql_database,
            'charset': 'utf8mb4'
        }
    
    def get_docker_mysql_connection_string(self) -> str:
        """Docker 환경에서의 MySQL 연결 문자열"""
        # Docker Compose에서는 서비스명을 호스트로 사용
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@mysql:3306/{self.mysql_database}"

class Config:
    """전체 설정 관리 클래스"""
    
    def __init__(self):
        self.db = DatabaseConfig()
        
        # 실행 환경 판단
        self.is_docker = os.getenv('DOCKER_ENV', 'false').lower() == 'true'
        self.is_runpod = os.getenv('RUNPOD_POD_ID') is not None
    
    def get_mysql_connection_string(self) -> str:
        """환경에 맞는 MySQL 연결 문자열 반환"""
        if self.is_docker:
            return self.db.get_docker_mysql_connection_string()
        else:
            return self.db.mysql_connection_string
    
    def get_workspace_path(self) -> str:
        """작업 디렉토리 경로 반환"""
        if self.is_runpod:
            return '/workspace'
        else:
            return os.getcwd()
    
    def get_model_save_dir(self) -> str:
        """모델 저장 디렉토리 반환"""
        if self.is_runpod:
            return '/workspace/models'
        else:
            return 'models'

# 전역 설정 인스턴스
config = Config()

# 편의 함수들
def get_mysql_connection_string() -> str:
    """MySQL 연결 문자열 가져오기"""
    return config.get_mysql_connection_string()

def get_mysql_config() -> dict:
    """MySQL 설정 딕셔너리 가져오기"""
    return config.db.mysql_connection_dict

def is_docker_environment() -> bool:
    """Docker 환경 여부 확인"""
    return config.is_docker

def is_runpod_environment() -> bool:
    """RunPod 환경 여부 확인"""
    return config.is_runpod

def get_model_paths() -> tuple:
    """모델과 전처리기 경로 반환"""
    return config.db.model_path, config.db.preprocessor_path

def get_workspace_path() -> str:
    """작업 디렉토리 경로 반환"""
    return config.get_workspace_path()

def get_model_save_dir() -> str:
    """모델 저장 디렉토리 반환"""
    return config.get_model_save_dir()