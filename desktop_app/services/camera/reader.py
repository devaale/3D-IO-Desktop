from typing import Tuple, List
import pyrealsense2 as rs
import json
import time


class CameraReader:
    CONFIG_LOAD_TIME = 3

    def __init__(
        self, width: int, height: int, fps: int, serial_num: str, config_file: str
    ):
        self._fps = fps
        self._width = width
        self._height = height
        self._serial_num = serial_num

        self._config_file = config_file

        self._camera = None
        self._pipeline = None
        self._context = rs.context()

    def _get_serials(self):
        return [x.get_info(rs.camera_info.serial_number) for x in self._context.devices]

    def _find_camera(self, serial_num: str) -> rs.device:
        serials = self._get_serials()

        try:
            index = serials.index(serial_num)
            return self._context.devices[index]
        except:
            return None

    def _enable(self, camera: rs.device) -> Tuple[rs.pipeline, bool]:
        try:
            serial = camera.get_info(rs.camera_info.serial_number)
            pipeline = rs.pipeline(self._context)
            config = rs.config()
            config.enable_device(serial)
            config.enable_stream(
                rs.stream.depth,
                self._width,
                self._height,
                rs.format.z16,
                self._fps,
            )
            config.enable_stream(
                rs.stream.color,
                self._width,
                self._height,
                rs.format.bgr8,
                self._fps,
            )
            pipeline.start(config)
            return (pipeline, True)
        except:
            print("[Camera Reader] Failed to enable camera")
            return (None, False)

    def intrinsics(self) -> rs.intrinsics:
        stream = self._pipeline.get_active_profile().get_stream(rs.stream.depth)

        instrinsics = stream.as_video_stream_profile().get_intrinsics()

        return instrinsics

    def _configure(self, camera: rs.device) -> bool:
        try:
            config = self._read_config(self._config_file)

            mode = rs.rs400_advanced_mode(camera)

            mode.toggle_advanced_mode(True)

            time.sleep(self.CONFIG_LOAD_TIME)

            mode.load_json(config)

            return True
        except:
            return False

    def _read_config(self, config_file: str) -> str:
        json_dict = {}

        with open(config_file) as file:
            for key, value in json.load(file).items():
                json_dict[key] = value

        return str(json_dict).replace("'", '"')

    def read(self, frames: int) -> Tuple[List[rs.video_frame], List[rs.depth_frame]]:

        depth_frames = []
        color_frames = []

        for _ in range(frames):
            try:
                frames = self._pipeline.wait_for_frames()
            except Exception as ex:
                print(f"[Camera reader] Failed to read frames: {ex}")
                continue

            depth_frames.append(frames.get_depth_frame())
            color_frames.append(frames.get_color_frame())

        return depth_frames, color_frames

    def connect(self) -> bool:
        camera = self._find_camera(self._serial_num)

        if not camera:
            return False

        configured = self._configure(camera)

        if not configured:
            return False

        self._pipeline, enabled = self._enable(camera)

        if not enabled:
            return False

        return True

    def disconnect(self) -> bool:
        try:
            self._pipeline.stop()
        except:
            print("[Camera Manager] Camera: " + self._serial_num + ", is not started.")
