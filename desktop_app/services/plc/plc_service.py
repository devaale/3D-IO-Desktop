from ...helpers import plc_block_helper, product_helper
from ...services.camera.camera_service import CameraService
from threading import Event
from .connection_service import PlcConnectionService

from ...helpers import plc_helper
from ...common.logger import logger
from ...common.plc_adapter import PlcAdapter

from ...models.plc_block import PlcBlock
from ...models.enums.plc_block import PLCCommandType, PLCDataType
import time


class PlcService:
    def __init__(
        self,
        plc_adapter: PlcAdapter = None,
        camera_service: CameraService = None,
        conn_service=None,
        processing_done_event: Event = None,
        camera_trigger_event: Event = None,
        plc_start_event: Event = None,
    ):
        self.__read_plc_blocks = []
        self.__write_plc_blocks = []
        self.__result_done_block = PlcBlock(
            "Scan done", None, 4, 0, PLCDataType.BOOL, PLCCommandType.SCAN_DONE, 1, 1
        )

        self.__plc_adapter = plc_adapter

        self.__conn_delay_sec = 1
        self.__connection_service = conn_service

        self.__wait_time = 0.005
        self.__stop_event = Event()

        self.__camera_trigger_event = camera_trigger_event
        self.__plc_start_event = plc_start_event
        self.__camera_service = camera_service
        self.__processing_done_event = processing_done_event

        self.__prev_product_type = 0
        self.__prev_learning_mode = False
        self.__prev_trigger_flag = False

    def __init_data(self):
        self.__read_plc_blocks = [
            plc_block_helper.get_plc_by_command(PLCCommandType.PRODUCT_TYPE),
            plc_block_helper.get_plc_by_command(PLCCommandType.LEARNING_MODE_ENABLE),
            plc_block_helper.get_plc_by_command(PLCCommandType.TRIGGER_FLAG),
        ]

        self.__write_plc_blocks = [
            plc_block_helper.get_plc_by_command(PLCCommandType.LEARNING_MODE_ACK),
            plc_block_helper.get_plc_by_command(PLCCommandType.TRIGGER_FLAG_ACK),
            plc_block_helper.get_plc_by_command(PLCCommandType.TEMPLATE_EXIST),
            plc_block_helper.get_plc_by_command(PLCCommandType.PRODUCT_TYPE_ACK),
        ]

        if not self.__connection_service:
            self.__connection_service = PlcConnectionService(self.__plc_adapter)
        self.__connection_service.init_data(PLCCommandType.LIFE_BIT)

        self.__stop_event.clear()

    def __start_sub_services(self):
        self.__connection_service.start(delay=self.__conn_delay_sec)

    def connect(self) -> bool:
        plc = plc_helper.get_plc()
        logger.info(
            "[PLC Service connecting to: " + str(plc.ip) + str(plc.rack) + str(plc.slot)
        )
        return self.__plc_adapter.connect(plc.ip, plc.rack, plc.slot)

    def connect_loop(self):
        connected = False
        while not connected:
            logger.error("[PLC Service is not connected, trying to reconnect...")
            connected = self.connect()
            time.sleep(1)

    def connected(self) -> bool:
        return self.__plc_adapter.connected()

    def run(self):
        logger.info("[PLC Service] Waiting for start event from camera...")
        self.__plc_start_event.wait(timeout=None)
        logger.info("[PLC Service] Starting")
        connected = self.connect()

        if connected:
            logger.info("[PLC Service] Connected")
            self.__init_data()
            self.__start_sub_services()
            try:
                while True:

                    if not self.connected():
                        self.connect_loop()

                    if self.__stop_event.is_set():
                        break

                    self.__read_write()

                    self.__stop_event.wait(self.__wait_time)
            finally:
                self.__stop_services()
        else:
            self.__stop_services()

    def __read_write(self):
        if self.__camera_service is None:
            return

        for plc_block in self.__read_plc_blocks:
            result = self.__plc_adapter.read_block_data(plc_block)
            print("BLOCK: ", plc_block.command_type)
            print("Value: ", result)

            if plc_block.command_type == PLCCommandType.LEARNING_MODE_ENABLE:
                if self.__prev_learning_mode != result:
                    result_block = self.get_write_block_by_type(
                        PLCCommandType.LEARNING_MODE_ACK
                    )
                    self.__plc_adapter.write_block_data(result_block, result)
                    if result:
                        logger.info("[PLC Service] Setting create reference")
                        if self.__camera_service is not None:
                            self.__camera_service.create_reference()
                    self.__prev_learning_mode = result

            elif plc_block.command_type == PLCCommandType.PRODUCT_TYPE:
                # print("roduct type =============================: ", result)
                if self.__prev_product_type != result:
                    # if result not in [x.value for x in ProductType]:
                    #     logger.error(
                    #         "[PLC Service] Product type not in Enum range. Setting camera to IDLE."
                    #     )
                    #     self.__camera_service.__command = CameraCommand.IDLE
                    #     continue

                    logger.info(
                        "[PLC Service] Setting product: "
                        + str(self.__prev_product_type)
                    )
                    result_block = self.get_write_block_by_type(
                        PLCCommandType.PRODUCT_TYPE_ACK
                    )
                    self.__plc_adapter.write_block_data(result_block, result)
                    result_block = self.get_write_block_by_type(
                        PLCCommandType.TEMPLATE_EXIST
                    )
                    has_template = self.check_product_has_reference(result)
                    self.__plc_adapter.write_block_data(result_block, has_template)

                    if self.__camera_service is not None:
                        self.__camera_service.set_product(result)
                    self.__prev_product_type = result

            elif plc_block.command_type == PLCCommandType.TRIGGER_FLAG:
                if self.__prev_trigger_flag is True and result is False:
                    scan_done_block_data = plc_block_helper.get_plc_by_command(
                        PLCCommandType.SCAN_DONE
                    )
                    self.__plc_adapter.write_block_data(scan_done_block_data, False)
                if self.__prev_trigger_flag != result:
                    result_block = self.get_write_block_by_type(
                        PLCCommandType.TRIGGER_FLAG_ACK
                    )
                    self.__plc_adapter.write_block_data(result_block, result)
                    if result:
                        logger.info("[PLC Service] Setting create reference")
                        if self.__camera_service is not None:
                            self.__camera_trigger_event.set()
                    self.__prev_trigger_flag = result

    def read_block_loop(self, block, value, criteria):
        while block is not criteria:
            value = self.__plc_adapter.read_block_data(block)
            time.sleep(0.1)
        return value

    def get_write_block_by_type(self, command_type: PLCCommandType):
        result_block = [
            block
            for block in self.__write_plc_blocks
            if block.command_type == command_type
        ][0]
        return result_block

    def check_product_has_reference(self, product_type):
        product = product_helper.get_product_by_type(product_type)
        has_reference = product_helper.get_product_has_reference(product.id)

        return has_reference

    def __stop_services(self):
        if self.__connection_service is not None:
            self.__connection_service.stop()

        if self.__plc_adapter is not None:
            self.__plc_adapter.disconnect()

    def stop(self):
        self.__stop_event.set()
        self.__stop_services()
        logger.warning("[PLC Service] Stopping")
