from dataclasses import dataclass, field
from typing import List

from desktop_app.models.product import Product
from desktop_app.common.interfaces.validator import Validator
from desktop_app.services.camera.camera_manager import DepthCamera
from desktop_app.common import utils
from desktop_app.services.camera import row_helper

class ValidationService:
    def __init__(self, validators: List[Validator]) -> None:
        self.validators = validators
    
    def run_validators(self, results, cameras: List[DepthCamera], product: Product, max_validations: int):
        [x.validate(results, cameras, product, max_validations) for x in self.validators]

@dataclass
class SinglePositionValidator(Validator):
    def validate(self, results, cameras: List[DepthCamera], product: Product, max_validations: int):
        self.max_sample_count = max_validations
        positions = []
        total_products = product.col_count * product.row_count

        for camera in cameras:
            row_start, take_rows = row_helper.get_camera_rows(camera.position, product)

            for col_count in range(product.col_count - 1, product.col_count):
                position = utils.get_reverse_mapped_position(col_count, row_start, total_products, 1)
                positions.append(position)

        valid, invalid = self.valid_invalid_list(results, positions)

        self.sample_count += 1
        self.count(valid, invalid)
        self.reset_counter(self.sample_count, len(valid) * self.max_sample_count, len(invalid) * self.max_sample_count)

    def reset_counter(self, curr_count: int, total_valid: int, total_invalid: int):
        if curr_count >= self.max_sample_count:
            print("[Single Pos Validator] Positively validated [FALSE products]: ", self.invalid_count, "/", total_invalid, " ~ ", (self.invalid_count / total_invalid) * 100, "%")
            print("[Single Pos Validator] Positively validated [TRUE products]: ", self.valid_count, "/", total_valid, " ~ ", (self.valid_count / total_valid) * 100, "%")
            self.sample_count = 0
            self.valid_count = 0
            self.invalid_count = 0

@dataclass
class SingleRowValidator(Validator):
    def validate(self, results, cameras: List[DepthCamera], product: Product, max_validations: int):
        self.max_sample_count = max_validations
        positions = []
        total_products = product.col_count * product.row_count

        for camera in cameras:
            row_start, take_rows = row_helper.get_camera_rows(camera.position, product)

            for col_count in range(0, product.col_count):
                position = utils.get_reverse_mapped_position(col_count, row_start, total_products, 1)
                positions.append(position)

        valid, invalid = self.valid_invalid_list(results, positions)

        self.sample_count += 1
        self.count(valid, invalid)
        self.reset_counter(self.sample_count, len(valid) * self.max_sample_count, len(invalid) * self.max_sample_count)

    def reset_counter(self, curr_count: int, total_valid: int, total_invalid: int):
        if curr_count >= self.max_sample_count:
            print("[Single Row Validator] Positively validated [FALSE products]: ", self.invalid_count, "/", total_invalid, " ~ ", (self.invalid_count / total_invalid) * 100, "%")
            print("[Single Row Validator] Positively validated [TRUE products]: ", self.valid_count, "/", total_valid, " ~ ", (self.valid_count / total_valid) * 100, "%")
            self.sample_count = 0
            self.valid_count = 0
            self.invalid_count = 0

@dataclass
class SingleColValidator(Validator):
    expected_valid_count: int = 0

    def validate(self, results, cameras: List[DepthCamera], product: Product, max_validations: int):
        self.max_sample_count = max_validations
        positions = []
        total_products = product.col_count * product.row_count

        for camera in cameras:
            row_start, take_rows = row_helper.get_camera_rows(camera.position, product)

            for row_count in range(row_start, row_start + take_rows):
                for col_count in range(product.col_count - 1, product.col_count):
                    position = utils.get_reverse_mapped_position(col_count, row_count, total_products, 1)
                    positions.append(position)

        valid, invalid = self.valid_invalid_list(results, positions)

        self.sample_count += 1
        self.count(valid, invalid)
        self.reset_counter(self.sample_count, len(valid) * self.max_sample_count, len(invalid) * self.max_sample_count)

    def reset_counter(self, curr_count: int, total_valid: int, total_invalid: int):
        if curr_count >= self.max_sample_count:
            print("[Single Col Validator] Positively validated [FALSE products]: ", self.invalid_count, "/", total_invalid, " ~ ", (self.invalid_count / total_invalid) * 100, "%")
            print("[Single Col Validator] Positively validated [TRUE products]: ", self.valid_count, "/", total_valid, " ~ ", (self.valid_count / total_valid) * 100, "%")
            self.sample_count = 0
            self.valid_count = 0
            self.invalid_count = 0



        

        
        
        