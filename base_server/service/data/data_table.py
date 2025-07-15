import csv
import json
import os
from typing import Dict, List, Type, TypeVar, Generic, Optional
from abc import ABC, abstractmethod
from service.core.logger import Logger

T = TypeVar('T')

class DataRow(ABC):
    """CSV 행 데이터의 베이스 클래스"""
    @abstractmethod
    def from_dict(self, data: dict):
        """딕셔너리에서 객체로 변환"""
        pass

class DataTable(Generic[T]):
    """CSV 데이터를 메모리에 로드하고 관리하는 테이블 클래스"""
    
    def __init__(self, row_class: Type[T], key_field: str = None):
        self._data: Dict[str, T] = {}
        self._row_class = row_class
        self._key_field = key_field
        self._file_path: Optional[str] = None
        
    def load_csv(self, file_path: str, encoding: str = 'utf-8') -> bool:
        """CSV 파일을 로드"""
        try:
            if not os.path.exists(file_path):
                Logger.error(f"CSV 파일이 존재하지 않습니다: {file_path}")
                return False
                
            self._file_path = file_path
            self._data.clear()
            
            with open(file_path, 'r', encoding=encoding) as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외하고 2번째 줄부터
                    try:
                        # 빈 값 처리
                        cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                        
                        # 행 객체 생성
                        row_obj = self._row_class()
                        row_obj.from_dict(cleaned_row)
                        
                        # 키 필드가 지정된 경우 해당 필드를 키로 사용
                        if self._key_field and hasattr(row_obj, self._key_field):
                            key = str(getattr(row_obj, self._key_field))
                            if key in self._data:
                                Logger.warn(f"중복 키 발견: {key} (파일: {file_path}, 행: {row_num})")
                            self._data[key] = row_obj
                        else:
                            # 키 필드가 없으면 행 번호를 키로 사용
                            self._data[str(row_num)] = row_obj
                            
                    except Exception as e:
                        Logger.error(f"CSV 행 파싱 실패 (파일: {file_path}, 행: {row_num}): {e}")
                        continue
                        
            Logger.info(f"CSV 로드 완료: {file_path} ({len(self._data)}개 행)")
            return True
            
        except Exception as e:
            Logger.error(f"CSV 파일 로드 실패: {file_path} - {e}")
            return False
            
    def load_json(self, file_path: str) -> bool:
        """JSON 파일을 로드"""
        try:
            if not os.path.exists(file_path):
                Logger.error(f"JSON 파일이 존재하지 않습니다: {file_path}")
                return False
                
            self._file_path = file_path
            self._data.clear()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        row_obj = self._row_class()
                        row_obj.from_dict(item)
                        
                        if self._key_field and hasattr(row_obj, self._key_field):
                            key = str(getattr(row_obj, self._key_field))
                            self._data[key] = row_obj
                        else:
                            self._data[str(idx)] = row_obj
                            
                elif isinstance(data, dict):
                    for key, item in data.items():
                        row_obj = self._row_class()
                        row_obj.from_dict(item)
                        self._data[key] = row_obj
                        
            Logger.info(f"JSON 로드 완료: {file_path} ({len(self._data)}개 항목)")
            return True
            
        except Exception as e:
            Logger.error(f"JSON 파일 로드 실패: {file_path} - {e}")
            return False
            
    def get(self, key: str) -> Optional[T]:
        """키로 데이터 조회"""
        return self._data.get(key)
        
    def get_all(self) -> List[T]:
        """모든 데이터 반환"""
        return list(self._data.values())
        
    def get_dict(self) -> Dict[str, T]:
        """딕셔너리 형태로 모든 데이터 반환"""
        return self._data.copy()
        
    def find(self, predicate) -> Optional[T]:
        """조건에 맞는 첫 번째 항목 찾기"""
        for item in self._data.values():
            if predicate(item):
                return item
        return None
        
    def find_all(self, predicate) -> List[T]:
        """조건에 맞는 모든 항목 찾기"""
        return [item for item in self._data.values() if predicate(item)]
        
    def reload(self) -> bool:
        """파일 다시 로드"""
        if self._file_path:
            if self._file_path.endswith('.csv'):
                return self.load_csv(self._file_path)
            elif self._file_path.endswith('.json'):
                return self.load_json(self._file_path)
        return False
        
    def count(self) -> int:
        """데이터 개수"""
        return len(self._data)
        
    def clear(self):
        """데이터 초기화"""
        self._data.clear()