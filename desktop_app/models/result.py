from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean
from ..app.database import Base


class Result(Base):
    __tablename__ = "result"
    id = Column(Integer, primary_key=True)
    camera_pos = Column(Integer)
    datetime = Column(DateTime)
    reference = Column(Boolean)
    product_id = Column(Integer, ForeignKey("product.id"))

    def __init__(self, camera_pos, datetime, product_id, reference=False):
        self.camera_pos = camera_pos
        self.datetime = datetime
        self.reference = reference
        self.product_id = product_id

    def __repr__(self):
        return "<Result {}>".format(
            self.scan_number + " " + self.datetime + " " + self.product_id
        )
