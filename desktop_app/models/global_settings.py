from sqlalchemy import Column, Integer, String
from desktop_app.app.database import Base

class GlobalSettings(Base):
  __tablename__ = 'global_settings'
  id = Column(Integer, primary_key=True)
  file_service_time_days = Column(Integer())
  camera_one_serial = Column(String())
  
  def __init__(self, file_service_time_days: int, camera_one_serial: str):
    self.file_service_time_days = file_service_time_days
    self.camera_one_serial = camera_one_serial
  
  def __repr__(self):
    return '<Global Settings {}>'.format(str(self.file_service_time))