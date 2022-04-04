import pyrealsense2 as rs
import json
import time

from ...common.logger import logger
from typing import Tuple


class Camera(object):
    def __init__(self, config_file: str, width: int, height: int):
        self.__width = width
        self.__height = height

        self.__config = rs.config
        self.__config_file = config_file

        self.__pipeline = rs.pipeline
        self.__advanced_mode = rs.rs400_advanced_mode
        self.__load_delay = 7

        self.__align = rs.align

        self.run = False

        self.__fps = 30
        self.__depth_fps = 30
        self.__depth_frame_saver = DepthFrameSaver(1)

        self.__disparity_shift = 0
        self.__dispose_frames_for_stabilization = 30

    def start(self):
        self.__run = True
        self.__pipeline.start()

    def stop(self):
        self.__run = False

    def init_configurations(self):
        self.__pipeline = rs.pipeline()

        self.__create_configure()

        self.__configure_advanced()

    def read_frames(self) -> Tuple[rs.depth_frame, bool]:
        self.__align_to_stream(rs.stream.depth)
        self.__stabilize_exposure()

        try:
            while self.__run:
                try:
                    frames = self.__pipeline.wait_for_frames()
                except Exception as ex:
                    logger.error("[Camera] Error occured waiting for frames: ", ex)
                    continue

                # aligned_frames = self.__align.process(frames)

                depth_frame = frames.get_depth_frame()

                if not depth_frame:
                    continue

                yield depth_frame, self.__run
        finally:
            self.__pipeline.stop()

    @staticmethod
    def post_process_depth_frame(
        depth_frame, decimation, spatial, hole_filling, threshold_depth
    ):
        assert depth_frame.is_depth_frame()

        filtered_frame = depth_frame

        if threshold_depth[0] == 1:
            filtered_frame = Camera.apply_threshold_filter(
                filtered_frame, threshold_depth
            )

        if decimation[0] == 1:
            filtered_frame = Camera.apply_decimation_filter(filtered_frame, decimation)

        if spatial[0] == 1:
            filtered_frame = Camera.apply_spatial_filter(filtered_frame, decimation)

        if hole_filling[0] == 1:
            filtered_frame = Camera.apply_hole_filling_filter(
                filtered_frame, decimation
            )

        return filtered_frame

    @staticmethod
    def apply_decimation_filter(frame, parameters):
        filter = rs.decimation_filter()
        filter_magnitude = rs.option.filter_magnitude
        filter.set_option(filter_magnitude, parameters[1])
        filtered_frame = filter.process(frame)

        return filtered_frame

    @staticmethod
    def apply_spatial_filter(frame, parameters):
        filter = rs.spatial_filter()

        filter_magnitude = rs.option.filter_magnitude
        filter_smooth_alpha = rs.option.filter_smooth_alpha
        filter_smooth_delta = rs.option.filter_smooth_delta
        filter_holes_fill = rs.option.holes_fill

        filter.set_option(filter_magnitude, parameters[1])
        filter.set_option(filter_smooth_alpha, parameters[2])
        filter.set_option(filter_smooth_delta, parameters[3])
        filter.set_option(filter_holes_fill, parameters[4])

        filtered_frame = filter.process(frame)

        return filtered_frame

    @staticmethod
    def apply_hole_filling_filter(frame, hole_fill: int = 0):
        filter = rs.hole_filling_filter()

        filter_holes_fill = rs.option.holes_fill

        filter.set_option(filter_holes_fill, hole_fill)

        filtered_frame = filter.process(frame)

        return filtered_frame

    @staticmethod
    def apply_threshold_filter(frame, depth_from: float, depth_to: float):
        filter = rs.threshold_filter()

        filter_min_dist = rs.option.min_distance
        filter_max_dist = rs.option.max_distance

        filter.set_option(filter_min_dist, depth_from)
        filter.set_option(filter_max_dist, depth_to)

        filtered_frame = filter.process(frame)

        return filtered_frame

    @staticmethod
    def apply_temporal_filter(
        frame, smooth_alpha: float = 0.4, smooth_delta: float = 20
    ):
        filter = rs.temporal_filter()

        filter_smooth_alpha = rs.option.filter_smooth_alpha
        filter_smooth_delta = rs.option.filter_smooth_delta

        filter.set_option(filter_smooth_alpha, smooth_alpha)
        filter.set_option(filter_smooth_delta, smooth_delta)

        filtered_frame = filter.process(frame)

        return filtered_frame

    def __align_to_stream(self, stream_to_align: rs.stream):
        self.__align = rs.align(stream_to_align)
        self.__align.set_option(rs.option.frames_queue_size, 2)

    def __stabilize_exposure(self):
        for _ in range(self.__dispose_frames_for_stabilization):
            frames = self.__pipeline.wait_for_frames()

    def __create_configure(self):
        config = rs.config()

        logger.info(
            "[Camera] Creating configuration: "
            + str(self.__width)
            + "x"
            + str(self.__height)
            + ", RGB FPS: "
            + str(self.__fps)
            + ", DEPTH FPS: "
            + str(self.__depth_fps),
        )
        config.enable_stream(
            rs.stream.depth,
            self.__width,
            self.__height,
            rs.format.z16,
            self.__depth_fps,
        )

        config.enable_stream(
            rs.stream.color, self.__width, self.__height, rs.format.bgr8, self.__fps
        )

        self.__config = config

    def __configure_advanced(self):
        advanced_config_string = self.__read_config()

        context = rs.context()

        device = context.query_devices()

        advanced_mode = rs.rs400_advanced_mode(device[0])

        advanced_mode.toggle_advanced_mode(True)

        logger.info(
            "[Camera] Loading advanced settings, waiting: "
            + str(self.__load_delay)
            + " seconds"
        )
        time.sleep(self.__load_delay)

        advanced_mode.load_json(advanced_config_string)

        self.__advanced_mode = advanced_mode

    def __read_config(self) -> str:
        json_dict = {}

        with open(self.__config_file) as file:
            for key, value in json.load(file).items():
                if "aux-param-disparityshift" in key:
                    self.__disparity_shift = int(value)

                json_dict[key] = value
        return str(json_dict).replace("'", '"')

    def set_sync(self):
        context = rs.context()

        device = context.query_devices()[0]

        device.first_depth_sensor().set_option(rs.option.inter_cam_sync_mode, 10)

    def get_active_profile(self) -> rs.pipeline_profile:
        return self.__pipeline.get_active_profile()

    def get_intrinsic(self) -> rs.intrinsics:
        stream_profile = self.get_active_profile().get_stream(rs.stream.depth)

        return stream_profile.as_video_stream_profile().get_intrinsics()

    def get_distance(self, distance: float, clip_value: float) -> float:
        distance = ((distance / 10) - clip_value) / self.get_depth_scale()

        return distance

    def get_depth_scale(self) -> float:
        depth_sensor = self.get_active_profile().get_device().first_depth_sensor()

        depth_scale = depth_sensor.get_depth_scale()

        return depth_scale

    def __del__(self):
        self.stop()
