from typing import List
import pyrealsense2 as rs
import numpy as np
import cv2 as cv
from desktop_app.common.logger import logger
import time
import json


class DepthCamera:
    def __init__(self, serial, position: int = 0):
        self.buffer = []
        self.color_buffer = []
        self.post_processed_buffer = []

        self.serial = serial
        self.position = position
        self.instrinsics = None

    def add_frame(self, depth_frame: rs.depth_frame):
        self.buffer.append(depth_frame)

    def add_color_frame(self, color_frame):
        self.color_buffer.append(color_frame)

    def add_post_processed_frame(self, frame: rs.frame):
        self.post_processed_buffer.append(frame)

    def set_instrinsics(self, intrinsics):
        self.instrinsics = intrinsics

    def auto_set_position(self, camera_one_serial: str):
        self.position = 0 if self.compare_serial(camera_one_serial) else 1

    def get_depth_settings_keys(self):
        return (
            ("depth_from", "depth_to")
            if self.position == 0
            else ("depth_from_2", "depth_to_2")
        )

    def compare_serial(self, other_serial: str) -> bool:
        return self.serial == other_serial


class CameraManager:
    def __init__(self, config_file: str, camera_one_serial: str):
        self.resolution_width = 848
        self.resolution_height = 480
        self.camera_one_serial = "138422075111"
        self.frame_rate = 30

        self.__config_load_time = 3
        self.__config_file = config_file

        self.__pipelines = []
        self.__cameras: List[DepthCamera] = []

    def find_devices(self):
        ctx = rs.context()
        serials = []

        if len(ctx.devices) > 0:
            for dev in ctx.devices:
                logger.info(
                    "[Camera Manager] Found device: "
                    + str(dev.get_info(rs.camera_info.name))
                    + str(dev.get_info(rs.camera_info.serial_number))
                )

                self.__configure_advanced(dev)

                serials.append(dev.get_info(rs.camera_info.serial_number))
        else:
            print("[Camera Manager] No Intel Device connected")

        return serials, ctx

    def enable_devices(
        self, serials, ctx, resolution_width=848, resolution_height=480, frame_rate=30
    ):
        pipelines = []
        for serial in serials:
            try:
                pipe = rs.pipeline(ctx)
                cfg = rs.config()
                cfg.enable_device(serial)
                cfg.enable_stream(
                    rs.stream.depth,
                    resolution_width,
                    resolution_height,
                    rs.format.z16,
                    frame_rate,
                )
                cfg.enable_stream(
                    rs.stream.color,
                    resolution_width,
                    resolution_height,
                    rs.format.bgr8,
                    frame_rate,
                )
                pipe.start(cfg)
                pipelines.append([serial, pipe])
            except:
                logger.error("[Camera Manager] Failed to enable cameras")

        return pipelines

    def add_frame(self, depth_frame: rs.depth_frame, serial: str) -> int:
        for i in range(len(self.__cameras)):
            if self.__cameras[i].serial == serial:
                self.__cameras[i].add_frame(depth_frame)

    def add_color_frame(self, color_frame, serial: str) -> int:
        for i in range(len(self.__cameras)):
            if self.__cameras[i].serial == serial:
                self.__cameras[i].add_color_frame(color_frame)

    def set_intrinsics(self, pipe, serial: str):
        for i in range(len(self.__cameras)):
            if self.__cameras[i].serial == serial:
                stream_profile = pipe.get_active_profile().get_stream(rs.stream.depth)

                instrinsics = stream_profile.as_video_stream_profile().get_intrinsics()

                self.__cameras[i].set_instrinsics(instrinsics)

    def __configure_advanced(self, device):
        advanced_config_string = self.__read_config(self.__config_file)

        advanced_mode = rs.rs400_advanced_mode(device)

        advanced_mode.toggle_advanced_mode(True)

        logger.info(
            "[Camera] Loading advanced settings"
            + str(device)
            + " waiting: "
            + str(self.__config_load_time)
            + " seconds"
        )
        time.sleep(self.__config_load_time)

        advanced_mode.load_json(advanced_config_string)

    def __read_config(self, config_file: str) -> str:
        json_dict = {}

        with open(config_file) as file:
            for key, value in json.load(file).items():
                json_dict[key] = value

        return str(json_dict).replace("'", '"')

    def read_frames(self, pipelines):
        depth_frames = []
        color_frames = []

        for (device, pipe) in pipelines:
            frames = pipe.wait_for_frames()

            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame:
                logger.warning("[Camera Manager] Invalid depth frame.")
                continue

            self.add_frame(depth_frame, device)
            self.add_color_frame(color_frame, device)

            self.set_intrinsics(pipe, device)

            depth_frames.append(depth_frame)
            color_frames.append(color_frame)

        return depth_frames

    def find_camera_positions(self, serials):
        cameras = []

        for serial in serials:
            camera = DepthCamera(serial)
            camera.auto_set_position(self.camera_one_serial)

            logger.info(
                "[Camera Manager] Found camera's ("
                + serial
                + ") position: ["
                + str(camera.position)
                + "]"
            )
            cameras.append(camera)

        return cameras

    def start_cameras(self):
        serials, ctx = self.find_devices()

        self.__cameras = self.find_camera_positions(serials)

        self.__cameras.sort(key=lambda x: x.position, reverse=False)

        self.__pipelines = self.enable_devices(
            serials, ctx, self.resolution_width, self.resolution_height, self.frame_rate
        )

    def stop_cameras(self):
        for (device, pipe) in self.__pipelines:
            try:
                pipe.stop()
            except Exception:
                logger.warning(
                    "[Camera Manager] Camera: " + str(device) + ", is not started."
                )

    def clear_buffers(self):
        for camera in self.__cameras:
            camera.buffer.clear()
            camera.color_buffer.clear()
            camera.post_processed_buffer.clear()

    def export_frames(self, frame_count):
        self.clear_buffers()

        for _ in range(frame_count):
            frames = self.read_frames(self.__pipelines)

        return self.__cameras
