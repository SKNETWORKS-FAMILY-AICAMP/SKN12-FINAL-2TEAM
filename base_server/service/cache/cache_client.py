from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional

class AbstractCacheClient(ABC):
    session_expire_time: int

    @abstractmethod
    def scan_keys(self, pattern: str) -> List[str]:
        pass

    @abstractmethod
    def delete_keys(self, pattern: str) -> int:
        pass

    @abstractmethod
    def get_key_count(self, pattern: str) -> int:
        pass

    @abstractmethod
    def set_string(self, key: str, val: str, expire: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    def get_string(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_add(self, key: str, val: str) -> bool:
        pass

    @abstractmethod
    def set_remove(self, key: str, val: str) -> bool:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def expire(self, key: str, seconds: int) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def incre(self, key: str) -> int:
        pass

    @abstractmethod
    def set_sorted_value(self, key: str, score: float, value: str) -> bool:
        pass

    @abstractmethod
    def set_sorted_value_bulk(self, key: str, pairs: List[Tuple[str, float]]) -> int:
        pass

    @abstractmethod
    def remove_sorted_value(self, key: str, value: str) -> bool:
        pass

    @abstractmethod
    def get_sorted_value_count(self, key: str) -> int:
        pass

    @abstractmethod
    def get_sorted_value_rank(self, key: str, value: str) -> int:
        pass

    @abstractmethod
    def get_sorted_value_rank_desc(self, key: str, value: str) -> int:
        pass

    @abstractmethod
    def get_sorted_value_score(self, key: str, value: str) -> float:
        pass

    @abstractmethod
    def get_sorted_value(self, key: str, from_rank: int, to_rank: int) -> List[str]:
        pass

    @abstractmethod
    def get_sorted_value_desc(self, key: str, from_rank: int, to_rank: int) -> List[str]:
        pass

    @abstractmethod
    def get_sorted_value_with_scores(self, key: str, from_rank: int, to_rank: int) -> Dict[str, float]:
        pass

    @abstractmethod
    def get_sorted_value_with_scores_desc(self, key: str, from_rank: int, to_rank: int) -> Dict[str, float]:
        pass

    @abstractmethod
    def get_set(self, key: str, value: str) -> Optional[str]:
        pass

    @abstractmethod
    def hash_set(self, key: str, field: str, value: str, expiry_second: int = 0) -> bool:
        pass

    @abstractmethod
    def hash_mset(self, key: str, pairs: List[Tuple[str, str]], expiry_second: int = 0) -> None:
        pass

    @abstractmethod
    def hash_get(self, key: str, field: str) -> Optional[str]:
        pass

    @abstractmethod
    def hash_mget(self, key: str, fields: List[str]) -> Dict[str, str]:
        pass

    @abstractmethod
    def hash_get_all(self, key: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def hash_scan(self, key: str, pattern: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def hash_remove(self, key: str, field: str) -> bool:
        pass

    @abstractmethod
    def get_sorted_value_by_score(self, key: str, from_score: float, to_score: float) -> List[str]:
        pass

    @abstractmethod
    def lpush(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def get_range_from_list(self, key: str, start_index: int, end_index: int) -> List[str]:
        pass

    @abstractmethod
    def set_random_members(self, key: str, count: int) -> List[str]:
        pass

    @abstractmethod
    def close(self):
        """자원 해제 (Dispose)"""
        pass
