from ...models.plc_block import PlcBlock
from ...helpers import plc_block_helper
from ...models.enums.plc_block import PLCCommandType, PLCDataType
from ...common.logger import logger


class PlcResultWriter(object):
    RESULT = PLCCommandType.RESULT
    SCAN_DONE = PLCCommandType.SCAN_DONE

    def __init__(self, plc_adapter=None):
        self.__result = None
        self.__scan_done = None
        self.__plc_adapter = plc_adapter

    def init_data(self):
        self.__result = plc_block_helper.get_plc_by_command(self.RESULT)
        self.__scan_done = plc_block_helper.get_plc_by_command(self.SCAN_DONE)

    def fake_write_result(self, offset_bit: int, value: bool):
        offset = self.get_offset(offset_bit)
        offset_bit_proper = self.get_offset_bit(offset_bit)

        print("PLC RESULT: [", offset, ", ", offset_bit_proper, "]: ", value)

    def write_result(self, offset_bit, value):
        offset = self.get_offset(offset_bit)
        offset_bit_proper = self.get_offset_bit(offset_bit)
        result = PlcBlock(
            "Result",
            None,
            offset,
            offset_bit_proper,
            PLCDataType.BOOL,
            PLCCommandType.RESULT,
            1,
            1,
        )
        self.__plc_adapter.write_block_data(result, value)

    def write_done(self, value):
        logger.info("[Result Writer] Result done: " + str(value))
        self.__plc_adapter.write_block_data(self.__scan_done, value)

    def get_offset(self, offset_bit):
        return self.__result.offset + (offset_bit // 8)
        # if offset_bit < 8:
        #     return self.__result.offset
        # elif offset_bit > 7 and offset_bit < 16:
        #     return self.__result.offset + 1
        # else:
        #     return self.__result.offset + 2

    def get_offset_bit(self, offset_bit):
        return offset_bit % 8
