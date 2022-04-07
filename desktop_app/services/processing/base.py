from abc import ABC, abstractclassmethod


class ProcessingStrategy(ABC):
    @abstractclassmethod
    def execute(cls):
        pass
