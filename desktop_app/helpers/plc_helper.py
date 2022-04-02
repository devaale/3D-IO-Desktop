from ..app.database import db_session
from ..models.plc import *

def get_plc():
    return Plc.query.one()