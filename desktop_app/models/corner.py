from sqlalchemy import Column, Integer, Float, ForeignKey
from ..app.database import Base


class Corner(Base):
    __tablename__ = "corner"
    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    average_height = Column(Float)
    reference_id = Column(Integer, ForeignKey("reference.id"))

    def __init__(self, position, average_height, reference_id):
        self.position = position
        self.average_height = average_height
        self.reference_id = reference_id

    def __repr__(self):
        return "<Corner {}>".format(self.position + " " + self.average_height)
