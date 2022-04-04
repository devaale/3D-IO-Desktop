from desktop_app.common.plc_adapter import PlcAdapter
from desktop_app.helpers import corner_helper, result_helper
from desktop_app.common.decorators import timing
from multiprocessing import Manager
from desktop_app.common import utils
from desktop_app.services.camera import (
    row_helper,
)
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.services.camera.models.enums.camera_command import CameraCommand
from desktop_app.models.enums.product import ProductType
from desktop_app.services.camera import reference_creation
import copy
import os
import time
from threading import Event

from typing import *

from . import (
    clustering_reference_creation,
    clustering_detection,
)

from .camera import Camera
from .processing import cloud_processing
from .visualization import Visualization

from ..settings import settings_reader
from ..plc.result_writer import PlcResultWriter

from ...helpers import reference_helper, product_helper, global_settings_helper
from ...common.logger import logger
from datetime import datetime

from .result_visualizer import ResultVisualizer
import numpy as np
import cv2
from .reader import CameraReader
import pyrealsense2 as rs

from desktop_app.services.camera import reader


class CameraService:
    # TODO: Export folders to appropriate classes services
    DETECTION_RESULT_FOLDER = "saved_data/detection/"
    REFERENCE_RESULT_FOLDER = "saved_data/reference/"

    # TODO: Export variable to appropriate bounds
    DIR_NAME = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(DIR_NAME, "configs/camera/no_auto_exp_second_peak.json")
    SAMPLE_COUNT = 5

    def __init__(
        self,
        manager: Manager,
        sensor_trigger_event: Event,
        processing_done_event: Event,
        plc_adapter: PlcAdapter = None,
        plc_start_event: Event = None,
    ):
        self.__running = False
        self.__manager = manager

        self.__processing_results = self.__manager.dict()
        self.__processing_results_db = self.__manager.list()

        self.__visualizer = Visualization()

        self.__plc_result_writer = None
        self.__plc_adapter = plc_adapter

        self.__settings = SettingsProxy()
        self.__command = CameraCommand.IDLE

        self.__selected_product = None

        self.__sensors_trigger_event = sensor_trigger_event
        self.__plc_start_event = plc_start_event

        self.__references = None

        self.__processing_done_event = processing_done_event

        self.__first_render = True
        self.__render_results = None
        self._camera_reader = CameraReader(
            848,
            480,
            30,
            "138422075111",
            "C:/Users/evald/Documents/Coding/Projects/University/3D-IO-Desktop/desktop_app/services/camera/configs/camera/no_auto_exp_second_peak.json",
        )
        self.__result_visualizer = ResultVisualizer()

    def __init_services(self):
        self.__plc_result_writer = PlcResultWriter(self.__plc_adapter)
        self.__plc_result_writer.init_data()
        self.__result_visualizer.create()

    def update_settings(self, product_model):
        if (
            self.__selected_product is not None
            and self.__selected_product.model == product_model
        ):

            logger.info("[Camera Service] Settings updated for: " + str(product_model))
            self.__settings.load(settings_reader.read_settings(product_model))

    # TODO: Use strategy factory -> Detection / Model creation or other type
    # of processing strategy choice mode
    def set_product(self, product_type: int):
        print("Product type: ", product_type)
        if product_type is not None:
            logger.info(
                "[Camera Service] Setting product: "
                + str(ProductType(product_type).name)
            )
            self.__selected_product = product_helper.get_product_by_type(product_type)
            print("Selected product: ", self.__selected_product)

            self.update_settings(self.__selected_product.model)
            self.update_references()
            self.auto_set_command()

    # change command to mode / state apply appropriate state based upon product
    def auto_set_command(self):
        self.__command = (
            CameraCommand.DETECT
            if self.__selected_product.has_reference
            else CameraCommand.CREATE_REF
        )
        if self.__command is CameraCommand.DETECT:
            logger.info("[Camera Service] PREPARING TO DETECT")
        else:
            logger.info("[Camera Service] PREPARING TO CREATE RERERENCE")

    def update_references(self):
        self.__references = reference_creation.get_references(
            self.__selected_product.id
        )
        logger.info(
            "[Camera Service] Updating references, count: "
            + str(len(self.__references))
        )

    def create_reference(self):
        self.__command = CameraCommand.CREATE_REF

    def set_manual_reference(self):
        self.__command = CameraCommand.CREATE_REF
        if self.__selected_product is None:
            logger.warning("[Camera Service]: Product is not set")
            return

        self.__sensors_trigger_event.set()

    def set_manual_detect(self):
        self.__command = CameraCommand.DETECT
        # self.__sensors_trigger_event.set()
        if self.__selected_product is None:
            logger.warning("[Camera Service]: Product is not set")
            return

        self.__sensors_trigger_event.set()

    def _connect_camera(self) -> bool:
        return self._camera_reader.connect()

    def run(self):
        self.__running = True
        camera_connected = self._connect_camera()
        if not camera_connected:
            print("Camera is not connected leaving...")

        self.__init_services()
        self.set_product(ProductType.FMB110.value)
        self.__plc_start_event.set()

        try:
            while self.__running:
                if (
                    self.__selected_product is None
                    or self.__command is CameraCommand.IDLE
                ):
                    continue

                if self.__sensors_trigger_event.is_set():

                    # TODO: Get sample count from database
                    depth_frames, color_frames = self._camera_reader.read(
                        self.SAMPLE_COUNT
                    )

                    if self.__command is CameraCommand.CREATE_REF:
                        self.__run_reference_creation(depth_frames)
                    elif self.__command is CameraCommand.DETECT:
                        self.__run_detection(depth_frames)

                    self.__save_results()
                    self.__result_visualizer.update(self.__processing_results)
                    self.__clear_results()
                    self.__sensors_trigger_event.clear()

                self.__live_view()
                self.__stream_frames()
                time.sleep(0.001)
        finally:
            self.__running = False
            self._camera_reader.disconnect()
            logger.info("[Camera Service] Stopping")

    # TODO: Create frame visualizer
    def __stream_frames(self):
        depth_frames, color_frames = self._camera_reader.read(1)

        color_image = np.asanyarray(color_frames[0].get_data())

        # Show images
        cv2.namedWindow("RealSense", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("RealSense", color_image)
        cv2.waitKey(1)

    # TODO: Create live visualizer class
    def __live_view(self):
        depth_frames, color_frames = self._camera_reader.read(1)

        if int(self.__settings.get("live_view")) == 0:
            self.__visualizer.destroy()
            return

        position = int(self.__settings.get("camera_to_view"))
        frames = self.__camera_post_processing(depth_frames)
        self.__visualize_camera_view(frames)

    def __print_results(self):
        for key in sorted(self.__processing_results):
            print("[", key, "]", " = ", self.__processing_results[key])

    def __save_results(self):
        if self.__command is CameraCommand.DETECT:
            self.__save_detection_results()
        elif self.__command is CameraCommand.CREATE_REF:
            self.__save_reference_creation_results()
            product_helper.update_has_reference(self.__selected_product.id)
            self.set_product(self.__selected_product.product_type)

    def __clear_results(self):
        self.__processing_results.clear()
        self.__processing_results_db[:] = []

    @timing
    def __save_detection_results(self):
        for result in self.__processing_results_db:
            result_helper.add(result.scan_number, result.datetime, result.product_id)

    def __save_reference_creation_results(self):
        reference_exists = self.__selected_product.has_reference

        if reference_exists:
            for reference in self.__processing_results_db:
                reference_id = reference_helper.get_reference(
                    reference.position,
                    reference.row_position,
                    self.__selected_product.id,
                    0,
                )
                for corner in reference.corners:
                    corner_helper.update_corner(
                        corner.position, corner.avg_height, reference_id
                    )
        else:
            for reference in self.__processing_results_db:
                reference_id = reference_helper.add_reference(
                    reference.position,
                    reference.row_position,
                    self.__selected_product.id,
                    0,
                )
                for corner in reference.corners:
                    corner_helper.add_corner(
                        corner.position, corner.avg_height, reference_id
                    )

    @timing
    def __camera_post_processing(
        self, depth_frames: List[rs.depth_frame]
    ) -> List[rs.depth_frame]:
        frames = []

        for depth_frame in depth_frames:
            frame = Camera.apply_threshold_filter(
                depth_frame,
                self.__settings.get("depth_from"),
                self.__settings.get("depth_to"),
            )
            frame = Camera.apply_temporal_filter(frame)
            frames.append(frame)

        return frames

    def __run_detection(self, depth_frames: List[rs.depth_frame]):
        logger.info(
            "[Camera Service] Running clustering processing strategy. Detecting."
        )
        frames = self.__camera_post_processing(depth_frames)
        self.__render_results = clustering_detection.detect(
            frames[0],
            frames,
            0,
            self._camera_reader.intrinsics(),
            self.__settings,
            self.__references,
            self.__selected_product,
            self.__processing_results,
            self.__processing_results_db,
            self.DETECTION_RESULT_FOLDER,
        )

    def __run_reference_creation(self, depth_frames: List[rs.depth_frame]):
        logger.info(
            "[Camera Service] Running clustering processing strategy. Creating Reference."
        )
        frames = self.__camera_post_processing(depth_frames)

        self.__render_results = clustering_reference_creation.create(
            frames[0],
            frames,
            0,
            self._camera_reader.intrinsics(),
            self.__settings,
            self.__selected_product,
            self.__processing_results,
            self.__processing_results_db,
            self.REFERENCE_RESULT_FOLDER,
        )

    def __visualize_camera_view(self, depth_frames: List[rs.depth_frame]):
        cloud = cloud_processing.process_cloud(
            self._camera_reader.intrinsics(), depth_frames[0], self.__settings
        )

        (
            cloud_to_process,
            original_cloud,
        ) = cloud_processing.check_special_case_pre_processing(
            cloud, self.__selected_product, self.__settings, 0
        )

        row_start, take_rows = row_helper.get_camera_rows(0, self.__selected_product)

        original_cloud = copy.deepcopy(cloud_to_process)
        self.__render_results = cloud_processing.extract_products_from_cloud(
            cloud_to_process,
            self.__settings,
            row_start,
            take_rows,
            self.__selected_product,
            original_cloud=original_cloud,
            camera_pos=0,
        )

        final_cloud = utils.sum_points_colors_to_cloud(self.__render_results)

        if self.__first_render:
            self.__visualizer.create_window()
            self.__visualizer.add_cloud(final_cloud)
        else:
            self.__visualizer.update_cloud(final_cloud)

        self.__first_render = False

    def running(self) -> bool:
        return self.__running

    def stop(self):
        self.__running = False
        self._camera_reader.disconnect()
        self.__command = CameraCommand.IDLE
