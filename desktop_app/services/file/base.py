from typing import Any
from abc import ABC, abstractclassmethod


class FileService(ABC):
    @abstractclassmethod
    def read(self, path: str) -> Any:
        pass

    @abstractclassmethod
    def write(self, path: str, data: Any):
        pass
