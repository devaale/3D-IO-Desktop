import snap7
from threading import Lock
from datetime import datetime

from desktop_app.helpers import plc_block_helper
from .logger import logger

from ..models.plc_block import PlcBlock
from ..models.enums.plc_block import PLCDataType, PLCDataTypeSize, PLCCommandType


class PlcAdapter(object):
    def __init__(self):
        self.__plc = snap7.client.Client()
        self.__lock = Lock()

    def connect(self, ip, rack, slot) -> bool:
        try:
            logger.info("[PLC] Connecting: " + str(ip))
            self.__plc.connect(ip, rack, slot)
            return self.__plc.get_connected()
        except Exception as Argument:
            logger.error("[PLC] Failed to connect to PLC: " + str(ip))
            return False

    def connected(self) -> bool:
        return self.__plc.get_connected()

    def disconnect(self):
        try:
            self.__plc.disconnect()
            logger.warn("[PLC] Disconnected")
        except Exception as Argument:
            logger.error("[PLC] Failed to disconnect" + str(Argument))

    def read_block_data(self, plc_block: PlcBlock):
        with self.__lock:
            try:
                DB_NUMBER = 246
                # print(str(datetime.now()) + "[READING PLC " + str(plc_block.command_type.name) + "]")
                if plc_block.data_type is PLCDataType.BOOL:
                    data_buffer = self.__plc.db_read(
                        DB_NUMBER, plc_block.offset, PLCDataTypeSize.BOOL
                    )
                    result = snap7.util.get_bool(data_buffer, 0, plc_block.offset_bit)
                    return result
                elif plc_block.data_type is PLCDataType.INT:
                    data_buffer = self.__plc.db_read(
                        DB_NUMBER, plc_block.offset, PLCDataTypeSize.INT
                    )
                    result = snap7.util.get_int(data_buffer, 0)
                    return result
                else:
                    print("PLC Block type doesn't exist " + str(plc_block.data_type))
            except Exception as Argument:
                print(
                    "Error occured while writting PLC Block:"
                    + str(plc_block.command_type)
                )
            finally:
                pass
                # print(str(datetime.now()) + "[READING DONE PLC " + str(plc_block.command_type.name) + "]")

    def write_block_data(self, plc_block: PlcBlock, value):
        with self.__lock:
            try:
                DB_NUMBER = 246
                logger.info(
                    str(datetime.now())
                    + "[WRITING PLC "
                    + str(plc_block.command_type.name)
                    + "] Offset: "
                    + str(plc_block.offset)
                    + ", OffsetBit: "
                    + str(plc_block.offset_bit)
                    + " | Value: "
                    + str(value)
                )
                if plc_block.data_type is PLCDataType.BOOL:
                    data_buffer = self.__plc.db_read(
                        DB_NUMBER, plc_block.offset, PLCDataTypeSize.BOOL
                    )
                    snap7.util.set_bool(data_buffer, 0, plc_block.offset_bit, value)
                    self.__plc.db_write(DB_NUMBER, plc_block.offset, data_buffer)
                elif plc_block.data_type is PLCDataType.INT:
                    data_buffer = bytearray(PLCDataTypeSize.INT)
                    snap7.util.set_int(data_buffer, 0, value)
                    self.__plc.db_write(DB_NUMBER, plc_block.offset, data_buffer)
                else:
                    print("PLC Block type doesn't exist " + str(plc_block.data_type))
            except Exception as Argument:
                print(
                    "Error occured while writting PLC Block:"
                    + str(plc_block.command_type)
                    + str(value)
                )
            finally:
                # print(str(datetime.now()) + "[WRITING DONE PLC " + str(plc_block.command_type.name) + "]")
                pass
