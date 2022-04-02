from abc import ABC, abstractmethod
from typing import List
from desktop_app.models.product import Product
from desktop_app.services.camera.camera_manager import DepthCamera
from dataclasses import dataclass, field

@dataclass
class Validator(ABC):
    valid_count: int = 0
    invalid_count: int = 0
    valid: list = field(default=list, init=True)
    
    sample_count: int = 0
    max_sample_count: int = 50

    @abstractmethod
    def validate(self, results, cameras: List[DepthCamera], product: Product, max_validations: int):
        pass

    @abstractmethod
    def reset_counter(self, curr_count: int, total_valid: int, total_invalid: int):
        pass
    
    def count(self, valid, invalid):
        for value in valid:
            if self.is_valid(value, True):
                self.valid_count += 1
        
        for value in invalid:
            if self.is_valid(value, False):
                self.invalid_count += 1

    def valid_invalid_list(self, results, positions):
        valid, invalid = [], []

        for key, value in results.items():
            if key in positions:
                invalid.append(value)
                continue
            valid.append(value)
        
        return valid, invalid

    def is_valid(self, value: bool, predicted: bool):
        return value == predicted