from abc import ABC, abstractmethod
class BaseFinanceTool(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_data(self, **kwargs):
        """모든 툴이 구현해야 하는 메서드. 반환 형식은 자유."""
        pass