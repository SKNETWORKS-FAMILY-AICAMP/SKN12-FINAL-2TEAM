from abc import ABC, abstractmethod

class AbstractCacheClientPool(ABC):
    @abstractmethod
    def new(self):
        pass
