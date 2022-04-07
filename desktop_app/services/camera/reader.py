import time
import pyrealsense2 as rs
from typing import Tuple, List

from desktop_app.errors.camera import CameraError
from desktop_app.services.file.json import JSONFileService


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
        self._config = rs.config()
        self._context = rs.context()

    def read(self, frames: int) -> Tuple[List[rs.video_frame], List[rs.depth_frame]]:

        depth_frames = []
        color_frames = []

        for _ in range(frames):
            try:
                frames = self._pipeline.wait_for_frames()
            except Exception as error:
                raise CameraError(f"Failed to read frames {error}") from error

            depth_frames.append(frames.get_depth_frame())
            color_frames.append(frames.get_color_frame())

        return depth_frames, color_frames

    def connect(self) -> bool:
        try:
            camera = self._find_camera()

            _ = self._configure(camera)

            self._pipeline = self._enable(camera)

            return True
        except Exception as error:
            raise CameraError(f"Failed to connect {error}") from error

    def disconnect(self) -> bool:
        try:
            self._pipeline.stop()
            return True
        except Exception as error:
            raise CameraError(f"Failed to disconnect {error}") from error

    def _find_camera(self) -> rs.device:
        serials = self._get_serials()

        index = serials.index(self._serial_num)

        return self._context.devices[index]

    def _get_serials(self):
        return [x.get_info(rs.camera_info.serial_number) for x in rs.context().devices]

    def _configure(self, camera: rs.device) -> None:
        config = JSONFileService.read(self._config_file)

        mode = rs.rs400_advanced_mode(camera)

        mode.toggle_advanced_mode(True)

        time.sleep(self.CONFIG_LOAD_TIME)

        mode.load_json(config)

    def _enable(self, camera: rs.device) -> rs.pipeline:
        pipeline = rs.pipeline(self._context)
        serial = camera.get_info(rs.camera_info.serial_number)

        self._config.enable_device(serial)
        self._enable_stream(rs.stream.depth, rs.format.z16)
        self._enable_stream(rs.stream.color, rs.format.bgr8)

        pipeline.start(self._config)
        return pipeline

    def _enable_stream(self, stream: rs.stream, format: rs.format):
        self._config.enable_stream(stream, self._width, self._height, format, self._fps)

    def intrinsics(self) -> rs.intrinsics:
        stream = self._pipeline.get_active_profile().get_stream(rs.stream.depth)

        instrinsics = stream.as_video_stream_profile().get_intrinsics()

        return instrinsics
