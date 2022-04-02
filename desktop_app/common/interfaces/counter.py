from abc import ABC, abstractmethod


class Counter(ABC):
    @abstractmethod
    def increment(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @property
    @abstractmethod
    def count(self):
        pass

    @count.setter
    @abstractmethod
    def count(self, value):
        pass

    @property
    @abstractmethod
    def max_count(self) -> bool:
        pass

    @max_count.setter
    @abstractmethod
    def max_count(self, value):
        pass
