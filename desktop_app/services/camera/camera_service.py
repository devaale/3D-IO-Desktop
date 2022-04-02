from datetime import datetime
from desktop_app.common.plc_adapter import PlcAdapter
from desktop_app.helpers import corner_helper, result_helper
from desktop_app.common.decorators import timing
from multiprocessing import Manager
from desktop_app.common import utils
from desktop_app.services.camera import (
    zone_detection,
    zone_reference_creation,
    row_helper,
)
from desktop_app.services.camera.data_saver import DataSaver
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.services.camera.models.enums.camera_command import CameraCommand
from desktop_app.models.enums.product import ProcessingStrategy, ProductType
from desktop_app.services.camera.camera_manager import CameraManager, DepthCamera

import copy
import os
import time
from threading import Event

from typing import *

from . import (
    reference_creation,
    clustering_reference_creation,
    clustering_detection,
    detection,
)

from .camera import Camera
from .processing import cloud_processing
from .visualization import Visualization

from ..settings import settings_reader
from .validation_service import (
    SingleColValidator,
    SinglePositionValidator,
    SingleRowValidator,
    ValidationService,
)
from ..plc.result_writer import PlcResultWriter

from ...helpers import reference_helper, product_helper, global_settings_helper
from ...common.logger import logger
from datetime import datetime

from desktop_app.services import camera
from .result_visualizer import ResultVisualizer
import numpy as np
import cv2


