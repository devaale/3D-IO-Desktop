from ..app.database import db_session
from ..models.global_settings import *

def get() -> GlobalSettings:
    return GlobalSettings.query.one()
