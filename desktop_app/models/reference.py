from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean, Float
from ..app.database import Base


class Reference(Base):
    __tablename__ = "reference"
    id = Column(Integer, primary_key=True)
    col_position = Column(Integer)
    row_position = Column(Integer)
    zone = Column(Integer)
    max_height = Column(Float)
    is_partial = Column(Boolean)
    corners = relationship("Corner", backref="reference", lazy="dynamic")
    product_id = Column(Integer, ForeignKey("product.id"))

    def __init__(
        self,
        col_position,
        row_position,
        product_id,
        zone: int = 0,
        max_height: float = 0,
        is_partial: bool = False,
    ):
        self.zone = zone
        self.col_position = col_position
        self.row_position = row_position
        self.product_id = product_id
        self.max_height = max_height
        self.is_partial = is_partial

    def __repr__(self):
        return "<Reference {}>".format(
            str(self.row_position) + " " + str(self.col_position)
        )
