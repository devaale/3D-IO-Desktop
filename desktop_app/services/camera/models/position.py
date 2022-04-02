from dataclasses import dataclass

@dataclass
class Position:
    row: int
    col: int
    mse: float
    rmse: float

    def calculate_mse(self, x, y):
        pass

    def calculate_rmse(self):
        pass