from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.orm import relationship
from ..app.database import Base



class ZoneReference(Base):
    __tablename__ = "zone_reference"
    id = Column(Integer, primary_key=True)
    row = Column(Integer)
    col = Column(Integer)
    mse = Column(Float)
    product_id = Column(Integer, ForeignKey("product.id"))

    def __init__(self, row, col, mse, product_id):
        self.row = row
        self.col = col
        self.mse = mse
        self.product_id = product_id

    def __repr__(self):
        return "<Reference {}>".format(
            str(self.row) + " " + str(self.col) + ", MSE: ", str(self.mse)
        )
    
    # def compare_position(self, other: Union[Self, Zone]) -> bool:
    #     return self.row == other.row and self.col == other.col
    
    # def validate(self, value: float, threshold: float) -> bool:
    #     #TODO: Decide on best statistic to use.
    #     return abs(self.mse - value) < threshold
