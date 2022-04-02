from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..app.database import Base

class Plc(Base):
  __tablename__ = 'plc'
  id = Column(Integer, primary_key=True)
  ip = Column(String())
  rack = Column(Integer, default=0)
  slot = Column(Integer, default=0)
  plc_blocks = relationship('PlcBlock', backref='plc', lazy='dynamic')
  
  def __init__(self, ip, rack, slot):
    self.ip = ip
    self.rack = rack
    self.slot = slot
  
  def __repr__(self):
    return '<Plc {}>'.format(str(self.ip) + ' ' + str(self.rack) + ' ' + str(self.slot))