class CameraService:
    DIR_NAME = os.path.dirname(os.path.abspath(__file__))
    DETECTION_RESULT_FOLDER = "saved_data/detection/"
    REFERENCE_RESULT_FOLDER = "saved_data/reference/"

    CONFIG_FILE = os.path.join(DIR_NAME, "configs/camera/no_auto_exp_second_peak.json")

    CAMERA_RES_X = 848
    CAMERA_RES_Y = 480
    CAMERA_FRAME_RATE = 30

    SAMPLE_COUNT = 5
    MAX_SCAN_NUM = 1

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

        self.__model_zones = []

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

        self.__validation_service = ValidationService(
            [SinglePositionValidator(), SingleRowValidator(), SingleColValidator()]
        )

        self.__validation_continue_event = Event()
        self.__processing_done_event = processing_done_event

        self.__first_render = True
        self.__render_results = None
        self.__camera_manager = None
        self.__result_visualizer = ResultVisualizer()

    def __init_cameras(self):
        global_settings = global_settings_helper.get()
        self.__camera_manager = CameraManager(
            self.CONFIG_FILE, global_settings.camera_one_serial
        )
        self.__camera_manager.start_cameras()

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

    def set_manual_validation(self):
        validation_count = int(self.__settings.get("validation_count"))

        for _ in range(validation_count):
            self.__sensors_trigger_event.set()
            self.__validation_continue_event.wait()
            self.__validation_continue_event.clear()

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

    def __validate(self, cameras: List[DepthCamera]):
        self.__validation_service.run_validators(
            self.__processing_results,
            cameras,
            self.__selected_product,
            int(self.__settings.get("validation_count")),
        )

    def run(self):
        self.__running = True
        self.__init_cameras()
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

                    cameras = self.__camera_manager.export_frames(self.SAMPLE_COUNT)

                    for camera in cameras:
                        if self.__command is CameraCommand.CREATE_REF:
                            self.__run_reference_creation(camera)
                        elif self.__command is CameraCommand.DETECT:
                            self.__run_detection(camera)

                    self.__save_results()
                    self.__result_visualizer.update(self.__processing_results)
                    self.__clear_results()
                    self.__sensors_trigger_event.clear()

                self.__live_view()
                self.__stream_frames()
                time.sleep(0.001)
        finally:
            self.__running = False
            self.__camera_manager.stop_cameras()
            logger.info("[Camera Service] Stopping")

    def __stream_frames(self):
        cameras = self.__camera_manager.export_frames(1)

        color_image = np.asanyarray(cameras[0].color_buffer[0].get_data())

        color_colormap_dim = color_image.shape

        # Show images
        cv2.namedWindow("RealSense", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("RealSense", color_image)
        cv2.waitKey(1)

    def __live_view(self):
        cameras = self.__camera_manager.export_frames(1)

        if int(self.__settings.get("live_view")) == 0:
            self.__visualizer.destroy()
            return

        position = int(self.__settings.get("camera_to_view"))
        self.__camera_post_processing(cameras[position])
        self.__visualize_camera_view(cameras[position])

    def __print_results(self):
        for key in sorted(self.__processing_results):
            print("[", key, "]", " = ", self.__processing_results[key])

    @timing
    def __send_results(self, fake: bool = False):
        for key, value in self.__processing_results.items():
            if fake:
                self.__plc_result_writer.fake_write_result(key, value)
                continue
            self.__plc_result_writer.write_result(key, value)

        self.__plc_result_writer.write_done(True)
        self.__processing_done_event.set()

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
    def __camera_post_processing(self, camera: DepthCamera):
        for i in range(len(camera.buffer)):
            depth_from, depth_to = camera.get_depth_settings_keys()
            frame = Camera.apply_threshold_filter(
                camera.buffer[i],
                self.__settings.get(depth_from),
                self.__settings.get(depth_to),
            )
            frame = Camera.apply_temporal_filter(frame)
            camera.add_post_processed_frame(frame)

    def __run_reference_creation(self, camera: DepthCamera):
        self.__camera_post_processing(camera)
        # TODO: Refactor
        if (
            self.__selected_product.processing_type
            is ProcessingStrategy.CLUSTERING.value
        ):
            self.__run_reference_creation_clustering(camera)
        elif (
            self.__selected_product.processing_type
            is ProcessingStrategy.BOUNDING_BOX.value
        ):
            self.__run_reference_creation_bounding_box(camera)
        elif (
            self.__selected_product.processing_type
            is ProcessingStrategy.ZONE_STATISTICS.value
        ):
            self.__run_reference_creation_zones(camera)

    def __run_detection(self, camera: DepthCamera):
        self.__camera_post_processing(camera)

        if (
            self.__selected_product.processing_type
            is ProcessingStrategy.CLUSTERING.value
        ):
            self.__run_detection_clustering(camera)
        elif (
            self.__selected_product.processing_type
            is ProcessingStrategy.BOUNDING_BOX.value
        ):
            self.__run_detection_bounding_box(camera)
        elif (
            self.__selected_product.processing_type
            is ProcessingStrategy.ZONE_STATISTICS.value
        ):
            self.__run_detection_zones(camera)

    def __run_detection_clustering(self, camera: DepthCamera):
        logger.info(
            "[Camera Service] Running clustering processing strategy. Detecting."
        )
        self.__render_results = clustering_detection.detect(
            camera.post_processed_buffer[0],
            camera.post_processed_buffer,
            camera.position,
            camera.instrinsics,
            self.__settings,
            self.__references,
            self.__selected_product,
            self.__processing_results,
            self.__processing_results_db,
            self.DETECTION_RESULT_FOLDER,
        )

        if camera.position == 1:
            self.__print_results()

    def __run_detection_bounding_box(self, camera: DepthCamera):
        logger.info("[Camera Service] Running bounding box strategy. Detecting.")
        if self.__command is CameraCommand.DETECT:
            products, clusters = detection.extract_products_from_frame(
                camera.post_processed_buffer,
                1,
                camera.instrinsics,
                self.__settings,
                self.__selected_product,
            )

            self.__run_compare_refs(camera, products, clusters, 1)
            self.__print_results()
            # self.send_results_plc()
            self.__save_detection_results()

    @timing
    def __run_compare_refs(self, camera: DepthCamera, products, clusters):
        products = detection.compare_to_refs(
            camera.post_processed_buffer[0],
            camera.instrinsics,
            self.__settings,
            products,
            clusters,
            self.__references,
            self.__selected_product,
            1,
            self.__processing_results,
            self.__processing_results_db,
            self.DETECTION_RESULT_FOLDER,
        )

        return products

    def __run_detection_zones(self, camera: DepthCamera):
        logger.info(
            "[Camera Service] Running clustering processing strategy. Detecting."
        )

        zone_references = self.__model_zones[camera.position - 1]

        self.__render_results = zone_detection.detect(
            camera.post_processed_buffer[0],
            camera.post_processed_buffer,
            camera.position,
            camera.instrinsics,
            self.__settings,
            zone_references,
            self.__selected_product,
            1,
            self.__processing_results,
            self.__processing_results_db,
            self.DETECTION_RESULT_FOLDER,
        )

        if camera.position == 1:
            self.__print_results()

    def __run_reference_creation_zones(self, camera: DepthCamera):
        if camera.position == 0:
            self.__model_zones.clear()

        logger.info(
            "[Camera Service] Running zones rmse processing strategy. Creating Reference."
        )
        (
            self.__render_results,
            camera_position,
            zones_model,
        ) = zone_reference_creation.create(
            camera.post_processed_buffer[0],
            camera.post_processed_buffer,
            camera.position,
            camera.instrinsics,
            self.__settings,
            self.__selected_product,
            1,
            self.__processing_results,
            self.__processing_results_db,
            self.REFERENCE_RESULT_FOLDER,
        )

        self.__model_zones.append(zones_model)

        if camera.position == 1:
            self.__print_results()

    def __run_reference_creation_clustering(self, camera: DepthCamera):
        logger.info(
            "[Camera Service] Running clustering processing strategy. Creating Reference."
        )
        self.__render_results = clustering_reference_creation.create(
            camera.post_processed_buffer[0],
            camera.post_processed_buffer,
            camera.position,
            camera.instrinsics,
            self.__settings,
            self.__selected_product,
            self.__processing_results,
            self.__processing_results_db,
            self.REFERENCE_RESULT_FOLDER,
        )

        if camera.position == 1:
            self.__print_results()

    def __run_reference_creation_bounding_box(self, camera: DepthCamera):
        logger.info(
            "[Camera Service] Running bounding box processing strategy. Creating Reference."
        )
        self.__render_results = reference_creation.create(
            camera.buffer[0],
            camera.buffer,
            camera.instrinsics,
            self.__settings,
            self.__selected_product,
            1,
            self.__processing_results,
            self.__processing_results_db,
            self.REFERENCE_RESULT_FOLDER,
            True,
        )

        if camera.position == 1:
            self.__print_results()

    def __visualize_camera_view(self, camera: DepthCamera):
        cloud = cloud_processing.process_cloud(
            camera.instrinsics, camera.post_processed_buffer[0], self.__settings
        )

        (
            cloud_to_process,
            original_cloud,
        ) = cloud_processing.check_special_case_pre_processing(
            cloud, self.__selected_product, self.__settings, camera.position
        )

        row_start, take_rows = row_helper.get_camera_rows(
            camera.position, self.__selected_product
        )

        original_cloud = copy.deepcopy(cloud_to_process)
        self.__render_results = cloud_processing.extract_products_from_cloud(
            cloud_to_process,
            self.__settings,
            row_start,
            take_rows,
            self.__selected_product,
            original_cloud=original_cloud,
            camera_pos=camera.position,
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
        self.__camera_manager.stop_cameras()
        self.__command = CameraCommand.IDLE
