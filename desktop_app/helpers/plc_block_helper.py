from ..app.database import db_session
from ..models.plc_block import *
from ..models.enums.plc_block import PLCCommandType, PLCDataType

def get_plc_by_command(command: PLCCommandType) -> PlcBlock:
    plc_block = PlcBlock.query.filter(PlcBlock.command_type == command).first()
    return plc_block