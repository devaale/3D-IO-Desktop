from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from ..app.database import Base


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    model = Column(String())
    row_count = Column(Integer)
    col_count = Column(Integer)
    product_type = Column(Integer)
    processing_type = Column(Integer)
    reference_type = Column(Integer)
    camera_1_rows = Column(Integer)
    camera_2_rows = Column(Integer)
    has_reference = Column(Boolean, default=False)
    references = relationship("Reference", backref="product", lazy="dynamic")
    results = relationship("Result", backref="product", lazy="dynamic")

    def __init__(
        self,
        model,
        row_count,
        col_count,
        camera_1_rows,
        camera_2_rows,
        product_type=1,
        processing_type=10,
        reference_type=1,
        sensor_type=1,
        selected=False,
        has_reference=False,
    ):
        self.model = model
        self.row_count = row_count
        self.col_count = col_count
        self.camera_1_rows = camera_1_rows
        self.camera_2_rows = camera_2_rows
        self.product_type = product_type
        self.processing_type = processing_type
        self.reference_type = reference_type
        self.sensor_type = sensor_type
        self.selected = selected
        self.has_reference = has_reference

    def __repr__(self):
        return "<Product {}>".format(self.model)
