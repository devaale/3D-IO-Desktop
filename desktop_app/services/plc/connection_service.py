from ...models.enums.plc_block import PLCCommandType
from ...common.logger import logger
from ...helpers import plc_block_helper
from ...common.plc_adapter import PlcAdapter
from ...common.periodic_timed_service import PeriodicTimedService


class PlcConnectionService(object):
    def __init__(self, plc_adapter: PlcAdapter):
        self.__connection_bit = False
        self.__connection_block = None
        self.__plc_adapter = plc_adapter

        self.__timed_service = None

    def init_data(self, conn_block_type: PLCCommandType):
        self.__connection_block = plc_block_helper.get_plc_by_command(conn_block_type)

    def start(self, delay):
        self.__timed_service = PeriodicTimedService(self.__notify_connected, delay)
        self.__timed_service.daemon = True
        self.__timed_service.start()

    def stop(self):
        if self.__timed_service is not None:
            self.__timed_service.stop()

    def __notify_connected(self):
        value = self.__connection_bit
        self.__plc_adapter.write_block_data(self.__connection_block, value)
        self.__connection_bit = not self.__connection_bit
