from numpy import product
from desktop_app.common import utils
from desktop_app.helpers import product_helper
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.models.enums.product import ProductType
import os
import time
from threading import Event

from typing import *

from desktop_app.errors.camera import CameraError
from desktop_app.services.camera.reader import CameraReader
from desktop_app.services.visualization.depth import Visualizer3D
from desktop_app.services.visualization.rgb import VisualizerRGB
from desktop_app.services.visualization.result import VisualizerResult
from desktop_app.services.processing.service import ProcessingService


class CameraService:

    # TODO: Export variable to appropriate bounds
    DIR_NAME = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(DIR_NAME, "configs/camera/no_auto_exp_second_peak.json")

    SAMPLE_COUNT = 5

    def __init__(self, sensor_trigger_event: Event, proc_service: ProcessingService):
        self._running = False
        self.connected = False

        self._results = dict()
        self._results_db = list()

        self._settings = SettingsProxy()

        self._trigger = sensor_trigger_event

        self._proc_service = ProcessingService()
        self._camera_reader = CameraReader(
            848,
            480,
            30,
            "823112061406",
            "C:/Users/evald/Documents/Coding/Projects/University/3D-IO-Desktop/desktop_app/services/camera/configs/camera/no_auto_exp_second_peak.json",
        )
        self._visualizer3D = Visualizer3D()
        self._visualizerRGB = VisualizerRGB()
        self._visualizer_result = VisualizerResult()

    def set_manual_reference(self):
        self._proc_service.detect = False
        self._trigger.set()

    def set_manual_detect(self):
        self._proc_service.detect = True
        self._trigger.set()

    def connect(self):
        try:
            self.connected = self._camera_reader.connect()
        except CameraError as error:
            self.connected = False
            print(error)

    def disconnect(self):
        try:
            self.connected = not self._camera_reader.disconnect()
        except CameraError as error:
            print(error)

    def run(self):
        self.connect()
        self._visualizer_result.create()

        try:
            while self.connected:
                if self._trigger.is_set():

                    # TODO: Get sample count from database
                    depth_frames = []
                    color_frames = []

                    try:
                        depth_frames, color_frames = self._camera_reader.read(
                            self.SAMPLE_COUNT
                        )
                    except CameraError as error:
                        print(error)
                        continue

                    self._proc_service.process(
                        depth_frames, self._camera_reader.intrinsics
                    )

                    # self.__save_results()
                    # self._visualizer_result.update(self._results)
                    # self.__clear_results()
                    self._trigger.clear()

                time.sleep(0.001)
        finally:
            self.disconnect()

    def _visualize(self):
        depth_frames, color_frames = self._camera_reader.read(1)
        results_cloud = self.__run_detection(depth_frames)
        self._visualizer3D.render(utils.sum_points_colors_to_cloud(results_cloud))
        self._visualizerRGB.render(color_frames[0])

    # @timing
    # def __camera_post_processing(
    #     self, depth_frames: List[rs.depth_frame]
    # ) -> List[rs.depth_frame]:
    #     frames = []

    #     for depth_frame in depth_frames:
    #         frame = Camera.apply_threshold_filter(
    #             depth_frame,
    #             self._settings.get("depth_from"),
    #             self._settings.get("depth_to"),
    #         )
    #         frame = Camera.apply_temporal_filter(frame)
    #         frames.append(frame)

    #     return frames

    # def __run_detection(self, depth_frames: List[rs.depth_frame]):
    #     logger.info(
    #         "[Camera Service] Running clustering processing strategy. Detecting."
    #     )
    #     frames = self.__camera_post_processing(depth_frames)
    #     results_cloud = clustering_detection.detect(
    #         frames[0],
    #         frames,
    #         0,
    #         self._camera_reader.intrinsics(),
    #         self._settings,
    #         self._references,
    #         self.__selected_product,
    #         self._results,
    #         self._results_db,
    #         self.DETECTION_RESULT_FOLDER,
    #     )

    #     return results_cloud

    # def __run_reference_creation(self, depth_frames: List[rs.depth_frame]):
    #     logger.info(
    #         "[Camera Service] Running clustering processing strategy. Creating Reference."
    #     )
    #     frames = self.__camera_post_processing(depth_frames)

    #     results_cloud = clustering_reference_creation.create(
    #         frames[0],
    #         frames,
    #         0,
    #         self._camera_reader.intrinsics(),
    #         self._settings,
    #         self.__selected_product,
    #         self._results,
    #         self._results_db,
    #         self.REFERENCE_RESULT_FOLDER,
    #     )

    #     return results_cloud

    def running(self) -> bool:
        return self._running

    def stop(self):
        self._running = False
        self._camera_reader.disconnect()
