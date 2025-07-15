from typing import Dict, Type, Optional
from .data_table import DataTable, DataRow
from service.core.logger import Logger
import os

class DataTableManager:
    """전역 데이터 테이블 관리자"""
    
    _instance = None
    _tables: Dict[str, DataTable] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataTableManager, cls).__new__(cls)
        return cls._instance
        
    @classmethod
    def register_table(cls, name: str, table: DataTable) -> bool:
        """테이블 등록"""
        if name in cls._tables:
            Logger.warn(f"테이블 이미 등록됨: {name}")
            return False
            
        cls._tables[name] = table
        Logger.info(f"테이블 등록: {name}")
        return True
        
    @classmethod
    def get_table(cls, name: str) -> Optional[DataTable]:
        """테이블 조회"""
        return cls._tables.get(name)
        
    @classmethod
    def load_all_tables(cls, base_path: str, table_configs: Dict[str, dict]) -> bool:
        """모든 테이블 로드
        
        Args:
            base_path: CSV/JSON 파일들이 있는 기본 경로
            table_configs: 테이블 설정 딕셔너리
                {
                    "table_name": {
                        "file": "filename.csv",
                        "row_class": RowClass,
                        "key_field": "id"  # optional
                    }
                }
        """
        success_count = 0
        
        for table_name, config in table_configs.items():
            try:
                file_name = config.get("file")
                row_class = config.get("row_class")
                key_field = config.get("key_field")
                
                if not file_name or not row_class:
                    Logger.error(f"테이블 설정 오류: {table_name}")
                    continue
                    
                # 테이블 생성
                table = DataTable(row_class, key_field)
                
                # 파일 경로 생성
                file_path = os.path.join(base_path, file_name)
                
                # 파일 로드
                if file_name.endswith('.csv'):
                    if table.load_csv(file_path):
                        cls.register_table(table_name, table)
                        success_count += 1
                elif file_name.endswith('.json'):
                    if table.load_json(file_path):
                        cls.register_table(table_name, table)
                        success_count += 1
                else:
                    Logger.error(f"지원하지 않는 파일 형식: {file_name}")
                    
            except Exception as e:
                Logger.error(f"테이블 로드 실패: {table_name} - {e}")
                
        Logger.info(f"테이블 로드 완료: {success_count}/{len(table_configs)}")
        return success_count > 0
        
    @classmethod
    def reload_table(cls, name: str) -> bool:
        """특정 테이블 다시 로드"""
        table = cls._tables.get(name)
        if table:
            return table.reload()
        return False
        
    @classmethod
    def reload_all_tables(cls) -> int:
        """모든 테이블 다시 로드"""
        success_count = 0
        for name, table in cls._tables.items():
            if table.reload():
                success_count += 1
                Logger.info(f"테이블 리로드 성공: {name}")
            else:
                Logger.error(f"테이블 리로드 실패: {name}")
        return success_count
        
    @classmethod
    def clear(cls):
        """모든 테이블 초기화"""
        cls._tables.clear()
        Logger.info("모든 테이블 초기화")