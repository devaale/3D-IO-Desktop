from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from ..app.database import Base
from .enums.plc_block import PLCDataType, PLCCommandType
    
class PlcBlock(Base):
  __tablename__ = 'plc_block'
  id = Column(Integer, primary_key=True)
  name = Column(String())
  value = Column(String())
  offset = Column(Integer)
  offset_bit = Column(Integer)
  data_type = Column(Enum(PLCDataType))
  command_type = Column(Enum(PLCCommandType))
  db_number = Column(Integer)
  plc_id = Column(Integer, ForeignKey('plc.id'))
  
  def __init__(self, name, value, offset, offset_bit, data_type, command_type, db_number, plc_id):
      self.name = name
      self.offset = offset
      self.value = value
      self.offset_bit = offset_bit
      self.data_type = data_type
      self.command_type = command_type
      self.db_number = db_number
      self.plc_id = plc_id

  def __repr__(self):
      return '<PlcBlock {}>'.format(self.name + ' ' + str(self.command_type) + ' ' + str(self.data_type))